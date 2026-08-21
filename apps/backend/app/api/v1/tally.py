# CredFlow Backend - Tally Sync Endpoints

from datetime import datetime, timezone
from uuid import UUID
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.config import settings
from app.core.database import get_db, get_tenant_db
from app.core.security import verify_api_key
from app.core.tenant import get_current_tenant_id
from app.models import TallyCompany, SyncLog, Customer, Invoice, Payment
from app.worker.celery_app import celery_app

router = APIRouter()


# Request/Response Models
class SyncCustomer(BaseModel):
    tally_ledger_guid: str
    name: str
    gstin: Optional[str] = None
    address: Optional[dict] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    credit_limit: Optional[float] = None
    payment_terms_days: Optional[int] = None


class SyncInvoice(BaseModel):
    tally_voucher_id: str
    voucher_number: str
    voucher_date: str  # YYYY-MM-DD
    due_date: str  # YYYY-MM-DD
    customer_tally_guid: str
    amount: float
    tax_amount: float
    total_amount: float
    gstin: Optional[str] = None
    place_of_supply: Optional[str] = None


class SyncPayment(BaseModel):
    tally_receipt_id: str
    invoice_tally_voucher_id: str
    customer_tally_guid: str
    amount: float
    payment_date: str  # YYYY-MM-DD
    payment_mode: str = "bank_transfer"
    reference_number: Optional[str] = None


class TallySyncRequest(BaseModel):
    company_id: str  # Tally company GUID
    synced_at: datetime
    customers: List[SyncCustomer] = []
    invoices: List[SyncInvoice] = []
    payments: List[SyncPayment] = []


class TallySyncResponse(BaseModel):
    sync_id: UUID
    status: str
    message: str


class SyncLogResponse(BaseModel):
    id: UUID
    company_id: UUID
    entity_type: str
    records_processed: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime]


class TallyCompanyResponse(BaseModel):
    id: UUID
    tally_guid: str
    name: str
    financial_year_start: str
    last_synced_at: Optional[datetime]
    agent_name: str


@router.post("/sync", status_code=status.HTTP_202_ACCEPTED, response_model=TallySyncResponse)
async def receive_tally_sync(
    request: TallySyncRequest,
    db: AsyncSession = Depends(get_db),
    x_agent_key: Optional[str] = Header(None, alias="X-Agent-Key"),
):
    """Receive sync payload from Tally agent."""
    # Verify agent API key
    if not x_agent_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "MISSING_API_KEY",
                    "message": "X-Agent-Key header required",
                },
            },
        )

    # Verify key
    import hashlib
    key_hash = hashlib.sha256(x_agent_key.encode()).hexdigest()

    from app.models import Agent
    result = await db.execute(
        select(Agent).where(Agent.api_key_hash == key_hash).where(Agent.deleted_at.is_(None))
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_API_KEY",
                    "message": "Invalid agent API key",
                },
            },
        )

    # Find or create tally company
    result = await db.execute(
        select(TallyCompany).where(TallyCompany.tally_guid == request.company_id).where(TallyCompany.tenant_id == agent.tenant_id)
    )
    tally_company = result.scalar_one_or_none()

    if not tally_company:
        # Create new company record
        tally_company = TallyCompany(
            tenant_id=agent.tenant_id,
            agent_id=agent.id,
            tally_guid=request.company_id,
            name=request.company_id,  # Will be updated with actual name from customer data
            financial_year_start=datetime.now().date(),
        )
        db.add(tally_company)
        await db.flush()

    # Create sync log
    sync_log = SyncLog(
        tenant_id=agent.tenant_id,
        agent_id=agent.id,
        company_id=tally_company.id,
        entity_type="mixed",
        records_processed=len(request.customers) + len(request.invoices) + len(request.payments),
        status="processing",
    )
    db.add(sync_log)
    await db.flush()

    # Enqueue background processing
    task = celery_app.send_task(
        "process_tally_sync",
        args=[str(sync_log.id), request.model_dump()],
        queue="tally",
    )

    await db.commit()

    return TallySyncResponse(
        sync_id=sync_log.id,
        status="queued",
        message="Sync queued for processing",
    )


@router.get("/companies", response_model=List[TallyCompanyResponse])
async def list_tally_companies(
    db: AsyncSession = Depends(get_tenant_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """List Tally companies for current tenant."""
    result = await db.execute(
        select(TallyCompany, func.coalesce(func.max(SyncLog.started_at), None).label("last_sync"))
        .outerjoin(SyncLog, TallyCompany.id == SyncLog.company_id)
        .where(TallyCompany.tenant_id == tenant_id)
        .where(TallyCompany.deleted_at.is_(None))
        .group_by(TallyCompany.id)
    )
    rows = result.all()

    return [
        TallyCompanyResponse(
            id=row.TallyCompany.id,
            tally_guid=row.TallyCompany.tally_guid,
            name=row.TallyCompany.name,
            financial_year_start=row.TallyCompany.financial_year_start.isoformat() if row.TallyCompany.financial_year_start else "",
            last_synced_at=row.last_sync,
            agent_name=row.TallyCompany.agent.name if row.TallyCompany.agent else "Unknown",
        )
        for row in rows
    ]


@router.get("/sync-logs", response_model=List[SyncLogResponse])
async def get_sync_logs(
    db: AsyncSession = Depends(get_tenant_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    company_id: Optional[UUID] = None,
    status_filter: Optional[str] = None,
    limit: int = 50,
    cursor: Optional[str] = None,
):
    """Get sync history."""
    from app.core.database import get_db_session
    
    query = select(SyncLog).where(SyncLog.tenant_id == tenant_id)
    
    if company_id:
        query = query.where(SyncLog.company_id == company_id)
    if status_filter:
        query = query.where(SyncLog.status == status_filter)
    
    query = query.order_by(SyncLog.started_at.desc())
    
    if cursor:
        # Decode cursor
        import base64
        import json
        try:
            cursor_data = json.loads(base64.b64decode(cursor).decode())
            cursor_time = datetime.fromisoformat(cursor_data["started_at"])
            query = query.where(SyncLog.started_at < cursor_time)
        except Exception:
            pass
    
    query = query.limit(limit + 1)
    result = await db.execute(query)
    logs = result.scalars().all()
    
    has_more = len(logs) > limit
    if has_more:
        logs = logs[:limit]
        next_cursor = base64.b64encode(json.dumps({"started_at": logs[-1].started_at.isoformat()}).encode()).decode()
    else:
        next_cursor = None
    
    return [
        SyncLogResponse(
            id=log.id,
            company_id=log.company_id,
            entity_type=log.entity_type,
            records_processed=log.records_processed,
            status=log.status,
            started_at=log.started_at,
            completed_at=log.completed_at,
        )
        for log in logs
    ]


@router.post("/sync/trigger")
async def trigger_manual_sync(
    company_id: UUID,
    db: AsyncSession = Depends(get_tenant_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Manually trigger sync for a company."""
    # Verify company belongs to tenant
    result = await db.execute(
        select(TallyCompany).where(TallyCompany.id == company_id).where(TallyCompany.tenant_id == tenant_id)
    )
    tally_company = result.scalar_one_or_none()

    if not tally_company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "COMPANY_NOT_FOUND",
                    "message": "Tally company not found",
                },
            },
        )

    # Create sync log
    sync_log = SyncLog(
        tenant_id=tenant_id,
        agent_id=tally_company.agent_id,
        company_id=tally_company.id,
        entity_type="manual",
        records_processed=0,
        status="processing",
    )
    db.add(sync_log)
    await db.flush()

    # Enqueue task
    from app.worker.celery_app import celery_app
    celery_app.send_task(
        "trigger_manual_sync",
        args=[str(sync_log.id), str(company_id)],
        queue="tally",
    )

    await db.commit()

    return {"success": True, "data": {"sync_id": str(sync_log.id), "status": "triggered"}}
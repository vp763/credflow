# CredFlow Backend - Agent Endpoints

from datetime import datetime, timezone
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.config import settings
from app.core.database import get_db
from app.core.security import generate_api_key, verify_api_key
from app.core.tenant import get_current_tenant_id
from app.models import Agent, TallyCompany, SyncLog

router = APIRouter()


# Request/Response Models
class AgentRegisterRequest(BaseModel):
    name: str
    tally_url: str = "http://localhost:9000"
    sync_interval_minutes: int = 15


class AgentRegisterResponse(BaseModel):
    id: UUID
    name: str
    api_key: str  # Only returned once!
    status: str


class AgentHeartbeatRequest(BaseModel):
    status: str = "online"
    version: Optional[str] = None
    last_sync_at: Optional[datetime] = None


class AgentHeartbeatResponse(BaseModel):
    agent_id: UUID
    server_time: datetime
    config_update_available: bool = False


class AgentResponse(BaseModel):
    id: UUID
    name: str
    status: str
    last_heartbeat_at: Optional[datetime]
    version: Optional[str]
    created_at: datetime


class AgentListResponse(BaseModel):
    agents: list[AgentResponse]
    total: int


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=AgentRegisterResponse)
async def register_agent(
    request: AgentRegisterRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Register a new Tally agent."""
    # Check if tenant already has an agent (MVP: one agent per tenant)
    existing = await db.execute(
        select(Agent).where(Agent.tenant_id == tenant_id).where(Agent.deleted_at.is_(None))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "AGENT_EXISTS",
                    "message": "Tenant already has an agent registered",
                },
            },
        )

    # Generate API key
    plain_key, key_hash = generate_api_key()

    # Create agent
    agent = Agent(
        tenant_id=tenant_id,
        name=request.name,
        api_key_hash=key_hash,
        status="inactive",
        config={
            "tally_url": request.tally_url,
            "sync_interval_minutes": request.sync_interval_minutes,
        },
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    return AgentRegisterResponse(
        id=agent.id,
        name=agent.name,
        api_key=plain_key,  # Only returned once!
        status=agent.status,
    )


@router.post("/heartbeat", response_model=AgentHeartbeatResponse)
async def agent_heartbeat(
    request: AgentHeartbeatRequest,
    db: AsyncSession = Depends(get_db),
    x_agent_key: str = Header(..., alias="X-Agent-Key"),
):
    """Agent heartbeat - called every 5 minutes."""
    # Verify API key
    import hashlib
    key_hash = hashlib.sha256(x_agent_key.encode()).hexdigest()

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

    # Update heartbeat
    agent.last_heartbeat_at = datetime.now(timezone.utc)
    agent.status = "active" if request.status == "online" else "offline"
    if request.version:
        agent.version = request.version

    await db.commit()

    return AgentHeartbeatResponse(
        agent_id=agent.id,
        server_time=datetime.now(timezone.utc),
        config_update_available=False,  # TODO: check for updates
    )


@router.get("", response_model=AgentListResponse)
async def list_agents(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    status_filter: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
):
    """List agents for current tenant."""
    query = select(Agent).where(Agent.tenant_id == tenant_id).where(Agent.deleted_at.is_(None))

    if status_filter:
        query = query.where(Agent.status == status_filter)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Get paginated results
    query = query.order_by(Agent.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    agents = result.scalars().all()

    return AgentListResponse(
        agents=[
            AgentResponse(
                id=a.id,
                name=a.name,
                status=a.status,
                last_heartbeat_at=a.last_heartbeat_at,
                version=a.version,
                created_at=a.created_at,
            )
            for a in agents
        ],
        total=total,
    )


@router.delete("/{agent_id}")
async def deactivate_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Deactivate agent."""
    result = await db.execute(
        select(Agent)
        .where(Agent.id == agent_id)
        .where(Agent.tenant_id == tenant_id)
        .where(Agent.deleted_at.is_(None))
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "AGENT_NOT_FOUND",
                    "message": "Agent not found",
                },
            },
        )

    agent.status = "inactive"
    agent.deleted_at = datetime.now(timezone.utc)
    await db.commit()

    return {"success": True, "data": {"message": "Agent deactivated"}}
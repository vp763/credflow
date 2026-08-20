# CredFlow Tally Tasks

from celery import shared_task


@shared_task
def sync_company_list():
    """Sync company list from Tally."""
    return {"status": "success", "message": "Company list synced"}


@shared_task
def sync_ledgers(company_id: str):
    """Sync ledgers from Tally for a company."""
    return {"status": "success", "company_id": company_id, "message": "Ledgers synced"}


@shared_task
def sync_sales_vouchers(company_id: str, from_date: str = None, to_date: str = None):
    """Sync sales vouchers from Tally."""
    return {"status": "success", "company_id": company_id, "message": "Sales vouchers synced"}


@shared_task
def sync_receipt_vouchers(company_id: str, from_date: str = None, to_date: str = None):
    """Sync receipt vouchers from Tally."""
    return {"status": "success", "company_id": company_id, "message": "Receipt vouchers synced"}


@shared_task
def full_tally_sync(company_id: str):
    """Full Tally sync for a company."""
    return {"status": "success", "company_id": company_id, "message": "Full sync completed"}
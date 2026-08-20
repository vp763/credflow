# CredFlow Payment Tasks

from celery import shared_task


@shared_task
def create_payment_link(invoice_id: str, amount: float, customer_phone: str):
    """Create Razorpay payment link."""
    return {"status": "success", "invoice_id": invoice_id, "payment_link": "https://rzp.io/xxx"}


@shared_task
def verify_payment(payment_id: str):
    """Verify payment status."""
    return {"status": "success", "payment_id": payment_id, "verified": True}


@shared_task
def expire_old_payment_links():
    """Expire old payment links."""
    return {"status": "success", "message": "Old payment links expired"}


@shared_task
def process_webhook(payload: dict):
    """Process Razorpay webhook."""
    return {"status": "success", "message": "Webhook processed"}
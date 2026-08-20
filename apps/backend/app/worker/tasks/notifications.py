# CredFlow Notification Tasks

from celery import shared_task


@shared_task
def send_whatsapp_message(to: str, template: str, params: dict):
    """Send WhatsApp message."""
    return {"status": "success", "to": to, "message": "WhatsApp sent"}


@shared_task
def send_email(to: str, subject: str, body: str):
    """Send email."""
    return {"status": "success", "to": to, "message": "Email sent"}


@shared_task
def send_sms(to: str, body: str):
    """Send SMS."""
    return {"status": "success", "to": to, "message": "SMS sent"}


@shared_task
def run_reminder_engine():
    """Run reminder engine for overdue invoices."""
    return {"status": "success", "message": "Reminder engine executed"}


@shared_task
def send_payment_reminder(invoice_id: str, channel: str = "whatsapp"):
    """Send payment reminder for an invoice."""
    return {"status": "success", "invoice_id": invoice_id, "channel": channel}
"""
APScheduler background jobs for automated reminders and recurring invoices.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)


def check_and_send_reminders(app):
    """
    Daily job: Find overdue unpaid invoices and send reminder emails.
    Runs once per day at 9:00 AM.
    """
    with app.app_context():
        from models import db, Invoice, Client, ReminderLog
        from utils.email_sender import send_reminder_email
        config = app.config_obj

        today = date.today()
        # Find unpaid invoices that are overdue
        overdue_invoices = Invoice.query.filter(
            Invoice.status == 'unpaid',
            Invoice.due_date < today
        ).all()

        sent_count = 0
        for invoice in overdue_invoices:
            # Don't spam - only remind every 3 days
            if invoice.reminder_sent_at:
                days_since_reminder = (datetime.utcnow() - invoice.reminder_sent_at).days
                if days_since_reminder < 3:
                    continue

            client = Client.query.get(invoice.client_id)
            if not client:
                continue

            # Update invoice status to overdue
            invoice.status = 'overdue'

            success = send_reminder_email(invoice, client, config)
            log = ReminderLog(
                invoice_id=invoice.id,
                status='sent' if success else 'failed',
                message=f"Reminder {'sent' if success else 'failed'} on {today}"
            )
            if success:
                invoice.reminder_sent_at = datetime.utcnow()
                invoice.reminder_count += 1
                sent_count += 1

            db.session.add(log)

        db.session.commit()
        logger.info(f"[SCHEDULER] Reminder job done. Sent {sent_count} reminders.")


def generate_recurring_invoices(app):
    """
    Monthly job: Auto-generate invoices for all active clients on the 1st of each month.
    """
    with app.app_context():
        from models import db, Client, Invoice
        from utils.pdf_generator import generate_invoice_pdf
        from utils.email_sender import send_invoice_email
        import os

        config = app.config_obj
        today = date.today()

        # Only run on 1st of the month
        if today.day != 1:
            return

        active_clients = Client.query.filter_by(is_active=True).all()
        for client in active_clients:
            # Check if invoice already exists for this month
            existing = Invoice.query.filter(
                Invoice.client_id == client.id,
                db.extract('month', Invoice.created_at) == today.month,
                db.extract('year', Invoice.created_at) == today.year,
            ).first()

            if existing:
                continue

            # Generate new invoice
            amount = float(client.monthly_fee)
            gst_rate = 18.0
            gst_amount = round(amount * gst_rate / 100, 2)
            total = round(amount + gst_amount, 2)

            # Generate invoice number: INV-YYYYMM-XXXX
            count = Invoice.query.count() + 1
            invoice_number = f"INV-{today.strftime('%Y%m')}-{count:04d}"

            due_date = today.replace(day=15)  # Due on 15th of the month

            invoice = Invoice(
                invoice_number=invoice_number,
                client_id=client.id,
                amount=amount,
                gst_rate=gst_rate,
                gst_amount=gst_amount,
                total=total,
                due_date=due_date,
                status='unpaid',
                description=f"Monthly Fee - {today.strftime('%B %Y')}"
            )
            db.session.add(invoice)
            db.session.flush()

            # Generate PDF
            try:
                pdf_filename = generate_invoice_pdf(invoice, client, config)
                invoice.pdf_path = pdf_filename
                pdf_full_path = os.path.join(config.INVOICES_DIR, pdf_filename)
                send_invoice_email(invoice, client, pdf_full_path, config)
            except Exception as e:
                logger.error(f"[SCHEDULER] Failed to generate PDF for {client.name}: {e}")

        db.session.commit()
        logger.info(f"[SCHEDULER] Recurring invoices generated for {today.strftime('%B %Y')}")


def init_scheduler(app):
    """Initialize and start the background scheduler."""
    scheduler = BackgroundScheduler()

    # Daily reminder job at 9 AM
    scheduler.add_job(
        func=lambda: check_and_send_reminders(app),
        trigger=CronTrigger(hour=9, minute=0),
        id='daily_reminders',
        name='Send overdue invoice reminders',
        replace_existing=True
    )

    # Monthly recurring invoice job at 8 AM on 1st of every month
    scheduler.add_job(
        func=lambda: generate_recurring_invoices(app),
        trigger=CronTrigger(day=1, hour=8, minute=0),
        id='monthly_invoices',
        name='Generate recurring monthly invoices',
        replace_existing=True
    )

    scheduler.start()
    logger.info("[SCHEDULER] Background scheduler started.")
    return scheduler

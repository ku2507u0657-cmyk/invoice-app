"""
utils/email.py — Email delivery via smtplib for InvoiceFlow.

Public API
----------
    send_invoice_email(invoice, app)               -> None
    send_reminder_email(invoice, app, days_overdue) -> None
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

logger = logging.getLogger(__name__)

class EmailError(Exception):
    """Raised when email delivery fails."""


# ─────────────────────────────────────────────────────────────
#  Public: send original invoice
# ─────────────────────────────────────────────────────────────

def send_invoice_email(invoice, app) -> None:
    try:
        cfg = app.config
        company_name = cfg.get("COMPANY_NAME", cfg.get("APP_NAME", "InvoiceFlow"))

        _guard_enabled(cfg)
        recipient = _resolve_recipient(invoice, cfg)

        # Build PDF bytes
        pdf_bytes = _safe_pdf(invoice, app)

        subject = f"Invoice {invoice.invoice_number} from {company_name}"

        html_body = _render_template(
            app,
            "emails/invoice_email.html",
            invoice=invoice,
            company_name=company_name
        )
        
        plain_body = _plain_invoice(invoice, company_name)

        # Construct the email message
        msg = MIMEMultipart("mixed")
        msg["From"] = f"{company_name} <{cfg.get('MAIL_FROM_ADDRESS')}>"
        msg["To"] = recipient
        msg["Subject"] = subject

        # Create alternative payload for plain-text and HTML
        body_part = MIMEMultipart("alternative")
        body_part.attach(MIMEText(plain_body, "plain"))
        body_part.attach(MIMEText(html_body, "html"))
        msg.attach(body_part)

        # Attach PDF if generated successfully
        if pdf_bytes:
            pdf_attachment = MIMEApplication(pdf_bytes, Name=f"{invoice.invoice_number}.pdf")
            pdf_attachment["Content-Disposition"] = f'attachment; filename="{invoice.invoice_number}.pdf"'
            msg.attach(pdf_attachment)

        # Send via SMTP
        with smtplib.SMTP(cfg.get("MAIL_SERVER"), cfg.get("MAIL_PORT", 587), timeout=10) as server:
            server.starttls()
            server.login(cfg.get("MAIL_USERNAME"), cfg.get("MAIL_PASSWORD"))
            server.send_message(msg)

        logger.info(
            "Invoice email sent via SMTP: %s -> %s",
            invoice.invoice_number,
            recipient
        )

    except Exception as e:
        raise EmailError(f"Email sending failed: {str(e)}")


# ─────────────────────────────────────────────────────────────
#  Public: send reminder
# ─────────────────────────────────────────────────────────────

def send_reminder_email(invoice, app, days_overdue: int = 0) -> None:
    try:
        cfg = app.config
        company_name = cfg.get("COMPANY_NAME", cfg.get("APP_NAME", "InvoiceFlow"))

        _guard_enabled(cfg)
        recipient = _resolve_recipient(invoice, cfg)

        pdf_bytes = _safe_pdf(invoice, app)

        subject = f"Reminder: Invoice {invoice.invoice_number} overdue"

        html_body = _render_template(
            app,
            "emails/reminder_email.html",
            invoice=invoice,
            company_name=company_name,
            days_overdue=days_overdue
        )
        
        plain_body = _plain_reminder(invoice, company_name, days_overdue)

        # Construct the email message
        msg = MIMEMultipart("mixed")
        msg["From"] = f"{company_name} <{cfg.get('MAIL_FROM_ADDRESS')}>"
        msg["To"] = recipient
        msg["Subject"] = subject

        # Create alternative payload for plain-text and HTML
        body_part = MIMEMultipart("alternative")
        body_part.attach(MIMEText(plain_body, "plain"))
        body_part.attach(MIMEText(html_body, "html"))
        msg.attach(body_part)

        # Attach PDF if generated successfully
        if pdf_bytes:
            pdf_attachment = MIMEApplication(pdf_bytes, Name=f"{invoice.invoice_number}.pdf")
            pdf_attachment["Content-Disposition"] = f'attachment; filename="{invoice.invoice_number}.pdf"'
            msg.attach(pdf_attachment)

        # Send via SMTP
        with smtplib.SMTP(cfg.get("MAIL_SERVER"), cfg.get("MAIL_PORT", 587), timeout=10) as server:
            server.starttls()
            server.login(cfg.get("MAIL_USERNAME"), cfg.get("MAIL_PASSWORD"))
            server.send_message(msg)

        logger.info(
            "Reminder sent via SMTP: %s -> %s",
            invoice.invoice_number,
            recipient
        )

    except Exception as e:
        raise EmailError(f"Reminder failed: {str(e)}")


# ─────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────

def _guard_enabled(cfg):
    if not cfg.get("MAIL_ENABLED", True):
        raise EmailError("Email sending is disabled.")


def _resolve_recipient(invoice, cfg):
    r = invoice.client.email or cfg.get("MAIL_FALLBACK_RECIPIENT")
    if not r:
        raise EmailError("No recipient email found.")
    return r


def _safe_pdf(invoice, app):
    try:
        from utils.pdf import build_invoice_pdf_bytes
        return build_invoice_pdf_bytes(invoice, app)
    except Exception as exc:
        logger.error("PDF build failed: %s", exc)
        return b""


def _render_template(app, path, **ctx):
    with app.app_context():
        return app.jinja_env.get_template(path).render(**ctx)

# ─────────────────────────────────────────────────────────────
#  Plain-text bodies
# ─────────────────────────────────────────────────────────────

def _plain_invoice(invoice, company_name):
    return (
        f"Dear {invoice.client.name},\n\n"
        f"Please find attached invoice {invoice.invoice_number} from {company_name}.\n\n"
        f"  Amount (excl. GST):  {invoice.amount_display}\n"
        f"  GST (18%):           {invoice.gst_display}\n"
        f"  Total Payable:       {invoice.total_display}\n"
        f"  Due Date:            {invoice.due_date.strftime('%d %B %Y')}\n\n"
        f"Please reference {invoice.invoice_number} when making payment.\n\n"
        f"Thank you,\n{company_name}"
    )


def _plain_reminder(invoice, company_name, days_overdue):
    ds = f"{days_overdue} day{'s' if days_overdue != 1 else ''}"
    return (
        f"Dear {invoice.client.name},\n\n"
        f"Invoice {invoice.invoice_number} from {company_name} is {ds} overdue.\n\n"
        f"  Invoice:    {invoice.invoice_number}\n"
        f"  Due Date:   {invoice.due_date.strftime('%d %B %Y')}\n"
        f"  Total Due:  {invoice.total_display}\n\n"
        f"Please arrange payment immediately. Quote {invoice.invoice_number} as reference.\n\n"
        f"Regards,\n{company_name}"
    )
"""Helper utilities for invoice number generation and other common tasks."""
import csv
import io
from datetime import datetime


def generate_invoice_number(client_id: int, year: int = None, month: int = None) -> str:
    """
    Generate a unique invoice number.
    Format: INV-YYYY-MM-XXXXXX  (timestamp-based for uniqueness)
    """
    now = datetime.utcnow()
    y = year or now.year
    m = month or now.month
    ts = now.strftime('%d%H%M%S')
    return f"INV-{y}-{m:02d}-{ts}{client_id}"


def invoices_to_csv(invoices) -> str:
    """Convert list of invoice dicts to CSV string."""
    output = io.StringIO()
    fieldnames = [
        'invoice_number', 'client_name', 'client_email', 'client_phone',
        'amount', 'gst_amount', 'total', 'due_date', 'status',
        'created_at', 'paid_at'
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for inv in invoices:
        writer.writerow({
            'invoice_number': inv.invoice_number,
            'client_name': inv.client.name if inv.client else '',
            'client_email': inv.client.email if inv.client else '',
            'client_phone': inv.client.phone if inv.client else '',
            'amount': inv.amount,
            'gst_amount': inv.gst_amount,
            'total': inv.total,
            'due_date': inv.due_date.strftime('%Y-%m-%d'),
            'status': inv.status,
            'created_at': inv.created_at.strftime('%Y-%m-%d %H:%M'),
            'paid_at': inv.paid_at.strftime('%Y-%m-%d %H:%M') if inv.paid_at else '',
        })
    return output.getvalue()

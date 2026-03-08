"""Invoice routes: create, view, mark paid, download PDF, export CSV."""
import os
import csv
import io
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, send_file, current_app, Response)
from flask_login import login_required
from datetime import date, timedelta
from models import db, Client, Invoice

invoices_bp = Blueprint('invoices', __name__, url_prefix='/invoices')


def _next_invoice_number():
    """Generate a unique invoice number: INV-YYYYMM-XXXX."""
    today = date.today()
    count = Invoice.query.count() + 1
    return f"INV-{today.strftime('%Y%m')}-{count:04d}"


@invoices_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')

    query = Invoice.query.join(Client)
    if status_filter:
        query = query.filter(Invoice.status == status_filter)
    if search:
        query = query.filter(Client.name.ilike(f'%{search}%'))

    invoices = query.order_by(Invoice.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('invoices/index.html', invoices=invoices,
                           status_filter=status_filter, search=search)


@invoices_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    clients = Client.query.filter_by(is_active=True).order_by(Client.name).all()

    if request.method == 'POST':
        client_id = request.form.get('client_id', type=int)
        amount = request.form.get('amount', '')
        gst_rate = float(request.form.get('gst_rate', 18.0))
        due_date_str = request.form.get('due_date', '')
        description = request.form.get('description', '').strip()

        errors = []
        client = None
        if not client_id:
            errors.append('Please select a client.')
        else:
            client = Client.query.get(client_id)
            if not client:
                errors.append('Client not found.')

        try:
            amount = float(amount)
            if amount <= 0:
                errors.append('Amount must be positive.')
        except (ValueError, TypeError):
            errors.append('Amount must be a valid number.')

        try:
            due_date = date.fromisoformat(due_date_str)
        except (ValueError, TypeError):
            errors.append('Please enter a valid due date.')
            due_date = None

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('invoices/form.html', clients=clients,
                                   form_data=request.form)

        gst_amount = round(amount * gst_rate / 100, 2)
        total = round(amount + gst_amount, 2)
        invoice_number = _next_invoice_number()

        invoice = Invoice(
            invoice_number=invoice_number,
            client_id=client_id,
            amount=amount,
            gst_rate=gst_rate,
            gst_amount=gst_amount,
            total=total,
            due_date=due_date,
            status='unpaid',
            description=description or f"Monthly Fee - {date.today().strftime('%B %Y')}"
        )
        db.session.add(invoice)
        db.session.flush()  # Get ID before commit

        # Generate PDF
        try:
            from utils.pdf_generator import generate_invoice_pdf
            config = current_app.config_obj
            pdf_filename = generate_invoice_pdf(invoice, client, config)
            invoice.pdf_path = pdf_filename
            pdf_full_path = os.path.join(config.INVOICES_DIR, pdf_filename)
        except Exception as e:
            flash(f'Warning: Could not generate PDF: {str(e)}', 'warning')
            pdf_full_path = None

        db.session.commit()

        # Send email
    try:
        from utils.email_sender import send_invoice_email
        config = current_app.config_obj
        if pdf_full_path and os.path.exists(pdf_full_path):
            pass
        # send_invoice_email(invoice, client, pdf_full_path, config)
    except Exception as e:
        flash(f'Warning: Could not send email: {str(e)}', 'warning')

    # Pre-fill amount from client's monthly fee
    preselect_client_id = request.args.get('client_id', type=int)
    default_due = (date.today() + timedelta(days=15)).isoformat()
    return render_template('invoices/form.html', clients=clients, form_data={
        'due_date': default_due,
        'gst_rate': 18,
        'client_id': preselect_client_id
    })


@invoices_bp.route('/<int:invoice_id>')
@login_required
def view(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template('invoices/view.html', invoice=invoice, client=invoice.client)


@invoices_bp.route('/<int:invoice_id>/mark-paid', methods=['POST'])
@login_required
def mark_paid(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    invoice.status = 'paid'
    invoice.paid_date = date.today()
    db.session.commit()
    flash(f'Invoice #{invoice.invoice_number} marked as paid!', 'success')
    return redirect(request.referrer or url_for('invoices.view', invoice_id=invoice_id))


@invoices_bp.route('/<int:invoice_id>/mark-unpaid', methods=['POST'])
@login_required
def mark_unpaid(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    invoice.status = 'unpaid'
    invoice.paid_date = None
    db.session.commit()
    flash(f'Invoice #{invoice.invoice_number} marked as unpaid.', 'info')
    return redirect(request.referrer or url_for('invoices.view', invoice_id=invoice_id))


@invoices_bp.route('/<int:invoice_id>/download')
@login_required
def download_pdf(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    config = current_app.config_obj

    if invoice.pdf_path:
        pdf_path = os.path.join(config.INVOICES_DIR, invoice.pdf_path)
        if os.path.exists(pdf_path):
            return send_file(pdf_path, as_attachment=True,
                             download_name=f'Invoice_{invoice.invoice_number}.pdf')

    # Regenerate if missing
    try:
        from utils.pdf_generator import generate_invoice_pdf
        pdf_filename = generate_invoice_pdf(invoice, invoice.client, config)
        invoice.pdf_path = pdf_filename
        db.session.commit()
        pdf_path = os.path.join(config.INVOICES_DIR, pdf_filename)
        return send_file(pdf_path, as_attachment=True,
                         download_name=f'Invoice_{invoice.invoice_number}.pdf')
    except Exception as e:
        flash(f'Could not generate PDF: {str(e)}', 'danger')
        return redirect(url_for('invoices.view', invoice_id=invoice_id))


@invoices_bp.route('/<int:invoice_id>/send-reminder', methods=['POST'])
@login_required
def send_reminder(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    config = current_app.config_obj
    try:
        from utils.email_sender import send_reminder_email
        from models import ReminderLog
        from datetime import datetime
        success = send_reminder_email(invoice, invoice.client, config)
        log = ReminderLog(invoice_id=invoice.id,
                          status='sent' if success else 'failed')
        if success:
            invoice.reminder_sent_at = datetime.utcnow()
            invoice.reminder_count += 1
        db.session.add(log)
        db.session.commit()
        flash('Reminder email sent!' if success else 'Failed to send reminder.', 
              'success' if success else 'danger')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(request.referrer or url_for('invoices.view', invoice_id=invoice_id))


@invoices_bp.route('/export-csv')
@login_required
def export_csv():
    """Export all invoices to CSV."""
    invoices = Invoice.query.join(Client).order_by(Invoice.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Invoice Number', 'Client Name', 'Client Email', 'Client Phone',
        'Amount', 'GST Rate', 'GST Amount', 'Total',
        'Status', 'Due Date', 'Paid Date', 'Created At'
    ])
    for inv in invoices:
        writer.writerow([
            inv.invoice_number, inv.client.name, inv.client.email, inv.client.phone,
            float(inv.amount), float(inv.gst_rate), float(inv.gst_amount), float(inv.total),
            inv.status, inv.due_date, inv.paid_date,
            inv.created_at.strftime('%Y-%m-%d %H:%M')
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=invoices_{date.today()}.csv'}
    )

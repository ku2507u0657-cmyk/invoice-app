"""Client management routes: CRUD operations."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from models import db, Client, Invoice

clients_bp = Blueprint('clients', __name__, url_prefix='/clients')


@clients_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    query = Client.query
    if search:
        query = query.filter(
            Client.name.ilike(f'%{search}%') | Client.email.ilike(f'%{search}%')
        )
    clients = query.order_by(Client.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('clients/index.html', clients=clients, search=search)


@clients_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        monthly_fee = request.form.get('monthly_fee', '')
        gst_number = request.form.get('gst_number', '').strip() or None

        # Validation
        errors = []
        if not name: errors.append('Name is required.')
        if not phone: errors.append('Phone is required.')
        if not email: errors.append('Email is required.')
        if not monthly_fee:
            errors.append('Monthly fee is required.')
        else:
            try:
                monthly_fee = float(monthly_fee)
                if monthly_fee <= 0:
                    errors.append('Monthly fee must be positive.')
            except ValueError:
                errors.append('Monthly fee must be a number.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('clients/form.html', action='add',
                                   form_data=request.form)

        client = Client(
            name=name, phone=phone, email=email,
            monthly_fee=monthly_fee, gst_number=gst_number
        )
        db.session.add(client)
        db.session.commit()
        flash(f'Client "{name}" added successfully!', 'success')
        return redirect(url_for('clients.index'))

    return render_template('clients/form.html', action='add', form_data={})


@clients_bp.route('/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(client_id):
    client = Client.query.get_or_404(client_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        monthly_fee = request.form.get('monthly_fee', '')
        gst_number = request.form.get('gst_number', '').strip() or None
        is_active = request.form.get('is_active') == 'on'

        errors = []
        if not name: errors.append('Name is required.')
        if not phone: errors.append('Phone is required.')
        if not email: errors.append('Email is required.')
        try:
            monthly_fee = float(monthly_fee)
            if monthly_fee <= 0: errors.append('Monthly fee must be positive.')
        except (ValueError, TypeError):
            errors.append('Monthly fee must be a number.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('clients/form.html', action='edit', client=client,
                                   form_data=request.form)

        client.name = name
        client.phone = phone
        client.email = email
        client.monthly_fee = monthly_fee
        client.gst_number = gst_number
        client.is_active = is_active
        db.session.commit()
        flash(f'Client "{name}" updated successfully!', 'success')
        return redirect(url_for('clients.index'))

    return render_template('clients/form.html', action='edit', client=client, form_data=client)


@clients_bp.route('/<int:client_id>/delete', methods=['POST'])
@login_required
def delete(client_id):
    client = Client.query.get_or_404(client_id)
    name = client.name
    db.session.delete(client)
    db.session.commit()
    flash(f'Client "{name}" deleted.', 'info')
    return redirect(url_for('clients.index'))


@clients_bp.route('/<int:client_id>/view')
@login_required
def view(client_id):
    client = Client.query.get_or_404(client_id)
    invoices = Invoice.query.filter_by(client_id=client_id).order_by(Invoice.created_at.desc()).all()
    return render_template('clients/view.html', client=client, invoices=invoices)

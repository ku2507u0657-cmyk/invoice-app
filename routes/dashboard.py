"""Dashboard route with revenue stats and charts."""
from flask import Blueprint, render_template, jsonify, current_app
from flask_login import login_required
from sqlalchemy import func, extract
from datetime import datetime, date
from models import db, Client, Invoice

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    today = date.today()
    
    # Monthly revenue (this month)
    monthly_revenue = db.session.query(func.sum(Invoice.total)).filter(
        Invoice.status == 'paid',
        extract('month', Invoice.created_at) == today.month,
        extract('year', Invoice.created_at) == today.year
    ).scalar() or 0

    # Total unpaid amount
    total_unpaid = db.session.query(func.sum(Invoice.total)).filter(
        Invoice.status.in_(['unpaid', 'overdue'])
    ).scalar() or 0

    # Active clients
    active_clients = Client.query.filter_by(is_active=True).count()

    # Total invoices
    total_invoices = Invoice.query.count()
    paid_invoices = Invoice.query.filter_by(status='paid').count()
    unpaid_invoices = Invoice.query.filter(Invoice.status.in_(['unpaid', 'overdue'])).count()
    overdue_invoices = Invoice.query.filter_by(status='overdue').count()

    # Recent invoices (last 10)
    recent_invoices = Invoice.query.order_by(Invoice.created_at.desc()).limit(10).all()

    return render_template('dashboard/index.html',
        monthly_revenue=monthly_revenue,
        total_unpaid=total_unpaid,
        active_clients=active_clients,
        total_invoices=total_invoices,
        paid_invoices=paid_invoices,
        unpaid_invoices=unpaid_invoices,
        overdue_invoices=overdue_invoices,
        recent_invoices=recent_invoices
    )


@dashboard_bp.route('/api/chart-data')
@login_required
def chart_data():
    """Return last 6 months revenue data for Chart.js."""
    today = date.today()
    months_data = []

    for i in range(5, -1, -1):
        month = today.month - i
        year = today.year
        if month <= 0:
            month += 12
            year -= 1

        revenue = db.session.query(func.sum(Invoice.total)).filter(
            Invoice.status == 'paid',
            extract('month', Invoice.created_at) == month,
            extract('year', Invoice.created_at) == year
        ).scalar() or 0

        billed = db.session.query(func.sum(Invoice.total)).filter(
            extract('month', Invoice.created_at) == month,
            extract('year', Invoice.created_at) == year
        ).scalar() or 0

        months_data.append({
            'month': datetime(year, month, 1).strftime('%b %Y'),
            'revenue': float(revenue),
            'billed': float(billed)
        })

    return jsonify(months_data)

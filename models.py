from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Admin(UserMixin, db.Model):
    """Admin user model for authentication."""
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, default='Admin')
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Admin {self.email}>'


class Client(db.Model):
    """Client model representing a student/gym member."""
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    monthly_fee = db.Column(db.Numeric(10, 2), nullable=False)
    gst_number = db.Column(db.String(15), nullable=True)  # GSTIN of client (optional)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to invoices
    invoices = db.relationship('Invoice', backref='client', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def total_paid(self):
        return sum(inv.total for inv in self.invoices if inv.status == 'paid')

    @property
    def total_unpaid(self):
        return sum(inv.total for inv in self.invoices if inv.status == 'unpaid')

    def __repr__(self):
        return f'<Client {self.name}>'


class Invoice(db.Model):
    """Invoice model."""
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    
    # Financial fields
    amount = db.Column(db.Numeric(10, 2), nullable=False)   # Base amount (subtotal)
    gst_rate = db.Column(db.Numeric(5, 2), default=18.0)    # GST rate in %
    gst_amount = db.Column(db.Numeric(10, 2), nullable=False)  # GST value
    total = db.Column(db.Numeric(10, 2), nullable=False)    # Total with GST
    
    # Dates
    due_date = db.Column(db.Date, nullable=False)
    paid_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Status: unpaid, paid, overdue
    status = db.Column(db.String(20), default='unpaid', nullable=False)
    
    # PDF file path (relative)
    pdf_path = db.Column(db.String(255), nullable=True)
    
    # For reminder tracking
    reminder_sent_at = db.Column(db.DateTime, nullable=True)
    reminder_count = db.Column(db.Integer, default=0)

    # Description / notes
    description = db.Column(db.String(500), nullable=True)

    @property
    def is_overdue(self):
        return self.status == 'unpaid' and self.due_date < datetime.utcnow().date()

    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'


class ReminderLog(db.Model):
    """Log of reminder emails sent."""
    __tablename__ = 'reminder_logs'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='sent')  # sent / failed
    message = db.Column(db.String(500), nullable=True)

    invoice = db.relationship('Invoice', backref='reminder_logs')

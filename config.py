import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
    
    # Use SQLite for local dev if no DATABASE_URL set
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///invoice_app.db')
    # Fix for Render/Railway PostgreSQL URL format
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', '')

    # Company Info
    COMPANY_NAME = os.environ.get('COMPANY_NAME', 'My Business')
    COMPANY_ADDRESS = os.environ.get('COMPANY_ADDRESS', '123 Street, City')
    COMPANY_PHONE = os.environ.get('COMPANY_PHONE', '+91 00000 00000')
    COMPANY_EMAIL = os.environ.get('COMPANY_EMAIL', 'info@mybusiness.com')
    COMPANY_GSTIN = os.environ.get('COMPANY_GSTIN', '')
    UPI_ID = os.environ.get('UPI_ID', 'business@upi')
    APP_URL = os.environ.get('APP_URL', 'http://localhost:5000')

    # Admin seed
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin@123')

    # Invoices directory
    INVOICES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'invoices')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

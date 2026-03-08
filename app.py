"""
InvoiceHub - Invoice Automation for Small Indian Businesses
Main application entry point.
"""
import os
import logging
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_name=None):
    """Application factory pattern."""
    app = Flask(__name__)

    # Load configuration
    from config import config
    cfg_name = config_name or os.environ.get('FLASK_ENV', 'development')
    cfg = config.get(cfg_name, config['default'])
    app.config.from_object(cfg)

    # Store config object for use in utils
    app.config_obj = cfg

    # Ensure invoices directory exists
    os.makedirs(cfg.INVOICES_DIR, exist_ok=True)

    # Initialize extensions
    from models import db
    db.init_app(app)

    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        from models import Admin
        return Admin.query.get(int(user_id))

    # Template context processor - inject config into all templates
    @app.context_processor
    def inject_config():
        return {'config': cfg}

    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.clients import clients_bp
    from routes.invoices import invoices_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(invoices_bp)

    # Create database tables and seed admin
    with app.app_context():
        db.create_all()
        _seed_admin(app, cfg)

    # Start background scheduler (only in production or if not in debug reloader)
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        try:
            from utils.scheduler import init_scheduler
            scheduler = init_scheduler(app)
            app.scheduler = scheduler
        except Exception as e:
            logger.warning(f"Scheduler could not start: {e}")

    logger.info(f"InvoiceHub started | DB: {cfg.SQLALCHEMY_DATABASE_URI[:30]}...")
    return app


def _seed_admin(app, cfg):
    """Create default admin user if none exists."""
    from models import Admin, db
    if Admin.query.count() == 0:
        admin = Admin(
            name='Admin',
            email=cfg.ADMIN_EMAIL
        )
        admin.set_password(cfg.ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()
        logger.info(f"[SEED] Admin created: {cfg.ADMIN_EMAIL}")


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

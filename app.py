"""Application factory and entry point for the Poultry Disease Detection app."""

from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from config import ensure_directories, get_config
from database.db import db, init_db
from extensions import limiter

# Extensions are created once and bound to the app inside create_app()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_class=None):
    """Create and configure the Flask application."""
    config_class = config_class or get_config()
    ensure_directories(config_class)

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Database and tables
    init_db(app)

    # CSRF protection for every POST request
    csrf.init_app(app)

    # Rate limiting (login and registration)
    limiter.init_app(app)

    # Login manager
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"
    login_manager.session_protection = "strong"

    from models import Farmer

    @login_manager.user_loader
    def load_user(user_id):
        """Load the logged-in farmer from the session user id."""
        try:
            return db.session.get(Farmer, int(user_id))
        except (TypeError, ValueError):
            return None

    # Blueprints
    from routes.analytics import analytics_bp
    from routes.auth import auth_bp
    from routes.export import export_bp
    from routes.history import history_bp
    from routes.main import main_bp
    from routes.scan import scan_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(export_bp)

    register_error_handlers(app)
    register_security_headers(app)

    return app


def register_error_handlers(app):
    """Attach custom error pages."""

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def file_too_large(error):
        return render_template("errors/413.html"), 413

    @app.errorhandler(429)
    def too_many_requests(error):
        return render_template("errors/429.html"), 429

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500


def register_security_headers(app):
    """Add basic security headers to every response."""

    @app.after_request
    def set_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        return response


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=app.config["DEBUG"])
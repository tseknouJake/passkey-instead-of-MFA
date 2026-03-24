"""
Route package initializer.

Registers all blueprints to the Flask app.
"""

from .main import main
from .auth_classic import auth_classic
from .auth_otp import auth_otp

def register_routes(app):
    """
    Register all route blueprints with the Flask app.

    Args:
        app (Flask): The Flask application instance.
    """
    app.register_blueprint(main)
    app.register_blueprint(auth_classic)
    app.register_blueprint(auth_otp)
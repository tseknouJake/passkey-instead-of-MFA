"""
Route package initializer.

Registers all blueprints to the Flask app.
"""

from .main import main

def register_routes(app):
    """
    Register all route blueprints with the Flask app.

    Args:
        app (Flask): The Flask application instance.
    """
    app.register_blueprint(main)
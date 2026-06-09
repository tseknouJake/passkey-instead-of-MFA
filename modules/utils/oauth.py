"""
Utility module for configuring and accessing OAuth providers.
"""

from flask import url_for
from authlib.integrations.flask_client import OAuth

oauth = OAuth()

def init_oauth(app):
    """
    Initialize OAuth with the Flask app.

    Authors:
    - Irina Vilcu
    - Leah Goldin
    """
    oauth.init_app(app)

    oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

def get_google_oauth():
    """
    Get the OAuth instance.

    Authors:
    - Irina Vilcu
    - Leah Goldin
    """
    return oauth

def get_google_oauth_error(app):
    """
    Validate Google OAuth configuration.

    Authors:
    - Irina Vilcu
    - Leah Goldin
    """
    client_id = app.config.get("GOOGLE_CLIENT_ID")
    client_secret = app.config.get("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        return "Google OAuth is not configured."

    if not client_id.endswith(".apps.googleusercontent.com"):
        return "Invalid Google client ID format."

    return None

def get_google_redirect_uri(app):
    """
    Get the redirect URI for Google OAuth.

    Authors:
    - Irina Vilcu
    - Leah Goldin
    """
    configured_uri = app.config.get("GOOGLE_REDIRECT_URI")
    if configured_uri:
        return configured_uri

    return url_for('auth_social.google_callback', _external=True)
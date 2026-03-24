from flask import Flask, render_template, request, redirect, url_for, session
import os
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
from modules.utils.encryptor import get_flask_secret_key
from modules.services.user_service import (
    get_user,
    create_social_user,
)
from modules.routes import register_routes

#TODO: extract routes URLs to be reusable

load_dotenv()
try:
    from authlib.integrations.flask_client import OAuth
    GOOGLE_OAUTH_AVAILABLE = True
except ModuleNotFoundError:
    OAuth = None
    GOOGLE_OAUTH_AVAILABLE = False

app = Flask(__name__)
register_routes(app)
app.config["GOOGLE_CLIENT_ID"] = (os.environ.get("GOOGLE_CLIENT_ID") or "").strip()
app.config["GOOGLE_CLIENT_SECRET"] = (os.environ.get("GOOGLE_CLIENT_SECRET") or "").strip()
app.config["GOOGLE_REDIRECT_URI"] = (os.environ.get("GOOGLE_REDIRECT_URI") or "").strip()
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)


def get_google_oauth_error():
    if not GOOGLE_OAUTH_AVAILABLE:
        return "Google login is unavailable: missing OAuth dependencies."

    client_id = app.config.get("GOOGLE_CLIENT_ID")
    client_secret = app.config.get("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        return "Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."

    if "your-" in client_id.lower() or "your-" in client_secret.lower():
        return "Google OAuth uses placeholder credentials. Replace them with real Google Cloud values."

    if not client_id.endswith(".apps.googleusercontent.com"):
        return "GOOGLE_CLIENT_ID format looks invalid."

    return None


def get_google_redirect_uri():
    configured_uri = app.config.get("GOOGLE_REDIRECT_URI")
    if configured_uri:
        return configured_uri
    return url_for("google_callback", _external=True)


oauth = OAuth(app) if GOOGLE_OAUTH_AVAILABLE else None
if oauth and not get_google_oauth_error():
    oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

def env_flag(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


app.secret_key = get_flask_secret_key()
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = env_flag("SESSION_COOKIE_SECURE")
app.config["PREFERRED_URL_SCHEME"] = "https" if env_flag("PREFERRED_URL_SCHEME_HTTPS") else "http"


@app.route('/google-login-page')
def google_login_page():
    oauth_error = get_google_oauth_error()
    return render_template(
        'google_login.html',
        error=oauth_error,
        oauth_available=oauth_error is None,
        callback_uri=get_google_redirect_uri()
    )

@app.route('/login/google')
def login_google():
    oauth_error = get_google_oauth_error()
    if oauth_error:
        return render_template(
            'google_login.html',
            error=oauth_error,
            oauth_available=False,
            callback_uri=get_google_redirect_uri()
        ), 503
    return oauth.google.authorize_redirect(get_google_redirect_uri())

@app.route('/auth/google/callback')
def google_callback():
    oauth_error = get_google_oauth_error()
    if oauth_error:
        return render_template(
            'google_login.html',
            error=oauth_error,
            oauth_available=False,
            callback_uri=get_google_redirect_uri()
        ), 503

    try:
        token = oauth.google.authorize_access_token()
    except Exception:
        return render_template(
            'google_login.html',
            error='Google OAuth callback failed. Verify client credentials and redirect URI.',
            oauth_available=False,
            callback_uri=get_google_redirect_uri()
        ), 401

    user_info = token.get('userinfo')
    if not user_info:
        user_info = oauth.google.parse_id_token(token, nonce=session.get('oauth_nonce'))

    email = user_info['email']
    if not get_user(email):
        create_social_user(email, 'google')

    session['username'] = email
    session['auth_method'] = 'social'
    session['social_verified'] = True
    session['classic_verified'] = False
    session['mfa_verified'] = False
    session['passkey_verified'] = False

    return redirect(url_for('main.dashboard'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, ssl_context='adhoc')

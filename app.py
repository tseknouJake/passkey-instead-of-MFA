from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pyotp
import qrcode
import io
import base64
from functools import wraps
import os
import ipaddress
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
from modules.utils.encryptor import get_flask_secret_key
from modules.services.user_service import (
    get_user,
    create_user,
    create_social_user,
    update_mfa_secret,
    add_passkey_credential
)
from modules.utils.decorators import login_required

load_dotenv()
try:
    from authlib.integrations.flask_client import OAuth
    GOOGLE_OAUTH_AVAILABLE = True
except ModuleNotFoundError:
    OAuth = None
    GOOGLE_OAUTH_AVAILABLE = False

app = Flask(__name__)
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


def normalize_passkey_host(hostname):
    host = (hostname or "").strip().lower().strip("[]")
    if not host:
        raise ValueError("Unable to determine the current hostname for passkey login.")

    if host == "localhost":
        return host

    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None

    if ip:
        if ip.is_loopback or ip.is_unspecified:
            return "localhost"
        raise ValueError("Passkeys require a domain name. Use localhost locally or serve the app from your HTTPS domain.")

    if "." not in host:
        raise ValueError("Passkeys require localhost or a fully qualified domain name.")

    return host


def get_passkey_rp_id():
    configured_rp_id = (os.environ.get("PASSKEY_RP_ID") or "").strip()
    if configured_rp_id:
        return normalize_passkey_host(configured_rp_id)
    return normalize_passkey_host(request.host.split(":", 1)[0])


app.secret_key = get_flask_secret_key()
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = env_flag("SESSION_COOKIE_SECURE")
app.config["PREFERRED_URL_SCHEME"] = "https" if env_flag("PREFERRED_URL_SCHEME_HTTPS") else "http"

@app.route('/')
def index():
    if 'username' in session and (
        session.get('mfa_verified') or
        session.get('passkey_verified') or
        session.get('classic_verified') or
        session.get('social_verified')
    ):
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.before_request
def normalize_local_passkey_origin():
    if os.environ.get("PASSKEY_RP_ID"):
        return None

    hostname = request.host.split(":", 1)[0]
    try:
        normalized_host = normalize_passkey_host(hostname)
    except ValueError:
        return None

    if normalized_host == hostname:
        return None

    host_port = request.host.split(":", 1)
    if len(host_port) == 2:
        target_host = f"{normalized_host}:{host_port[1]}"
    else:
        target_host = normalized_host

    return redirect(f"{request.scheme}://{target_host}{request.full_path.rstrip('?')}", code=302)

# ============================================
# User Registration
# ============================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validation
        if not username or not password:
            return render_template('register.html', error='Username and password are required')

        if len(password) < 8:
            return render_template('register.html', error='Password must be at least 8 characters')

        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')

        if get_user(username):
            return render_template('register.html', error='Username already exists')

        # Create new user
        create_user(username, password)

        # Auto-login after registration
        session['username'] = username
        session['registered'] = True
        return redirect(url_for('setup_choice'))

    return render_template('register.html')

@app.route('/setup-choice')
def setup_choice():
    """Choose authentication method after registration"""
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('setup_choice.html', username=session['username'])

# ============================================
# MFA Authentication Routes
# ============================================

@app.route('/login', methods=['GET', 'POST'])
def password_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = get_user(username)
        if user and user.get('password') == password:
            session['username'] = username
            session['auth_method'] = 'classic'
            session['classic_verified'] = True
            session['mfa_verified'] = False
            session['passkey_verified'] = False
            session['social_verified'] = False
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

@app.route('/mfa-login', methods=['GET', 'POST'])
def mfa_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = get_user(username)
        if user and user['password'] == password:
            session['username'] = username
            session['auth_method'] = 'mfa'
            session['mfa_verified'] = False
            session['passkey_verified'] = False
            session['classic_verified'] = False
            session['social_verified'] = False

            user = get_user(username)

            if user and user['mfa_secret']:
                return redirect(url_for('verify_mfa'))
            else:
                return redirect(url_for('setup_mfa'))
        else:
            return render_template('mfa_login.html', error='Invalid credentials')

    return render_template('mfa_login.html')

@app.route('/setup-mfa')
def setup_mfa():
    if 'username' not in session:
        return redirect(url_for('mfa_login'))

    username = session['username']

    secret = pyotp.random_base32()
    update_mfa_secret(username, secret)

    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(username, issuer_name="MFA Demo")

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return render_template('setup_mfa.html', qr_code=img_str, secret=secret)

@app.route('/verify-mfa', methods=['GET', 'POST'])
def verify_mfa():
    if 'username' not in session:
        return redirect(url_for('mfa_login'))

    username = session['username']

    if request.method == 'POST':
        token = request.form.get('token')
        user = get_user(username)
        secret = user['mfa_secret']

        totp = pyotp.TOTP(secret)
        if totp.verify(token, valid_window=1):
            session['mfa_verified'] = True
            session['classic_verified'] = False
            session['social_verified'] = False
            return redirect(url_for('dashboard'))
        else:
            return render_template('verify_mfa.html', error='Invalid MFA code')

    return render_template('verify_mfa.html')

# ============================================
# Passkey Authentication Routes
# ============================================

@app.route('/passkey-login', methods=['GET', 'POST'])
def passkey_login():
    return render_template('passkey_login.html')

@app.route('/passkey-register', methods=['GET', 'POST'])
def passkey_register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = get_user(username)
        if user and user['password'] == password:
            session['username'] = username
            session['auth_method'] = 'passkey'
            session['passkey_verified'] = False
            session['classic_verified'] = False
            session['social_verified'] = False
            return render_template('passkey_register.html', username=username)
        else:
            return render_template('passkey_register.html', error='Invalid credentials')

    return render_template('passkey_register.html')

@app.route('/api/passkey/register-options', methods=['POST'])
def passkey_register_options():
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not authenticated'}), 401

    rp_id = get_passkey_rp_id()
    challenge = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
    session['passkey_challenge'] = challenge

    options = {
        'challenge': challenge,
        'rp': {
            'name': 'Passkey Demo',
            'id': rp_id
        },
        'user': {
            'id': base64.urlsafe_b64encode(username.encode()).decode('utf-8').rstrip('='),
            'name': username,
            'displayName': username
        },
        'pubKeyCredParams': [
            {'type': 'public-key', 'alg': -7},
            {'type': 'public-key', 'alg': -257}
        ],
        'timeout': 60000,
        'attestation': 'none',
        'authenticatorSelection': {
            'authenticatorAttachment': 'platform',
            'requireResidentKey': False,
            'userVerification': 'required'
        }
    }

    return jsonify(options)

@app.route('/api/passkey/register-verify', methods=['POST'])
def passkey_register_verify():
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not authenticated'}), 401

    credential = request.json

    add_passkey_credential(username, credential)

    session['passkey_verified'] = True

    return jsonify({'success': True})

@app.route('/api/passkey/login-options', methods=['POST'])
def passkey_login_options():
    data = request.json
    username = data.get('username')

    user = get_user(username)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not user['passkey_credentials']:
        return jsonify({'error': 'No passkey registered'}), 404

    rp_id = get_passkey_rp_id()
    challenge = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
    session['passkey_challenge'] = challenge
    session['username'] = username

    allowed_credentials = [
        {
            'type': 'public-key',
            'id': cred['rawId']
        }
        for cred in user['passkey_credentials']
    ]

    options = {
        'challenge': challenge,
        'timeout': 60000,
        'rpId': rp_id,
        'allowCredentials': allowed_credentials,
        'userVerification': 'required'
    }

    return jsonify(options)

@app.route('/api/passkey/login-verify', methods=['POST'])
def passkey_login_verify():
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not authenticated'}), 401

    session['auth_method'] = 'passkey'
    session['passkey_verified'] = True
    session['mfa_verified'] = False
    session['classic_verified'] = False
    session['social_verified'] = False

    return jsonify({'success': True})

# ============================================
# Dashboard & Logout
# ============================================

@app.route('/dashboard')
@login_required
def dashboard():
    auth_method = session.get('auth_method')
    return render_template('dashboard.html', 
                         username=session['username'],
                         auth_method=auth_method)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

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

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, ssl_context='adhoc')

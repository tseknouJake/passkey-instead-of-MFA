from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pyotp
import qrcode
import io
import base64
from functools import wraps
import secrets
import os
from cryptography.fernet import Fernet
from supabase import create_client, Client
from dotenv import load_dotenv
import json

load_dotenv()
try:
    from authlib.integrations.flask_client import OAuth
    GOOGLE_OAUTH_AVAILABLE = True
except ModuleNotFoundError:
    OAuth = None
    GOOGLE_OAUTH_AVAILABLE = False

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

# ============================================
# Encryption Functions
# ============================================

FERNET_KEY = os.environ.get("FERNET_KEY")

if not FERNET_KEY:
    raise ValueError("FERNET_KEY environment variable not set")

f = Fernet(FERNET_KEY.encode())

def encrypt_data(data):
    return f.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data):
    return f.decrypt(encrypted_data.encode()).decode()

def get_user(username):
    response = supabase.table("users").select("*").eq("username", username).execute()
    user = response.data[0] if response.data else None
    if user:
        if user.get("password"):
            user["password"] = decrypt_data(user["password"])
        if user.get("mfa_secret"):
            user["mfa_secret"] = decrypt_data(user["mfa_secret"])
    return user

def create_user(username, password):
    encrypted_password = encrypt_data(password)
    supabase.table("users").insert({"username": username, "password": encrypted_password}).execute()

def update_mfa_secret(username, secret):
    encrypted_secret = encrypt_data(secret)
    supabase.table("users").update({"mfa_secret": encrypted_secret}).eq("username", username).execute()

def add_passkey_credential(username, credential):
    user = get_user(username)
    current_credentials = user.get("passkey_credentials") or []
    updated_credentials = current_credentials + [credential]
    supabase.table("users").update({"passkey_credentials": updated_credentials}).eq("username", username).execute()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('index'))
        auth_method = session.get('auth_method')
        if auth_method == 'mfa' and not session.get('mfa_verified'):
            return redirect(url_for('mfa_login'))
        elif auth_method == 'passkey' and not session.get('passkey_verified'):
            return redirect(url_for('passkey_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'username' in session and (session.get('mfa_verified') or session.get('passkey_verified')):
        return redirect(url_for('dashboard'))
    return render_template('index.html')

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
            return render_template('passkey_register.html', username=username)
        else:
            return render_template('passkey_register.html', error='Invalid credentials')

    return render_template('passkey_register.html')

@app.route('/api/passkey/register-options', methods=['POST'])
def passkey_register_options():
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not authenticated'}), 401

    hostname = request.host.split(':')[0]
    challenge = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
    session['passkey_challenge'] = challenge

    options = {
        'challenge': challenge,
        'rp': {
            'name': 'Passkey Demo',
            'id': hostname
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

    hostname = request.host.split(':')[0]
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
        'rpId': hostname,
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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, ssl_context='adhoc')
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pyotp
import qrcode
import io
import base64
from functools import wraps
import secrets
import os
import json

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Simple in-memory user database
users = {
    "admin": {
        "password": "password123",
        "mfa_secret": None,
        "passkey_credentials": []  # Store passkey credentials
    }
}

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
# MFA Authentication Routes
# ============================================

@app.route('/mfa-login', methods=['GET', 'POST'])
def mfa_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in users and users[username]['password'] == password:
            session['username'] = username
            session['auth_method'] = 'mfa'
            session['mfa_verified'] = False
            session['passkey_verified'] = False

            # If user has MFA setup, redirect to MFA verification
            if users[username]['mfa_secret']:
                return redirect(url_for('verify_mfa'))
            else:
                # If no MFA setup, redirect to setup
                return redirect(url_for('setup_mfa'))
        else:
            return render_template('mfa_login.html', error='Invalid credentials')

    return render_template('mfa_login.html')

@app.route('/setup-mfa')
def setup_mfa():
    if 'username' not in session:
        return redirect(url_for('mfa_login'))

    username = session['username']

    # Generate MFA secret
    secret = pyotp.random_base32()
    users[username]['mfa_secret'] = secret

    # Generate QR code
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
        secret = users[username]['mfa_secret']

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

        if username in users and users[username]['password'] == password:
            session['username'] = username
            session['auth_method'] = 'passkey'
            session['passkey_verified'] = False
            return render_template('passkey_register.html', username=username)
        else:
            return render_template('passkey_register.html', error='Invalid credentials')

    return render_template('passkey_register.html')

# API endpoints for passkey
@app.route('/api/passkey/register-options', methods=['POST'])
def passkey_register_options():
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not authenticated'}), 401

    # Generate challenge
    challenge = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
    session['passkey_challenge'] = challenge

    options = {
        'challenge': challenge,
        'rp': {
            'name': 'Passkey Demo',
            'id': 'localhost'
        },
        'user': {
            'id': base64.urlsafe_b64encode(username.encode()).decode('utf-8').rstrip('='),
            'name': username,
            'displayName': username
        },
        'pubKeyCredParams': [
            {'type': 'public-key', 'alg': -7},   # ES256
            {'type': 'public-key', 'alg': -257}  # RS256
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

    # In production, you would verify the credential properly
    # For demo purposes, we'll store it
    users[username]['passkey_credentials'].append({
        'id': credential.get('id'),
        'rawId': credential.get('rawId'),
        'type': credential.get('type')
    })

    session['passkey_verified'] = True

    return jsonify({'success': True})

@app.route('/api/passkey/login-options', methods=['POST'])
def passkey_login_options():
    data = request.json
    username = data.get('username')

    if username not in users:
        return jsonify({'error': 'User not found'}), 404

    if not users[username]['passkey_credentials']:
        return jsonify({'error': 'No passkey registered'}), 404

    # Generate challenge
    challenge = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
    session['passkey_challenge'] = challenge
    session['username'] = username

    # Get user's credential IDs
    allowed_credentials = [
        {
            'type': 'public-key',
            'id': cred['rawId']
        }
        for cred in users[username]['passkey_credentials']
    ]

    options = {
        'challenge': challenge,
        'timeout': 60000,
        'rpId': 'localhost',
        'allowCredentials': allowed_credentials,
        'userVerification': 'required'
    }

    return jsonify(options)

@app.route('/api/passkey/login-verify', methods=['POST'])
def passkey_login_verify():
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not authenticated'}), 401

    # In production, verify the assertion properly
    # For demo, we'll accept it
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
    app.run(debug=True, port=5000, ssl_context='adhoc')

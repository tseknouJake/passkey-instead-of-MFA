from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pyotp
import qrcode
import io
import base64
from functools import wraps
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Generate a secure secret key

# Simple in-memory user database (replace with real database in production)
users = {
    "admin": {
        "password": "password123",  # In production, use hashed passwords!
        "mfa_secret": None
    }
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or not session.get('mfa_verified'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'username' in session and session.get('mfa_verified'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in users and users[username]['password'] == password:
            session['username'] = username
            session['mfa_verified'] = False

            # If user has MFA setup, redirect to MFA verification
            if users[username]['mfa_secret']:
                return redirect(url_for('verify_mfa'))
            else:
                # If no MFA setup, redirect to setup
                return redirect(url_for('setup_mfa'))
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

@app.route('/setup-mfa')
def setup_mfa():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    # Generate MFA secret
    secret = pyotp.random_base32()
    users[username]['mfa_secret'] = secret

    # Generate QR code
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(username, issuer_name="MyWebsite")

    # Create QR code image
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return render_template('setup_mfa.html', qr_code=img_str, secret=secret)

@app.route('/verify-mfa', methods=['GET', 'POST'])
def verify_mfa():
    if 'username' not in session:
        return redirect(url_for('login'))

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

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=session['username'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)

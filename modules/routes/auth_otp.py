"""
Multi-Factor Authentication (MFA) routes using TOTP.

Handles:
- MFA login
- MFA setup (QR code generation)
- MFA verification
"""

#TODO: use just OTP without MFA (for consistency, according to the feedback from examiners at proposal discussion)
# can be done at a later stage - not necessary for the prototype

from flask import Blueprint, render_template, request, redirect, url_for, session
import pyotp
import qrcode
import io
import base64
from modules.services.user_service import get_user, update_mfa_secret

auth_otp = Blueprint('auth_otp', __name__, url_prefix='/auth')


@auth_otp.route('/mfa-login', methods=['GET', 'POST'])
def mfa_login():
    """
    MFA login route.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = get_user(username)
        if user and user.get('password') == password:
            session['username'] = username
            session['auth_method'] = 'mfa'
            session['mfa_verified'] = False
            session['passkey_verified'] = False
            session['classic_verified'] = False
            session['social_verified'] = False

            if user and user.get('mfa_secret'):
                return redirect(url_for('auth_otp.verify_mfa'))
            else:
                return redirect(url_for('auth_otp.setup_mfa'))
        else:
            return render_template('mfa_login.html', error='Invalid credentials')

    return render_template('mfa_login.html')


@auth_otp.route('/setup-mfa')
def setup_mfa():
    """
    Generate a TOTP secret and QR code for MFA setup.
    """

    if 'username' not in session: #TODO: potentially switch to using login_required here
        return redirect(url_for('auth_otp.mfa_login'))

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


@auth_otp.route('/verify-mfa', methods=['GET', 'POST'])
def verify_mfa():
    """
    Verify the TOTP code submitted by the user.
    """

    if 'username' not in session: #TODO: potentially switch to using login_required here
        return redirect(url_for('auth_otp.mfa_login'))

    username = session['username']

    if request.method == 'POST':
        token = request.form.get('token')
        user = get_user(username)
        secret = user.get('mfa_secret')

        totp = pyotp.TOTP(secret)
        if totp.verify(token, valid_window=1):
            session['mfa_verified'] = True
            session['classic_verified'] = False
            session['social_verified'] = False
            return redirect(url_for('main.dashboard'))
        else:
            return render_template('verify_mfa.html', error='Invalid MFA code')

    return render_template('verify_mfa.html')
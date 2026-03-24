"""
Passkey (WebAuthn) authentication routes.

Handles:
- Passkey registration
- Passkey login
- WebAuthn API endpoints
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect
import os
import base64

from modules.services.user_service import get_user, add_passkey_credential
from modules.utils.passkey_helpers import normalize_passkey_host, get_passkey_rp_id

auth_passkey = Blueprint('auth_passkey', __name__)

@auth_passkey.before_request
def normalize_passkey_origin():
    """
    Normalize the request origin for passkey (WebAuthn) compatibility.

    Ensures that the hostname used in the request matches the expected
    relying party ID (RP ID), especially when developing locally.

    If the hostname differs (e.g., 127.0.0.1 vs localhost), the request
    is redirected to a normalized host.

    Returns:
        Response | None: A redirect response if normalization is needed,
        otherwise None to continue processing.
    """

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

    return redirect(
        f"{request.scheme}://{target_host}{request.full_path.rstrip('?')}",
        code=302
    )


#TODO: are methods needed here?
@auth_passkey.route('/passkey-login', methods=['GET', 'POST'])
def passkey_login():
    """
    Render passkey login page.
    """
    return render_template('passkey_login.html')


@auth_passkey.route('/passkey-register', methods=['GET', 'POST'])
def passkey_register():
    """
    Authenticate user before allowing passkey registration.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = get_user(username)
        if user and user.get('password') == password:
            session['username'] = username
            session['auth_method'] = 'passkey'
            session['passkey_verified'] = False
            session['classic_verified'] = False
            session['social_verified'] = False

            return render_template('passkey_register.html', username=username)
        else:
            return render_template('passkey_register.html', error='Invalid credentials')

    return render_template('passkey_register.html')


@auth_passkey.route('/api/passkey/register-options', methods=['POST'])
def passkey_register_options():
    """
    Generate WebAuthn registration options for the client.

    Creates a challenge and returns the PublicKeyCredentialCreationOptions
    required for registering a new passkey.

    Stores the challenge in the session for later verification.

    Returns:
        JSON: Registration options including challenge, RP info, and user info.
    """

    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not authenticated'}), 401

    rp_id = get_passkey_rp_id()

    challenge = base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip('=')
    session['passkey_challenge'] = challenge

    options = {
        'challenge': challenge,
        'rp': {
            'name': 'Passkey Demo',
            'id': rp_id
        },
        'user': {
            'id': base64.urlsafe_b64encode(username.encode()).decode().rstrip('='), #TODO: don't we have a decrypt function for this?
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


@auth_passkey.route('/api/passkey/register-verify', methods=['POST'])
def passkey_register_verify():
    """
    Verify and store a newly created passkey credential.

    Receives the credential from the client after WebAuthn registration
    and stores it in the user's record.

    Marks the session as passkey-verified.

    Returns:
        JSON: सफलता response indicating successful registration.
    """

    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not authenticated'}), 401

    credential = request.json

    add_passkey_credential(username, credential)

    session['passkey_verified'] = True

    return jsonify({'success': True})


@auth_passkey.route('/api/passkey/login-options', methods=['POST'])
def passkey_login_options():
    """
    Generate WebAuthn authentication options for login.

    Creates a challenge and returns the PublicKeyCredentialRequestOptions
    for verifying an existing passkey.

    Includes allowed credentials for the user.

    Stores the challenge and username in the session.

    Returns:
        JSON: Authentication options including challenge and allowed credentials.
    """

    data = request.json
    username = data.get('username')

    user = get_user(username)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not user.get('passkey_credentials'):
        return jsonify({'error': 'No passkey registered'}), 404

    rp_id = get_passkey_rp_id()

    challenge = base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip('=') #TODO: same as before - decryption?
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


@auth_passkey.route('/api/passkey/login-verify', methods=['POST'])
def passkey_login_verify():
    """
    Verify a passkey authentication response.

    Marks the user as authenticated via passkey after successful verification.

    (Note: Cryptographic verification should be implemented for production.)

    Returns:
        JSON: Success response indicating authentication completion.
    """
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not authenticated'}), 401

    session['auth_method'] = 'passkey'
    session['passkey_verified'] = True
    session['mfa_verified'] = False
    session['classic_verified'] = False
    session['social_verified'] = False

    return jsonify({'success': True})
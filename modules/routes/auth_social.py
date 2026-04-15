"""
Social authentication routes (Google OAuth).

Handles:
- Rendering login page
- Redirecting to Google
- Handling OAuth callback
"""

from flask import Blueprint, render_template, redirect, session, url_for, request
from modules.services.user_service import get_user, create_user, add_email_credential, get_user_by_email
from modules.utils.oauth import get_google_oauth, get_google_oauth_error, get_google_redirect_uri
from modules.routes.auth_classic import create_user_session
from flask import current_app

auth_social = Blueprint('auth_social', __name__, url_prefix='/auth')


@auth_social.route('/google-login-page')
def google_login_page():
    """
    Render the Google login page with configuration status.
    """
    oauth_error = get_google_oauth_error(current_app)

    return render_template(
        'google_login.html',
        error=oauth_error,
        oauth_available=oauth_error is None,
        callback_uri=get_google_redirect_uri(current_app)
    )


@auth_social.route('/login/google')
def login_google():
    """
    Redirect user to Google OAuth provider.
    """
    oauth_error = get_google_oauth_error(current_app)
    if oauth_error:
        return render_template(
            'google_login.html',
            error=oauth_error,
            oauth_available=False,
            callback_uri=get_google_redirect_uri(current_app)
        ), 503

    oauth = get_google_oauth()
    return oauth.google.authorize_redirect(get_google_redirect_uri(current_app))


@auth_social.route('/google/callback')
def google_callback():
    """
    Handle Google OAuth callback and log the user in.

    Authors:
        | Irina Vilcu
        | Leah Goldin
    """
    oauth_error = get_google_oauth_error(current_app)
    if oauth_error:
        return render_template(
            'google_login.html',
            error=oauth_error,
            oauth_available=False,
            callback_uri=get_google_redirect_uri(current_app)
        ), 503

    oauth = get_google_oauth()

    try:
        token = oauth.google.authorize_access_token()
    except Exception:
        return render_template(
            'google_login.html',
            error='Google OAuth callback failed. Verify client credentials and redirect URI.',
            oauth_available=False,
            callback_uri=get_google_redirect_uri(current_app)
        ), 401

    user_info = token.get('userinfo')
    if not user_info:
        user_info = oauth.google.parse_id_token(
            token, nonce=session.get('oauth_nonce'))

    email = user_info['email']

    if session.get('oauth_purpose') == 'setup':
        session.pop('oauth_purpose', None)
        username = session.get('username')
        if username:
            try:
                existing_user = get_user_by_email(email)
                if existing_user:
                    return render_template(
                        'google_login.html',
                        error='This Google account is already linked to another account. Try logging in.',
                        oauth_available=True,
                        callback_uri=get_google_redirect_uri(current_app)
                    ), 409
            except ValueError as e:
                return render_template(
                    'google_login.html',
                    error='Account linking failed due to a database integrity error (duplicate emails). Try with a different email address.',
                    oauth_available=True,
                    callback_uri=get_google_redirect_uri(current_app)
                ), 500

            add_email_credential(username, email)
            
            session['social_verified'] = True
            session['classic_verified'] = False
            session['mfa_verified'] = False
            session['passkey_verified'] = False
            return redirect('/questionnaire')
        return redirect(url_for('main.index'))

    try:
        user_record = get_user_by_email(email)
    except ValueError as e:
        return render_template(
            'google_login.html',
            error='Login failed due to a database integrity error (duplicate emails). Try with a different email address.',
            oauth_available=True,
            callback_uri=get_google_redirect_uri(current_app)
        ), 500

    if not user_record:
        session['pending_social_email'] = email
        session['pending_social_provider'] = 'google'
        return redirect(url_for('auth_social.set_up_password'))

    actual_username = user_record['username']
    create_user_session(actual_username, auth_method='social')
    session['social_verified'] = True
    return redirect('/questionnaire')


@auth_social.route('/social/set-up-password', methods=['GET', 'POST'])
def set_up_password():
    """
        Handle password setup for users registering via social login.

        Authors:
            | Irina Vilcu
            | Leah Goldin
            | Mariam Kamara
            | Condoleezza Agbeko
    """

    if 'pending_social_email' not in session:
        return redirect(url_for('main.index'))
    email = session['pending_social_email']

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username:
            return render_template('register.html', error='Please enter a username.', username=username)
        if get_user(username):
            return render_template('register.html', error='Username already taken. Please choose another one.', username=username)
        if not password:
            return render_template('register.html', error='Please enter a password.', username=username)
        if len(password) < 8:
            return render_template('register.html', error='Password must be at least 8 characters.', username=username)
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match.', username=username)

        session.pop('pending_social_email')
        session.pop('pending_social_provider')

        create_user(username, password) 
        add_email_credential(username, email) 
        create_user_session(username, auth_method='social')
        session['social_verified'] = True
        return redirect('/questionnaire')
        
    return render_template('register.html', error='')

@auth_social.route('/social/setup-social')
def setup_social():
    if 'username' not in session:
        return redirect(url_for('main.index'))

    oauth_error = get_google_oauth_error(current_app)
    if oauth_error:
        return render_template(
            'google_login.html',
            error=oauth_error,
            oauth_available=False,
            callback_uri=get_google_redirect_uri(current_app)
        ), 503

    session['oauth_purpose'] = 'setup'
    oauth = get_google_oauth()
    return oauth.google.authorize_redirect(get_google_redirect_uri(current_app))

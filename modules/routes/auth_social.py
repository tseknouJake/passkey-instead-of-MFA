"""
Social authentication routes (Google OAuth).

Handles:
- Rendering login page
- Redirecting to Google
- Handling OAuth callback
"""

#TODO: doesn't work in deployment (nor on a foreign host, where env variables don't match localy)
#TODO: add set up route to link to an existing account
#TODO: require entering a password, when loging in for the first time, in order to save as an account that can be used with other routes
# @Irina

from flask import Blueprint, render_template, redirect, session, url_for
from modules.services.user_service import get_user, create_social_user
from modules.utils.oauth import get_google_oauth, get_google_oauth_error, get_google_redirect_uri
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


@auth_social.route('/auth/google/callback')
def google_callback():
    """
    Handle Google OAuth callback and log the user in.
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
"""
Main application routes.

Handles general navigation such as landing page,
dashboard, and logout.
"""

from flask import Blueprint, render_template, session, redirect, url_for, send_from_directory
from modules.utils.decorators import cancel_login_timer, login_required, complete_login_timer, cancel_login_timer

main = Blueprint('main', __name__)


@main.route('/')
@cancel_login_timer
def index():
    """
    Landing page.

    Redirects authenticated users to the dashboard.
    """
    if is_authenticated():
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')


def is_authenticated():
    return 'username' in session and (
        session.get('mfa_verified') or
        session.get('passkey_verified') or
        session.get('classic_verified') or
        session.get('social_verified')
    )


@main.route('/dashboard')
@login_required
@complete_login_timer
def dashboard():
    """
    User dashboard.

    Accessible only after successful authentication.
    """
    username = session['username']
    auth_method = session.get('auth_method')
    return render_template(
        'dashboard.html',
        username=username,
        auth_method=auth_method
    )


@main.route('/questionnaire')
@complete_login_timer
def questionnaire():
    return send_from_directory('questionnaire', 'index.html')


@main.route('/questionnaire/<path:filename>')
def questionnaire_static(filename):
    return send_from_directory('questionnaire', filename)


@main.route('/logout')
def logout():
    """
    Log out the current user by clearing the session.
    """
    session.clear()
    return redirect(url_for('main.index'))

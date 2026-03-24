"""
Main application routes.

Handles general navigation such as landing page,
dashboard, and logout.
"""

from flask import Blueprint, render_template, session, redirect, url_for
from modules.utils.decorators import login_required

main = Blueprint('main', __name__)


@main.route('/')
def index():
    """
    Landing page.

    Redirects authenticated users to the dashboard.
    """
    if 'username' in session and (
        session.get('mfa_verified') or
        session.get('passkey_verified') or
        session.get('classic_verified') or
        session.get('social_verified')
    ):
        return redirect(url_for('main.dashboard'))

    return render_template('index.html')


@main.route('/dashboard')
@login_required
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


@main.route('/logout')
def logout():
    """
    Log out the current user by clearing the session.
    """
    session.clear()
    return redirect(url_for('main.index'))
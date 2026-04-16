"""
Main application routes.

Handles general navigation such as landing page,
dashboard, and logout.
"""

from flask import Blueprint, render_template, session, redirect, url_for, send_from_directory
from modules.services.study_service import (
    StudyStorageSetupError,
    get_auth_method_label,
    get_study_response,
)
from modules.utils.decorators import login_required

main = Blueprint('main', __name__)


@main.route('/')
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
def dashboard():
    """
    User dashboard.

    Accessible only after successful authentication.
    """
    username = session['username']
    auth_method = session.get('auth_method')
    study_error = None
    study_response = None

    if auth_method:
        try:
            study_response = get_study_response(username, auth_method)
        except StudyStorageSetupError as exc:
            study_error = str(exc)

    return render_template(
        'dashboard.html',
        username=username,
        auth_method=auth_method,
        auth_method_label=get_auth_method_label(auth_method),
        study_completed=study_response is not None,
        study_available=study_error is None,
        study_error=study_error,
    )


@main.route('/questionnaire')
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

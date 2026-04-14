"""
Classic username/password authentication routes.

Handles:
- User registration
- Classic login
"""

from flask import Blueprint, render_template, request, redirect, url_for, session
from modules.services.user_service import get_user, create_user, verify_user_password
from modules.utils.decorators import increment_failed_login, login_required
from modules.utils.decorators import start_login_timer

auth_classic = Blueprint('auth_classic', __name__, url_prefix='/auth')


def validate_registration(username, password, confirm_password):
    """
    Validate registration from input
    """
    if not username or not password:
        return 'Username and password are required'
    if len(password) < 8:
        return 'Password must be at least 8 characters'
    if password != confirm_password:
        return 'Passwords do not match'
    if get_user(username):
        return 'Username already exists'
    return None


def create_user_session(username, auth_method='classic'):
    session['username'] = username
    session['auth_method'] = auth_method
    session['classic_verified'] = auth_method == 'classic'
    session['mfa_verified'] = False
    session['passkey_verified'] = False
    session['social_verified'] = False


@auth_classic.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration route.
    """

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        error = validate_registration(username, password, confirm_password)
        if error:
            return render_template('register.html', error=error)

        create_user(username, password)
        create_user_session(username)
        session['registered'] = True

        return redirect(url_for('auth_classic.setup_choice'))

    return render_template('register.html')


@auth_classic.route('/setup-choice')
@login_required
def setup_choice():
    """
    Choose authentication method after registration.
    """
    if 'username' not in session:
        return redirect(url_for('main.index'))
    return render_template('setup_choice.html', username=session['username'])


@auth_classic.route('/login', methods=['GET', 'POST'])
@start_login_timer
def password_login():
    """
    Classic login route (username + password).
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = get_user(username)
        if not verify_user_password(user, password):
            increment_failed_login()
            return render_template('login.html', error='Invalid credentials')

        create_user_session(username)

        return redirect('/questionnaire')

    return render_template('login.html')

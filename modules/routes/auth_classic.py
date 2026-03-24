"""
Classic username/password authentication routes.

Handles:
- User registration
- Classic login
"""

from flask import Blueprint, render_template, request, redirect, url_for, session
from modules.services.user_service import get_user, create_user
from modules.utils.decorators import login_required

auth_classic = Blueprint('auth_classic', __name__, url_prefix='/auth')

@auth_classic.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration route.
    """
    #TODO: refactor into multiple functions
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not password:
            return render_template('register.html', error='Username and password are required')

        if len(password) < 8:
            return render_template('register.html', error='Password must be at least 8 characters')

        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')

        if get_user(username):
            return render_template('register.html', error='Username already exists')

        create_user(username, password)

        session['username'] = username
        session['auth_method'] = 'classic'
        session['classic_verified'] = True
        session['mfa_verified'] = False
        session['passkey_verified'] = False
        session['social_verified'] = False
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

#TODO: rename to just login maybe? because when it is used, it is called under "auth_classic" anyway
@auth_classic.route('/login', methods=['GET', 'POST'])
def password_login():
    """
    Classic login route (username + password).
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = get_user(username)
        if user and user.get('password') == password:
            session['username'] = username
            session['auth_method'] = 'classic'
            session['classic_verified'] = True
            session['mfa_verified'] = False
            session['passkey_verified'] = False
            session['social_verified'] = False
            return redirect(url_for('main.dashboard'))

        return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')
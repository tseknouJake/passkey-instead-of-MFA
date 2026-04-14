"""
Custom decorators used across the application.

This module contains reusable decorators for handling
authentication and access control.
"""

# TODO: @Enna add a time measuring feature that will be reused in all the routes and will log all the data in some
# kind of log file (can be txt for now)

from functools import wraps
from flask import session, redirect, url_for

import time

login_time = None
login_method = None
failed_logins = 0

def increment_failed_login():
    global failed_logins
    failed_logins += 1

def start_login_timer(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        global login_time
        global login_method

        if not login_time:
            login_time = time.time()
            login_method = f.__name__

        return f(*args, **kwargs)
    return decorated_function

def cancel_login_timer(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        global login_time
        global login_method
        global failed_logins

        failed_logins = 0
        login_time = None
        login_method = None

        return f(*args, **kwargs)
    return decorated_function

def complete_login_timer(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        global login_time
        global login_method
        global failed_logins

        if login_time:
            now = time.time()
            elapsed = now - login_time

            with open("log.txt", "a") as file:
                _ = file.write(f"login method: {login_method}, time elapsed: {elapsed}, user: {session['username']}, failed logins: {failed_logins}\n")

            login_time = None

        failed_logins = 0

        return f(*args, **kwargs)
    return decorated_function
    

def login_required(f):
    """
    Ensure that a user is authenticated before accessing a route.

    This decorator checks the session for a logged-in user and verifies
    that the appropriate authentication method has been completed.

    Redirects the user to the appropriate login step if not verified.

    Args:
        f (function): The route function to protect.

    Returns:
        function: The wrapped function.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('main.index'))

        auth_method = session.get('auth_method')

        if auth_method == 'mfa' and not session.get('mfa_verified'):
            return redirect(url_for('auth_otp.mfa_login'))

        elif auth_method == 'passkey' and not session.get('passkey_verified'):
            return redirect(url_for('auth_passkey.passkey_login'))

        elif auth_method == 'social' and not session.get('social_verified'):
            return redirect(url_for('main.index'))

        elif auth_method == 'classic' and not session.get('classic_verified'):
            return redirect(url_for('auth_classic.password_login'))

        return f(*args, **kwargs)
    return decorated_function

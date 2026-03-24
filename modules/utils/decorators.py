"""
Custom decorators used across the application.

This module contains reusable decorators for handling
authentication and access control.
"""
#TODO: make a class maybe?

from functools import wraps
from flask import session, redirect, url_for

def login_required(f): #TODO: refactor nested function
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
            return redirect(url_for('mfa_login'))

        elif auth_method == 'passkey' and not session.get('passkey_verified'):
            return redirect(url_for('passkey_login'))

        elif auth_method == 'social' and not session.get('social_verified'):
            return redirect(url_for('main.index'))

        elif auth_method == 'classic' and not session.get('classic_verified'):
            return redirect(url_for('password_login'))

        return f(*args, **kwargs)
    return decorated_function
"""
Service layer for handling user-related operations.

This module abstracts all database interactions and ensures
that encryption, hashing, and credential verification are handled consistently.
"""

import logging
import os
from pathlib import Path

from modules.database import supabase
from modules.utils.storage_fallback import Storage
from modules.utils.encryptor import (
    encrypt_data,
    hash_password,
    is_password_hash,
    maybe_decrypt_data,
    verify_password_value,
)

logger = logging.getLogger(__name__)
LOCAL_USERS_FILE = Path(
    (os.environ.get("LOCAL_USERS_FILE") or Path(__file__).resolve().parents[2] / "users.json")
).expanduser()
_storage = Storage(
    path=LOCAL_USERS_FILE,
    default={},
    label="user store",
    supabase_client=supabase,
)


def _get_local_user_record(username: str) -> dict | None:
    """
    Retrieve a local user record and attach the username field used by the app.
    """
    user = _storage.read().get(username)
    if not isinstance(user, dict):
        return None
    return {"username": username, **user}


def get_user(username: str) -> dict | None:
    """
    Retrieve a user from the database by username and decrypt non-password sensitive fields.

    Args:
        username (str): The username of the user.

    Returns:
        dict | None: The user object if found, otherwise None.
    """
    def remote_operation():
        response = supabase.table("users").select("*").eq("username", username).execute()
        return response.data[0] if response.data else None

    def local_operation():
        return _get_local_user_record(username)

    user = _storage.run(remote_operation, local_operation)

    if user:
        if user.get("mfa_secret"): #TODO: what is that and why?
            user["mfa_secret"] = maybe_decrypt_data(user["mfa_secret"])

    return user

def get_user_by_email(email: str) -> dict | None:
    """
    Retrieve a user by their email.

    Args:
        email (str): The email of the user.

    Returns:
        dict | None: The user object if found, otherwise None.

    Authors:
        | Leah Goldin
    """
    response = supabase.table("users").select("*").eq("email", email).execute()

    if response.data:
        if len(response.data) > 1:
            raise ValueError(f"Database Integrity Error: Multiple users found with the same email ({email})")
        user = response.data[0]
    else:
        user = None

    if user:
        if user.get("mfa_secret"): #TODO: what is that and why?
            user["mfa_secret"] = maybe_decrypt_data(user["mfa_secret"])

    return user


def create_user(username: str, password: str) -> None:
    """
    Create a new user with a hashed password.

    Args:
        username (str): The username.
        password (str): The plaintext password.
    """
    password_hash = hash_password(password)

    def remote_operation():
        supabase.table("users").insert({
            "username": username,
            "password": password_hash
        }).execute()

    def local_operation():
        users = _storage.read()
        users[username] = {
            "password": password_hash,
            "mfa_secret": None,
            "passkey_credentials": []
        }
        _storage.write(users)

    _storage.run(remote_operation, local_operation)


def update_user_password(username: str, password_value: str) -> None:
    """
    Update a user's stored password value.
    """
    def remote_operation():
        supabase.table("users").update({
            "password": password_value
        }).eq("username", username).execute()

    def local_operation():
        users = _storage.read()
        user = users.setdefault(username, {})
        user["password"] = password_value
        user.setdefault("mfa_secret", None)
        user.setdefault("passkey_credentials", [])
        _storage.write(users)

    _storage.run(remote_operation, local_operation)


def verify_user_password(user: dict | None, candidate_password: str | None) -> bool:
    """
    Verify a user's password and lazily migrate legacy values to hashes.
    """
    if not user or not candidate_password:
        return False

    stored_password = user.get("password")
    if not verify_password_value(stored_password, candidate_password):
        return False

    if stored_password and not is_password_hash(stored_password):
        password_hash = hash_password(candidate_password)
        update_user_password(user["username"], password_hash)
        user["password"] = password_hash

    return True

def update_mfa_secret(username: str, secret: str) -> None:
    """
    Store an encrypted MFA secret for a user.

    Args:
        username (str): The username.
        secret (str): The MFA secret.
    """
    encrypted_secret = encrypt_data(secret)

    def remote_operation():
        supabase.table("users").update({
            "mfa_secret": encrypted_secret
        }).eq("username", username).execute()

    def local_operation():
        users = _storage.read()
        user = users.setdefault(username, {})
        user["mfa_secret"] = encrypted_secret
        user.setdefault("password", None)
        user.setdefault("passkey_credentials", [])
        _storage.write(users)

    _storage.run(remote_operation, local_operation)


def add_passkey_credential(username: str, credential: dict) -> None:
    """
    Add a passkey credential to a user's stored credentials.

    Args:
        username (str): The username.
        credential (dict): The WebAuthn credential object.
    """
    user = get_user(username) or {"username": username}

    current_credentials = user.get("passkey_credentials") or []
    updated_credentials = current_credentials + [credential]

    def remote_operation():
        supabase.table("users").update({
            "passkey_credentials": updated_credentials
        }).eq("username", username).execute()

    def local_operation():
        users = _storage.read()
        local_user = users.setdefault(username, {})
        local_user["passkey_credentials"] = updated_credentials
        local_user.setdefault("password", None)
        local_user.setdefault("mfa_secret", None)
        _storage.write(users)

    _storage.run(remote_operation, local_operation)


def add_email_credential(username: str, email: str) -> None:
    """
    Add an email credential to a user's stored credentials.

    Args:
        username (str): The username.
        email (str): The user's email address.

    Authors:
        | Leah Goldin
    """

    def remote_operation():
        supabase.table("users").update({
            "email": email
        }).eq("username", username).execute()

    def local_operation():
        users = _storage.read()
        local_user = users.setdefault(username, {})
        local_user["email"] = email
        local_user.setdefault("password", None)
        _storage.write(users)

    _storage.run(remote_operation, local_operation)

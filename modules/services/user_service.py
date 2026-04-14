"""
Service layer for handling user-related operations.

This module abstracts all database interactions and ensures
that encryption, hashing, and credential verification are handled consistently.
"""

import json
import logging
import os
from pathlib import Path

import httpx

from modules.database import supabase
from modules.utils.encryptor import (
    encrypt_data,
    hash_password,
    is_password_hash,
    maybe_decrypt_data,
    verify_password_value,
)

logger = logging.getLogger(__name__)
AUTH_STORAGE_BACKEND = (os.environ.get("AUTH_STORAGE_BACKEND") or "auto").strip().lower()
LOCAL_USERS_FILE = Path(
    (os.environ.get("LOCAL_USERS_FILE") or Path(__file__).resolve().parents[2] / "users.json")
).expanduser()
_fallback_logged = False


def _log_local_fallback(reason: str) -> None:
    """
    Log the storage fallback once so local development failures stay visible
    without spamming every request.
    """
    global _fallback_logged
    if _fallback_logged:
        return

    logger.warning(
        "Supabase unavailable; falling back to local user store at %s (%s)",
        LOCAL_USERS_FILE,
        reason,
    )
    _fallback_logged = True


def _read_local_users() -> dict:
    """
    Load the local JSON user store.
    """
    if not LOCAL_USERS_FILE.exists():
        return {}

    try:
        with LOCAL_USERS_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        logger.exception("Failed to read local user store from %s", LOCAL_USERS_FILE)
        return {}

    return data if isinstance(data, dict) else {}


def _write_local_users(users: dict) -> None:
    """
    Persist the local JSON user store atomically.
    """
    LOCAL_USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_path = LOCAL_USERS_FILE.with_suffix(f"{LOCAL_USERS_FILE.suffix}.tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(users, handle, indent=4)
        handle.write("\n")
    temp_path.replace(LOCAL_USERS_FILE)


def _get_local_user_record(username: str) -> dict | None:
    """
    Retrieve a local user record and attach the username field used by the app.
    """
    user = _read_local_users().get(username)
    if not isinstance(user, dict):
        return None
    return {"username": username, **user}


def _use_local_store() -> bool:
    """
    Determine whether requests should use the local JSON store directly.
    """
    if AUTH_STORAGE_BACKEND == "file":
        return True

    if AUTH_STORAGE_BACKEND == "supabase":
        return False

    if supabase is None:
        _log_local_fallback("Supabase configuration is missing")
        return True

    return False


def _with_storage_fallback(remote_operation, local_operation):
    """
    Use Supabase when available and reachable, otherwise fall back to the local store.
    """
    if _use_local_store():
        return local_operation()

    try:
        return remote_operation()
    except httpx.RequestError as exc:
        _log_local_fallback(str(exc))
        return local_operation()


def get_user(username: str) -> dict | None:
    """
    Retrieve a user by username and decrypt non-password sensitive fields.

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

    user = _with_storage_fallback(remote_operation, local_operation)

    if user:
        if user.get("mfa_secret"):
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
        users = _read_local_users()
        users[username] = {
            "password": password_hash,
            "mfa_secret": None,
            "passkey_credentials": []
        }
        _write_local_users(users)

    _with_storage_fallback(remote_operation, local_operation)


def update_user_password(username: str, password_value: str) -> None:
    """
    Update a user's stored password value.
    """
    def remote_operation():
        supabase.table("users").update({
            "password": password_value
        }).eq("username", username).execute()

    def local_operation():
        users = _read_local_users()
        user = users.setdefault(username, {})
        user["password"] = password_value
        user.setdefault("mfa_secret", None)
        user.setdefault("passkey_credentials", [])
        _write_local_users(users)

    _with_storage_fallback(remote_operation, local_operation)


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
        users = _read_local_users()
        user = users.setdefault(username, {})
        user["mfa_secret"] = encrypted_secret
        user.setdefault("password", None)
        user.setdefault("passkey_credentials", [])
        _write_local_users(users)

    _with_storage_fallback(remote_operation, local_operation)


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
        users = _read_local_users()
        local_user = users.setdefault(username, {})
        local_user["passkey_credentials"] = updated_credentials
        local_user.setdefault("password", None)
        local_user.setdefault("mfa_secret", None)
        _write_local_users(users)

    _with_storage_fallback(remote_operation, local_operation)

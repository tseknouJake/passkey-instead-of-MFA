"""
Service layer for handling user-related operations.

This module abstracts all database interactions and ensures
that encryption, hashing, and credential verification are handled consistently.
"""

from modules.database import supabase
from modules.utils.encryptor import (
    encrypt_data,
    hash_password,
    is_password_hash,
    maybe_decrypt_data,
    verify_password_value,
)


def get_user(username: str) -> dict | None:
    """
    Retrieve a user by username and decrypt non-password sensitive fields.

    Args:
        username (str): The username of the user.

    Returns:
        dict | None: The user object if found, otherwise None.
    """
    response = supabase.table("users").select("*").eq("username", username).execute()
    user = response.data[0] if response.data else None

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

    supabase.table("users").insert({
        "username": username,
        "password": password_hash
    }).execute()


def update_user_password(username: str, password_value: str) -> None:
    """
    Update a user's stored password value.
    """
    supabase.table("users").update({
        "password": password_value
    }).eq("username", username).execute()


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

    supabase.table("users").update({
        "mfa_secret": encrypted_secret
    }).eq("username", username).execute()


def add_passkey_credential(username: str, credential: dict) -> None:
    """
    Add a passkey credential to a user's stored credentials.

    Args:
        username (str): The username.
        credential (dict): The WebAuthn credential object.
    """
    user = get_user(username)

    current_credentials = user.get("passkey_credentials") or []
    updated_credentials = current_credentials + [credential]

    supabase.table("users").update({
        "passkey_credentials": updated_credentials
    }).eq("username", username).execute()


def add_email_credential(username: str, email: str) -> None:
    """
    Add an email credential to a user's stored credentials.

    Args:
        username (str): The username.
        email (str): The user's email address.

    Authors:
        | Leah Goldin
    """

    supabase.table("users").update({
        "email": email
    }).eq("username", username).execute()
"""
Service layer for handling user-related operations.

This module abstracts all database interactions and ensures
that encryption/decryption is handled consistently.
"""

from modules.database import supabase
from modules.utils.encryptor import encrypt_data, decrypt_data


def get_user(username: str) -> dict | None:
    """
    Retrieve a user by username and decrypt sensitive fields.

    Args:
        username (str): The username of the user.

    Returns:
        dict | None: The user object if found, otherwise None.
    """
    response = supabase.table("users").select("*").eq("username", username).execute()
    user = response.data[0] if response.data else None

    if user:
        if user.get("password"):
            user["password"] = decrypt_data(user["password"])
        if user.get("mfa_secret"):
            user["mfa_secret"] = decrypt_data(user["mfa_secret"])

    return user


def create_user(username: str, password: str) -> None:
    """
    Create a new user with an encrypted password.

    Args:
        username (str): The username.
        password (str): The plaintext password.
    """
    encrypted_password = encrypt_data(password)

    supabase.table("users").insert({
        "username": username,
        "password": encrypted_password
    }).execute()

#TODO: remove and use "create_user" instead (require entering a password at first login)
# @Irina
def create_social_user(username: str, provider: str) -> None:
    """
    Create a user registered via a social provider.

    Args:
        username (str): Typically the user's email.
        provider (str): The social provider (e.g., 'google').
    """
    supabase.table("users").insert({
        "username": username,
        "password": None
    }).execute()


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
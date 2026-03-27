"""
Utility module for handling symmetric encryption and decryption
using Fernet (AES-based encryption).

Also provides a fallback mechanism for generating a stable Flask
secret key when one is not explicitly configured.
"""

import os
import hashlib
import secrets
from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

FERNET_KEY = os.environ.get("FERNET_KEY")

if not FERNET_KEY:
    raise ValueError("FERNET_KEY environment variable not set")

f = Fernet(FERNET_KEY.encode())


def encrypt_data(data: str) -> str:
    """
    Encrypt a plaintext string using Fernet symmetric encryption.

    Args:
        data (str): The plaintext data to encrypt.

    Returns:
        str: The encrypted data as a base64-encoded string.
    """
    return f.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """
    Decrypt a previously encrypted string using Fernet.

    Args:
        encrypted_data (str): The encrypted base64-encoded string.

    Returns:
        str: The original decrypted plaintext.
    """
    return f.decrypt(encrypted_data.encode()).decode()


def maybe_decrypt_data(value: str | None) -> str | None:
    """
    Decrypt Fernet value when possible else return it unchanged.
    """
    if not value:
        return value

    try:
        return decrypt_data(value)
    except InvalidToken:
        return value


def is_password_hash(value: str | None) -> bool:
    """
    Checks if stored password is already a Werkzeug hash
    Returns:
        bool
    """
    return isinstance(value, str) and value.startswith(("scrypt:", "pbkdf2:"))


def hash_password(password: str) -> str:
    """
    Generate password hash
    """
    return generate_password_hash(password)


def verify_password_value(stored_password: str | None, candidate_password: str | None) -> bool:
    """
    Verify a candidate password against hashed or legacy stored values
    """
    if not stored_password or not candidate_password:
        return False

    if is_password_hash(stored_password):
        return check_password_hash(stored_password, candidate_password)

    legacy_password = maybe_decrypt_data(stored_password)
    return secrets.compare_digest(legacy_password, candidate_password)

def get_flask_secret_key() -> str:
    """
    Retrieve the Flask SECRET_KEY from environment variables.

    If not set, generates a deterministic fallback based on the
    Fernet key to ensure session consistency across gunicorn workers.

    Returns:
        str: A secret key suitable for Flask session signing.
    """
    configured_secret = (os.environ.get("SECRET_KEY") or "").strip()
    if configured_secret:
        return configured_secret

    return hashlib.sha256(FERNET_KEY.encode()).hexdigest()

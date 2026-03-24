"""
Utility module for handling symmetric encryption and decryption
using Fernet (AES-based encryption).

Also provides a fallback mechanism for generating a stable Flask
secret key when one is not explicitly configured.
"""

import os
import hashlib
from cryptography.fernet import Fernet
from dotenv import load_dotenv

#TODO: add password hashing @Jake

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
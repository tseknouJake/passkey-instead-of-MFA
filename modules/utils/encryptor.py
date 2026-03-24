import os
import hashlib
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

FERNET_KEY = os.environ.get("FERNET_KEY")

if not FERNET_KEY:
    raise ValueError("FERNET_KEY environment variable not set")

f = Fernet(FERNET_KEY.encode())


def encrypt_data(data: str) -> str:
    return f.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    return f.decrypt(encrypted_data.encode()).decode()

def get_flask_secret_key() -> str:
    configured_secret = (os.environ.get("SECRET_KEY") or "").strip()
    if configured_secret:
        return configured_secret

    return hashlib.sha256(FERNET_KEY.encode()).hexdigest()
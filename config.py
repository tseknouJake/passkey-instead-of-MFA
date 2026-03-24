import os
from dotenv import load_dotenv

def env_flag(name, default=False):
    """Return True if the given environment variable is set to a truthy value."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    """Flask configuration."""
    load_dotenv()

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = env_flag("SESSION_COOKIE_SECURE")
    PREFERRED_URL_SCHEME = "https" if env_flag("PREFERRED_URL_SCHEME_HTTPS") else "http"

    GOOGLE_CLIENT_ID = (os.getenv("GOOGLE_CLIENT_ID") or "").strip()
    GOOGLE_CLIENT_SECRET = (os.getenv("GOOGLE_CLIENT_SECRET") or "").strip()
    GOOGLE_REDIRECT_URI = (os.getenv("GOOGLE_REDIRECT_URI") or "").strip()

    FERNET_KEY = os.getenv("FERNET_KEY")
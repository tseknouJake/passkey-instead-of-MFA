from flask import Flask
import os
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
from modules.utils.oauth import init_oauth
from modules.utils.encryptor import get_flask_secret_key
from modules.routes import register_routes

#TODO: extract routes URLs to be reusable

load_dotenv()

app = Flask(__name__)

app.secret_key = get_flask_secret_key()

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

app.config["GOOGLE_CLIENT_ID"] = (os.environ.get("GOOGLE_CLIENT_ID") or "").strip()
app.config["GOOGLE_CLIENT_SECRET"] = (os.environ.get("GOOGLE_CLIENT_SECRET") or "").strip()
app.config["GOOGLE_REDIRECT_URI"] = (os.environ.get("GOOGLE_REDIRECT_URI") or "").strip()

def env_flag(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = env_flag("SESSION_COOKIE_SECURE")
app.config["PREFERRED_URL_SCHEME"] = "https" if env_flag("PREFERRED_URL_SCHEME_HTTPS") else "http"

init_oauth(app)
register_routes(app)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, ssl_context='adhoc')
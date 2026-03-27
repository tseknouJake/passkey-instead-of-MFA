from flask import Flask
import os
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config
from modules.utils.oauth import init_oauth
from modules.utils.encryptor import get_flask_secret_key
from modules.routes import register_routes
app = Flask(__name__)
app.config.from_object(Config)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

app.secret_key = get_flask_secret_key()

init_oauth(app)
register_routes(app)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, ssl_context='adhoc')
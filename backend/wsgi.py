"""
WSGI entry point for Gunicorn.
"""

import os
from app import create_app
from app.config import config_by_name

config_name = os.environ.get("FLASK_ENV", "development")
config_class = config_by_name.get(config_name)

app = create_app(config_class)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))



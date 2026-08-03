import os

from application.factory import create_app

# Config is the production config. Local dev and tests opt out via FLASK_CONFIG
# (see .flaskenv), which is excluded from the image - so production gets Config.
app = create_app(os.getenv("FLASK_CONFIG") or "application.config.Config")

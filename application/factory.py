from dotenv import load_dotenv
from flask import Flask, render_template

import application.models  # noqa: F401

load_dotenv()


def create_app(config_filename):
    app = Flask(__name__)
    app.config.from_object(config_filename)
    register_errorhandlers(app)
    register_blueprints(app)
    register_extensions(app)
    register_commands(app)
    return app


def register_errorhandlers(app):
    def render_error(error):
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, "code", 500)
        return render_template("{0}.html".format(error_code)), error_code

    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None


def register_blueprints(app):
    from application.frontend.views import frontend
    from application.search.views import search_bp
    from application.visualisations.views import visualisations_bp

    app.register_blueprint(frontend)
    app.register_blueprint(search_bp)
    app.register_blueprint(visualisations_bp)


def register_extensions(app):
    from application.extensions import db, migrate

    db.init_app(app)
    migrate.init_app(app, db)


def register_commands(app):
    from application.commands import sandbox_cli

    app.cli.add_command(sandbox_cli)

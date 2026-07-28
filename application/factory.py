from dotenv import load_dotenv
from flask import Flask, render_template

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
    from application.api.views import api_bp
    from application.collections.views import collections_bp
    from application.frontend.views import frontend
    from application.search.views import search_bp
    from application.visualisations.views import visualisations_bp

    app.register_blueprint(frontend)
    app.register_blueprint(visualisations_bp, prefix="/attic")
    app.register_blueprint(search_bp, url_prefix="/search")
    app.register_blueprint(collections_bp)
    app.register_blueprint(api_bp, url_prefix="/api")


def register_extensions(app):
    pass


def register_commands(app):
    from application.commands import sandbox_cli

    app.cli.add_command(sandbox_cli)

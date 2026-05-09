from flask import Blueprint, render_template, url_for

from application.visualisations.air_pollution.views import air_pollution
from application.visualisations.bank_rate.views import bank_rate

visualisations_bp = Blueprint("visualisations", __name__, url_prefix="/visualisations")
visualisations_bp.register_blueprint(air_pollution)
visualisations_bp.register_blueprint(bank_rate)


@visualisations_bp.route("/")
def index():
    breadcrumbs = [
        {"page": "Home", "href": url_for("frontend.index")},
        {"page": "Visualisations"},
    ]

    return render_template("visualisations.html", breadcrumbs=breadcrumbs)

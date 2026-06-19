from flask import Blueprint, render_template, url_for

frontend = Blueprint("frontend", __name__, template_folder="templates")


@frontend.route("/")
def index():
    return render_template("index.html")


@frontend.route("/attic")
def attic():
    breadcrumbs = [
        {"page": "Home", "href": url_for("frontend.index")},
        {"page": "Attic"},
    ]
    return render_template("attic.html", breadcrumbs=breadcrumbs)

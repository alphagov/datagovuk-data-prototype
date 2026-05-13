from flask import Blueprint, render_template, url_for
from markdown_it import MarkdownIt
from markupsafe import Markup
from sqlalchemy.orm import joinedload

frontend = Blueprint("frontend", __name__, template_folder="templates")


@frontend.route("/")
def index():
    return render_template("index.html")

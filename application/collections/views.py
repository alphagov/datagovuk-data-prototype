import os

import frontmatter
import markdown as md_lib
from flask import Blueprint, abort, current_app, render_template
from markupsafe import Markup
from werkzeug.utils import safe_join

collections_bp = Blueprint("collections", __name__, template_folder="../templates")


@collections_bp.route("/collection/<topic>/<dataset_name>")
def detail(topic, dataset_name):
    """Render a single collection topic's markdown as a page."""
    path = safe_join(current_app.config["COLLECTIONS_DIR"], topic, f"{dataset_name}.md")
    if path is None or not os.path.isfile(path):
        abort(404)

    doc = frontmatter.load(path)
    body_html = Markup(md_lib.markdown(doc.content, extensions=["extra"]))

    return render_template(
        "topic.html",
        topic=topic,
        collection_title=topic.replace("-", " ").capitalize(),
        title=doc.metadata.get("title", dataset_name),
        meta=doc.metadata,
        body_html=body_html,
    )

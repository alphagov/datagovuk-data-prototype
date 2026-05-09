from flask import Blueprint, render_template, url_for
from markdown_it import MarkdownIt
from markupsafe import Markup
from sqlalchemy.orm import joinedload

from application.models import Collection, Topic

frontend = Blueprint("frontend", __name__, template_folder="templates")


@frontend.route("/")
def index():
    return render_template("index.html")


@frontend.route("/collections")
def get_collections():
    collections = Collection.query.all()
    breadcrumbs = [
        {"page": "Home", "href": url_for("frontend.index")},
        {"page": "Collections"},
    ]
    return render_template(
        "collections.html", collections=collections, breadcrumbs=breadcrumbs
    )


@frontend.route("/collections/<string:slug>")
def get_collection(slug):
    collection = Collection.query.filter(Collection.slug == slug).first_or_404()
    breadcrumbs = [
        {"page": "Home", "href": url_for("frontend.index")},
        {"page": "Collections", "href": url_for("frontend.get_collections")},
        {"page": collection.title},
    ]
    return render_template(
        "collection.html", collection=collection, breadcrumbs=breadcrumbs
    )


@frontend.route("/collections/<string:slug>/<string:topic_slug>")
def get_topic(slug, topic_slug):
    topic = (
        Topic.query.join(Topic.collection)
        .filter(Collection.slug == slug, Topic.slug == topic_slug)
        .options(
            joinedload(Topic.collection),
            joinedload(Topic.links),
        )
        .first_or_404()
    )

    breadcrumbs = [
        {"page": "Home", "href": url_for("frontend.index")},
        {"page": "Collections", "href": url_for("frontend.get_collections")},
        {
            "page": slug.replace("-", " ").capitalize(),
            "href": url_for("frontend.get_collection", slug=slug),
        },
        {"page": topic.title},
    ]
    md = MarkdownIt("commonmark")
    content = md.render(topic.body)
    return render_template(
        "topic.html",
        topic=topic,
        content=Markup(content),
        breadcrumbs=breadcrumbs,
    )

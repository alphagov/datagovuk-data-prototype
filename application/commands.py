import os

import click
import frontmatter
import sqlalchemy as sa
from flask import current_app
from flask.cli import AppGroup

from application.embeddings import (
    content_hash,
    embed_batch,
    embedding_input,
)
from application.extensions import db
from application.models import Collection, Link, LinkType, Topic

sandbox_cli = AppGroup("sandbox")


@sandbox_cli.command(name="content")
def content():
    collections = os.listdir(current_app.config["COLLECTIONS_DIR"])
    for collection in collections:
        c = Collection.query.filter(Collection.slug == collection).first()
        if c is None:
            slug = collection
            title = slug.replace("-", " ").capitalize()
            c = Collection(title=title, slug=slug)
            db.session.add(c)
            db.session.commit()
        else:
            print(f"Collection {collection} in db already")
        _add_topics(c)


@sandbox_cli.command(name="clear")
def clear_data():
    confirm = input("This will delete all data. Type 'yes' to continue: ")
    if confirm != "yes":
        print("clear not run")
        return
    for model in [Link, Topic, Collection]:
        db.session.query(model).delete()
        db.session.commit()


def _parse_links(metadata):
    links = []
    for website in metadata.get("websites", []):
        links.append(
            {
                "url": website["url"],
                "link_text": website["link-text"],
                "link_type": LinkType("website"),
            }
        )
    for link_type in ["api", "dataset"]:
        entry = metadata.get(link_type)
        if entry is not None:
            links.append(
                {
                    "url": entry["url"],
                    "link_text": entry["link-text"],
                    "link_type": LinkType(link_type),
                }
            )
    return links


def _sync_links(topic, parsed_links):
    existing = {(link.url, link.link_type): link for link in topic.links}
    seen = set()
    for link_data in parsed_links:
        key = (link_data["url"], link_data["link_type"])
        seen.add(key)
        if key in existing:
            existing[key].link_text = link_data["link_text"]
        else:
            topic.links.append(Link(**link_data))
    for key, link in existing.items():
        if key not in seen:
            db.session.delete(link)


def _maybe_update_embedding(topic):
    """Recompute topic.embedding only if title+body has changed since last embed."""
    new_hash = content_hash(topic.title, topic.body)
    if topic.content_hash == new_hash and topic.embedding is not None:
        return
    [vector] = embed_batch([embedding_input(topic.title, topic.body)])
    topic.embedding = vector
    topic.content_hash = new_hash


@sandbox_cli.command(name="embed")
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="embed every topic, not just ones with a stale or missing embedding.",
)
@click.option(
    "--batch-size",
    default=100,
    show_default=True,
    help="Number of topics per embeddings run.",
)
def embed(force, batch_size):
    query = Topic.query
    if not force:
        query = query.filter(
            sa.or_(Topic.embedding.is_(None), Topic.content_hash.is_(None))
        )
    topics = query.all()

    if not topics:
        print("Nothing to embed")
        return

    print(f"Embedding {len(topics)} topics in batches of {batch_size}")
    total = 0
    for start in range(0, len(topics), batch_size):
        chunk = topics[start : start + batch_size]
        inputs = [embedding_input(t.title, t.body) for t in chunk]
        vectors = embed_batch(inputs)
        for topic, vector in zip(chunk, vectors):
            topic.embedding = vector
            topic.content_hash = content_hash(topic.title, topic.body)
        db.session.commit()
        total += len(chunk)
        print(f"  {total}/{len(topics)}")
    print("Done")


def _add_topics(collection):
    collection_dir = os.path.join(
        current_app.config["COLLECTIONS_DIR"], collection.slug
    )
    files = os.listdir(collection_dir)
    for filename in files:
        try:
            slug = filename.replace(".md", "")
            markdown_file_path = os.path.join(collection_dir, filename)
            md = frontmatter.load(markdown_file_path)

            t = Topic.query.filter(
                Topic.collection_id == collection.id, Topic.slug == slug
            ).first()
            if t is None:
                t = Topic(slug=slug)
                collection.topics.append(t)

            t.title = md.metadata["title"]
            t.body = md.content
            t.search_vector = sa.func.to_tsvector(
                "english", sa.literal(f"{t.title} {t.body}")
            )
            _sync_links(t, _parse_links(md.metadata))
            _maybe_update_embedding(t)

            db.session.add(collection)
            db.session.commit()
        except Exception as e:
            print(e)
            print(f"Error processing {filename}")
            db.session.rollback()

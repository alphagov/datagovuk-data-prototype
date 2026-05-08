import datetime
import enum
import uuid

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from application.config import Config
from application.extensions import db


class LinkType(enum.Enum):
    website = "website"
    dataset = "dataset"
    api = "api"


class BaseModel(db.Model):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    updated: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )


class Collection(BaseModel):
    __tablename__ = "collection"

    slug: Mapped[str] = mapped_column(sa.String, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(sa.String, nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    topics: Mapped[list["Topic"]] = relationship(back_populates="collection")


class Topic(BaseModel):
    __tablename__ = "topic"
    __table_args__ = (
        sa.UniqueConstraint("collection_id", "slug"),
        sa.Index("ix_topic_search_vector", "search_vector", postgresql_using="gin"),
        sa.Index(
            "ix_topic_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    title: Mapped[str] = mapped_column(sa.String, nullable=False)
    slug: Mapped[str] = mapped_column(sa.String, nullable=False)
    collection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("collection.id"), nullable=False
    )
    body: Mapped[str] = mapped_column(sa.Text, nullable=False)
    visualisation_data: Mapped[dict | None] = mapped_column(
        MutableDict.as_mutable(JSONB), nullable=True
    )
    search_vector = mapped_column(TSVECTOR, nullable=True)
    embedding = mapped_column(Vector(Config.EMBEDDING_DIM), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    collection: Mapped["Collection"] = relationship(back_populates="topics")
    links: Mapped[list["Link"]] = relationship(back_populates="topic")


class Link(BaseModel):
    __tablename__ = "link"

    url: Mapped[str] = mapped_column(sa.String, nullable=False)
    link_text: Mapped[str] = mapped_column(sa.String, nullable=False)
    link_type: Mapped[LinkType] = mapped_column(
        sa.Enum(LinkType, name="linktype", create_constraint=False, native_enum=True),
        nullable=False,
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("topic.id"), nullable=False
    )
    topic: Mapped["Topic"] = relationship(back_populates="links")

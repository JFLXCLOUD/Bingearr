"""A marathon (a built, server-bound binge experience) and its resolved items."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base
from .mixins import TimestampMixin


class Marathon(TimestampMixin, Base):
    __tablename__ = "marathons"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    server_id: Mapped[int | None] = mapped_column(
        ForeignKey("media_servers.id", ondelete="SET NULL"), nullable=True
    )

    type: Mapped[str] = mapped_column(String(16), default="manual")  # manual|rule|timeboxed
    ordering: Mapped[str] = mapped_column(String(16), default="custom")
    watch_filter: Mapped[str] = mapped_column(String(16), default="all")

    # JSON blob for rule-based / time-boxed config (see ROADMAP rule_config).
    rule_config: Mapped[str | None] = mapped_column(Text, nullable=True)

    # NeXroll category/sequence id, applied when the marathon becomes active.
    preroll_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)

    target_kind: Mapped[str] = mapped_column(String(16), default="playlist")  # playlist|collection
    server_playlist_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    schedule: Mapped[str | None] = mapped_column(Text, nullable=True)

    items: Mapped[list["MarathonItem"]] = relationship(
        back_populates="marathon",
        cascade="all, delete-orphan",
        order_by="MarathonItem.position",
    )


class MarathonItem(Base):
    __tablename__ = "marathon_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    marathon_id: Mapped[int] = mapped_column(
        ForeignKey("marathons.id", ondelete="CASCADE")
    )
    position: Mapped[int] = mapped_column(Integer, default=0)

    # Plex ratingKey / Jellyfin Item Id of the resolved local item.
    server_item_id: Mapped[str] = mapped_column(String(128))
    title: Mapped[str] = mapped_column(String(512))
    runtime_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    watched: Mapped[bool] = mapped_column(default=False)

    marathon: Mapped[Marathon] = relationship(back_populates="items")

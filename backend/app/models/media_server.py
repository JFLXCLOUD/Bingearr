"""A connected Plex or Jellyfin server."""

from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db.database import Base
from .mixins import TimestampMixin


class MediaServer(TimestampMixin, Base):
    __tablename__ = "media_servers"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(16))  # plex | jellyfin
    name: Mapped[str] = mapped_column(String(128))
    base_url: Mapped[str] = mapped_column(String(512))
    # Plex token or Jellyfin api key.
    token: Mapped[str] = mapped_column(String(512))
    user_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

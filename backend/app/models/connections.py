"""External service connections: NeXroll (prerolls) and the Arrs (gap-fill)."""

from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db.database import Base
from .mixins import TimestampMixin


class NeXrollConnection(TimestampMixin, Base):
    __tablename__ = "nexroll_connections"

    id: Mapped[int] = mapped_column(primary_key=True)
    base_url: Mapped[str] = mapped_column(String(512))
    api_key: Mapped[str] = mapped_column(String(512))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class ArrConnection(TimestampMixin, Base):
    __tablename__ = "arr_connections"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(16))  # radarr | sonarr
    base_url: Mapped[str] = mapped_column(String(512))
    api_key: Mapped[str] = mapped_column(String(512))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

"""Pydantic request/response models."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


# --- Media servers ---------------------------------------------------------
class ServerCreate(BaseModel):
    type: Literal["plex", "jellyfin"]
    name: str
    base_url: str
    token: str
    user_id: Optional[str] = None
    enabled: bool = True


class ServerUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    token: Optional[str] = None
    user_id: Optional[str] = None
    enabled: Optional[bool] = None


class ServerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    name: str
    base_url: str
    user_id: Optional[str] = None
    enabled: bool
    created_at: datetime
    updated_at: datetime
    # token is intentionally never serialized back out.


class LibrarySectionOut(BaseModel):
    key: str
    title: str
    type: str
    item_count: Optional[int] = None


class ServerTestResult(BaseModel):
    ok: bool
    name: Optional[str] = None
    version: Optional[str] = None
    message: Optional[str] = None
    libraries: list[LibrarySectionOut] = []


# --- Marathons -------------------------------------------------------------
class MarathonCreate(BaseModel):
    name: str
    description: Optional[str] = None
    server_id: Optional[int] = None
    type: Literal["manual", "rule", "timeboxed"] = "manual"
    ordering: str = "custom"
    watch_filter: Literal["all", "unwatched", "in_progress"] = "all"
    target_kind: Literal["playlist", "collection"] = "playlist"


class MarathonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    server_id: Optional[int] = None
    type: str
    ordering: str
    watch_filter: str
    target_kind: str
    server_playlist_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class HealthOut(BaseModel):
    status: str
    app: str
    version: str

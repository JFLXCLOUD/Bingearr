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


class LibraryItemOut(BaseModel):
    id: str
    title: str
    type: str
    year: Optional[int] = None
    runtime_minutes: Optional[int] = None


class CollectionOut(BaseModel):
    id: str
    title: str
    item_count: Optional[int] = None


# --- Marathons -------------------------------------------------------------
class MarathonItemIn(BaseModel):
    server_item_id: str
    title: str
    runtime_minutes: Optional[int] = None


class MarathonItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    position: int
    server_item_id: str
    title: str
    runtime_minutes: Optional[int] = None
    watched: bool


class ScheduleConfig(BaseModel):
    frequency: Literal["off", "hourly", "daily", "weekly"] = "off"
    time: Optional[str] = None  # "HH:MM" for daily/weekly (server local time)
    weekday: Optional[int] = None  # 0=Mon .. 6=Sun for weekly


class MarathonCreate(BaseModel):
    name: str
    description: Optional[str] = None
    server_id: Optional[int] = None
    type: Literal["manual", "rule", "timeboxed"] = "manual"
    ordering: str = "custom"
    watch_filter: Literal["all", "unwatched", "in_progress"] = "all"
    target_kind: Literal["playlist", "collection"] = "playlist"
    items: list[MarathonItemIn] = []
    # Recipe for rule/smart marathons (re-resolved on scheduled rebuilds).
    rule_config: Optional[dict] = None
    schedule: Optional[ScheduleConfig] = None


class MarathonUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    # When provided, fully replaces the ordered item list.
    items: Optional[list[MarathonItemIn]] = None
    rule_config: Optional[dict] = None
    schedule: Optional[ScheduleConfig] = None


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
    item_count: int = 0
    total_runtime_minutes: int = 0
    rule_config: Optional[dict] = None
    schedule: Optional[dict] = None
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class MarathonDetail(MarathonRead):
    items: list[MarathonItemOut] = []


class PushResult(BaseModel):
    ok: bool
    server_playlist_id: Optional[str] = None
    item_count: int = 0
    message: Optional[str] = None


class HealthOut(BaseModel):
    status: str
    app: str
    version: str

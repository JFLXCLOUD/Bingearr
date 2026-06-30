"""Marathon CRUD + build/push to the media server."""

from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...db.database import get_session
from ...models import Marathon, MarathonItem
from ...services.builder import PushError, push_marathon
from ...services.scheduler import compute_next_run, rebuild_and_push
from ..deps import require_api_key
from ..schemas import (
    MarathonCreate,
    MarathonDetail,
    MarathonItemIn,
    MarathonRead,
    MarathonUpdate,
    PushResult,
    ScheduleConfig,
)

router = APIRouter(
    prefix="/api/marathons",
    tags=["marathons"],
    dependencies=[Depends(require_api_key)],
)


def _set_items(marathon: Marathon, items: list[MarathonItemIn]) -> None:
    """Replace a marathon's items with a freshly ordered list."""
    marathon.items.clear()
    for pos, item in enumerate(items):
        marathon.items.append(
            MarathonItem(
                position=pos,
                server_item_id=item.server_item_id,
                title=item.title,
                runtime_minutes=item.runtime_minutes,
            )
        )


def _read(marathon: Marathon) -> MarathonRead:
    return MarathonRead(
        id=marathon.id,
        name=marathon.name,
        description=marathon.description,
        server_id=marathon.server_id,
        type=marathon.type,
        ordering=marathon.ordering,
        watch_filter=marathon.watch_filter,
        target_kind=marathon.target_kind,
        server_playlist_id=marathon.server_playlist_id,
        item_count=len(marathon.items),
        total_runtime_minutes=sum(i.runtime_minutes or 0 for i in marathon.items),
        rule_config=json.loads(marathon.rule_config) if marathon.rule_config else None,
        schedule=json.loads(marathon.schedule) if marathon.schedule else None,
        last_run_at=marathon.last_run_at,
        next_run_at=marathon.next_run_at,
        created_at=marathon.created_at,
        updated_at=marathon.updated_at,
    )


def _apply_recipe(marathon: Marathon, rule_config: dict | None) -> None:
    marathon.rule_config = json.dumps(rule_config) if rule_config else None
    kind = (rule_config or {}).get("kind")
    if kind == "smart":
        marathon.type = "timeboxed"
    elif kind in ("series", "collection"):
        marathon.type = "rule"
    else:
        marathon.type = "manual"


def _apply_schedule(marathon: Marathon, schedule: ScheduleConfig | None) -> None:
    if schedule is None or schedule.frequency == "off":
        marathon.schedule = None
        marathon.next_run_at = None
        return
    cfg = schedule.model_dump()
    marathon.schedule = json.dumps(cfg)
    marathon.next_run_at = compute_next_run(cfg, datetime.now())


def _detail(marathon: Marathon) -> MarathonDetail:
    base = _read(marathon)
    return MarathonDetail(
        **base.model_dump(),
        items=sorted(marathon.items, key=lambda i: i.position),
    )


def _get_or_404(db: Session, marathon_id: int) -> Marathon:
    marathon = db.get(Marathon, marathon_id)
    if marathon is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marathon not found.")
    return marathon


@router.get("", response_model=list[MarathonRead])
def list_marathons(db: Session = Depends(get_session)) -> list[MarathonRead]:
    marathons = db.scalars(select(Marathon).order_by(Marathon.id)).all()
    return [_read(m) for m in marathons]


@router.post("", response_model=MarathonDetail, status_code=status.HTTP_201_CREATED)
def create_marathon(body: MarathonCreate, db: Session = Depends(get_session)) -> MarathonDetail:
    marathon = Marathon(
        name=body.name,
        description=body.description,
        server_id=body.server_id,
        ordering=body.ordering,
        watch_filter=body.watch_filter,
        target_kind=body.target_kind,
    )
    _set_items(marathon, body.items)
    _apply_recipe(marathon, body.rule_config)
    _apply_schedule(marathon, body.schedule)
    db.add(marathon)
    db.commit()
    db.refresh(marathon)
    return _detail(marathon)


@router.get("/{marathon_id}", response_model=MarathonDetail)
def get_marathon(marathon_id: int, db: Session = Depends(get_session)) -> MarathonDetail:
    return _detail(_get_or_404(db, marathon_id))


@router.put("/{marathon_id}", response_model=MarathonDetail)
def update_marathon(
    marathon_id: int, body: MarathonUpdate, db: Session = Depends(get_session)
) -> MarathonDetail:
    marathon = _get_or_404(db, marathon_id)
    provided = body.model_dump(exclude_unset=True)
    if "name" in provided and body.name is not None:
        marathon.name = body.name
    if "description" in provided:
        marathon.description = body.description
    if "items" in provided and body.items is not None:
        _set_items(marathon, body.items)
    if "rule_config" in provided:
        _apply_recipe(marathon, body.rule_config)
    if "schedule" in provided:
        _apply_schedule(marathon, body.schedule)
    db.commit()
    db.refresh(marathon)
    return _detail(marathon)


@router.delete("/{marathon_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_marathon(marathon_id: int, db: Session = Depends(get_session)) -> None:
    marathon = _get_or_404(db, marathon_id)
    db.delete(marathon)
    db.commit()


@router.post("/{marathon_id}/push", response_model=PushResult)
def push(marathon_id: int, db: Session = Depends(get_session)) -> PushResult:
    marathon = _get_or_404(db, marathon_id)
    try:
        result = push_marathon(db, marathon)
    except PushError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return PushResult(**result)


@router.post("/{marathon_id}/rebuild", response_model=PushResult)
def rebuild(marathon_id: int, db: Session = Depends(get_session)) -> PushResult:
    """Re-resolve a recipe marathon's contents, then push (manual 'run now')."""
    marathon = _get_or_404(db, marathon_id)
    try:
        result = rebuild_and_push(db, marathon)
    except PushError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return PushResult(**result)

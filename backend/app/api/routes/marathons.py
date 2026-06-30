"""Marathon CRUD + build/push to the media server."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...db.database import get_session
from ...models import Marathon, MarathonItem
from ...services.builder import PushError, push_marathon
from ..deps import require_api_key
from ..schemas import (
    MarathonCreate,
    MarathonDetail,
    MarathonItemIn,
    MarathonRead,
    MarathonUpdate,
    PushResult,
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
        created_at=marathon.created_at,
        updated_at=marathon.updated_at,
    )


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
    data = body.model_dump(exclude={"items"})
    marathon = Marathon(**data)
    _set_items(marathon, body.items)
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
    if body.name is not None:
        marathon.name = body.name
    if body.description is not None:
        marathon.description = body.description
    if body.items is not None:
        _set_items(marathon, body.items)
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

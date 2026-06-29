"""Marathon CRUD.

Phase 0 persists marathons; the builder/resolve/push logic lands in Phase 1.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...db.database import get_session
from ...models import Marathon
from ..deps import require_api_key
from ..schemas import MarathonCreate, MarathonRead

router = APIRouter(
    prefix="/api/marathons",
    tags=["marathons"],
    dependencies=[Depends(require_api_key)],
)


@router.get("", response_model=list[MarathonRead])
def list_marathons(db: Session = Depends(get_session)) -> list[Marathon]:
    return list(db.scalars(select(Marathon).order_by(Marathon.id)).all())


@router.post("", response_model=MarathonRead, status_code=status.HTTP_201_CREATED)
def create_marathon(
    body: MarathonCreate, db: Session = Depends(get_session)
) -> Marathon:
    marathon = Marathon(**body.model_dump())
    db.add(marathon)
    db.commit()
    db.refresh(marathon)
    return marathon


@router.get("/{marathon_id}", response_model=MarathonRead)
def get_marathon(marathon_id: int, db: Session = Depends(get_session)) -> Marathon:
    marathon = db.get(Marathon, marathon_id)
    if marathon is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marathon not found.")
    return marathon


@router.delete("/{marathon_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_marathon(marathon_id: int, db: Session = Depends(get_session)) -> None:
    marathon = db.get(Marathon, marathon_id)
    if marathon is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marathon not found.")
    db.delete(marathon)
    db.commit()

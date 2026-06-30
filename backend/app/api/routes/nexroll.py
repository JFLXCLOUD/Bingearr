"""NeXroll connection management + preroll discovery."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...clients.nexroll import NeXrollClient
from ...config import settings
from ...db.database import get_session
from ...models import NeXrollConnection
from ..deps import require_api_key
from ..schemas import (
    NeXrollCreate,
    NeXrollRead,
    NeXrollStatus,
    NeXrollUpdate,
    PrerollOut,
)

router = APIRouter(
    prefix="/api/nexroll",
    tags=["nexroll"],
    dependencies=[Depends(require_api_key)],
)


def _get_or_404(db: Session, conn_id: int) -> NeXrollConnection:
    conn = db.get(NeXrollConnection, conn_id)
    if conn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NeXroll connection not found.")
    return conn


def _client(conn: NeXrollConnection) -> NeXrollClient:
    return NeXrollClient(conn.base_url, conn.api_key, timeout=settings.plex_timeout)


@router.get("", response_model=list[NeXrollRead])
def list_connections(db: Session = Depends(get_session)):
    return list(db.scalars(select(NeXrollConnection).order_by(NeXrollConnection.id)).all())


@router.post("", response_model=NeXrollRead, status_code=status.HTTP_201_CREATED)
def create_connection(body: NeXrollCreate, db: Session = Depends(get_session)):
    conn = NeXrollConnection(**body.model_dump())
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


@router.patch("/{conn_id}", response_model=NeXrollRead)
def update_connection(conn_id: int, body: NeXrollUpdate, db: Session = Depends(get_session)):
    conn = _get_or_404(db, conn_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(conn, field, value)
    db.commit()
    db.refresh(conn)
    return conn


@router.delete("/{conn_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(conn_id: int, db: Session = Depends(get_session)) -> None:
    conn = _get_or_404(db, conn_id)
    db.delete(conn)
    db.commit()


@router.get("/{conn_id}/status", response_model=NeXrollStatus)
def connection_status(conn_id: int, db: Session = Depends(get_session)) -> NeXrollStatus:
    conn = _get_or_404(db, conn_id)
    try:
        info = _client(conn).status()
    except Exception as exc:  # noqa: BLE001 — surface unreachable NeXroll cleanly
        return NeXrollStatus(ok=False, message=str(exc))
    return NeXrollStatus(
        ok=bool(info.get("ok", True)),
        version=info.get("version"),
        server_connected=info.get("server_connected"),
    )


@router.get("/{conn_id}/prerolls", response_model=list[PrerollOut])
def list_prerolls(conn_id: int, db: Session = Depends(get_session)):
    conn = _get_or_404(db, conn_id)
    try:
        return _client(conn).list_prerolls()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

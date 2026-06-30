"""Media-server CRUD + connection test."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...clients import get_media_client
from ...clients.base import MediaServerClient
from ...db.database import get_session
from ...models import MediaServer
from ..deps import require_api_key
from ..schemas import (
    LibraryItemOut,
    LibrarySectionOut,
    ServerCreate,
    ServerRead,
    ServerTestResult,
    ServerUpdate,
)

router = APIRouter(
    prefix="/api/servers",
    tags=["servers"],
    dependencies=[Depends(require_api_key)],
)


def _get_or_404(db: Session, server_id: int) -> MediaServer:
    server = db.get(MediaServer, server_id)
    if server is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found.")
    return server


def _client_or_error(server: MediaServer) -> MediaServerClient:
    try:
        return get_media_client(server)
    except NotImplementedError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc))


@router.get("", response_model=list[ServerRead])
def list_servers(db: Session = Depends(get_session)) -> list[MediaServer]:
    return list(db.scalars(select(MediaServer).order_by(MediaServer.id)).all())


@router.post("", response_model=ServerRead, status_code=status.HTTP_201_CREATED)
def create_server(body: ServerCreate, db: Session = Depends(get_session)) -> MediaServer:
    server = MediaServer(**body.model_dump())
    db.add(server)
    db.commit()
    db.refresh(server)
    return server


@router.get("/{server_id}", response_model=ServerRead)
def get_server(server_id: int, db: Session = Depends(get_session)) -> MediaServer:
    return _get_or_404(db, server_id)


@router.patch("/{server_id}", response_model=ServerRead)
def update_server(
    server_id: int, body: ServerUpdate, db: Session = Depends(get_session)
) -> MediaServer:
    server = _get_or_404(db, server_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(server, field, value)
    db.commit()
    db.refresh(server)
    return server


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_server(server_id: int, db: Session = Depends(get_session)) -> None:
    server = _get_or_404(db, server_id)
    db.delete(server)
    db.commit()


@router.post("/{server_id}/test", response_model=ServerTestResult)
def test_server(server_id: int, db: Session = Depends(get_session)) -> ServerTestResult:
    server = _get_or_404(db, server_id)
    client = _client_or_error(server)

    info = client.test_connection()
    if not info.ok:
        return ServerTestResult(ok=False, message=info.message)

    libraries = [
        LibrarySectionOut(key=s.key, title=s.title, type=s.type, item_count=s.item_count)
        for s in client.list_libraries()
    ]
    return ServerTestResult(
        ok=True, name=info.name, version=info.version, libraries=libraries
    )


@router.get("/{server_id}/libraries", response_model=list[LibrarySectionOut])
def list_libraries(server_id: int, db: Session = Depends(get_session)):
    server = _get_or_404(db, server_id)
    client = _client_or_error(server)
    try:
        return [
            LibrarySectionOut(key=s.key, title=s.title, type=s.type, item_count=s.item_count)
            for s in client.list_libraries()
        ]
    except Exception as exc:  # noqa: BLE001 — surface upstream errors as 502
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.get("/{server_id}/libraries/{library_key}/items", response_model=list[LibraryItemOut])
def list_library_items(
    server_id: int,
    library_key: str,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_session),
):
    server = _get_or_404(db, server_id)
    client = _client_or_error(server)
    try:
        items = client.list_items(library_key, search=search, limit=limit, offset=offset)
    except Exception as exc:  # noqa: BLE001 — surface upstream errors as 502
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    return [
        LibraryItemOut(
            id=i.id, title=i.title, type=i.type, year=i.year, runtime_minutes=i.runtime_minutes
        )
        for i in items
    ]

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from google.cloud.firestore import Client

from app.core.security import get_current_user_id
from app.db.session import get_db
from app.db.repositories import NoteRepository
from app.schemas.note import NoteIn, NoteOut, NoteUpdate, PaginatedNotes

router = APIRouter(prefix="/notes")

@router.get("", response_model=PaginatedNotes, summary="List user's notes")
def list_notes(
    search: Optional[str] = Query(None, description="Search by title or content"),
    pinned: Optional[bool] = Query(None, description="Filter by pinned status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort: str = Query("updated_at_desc", pattern="^(updated_at_desc|updated_at_asc|pinned_desc)$", description="Sort order"),
    db: Client = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
) -> PaginatedNotes:
    repo = NoteRepository(db)
    items, total = repo.list_notes(
        owner_id=current_user_id,
        search=search,
        pinned=pinned,
        page=page,
        page_size=page_size,
        sort=sort,
    )
    return {
        "items": [
            NoteOut(
                id=n["id"],
                title=n["title"],
                content=n["content"],
                pinned=n["pinned"],
                updated_at=n["updated_at"],
            )
            for n in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }

@router.post("", response_model=NoteOut, status_code=201, summary="Create a note")
def create_note(
    body: NoteIn,
    db: Client = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
) -> NoteOut:
    repo = NoteRepository(db)
    note = repo.create(owner_id=current_user_id, title=body.title, content=body.content, pinned=body.pinned)
    return NoteOut(id=note["id"], title=note["title"], content=note["content"], pinned=note["pinned"], updated_at=note["updated_at"])

@router.put("/{note_id}", response_model=NoteOut, summary="Update a note")
def update_note(
    note_id: str,
    body: NoteUpdate,
    db: Client = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
) -> NoteOut:
    repo = NoteRepository(db)
    owned = repo.get_owned(note_id, current_user_id)
    if not owned:
        raise HTTPException(status_code=404, detail="Note not found")
    updated = repo.update(note_id, title=body.title, content=body.content, pinned=body.pinned)
    return NoteOut(id=updated["id"], title=updated["title"], content=updated["content"], pinned=updated["pinned"], updated_at=updated["updated_at"])

@router.delete("/{note_id}", status_code=204, summary="Delete a note")
def delete_note(
    note_id: str,
    db: Client = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
) -> None:
    repo = NoteRepository(db)
    owned = repo.get_owned(note_id, current_user_id)
    if not owned:
        raise HTTPException(status_code=404, detail="Note not found")
    repo.delete(note_id)

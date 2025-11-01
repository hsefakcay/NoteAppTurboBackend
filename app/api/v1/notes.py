"""Notes API endpoints."""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from google.cloud.firestore import Client

from app.core.logging_config import get_logger
from app.core.security import get_current_user_id
from app.core.exceptions import NotFoundError
from app.core.constants import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    SORT_UPDATED_AT_DESC,
)
from app.db.session import get_db
from app.db.repositories import NoteRepository
from app.schemas.note import NoteIn, NoteOut, NoteUpdate, PaginatedNotes

logger = get_logger(__name__)
router = APIRouter(prefix="/notes")

@router.get("", response_model=PaginatedNotes, summary="List user's notes")
def list_notes(
    search: Optional[str] = Query(None, description="Search by title or content"),
    pinned: Optional[bool] = Query(None, description="Filter by pinned status"),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Page number"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Items per page"),
    sort: str = Query(SORT_UPDATED_AT_DESC, pattern="^(updated_at_desc|updated_at_asc|pinned_desc)$", description="Sort order"),
    db: Client = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
) -> PaginatedNotes:
    """List notes for the current user with pagination and filtering.
    
    Args:
        search: Optional search term for title or content
        pinned: Optional filter for pinned/unpinned notes
        page: Page number (starts at 1)
        page_size: Number of items per page
        sort: Sort order (updated_at_desc, updated_at_asc, pinned_desc)
        db: Firestore client dependency
        current_user_id: Current authenticated user ID
        
    Returns:
        PaginatedNotes with items, total count, and pagination info
    """
    logger.debug(f"Listing notes for user {current_user_id}, page {page}, size {page_size}")
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
    """Create a new note for the current user.
    
    Args:
        body: Note input data (title, content, pinned)
        db: Firestore client dependency
        current_user_id: Current authenticated user ID
        
    Returns:
        Created NoteOut object
    """
    logger.info(f"Creating note for user {current_user_id}")
    repo = NoteRepository(db)
    note = repo.create(
        owner_id=current_user_id,
        title=body.title,
        content=body.content,
        pinned=body.pinned,
    )
    logger.debug(f"Note created with ID: {note['id']}")
    return NoteOut(
        id=note["id"],
        title=note["title"],
        content=note["content"],
        pinned=note["pinned"],
        updated_at=note["updated_at"],
    )

@router.put("/{note_id}", response_model=NoteOut, summary="Update a note")
def update_note(
    note_id: str,
    body: NoteUpdate,
    db: Client = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
) -> NoteOut:
    """Update an existing note.
    
    Args:
        note_id: ID of the note to update
        body: Note update data (all fields optional)
        db: Firestore client dependency
        current_user_id: Current authenticated user ID
        
    Returns:
        Updated NoteOut object
        
    Raises:
        NotFoundError: If note doesn't exist or doesn't belong to user
    """
    logger.info(f"Updating note {note_id} for user {current_user_id}")
    repo = NoteRepository(db)
    owned = repo.get_owned(note_id, current_user_id)
    if not owned:
        logger.warning(f"Note {note_id} not found or not owned by user {current_user_id}")
        raise NotFoundError(resource="Note")
    
    updated = repo.update(
        note_id,
        title=body.title,
        content=body.content,
        pinned=body.pinned,
    )
    logger.debug(f"Note {note_id} updated successfully")
    return NoteOut(
        id=updated["id"],
        title=updated["title"],
        content=updated["content"],
        pinned=updated["pinned"],
        updated_at=updated["updated_at"],
    )

@router.patch("/{note_id}/pin", response_model=NoteOut, summary="Toggle note pin status")
def toggle_pin(
    note_id: str,
    pinned: bool = Query(..., description="Pin status"),
    db: Client = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
) -> NoteOut:
    """Toggle pin status of a note.
    
    Args:
        note_id: ID of the note to pin/unpin
        pinned: Pin status (True to pin, False to unpin)
        db: Firestore client dependency
        current_user_id: Current authenticated user ID
        
    Returns:
        Updated NoteOut object
        
    Raises:
        NotFoundError: If note doesn't exist or doesn't belong to user
    """
    logger.info(f"Toggling pin status for note {note_id} to {pinned}")
    repo = NoteRepository(db)
    owned = repo.get_owned(note_id, current_user_id)
    if not owned:
        logger.warning(f"Note {note_id} not found or not owned by user {current_user_id}")
        raise NotFoundError(resource="Note")
    
    updated = repo.toggle_pin(note_id, pinned)
    logger.debug(f"Note {note_id} pin status updated to {pinned}")
    return NoteOut(
        id=updated["id"],
        title=updated["title"],
        content=updated["content"],
        pinned=updated["pinned"],
        updated_at=updated["updated_at"],
    )

@router.delete("/{note_id}", status_code=204, summary="Delete a note")
def delete_note(
    note_id: str,
    db: Client = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
) -> None:
    """Delete a note.
    
    Args:
        note_id: ID of the note to delete
        db: Firestore client dependency
        current_user_id: Current authenticated user ID
        
    Raises:
        NotFoundError: If note doesn't exist or doesn't belong to user
    """
    logger.info(f"Deleting note {note_id} for user {current_user_id}")
    repo = NoteRepository(db)
    owned = repo.get_owned(note_id, current_user_id)
    if not owned:
        logger.warning(f"Note {note_id} not found or not owned by user {current_user_id}")
        raise NotFoundError(resource="Note")
    
    repo.delete(note_id)
    logger.debug(f"Note {note_id} deleted successfully")

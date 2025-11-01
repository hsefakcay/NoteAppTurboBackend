"""Repository layer for Firestore database operations."""
from typing import Optional, Tuple, List, Dict, Any
from google.cloud.firestore import Client, DocumentSnapshot
from datetime import datetime, timezone

from app.core.constants import (
    NOTES_COLLECTION,
    SORT_UPDATED_AT_DESC,
    SORT_UPDATED_AT_ASC,
    SORT_PINNED_DESC,
)

# Type alias for sort keys
SortKey = str  # "updated_at_desc" | "updated_at_asc" | "pinned_desc"

# Default datetime for sorting (epoch)
DEFAULT_DATETIME = datetime(1970, 1, 1, tzinfo=timezone.utc)


class NoteRepository:
    """Repository for Note CRUD operations in Firestore."""

    def __init__(self, db: Client):
        """Initialize repository with Firestore client.
        
        Args:
            db: Firestore Client instance
        """
        self.db = db
        self.col = self.db.collection(NOTES_COLLECTION)

    def _doc_to_noteout(self, doc: DocumentSnapshot) -> Dict[str, Any]:
        """Convert Firestore document to note dictionary.
        
        Args:
            doc: Firestore DocumentSnapshot
            
        Returns:
            Dictionary with note data
        """
        data = doc.to_dict() or {}
        return {
            "id": doc.id,
            "title": data.get("title", ""),
            "content": data.get("content", ""),
            "pinned": bool(data.get("pinned", False)),
            "updated_at": data.get("updated_at"),
            "owner_id": data.get("owner_id"),
        }

    def list_notes(
        self,
        owner_id: str,
        search: Optional[str],
        pinned: Optional[bool],
        page: int,
        page_size: int,
        sort: SortKey,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List notes for a user with filtering, searching, and pagination.
        
        Args:
            owner_id: Owner user ID
            search: Optional search term for title/content (in-memory filter)
            pinned: Optional filter for pinned status
            page: Page number (1-indexed)
            page_size: Number of items per page
            sort: Sort key (updated_at_desc, updated_at_asc, pinned_desc)
            
        Returns:
            Tuple of (list of note dicts, total count)
            
        Note:
            Search is done in-memory as Firestore doesn't support case-insensitive
            substring search natively. This may be slow for large datasets.
        """
        # Base filter: owner_id
        query = self.col.where("owner_id", "==", owner_id)
        if pinned is not None:
            query = query.where("pinned", "==", pinned)

        # Firestore doesn't support case-insensitive substring search natively;
        # we apply in-memory filtering for search
        docs = list(query.stream())
        items = [self._doc_to_noteout(d) for d in docs]

        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            items = [
                it for it in items
                if search_lower in (it["title"] or "").lower()
                or search_lower in (it["content"] or "").lower()
            ]

        # Sort items
        if sort == SORT_UPDATED_AT_ASC:
            items.sort(
                key=lambda it: it.get("updated_at") or DEFAULT_DATETIME
            )
        elif sort == SORT_PINNED_DESC:
            # Pinned items first, then by updated_at desc
            items.sort(
                key=lambda it: (
                    0 if it.get("pinned", False) else 1,
                    -(it.get("updated_at") or DEFAULT_DATETIME).timestamp(),
                )
            )
        else:  # default: updated_at_desc
            items.sort(
                key=lambda it: it.get("updated_at") or DEFAULT_DATETIME,
                reverse=True,
            )

        # Pagination
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return items[start:end], total

    def create(
        self, owner_id: str, title: str, content: str, pinned: bool
    ) -> Dict[str, Any]:
        """Create a new note.
        
        Args:
            owner_id: Owner user ID
            title: Note title
            content: Note content
            pinned: Whether note is pinned
            
        Returns:
            Dictionary with created note data
        """
        now = datetime.now(timezone.utc)
        doc_ref = self.col.document()  # Auto-generated ID
        data = {
            "title": title,
            "content": content,
            "pinned": bool(pinned),
            "updated_at": now,
            "owner_id": owner_id,
        }
        doc_ref.set(data)
        doc = doc_ref.get()
        return self._doc_to_noteout(doc)

    def get_owned(self, note_id: str, owner_id: str) -> Optional[Dict[str, Any]]:
        """Get a note by ID if it exists and is owned by the user.
        
        Args:
            note_id: Note document ID
            owner_id: Expected owner user ID
            
        Returns:
            Note dictionary if found and owned, None otherwise
        """
        doc = self.col.document(note_id).get()
        if not doc.exists:
            return None
        data = self._doc_to_noteout(doc)
        return data if data.get("owner_id") == owner_id else None

    def update(
        self,
        note_id: str,
        *,
        title: Optional[str],
        content: Optional[str],
        pinned: Optional[bool],
    ) -> Dict[str, Any]:
        """Update a note's fields.
        
        Args:
            note_id: Note document ID
            title: Optional new title
            content: Optional new content
            pinned: Optional new pinned status
            
        Returns:
            Dictionary with updated note data
        """
        updates = {"updated_at": datetime.now(timezone.utc)}
        if title is not None:
            updates["title"] = title
        if content is not None:
            updates["content"] = content
        if pinned is not None:
            updates["pinned"] = bool(pinned)
        self.col.document(note_id).update(updates)
        return self._doc_to_noteout(self.col.document(note_id).get())

    def toggle_pin(self, note_id: str, pinned: bool) -> Dict[str, Any]:
        """Pin/unpin a note without updating timestamp.
        
        Args:
            note_id: Note document ID
            pinned: Pin status (True to pin, False to unpin)
            
        Returns:
            Dictionary with updated note data
        """
        updates = {"pinned": bool(pinned)}
        self.col.document(note_id).update(updates)
        return self._doc_to_noteout(self.col.document(note_id).get())

    def delete(self, note_id: str) -> None:
        """Delete a note by ID.
        
        Args:
            note_id: Note document ID to delete
        """
        self.col.document(note_id).delete()

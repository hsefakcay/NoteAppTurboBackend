from typing import Iterable, Optional, Tuple, List, Dict, Any
from uuid import UUID as UUID_t
from google.cloud.firestore import Client
from datetime import datetime, timezone

SortKey = str  # "updated_at_desc" | "updated_at_asc" | "pinned_desc"

class NoteRepository:
    def __init__(self, db: Client):
        self.db = db
        self.col = self.db.collection("notes")

    def _doc_to_noteout(self, doc) -> Dict[str, Any]:
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
        # Temel filtre: owner_id
        query = self.col.where("owner_id", "==", owner_id)
        if pinned is not None:
            query = query.where("pinned", "==", pinned)

        # Firestore'da ilike/contains native yok; in-memory filtre uygulayacağız
        docs = list(query.stream())
        items = [self._doc_to_noteout(d) for d in docs]

        if search:
            q = search.lower()
            items = [
                it for it in items
                if q in (it["title"] or "").lower() or q in (it["content"] or "").lower()
            ]

        # Sıralama
        def sort_key(it):
            return (
                (not it.get("pinned", False)) if sort == "pinned_desc" else 0,
                it.get("updated_at") or datetime(1970, 1, 1, tzinfo=timezone.utc),
            )
        reverse = True
        if sort == "updated_at_asc":
            items.sort(key=lambda it: it.get("updated_at") or datetime(1970,1,1, tzinfo=timezone.utc))
        elif sort == "pinned_desc":
            # pinned True önce, sonra updated_at desc
            items.sort(key=lambda it: (
                0 if it.get("pinned", False) else 1,
                -(it.get("updated_at") or datetime(1970,1,1, tzinfo=timezone.utc)).timestamp(),
            ))
        else:
            items.sort(key=lambda it: it.get("updated_at") or datetime(1970,1,1, tzinfo=timezone.utc), reverse=True)

        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return items[start:end], total

    def create(self, owner_id: str, title: str, content: str, pinned: bool):
        now = datetime.now(timezone.utc)
        doc_ref = self.col.document()  # otomatik id
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
        doc = self.col.document(note_id).get()
        if not doc.exists:
            return None
        data = self._doc_to_noteout(doc)
        return data if data.get("owner_id") == owner_id else None

    def update(self, note_id: str, *, title: Optional[str], content: Optional[str], pinned: Optional[bool]):
        updates = {"updated_at": datetime.now(timezone.utc)}
        if title is not None:
            updates["title"] = title
        if content is not None:
            updates["content"] = content
        if pinned is not None:
            updates["pinned"] = bool(pinned)
        self.col.document(note_id).update(updates)
        return self._doc_to_noteout(self.col.document(note_id).get())

    def delete(self, note_id: str) -> None:
        self.col.document(note_id).delete()

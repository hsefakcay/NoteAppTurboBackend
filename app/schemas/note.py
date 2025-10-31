from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class NoteIn(BaseModel):
    title: str = Field(..., examples=["Deneme"])
    content: str = Field(..., examples=["İçerik"])
    pinned: bool = Field(default=False, examples=[False])

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    pinned: Optional[bool] = None

class NoteOut(BaseModel):
    id: str
    title: str
    content: str
    pinned: bool
    updated_at: datetime

class PaginatedNotes(BaseModel):
    items: List[NoteOut]
    total: int
    page: int
    page_size: int

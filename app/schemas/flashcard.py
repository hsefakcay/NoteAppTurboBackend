from typing import List
from pydantic import BaseModel, Field


class Flashcard(BaseModel):
    question: str = Field(..., description="The flashcard question", examples=["What is photosynthesis?"])
    answer: str = Field(..., description="The flashcard answer", examples=["The process by which plants convert light into energy"])


class FlashcardRequest(BaseModel):
    note_content: str = Field(
        ..., 
        description="The note content to generate flashcards from",
        examples=["Photosynthesis is the process by which plants use sunlight to produce energy from carbon dioxide and water."]
    )


class FlashcardResponse(BaseModel):
    flashcards: List[Flashcard] = Field(..., description="List of generated flashcards")
    note_content_preview: str = Field(..., description="Preview of the input note content")


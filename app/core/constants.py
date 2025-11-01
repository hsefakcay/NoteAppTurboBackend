"""Application-wide constants."""
from typing import Final

# Flashcard generation constants
MIN_NOTE_CONTENT_LENGTH: Final[int] = 10
MAX_NOTE_CONTENT_LENGTH: Final[int] = 5000
MAX_FLASHCARDS: Final[int] = 5
MAX_PREVIEW_LENGTH: Final[int] = 100

# API constants
GEMINI_API_BASE_URL: Final[str] = "https://generativelanguage.googleapis.com/v1"
API_TIMEOUT_SECONDS: Final[float] = 30.0

# Pagination defaults
DEFAULT_PAGE: Final[int] = 1
DEFAULT_PAGE_SIZE: Final[int] = 20
MAX_PAGE_SIZE: Final[int] = 100

# Sort options
SORT_UPDATED_AT_DESC: Final[str] = "updated_at_desc"
SORT_UPDATED_AT_ASC: Final[str] = "updated_at_asc"
SORT_PINNED_DESC: Final[str] = "pinned_desc"

VALID_SORT_OPTIONS: Final[tuple[str, ...]] = (
    SORT_UPDATED_AT_DESC,
    SORT_UPDATED_AT_ASC,
    SORT_PINNED_DESC,
)

# Collection names
NOTES_COLLECTION: Final[str] = "notes"

# Error codes
ERROR_CODE_NOT_FOUND: Final[str] = "not_found"
ERROR_CODE_UNAUTHORIZED: Final[str] = "unauthorized"
ERROR_CODE_VALIDATION_ERROR: Final[str] = "validation_error"
ERROR_CODE_RATE_LIMIT_EXCEEDED: Final[str] = "rate_limit_exceeded"
ERROR_CODE_INTERNAL_SERVER_ERROR: Final[str] = "internal_server_error"


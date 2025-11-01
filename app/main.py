from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.api.v1.notes import router as notes_router
from app.api.v1.flashcards import router as flashcards_router

limiter = Limiter(key_func=get_remote_address) if settings.rate_limit_enabled else None

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Note App Turbo - FastAPI backend with Firebase Auth and Firestore",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# Health check endpoint
@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": settings.app_name}

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limit (optional)
if limiter:
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    @app.exception_handler(RateLimitExceeded)
    def rate_limit_handler(request, exc):  # type: ignore
        return settings.error_response("Too many requests", code="rate_limit_exceeded", status_code=429)

# Routers
app.include_router(notes_router, prefix="/api", tags=["notes"])
app.include_router(flashcards_router, prefix="/api", tags=["flashcards"])

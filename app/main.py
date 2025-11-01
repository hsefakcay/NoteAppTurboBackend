"""FastAPI application entry point."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.core.exceptions import BaseAPIException
from app.core.constants import ERROR_CODE_RATE_LIMIT_EXCEEDED, ERROR_CODE_INTERNAL_SERVER_ERROR
from app.api.v1.notes import router as notes_router
from app.api.v1.flashcards import router as flashcards_router

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Initialize rate limiter if enabled
limiter = Limiter(key_func=get_remote_address) if settings.rate_limit_enabled else None

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Note App Turbo - FastAPI backend with Firebase Auth and Firestore",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# Global exception handlers
@app.exception_handler(BaseAPIException)
async def api_exception_handler(request: Request, exc: BaseAPIException):
    """Handle custom API exceptions."""
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "code": exc.code,
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other unhandled exceptions."""
    from fastapi.responses import JSONResponse
    from fastapi import status
    logger.exception(
        f"Unhandled exception in {request.method} {request.url.path}",
        exc_info=exc,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "code": ERROR_CODE_INTERNAL_SERVER_ERROR,
        },
    )

# Health check endpoint
@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Health check endpoint.
    
    Returns:
        Dictionary with status and service name
    """
    return {"status": "healthy", "service": settings.app_name}

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limit middleware (optional)
if limiter:
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    @app.exception_handler(RateLimitExceeded)
    def rate_limit_handler(request: Request, exc: RateLimitExceeded):  # type: ignore
        """Handle rate limit exceeded errors."""
        return settings.error_response(
            "Too many requests",
            code=ERROR_CODE_RATE_LIMIT_EXCEEDED,
            status_code=429,
        )

# API routers
app.include_router(notes_router, prefix="/api", tags=["notes"])
app.include_router(flashcards_router, prefix="/api", tags=["flashcards"])

logger.info(f"Application '{settings.app_name}' started successfully")

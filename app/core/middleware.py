"""Custom middleware for error handling."""
import logging
from typing import Callable
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.exceptions import BaseAPIException
from app.core.constants import ERROR_CODE_INTERNAL_SERVER_ERROR

logger = logging.getLogger(__name__)


async def exception_handler_middleware(
    request: Request,
    call_next: Callable,
) -> JSONResponse:
    """Global exception handler middleware.
    
    Catches unhandled exceptions and returns consistent error responses.
    """
    try:
        response = await call_next(request)
        return response
    except BaseAPIException as e:
        # Custom API exceptions are handled explicitly
        return JSONResponse(
            status_code=e.status_code,
            content={
                "detail": e.detail,
                "code": e.code,
            },
        )
    except Exception as e:
        # Log unexpected errors
        logger.exception(
            f"Unhandled exception in {request.method} {request.url.path}",
            exc_info=e,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "code": ERROR_CODE_INTERNAL_SERVER_ERROR,
            },
        )


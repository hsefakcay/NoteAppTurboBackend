"""Custom exception classes for the application."""
from typing import Optional
from fastapi import HTTPException, status


class BaseAPIException(HTTPException):
    """Base exception class for API errors."""
    
    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: Optional[str] = None,
        headers: Optional[dict] = None,
    ):
        self.code = code
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class NotFoundError(BaseAPIException):
    """Raised when a resource is not found."""
    
    def __init__(self, detail: str = "Resource not found", resource: Optional[str] = None):
        if resource:
            detail = f"{resource} not found"
        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND,
            code="not_found",
        )


class UnauthorizedError(BaseAPIException):
    """Raised when authentication fails."""
    
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="unauthorized",
        )


class ValidationError(BaseAPIException):
    """Raised when validation fails."""
    
    def __init__(self, detail: str = "Validation error"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            code="validation_error",
        )


class ExternalAPIError(BaseAPIException):
    """Raised when external API calls fail."""
    
    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_502_BAD_GATEWAY,
        service: Optional[str] = None,
    ):
        if service:
            detail = f"{service} API error: {detail}"
        super().__init__(
            detail=detail,
            status_code=status_code,
            code="external_api_error",
        )


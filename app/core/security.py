"""Firebase authentication and security utilities."""
import logging
import os
from typing import Optional
from functools import lru_cache

import firebase_admin
from firebase_admin import auth as fb_auth, credentials
from fastapi import Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.exceptions import UnauthorizedError

logger = logging.getLogger(__name__)
http_bearer = HTTPBearer(auto_error=False)


def ensure_firebase_app() -> bool:
    """Initialize Firebase Admin SDK (only once).
    
    Uses LRU cache to ensure it's only initialized once.
    
    Returns:
        True if initialization successful, False otherwise
    """
    try:
        # Check if app already exists
        firebase_admin.get_app()
        return True
    except ValueError:
        # App not yet initialized, proceed to initialize
        pass
    
    try:
        # Use emulator if configured
        if os.getenv("FIRESTORE_EMULATOR_HOST"):
            firebase_admin.initialize_app()
            logger.info("Firebase Admin SDK initialized with emulator")
            return True
            
        # Use service account credentials if provided
        if settings.google_application_credentials and os.path.exists(settings.google_application_credentials):
            cred = credentials.Certificate(settings.google_application_credentials)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized with service account")
        else:
            # Use application default credentials
            firebase_admin.initialize_app()
            logger.info("Firebase Admin SDK initialized with default credentials")
        return True
    except ValueError as e:
        # App might already be initialized in another thread/process
        logger.warning(f"Firebase app already initialized or error: {e}")
        return True
    except Exception as e:
        logger.error(f"Firebase Admin SDK initialization failed: {e}", exc_info=True)
        return False


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(http_bearer),
) -> str:
    """Extract and verify Firebase ID token to get current user ID.
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        
    Returns:
        Firebase user ID (uid)
        
    Raises:
        UnauthorizedError: If token is missing, invalid, or verification fails
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Missing or invalid Authorization header")
    
    token = credentials.credentials
    
    # Ensure Firebase is initialized
    if not ensure_firebase_app():
        logger.error("Failed to initialize Firebase Admin SDK")
        raise UnauthorizedError("Authentication service unavailable")

    try:
        decoded = fb_auth.verify_id_token(token)
        uid = decoded.get("uid")
        if not uid:
            logger.warning("Token decoded but missing uid field")
            raise UnauthorizedError("Invalid token: missing user ID")
        return uid
    except fb_auth.InvalidIdTokenError as e:
        logger.warning(f"Invalid Firebase ID token: {e}")
        raise UnauthorizedError("Invalid Firebase ID token") from e
    except fb_auth.ExpiredIdTokenError as e:
        logger.warning(f"Expired Firebase ID token: {e}")
        raise UnauthorizedError("Expired Firebase ID token") from e
    except fb_auth.RevokedIdTokenError as e:
        logger.warning(f"Revoked Firebase ID token: {e}")
        raise UnauthorizedError("Revoked Firebase ID token") from e
    except Exception as e:
        logger.error(f"Unexpected error verifying Firebase token: {e}", exc_info=True)
        raise UnauthorizedError("Token verification failed") from e

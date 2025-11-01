"""Firestore database session management."""
from firebase_admin import firestore
from google.cloud.firestore import Client

from app.core.security import ensure_firebase_app


def get_db() -> Client:
    """Provide Firestore Client as a dependency.
    
    Yields:
        Firestore Client instance
        
    Note:
        Firestore emulator support: If FIRESTORE_EMULATOR_HOST env var is set,
        client automatically connects to it.
    """
    # Ensure Firebase Admin SDK is initialized
    ensure_firebase_app()
    # Get Firestore client from Firebase Admin SDK
    client = firestore.client()
    try:
        yield client
    finally:
        # Firestore Client doesn't require explicit closing
        pass

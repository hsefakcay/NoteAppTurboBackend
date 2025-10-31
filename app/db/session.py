from firebase_admin import firestore
from app.core.security import _ensure_firebase_app

# Firestore emulator destegi icin: FIRESTORE_EMULATOR_HOST env var ise client otomatik ona baglanir

def get_db():
    """Firestore Client'i dependency olarak sağlar"""
    # Firebase Admin SDK'nın initialize edildiğinden emin ol
    _ensure_firebase_app()
    # Firebase Admin SDK üzerinden Firestore client al
    client = firestore.client()
    try:
        yield client
    finally:
        # Firestore Client kapatma gerektirmez; placeholder
        pass

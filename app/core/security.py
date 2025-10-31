from fastapi import Depends, Header, Security
from fastapi import HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth as fb_auth, credentials
from app.core.config import settings
from functools import lru_cache
import json
import os
from typing import Optional

http_bearer = HTTPBearer(auto_error=False)

@lru_cache(maxsize=1)
def _ensure_firebase_app() -> bool:
    """Firebase Admin SDK'yı initialize eder (sadece bir kez)"""
    try:
        # Mevcut app'i kontrol et
        firebase_admin.get_app()
        return True
    except ValueError:
        # App henüz initialize edilmemiş, şimdi initialize et
        pass
    
    try:
        if os.getenv("FIRESTORE_EMULATOR_HOST"):
            firebase_admin.initialize_app()
            return True
            
        if settings.google_application_credentials and os.path.exists(settings.google_application_credentials):
            cred = credentials.Certificate(settings.google_application_credentials)
            firebase_admin.initialize_app(cred)
        else:
            firebase_admin.initialize_app()
        return True
    except Exception as e:
        print(f"Firebase Admin SDK initialize hatası: {e}")
        return False

async def get_current_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Security(http_bearer)) -> str:
    if not credentials or not credentials.scheme.lower() == "bearer":
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = credentials.credentials

    _ensure_firebase_app()

    try:
        decoded = fb_auth.verify_id_token(token)
        uid = decoded.get("uid")
        if not uid:
            raise ValueError("uid missing")
        return uid
    except Exception as ex:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="Invalid Firebase ID token") from ex

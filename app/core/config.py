from typing import List, Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi.responses import JSONResponse
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=os.getenv("ENV_FILE", ".env"), extra="ignore")

    app_name: str = "Note App Turbo API"
    env: str = os.getenv("ENV", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    port: int = int(os.getenv("PORT", "8000"))

    cors_origins: List[str] = (
        os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:5173,http://localhost:5500,exp://127.0.0.1:19000,exp://localhost:19000,http://10.0.2.2:3000",
        ).split(",")
    )

    firebase_project_id: Optional[str] = os.getenv("FIREBASE_PROJECT_ID")
    google_application_credentials: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true"
    rate_limit: str = os.getenv("RATE_LIMIT", "100/10minute")

    @staticmethod
    def error_response(detail: str, code: Optional[str] = None, status_code: int = 400) -> JSONResponse:
        payload: dict[str, str] = {"detail": detail}
        if code:
            payload["code"] = code
        return JSONResponse(status_code=status_code, content=payload)

settings = Settings()

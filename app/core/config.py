from typing import List, Optional, Any, Union
from pydantic import BaseModel, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi.responses import JSONResponse
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=os.getenv("ENV_FILE", ".env"), extra="ignore")

    app_name: str = "Note App Turbo API"
    env: str = "development"
    debug: bool = True
    port: int = 8000

    # Can be either string (from .env) or list (after parsing)
    cors_origins: Union[str, List[str]] = "http://localhost:3000,http://localhost:5173,http://localhost:5500,exp://127.0.0.1:19000,exp://localhost:19000,http://10.0.2.2:3000"

    firebase_project_id: Optional[str] = None
    google_application_credentials: Optional[str] = None

    rate_limit_enabled: bool = False
    rate_limit: str = "100/10minute"

    # Google Gemini AI API
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"
    
    @model_validator(mode='after')
    def convert_cors_origins(self) -> 'Settings':
        """Convert comma-separated CORS origins string to list"""
        if isinstance(self.cors_origins, str):
            self.cors_origins = [origin.strip() for origin in self.cors_origins.split(",")]
        return self

    @staticmethod
    def error_response(detail: str, code: Optional[str] = None, status_code: int = 400) -> JSONResponse:
        payload: dict[str, str] = {"detail": detail}
        if code:
            payload["code"] = code
        return JSONResponse(status_code=status_code, content=payload)

settings = Settings()

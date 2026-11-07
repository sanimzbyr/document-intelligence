"""
Application configuration using Pydantic Settings.
Loads from environment variables and .env file.
Supports Free LLM Providers: Google Gemini, Groq, OpenRouter, Ollama, and OpenAI.
"""
from typing import List, Union, Tuple, Optional
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    APP_NAME: str = "AI Document Intelligence"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "development-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./storage/app.db"
    
    # Celery & Redis
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_ALWAYS_EAGER: bool = True
    
    # File Storage
    STORAGE_DIR: str = "./storage"
    MAX_UPLOAD_SIZE_MB: int = 50
    
    # LLM / AI Configuration (Supports Free Tiers: Google Gemini, Groq, OpenRouter, Ollama)
    LLM_PROVIDER: str = "gemini"  # "gemini" (Free), "groq" (Free), "openrouter" (Free), "ollama" (Local Free), "openai"
    LLM_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    
    LLM_MODEL: str = ""
    LLM_BASE_URL: str = ""
    
    # Default fallbacks
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # OCR & PDF Processing
    TESSERACT_CMD: str = "tesseract"
    POPPLER_PATH: str = ""
    
    # Rate Limiting
    RATE_LIMIT_UPLOAD: str = "60/minute"
    RATE_LIMIT_API: str = "300/minute"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000"
        ]

    def get_llm_credentials(self) -> Tuple[str, str, Optional[str], str]:
        """
        Resolve LLM credentials and endpoints.
        Returns: (provider, api_key, base_url, model)
        """
        provider = (self.LLM_PROVIDER or "gemini").lower()
        api_key = self.LLM_API_KEY

        # Check provider-specific keys if general key not specified
        if not api_key:
            if provider == "gemini" and self.GEMINI_API_KEY:
                api_key = self.GEMINI_API_KEY
            elif provider == "groq" and self.GROQ_API_KEY:
                api_key = self.GROQ_API_KEY
            elif provider == "openai" and self.OPENAI_API_KEY:
                api_key = self.OPENAI_API_KEY
            elif self.GEMINI_API_KEY:
                provider = "gemini"
                api_key = self.GEMINI_API_KEY
            elif self.GROQ_API_KEY:
                provider = "groq"
                api_key = self.GROQ_API_KEY
            elif self.OPENAI_API_KEY:
                provider = "openai"
                api_key = self.OPENAI_API_KEY

        base_url = self.LLM_BASE_URL
        model = self.LLM_MODEL

        # Configure defaults for free providers
        if provider == "gemini":
            base_url = base_url or "https://generativelanguage.googleapis.com/v1beta/openai/"
            model = model or "gemini-flash-lite-latest"
        elif provider == "groq":
            base_url = base_url or "https://api.groq.com/openai/v1"
            model = model or "llama-3.3-70b-versatile"
        elif provider == "openrouter":
            base_url = base_url or "https://openrouter.ai/api/v1"
            model = model or "meta-llama/llama-3.3-70b-instruct:free"
        elif provider == "ollama":
            base_url = base_url or "http://localhost:11434/v1"
            model = model or "llama3.2"
            api_key = api_key or "ollama"
        elif provider == "openai":
            base_url = base_url or None
            model = model or "gpt-4o"

        return provider, api_key, base_url, model

    model_config = SettingsConfigDict(
        env_file=[
            os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"),
            os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
            ".env"
        ],
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
os.makedirs(settings.STORAGE_DIR, exist_ok=True)

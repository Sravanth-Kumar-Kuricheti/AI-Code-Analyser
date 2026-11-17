import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    PROJECT_NAME: str = "RepoPilot-AI"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    # Storage & Workspace
    REPO_STORAGE_PATH: str = str(BASE_DIR / "data" / "repos")
    CACHE_DIR: str = str(BASE_DIR / "data" / "cache")
    MAX_FILE_SIZE_KB: int = 500
    
    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'repopilot.db'}"
    
    # Vector Database
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_IN_MEMORY: bool = True
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # LLM Settings
    GROQ_API_KEY: str = ""
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    FALLBACK_TO_MOCK_LLM: bool = True
    
    # GitHub Integration
    GITHUB_TOKEN: str = ""
    
    # Workers
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_CELERY: bool = False
    
    # Server URLs
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    BACKEND_API_URL: str = "http://127.0.0.1:8000"

settings = Settings()

# Synchronize Streamlit Cloud secrets if running on Streamlit Cloud
try:
    import streamlit as st
    for k in ("GROQ_API_KEY", "GITHUB_TOKEN", "DATABASE_URL", "BACKEND_API_URL", "LLM_MODEL"):
        try:
            val = st.secrets.get(k)
            if val:
                setattr(settings, k, str(val))
                os.environ[k] = str(val)
        except Exception:
            pass
except Exception:
    pass

# Ensure storage directories exist
os.makedirs(settings.REPO_STORAGE_PATH, exist_ok=True)
os.makedirs(settings.CACHE_DIR, exist_ok=True)

"""Configuration management for the application.

Note: Uses OpenAI Responses API with o4-mini model.
The Responses API uses reasoning={"effort": "high"} instead of temperature.
"""
import os
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings."""
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Model Configuration - ALL use o4-mini with Responses API
    default_model: str = os.getenv("DEFAULT_MODEL", "o4-mini")
    ocr_model: str = os.getenv("OCR_MODEL", "o4-mini")
    topic_model: str = os.getenv("TOPIC_MODEL", "o4-mini")
    explanation_model: str = os.getenv("EXPLANATION_MODEL", "o4-mini")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
    
    # Reasoning effort for Responses API (low, medium, high)
    # Note: Responses API doesn't support temperature, use reasoning_effort instead
    reasoning_effort: Literal["low", "medium", "high"] = os.getenv("REASONING_EFFORT", "high")
    
    # Weaviate Configuration
    weaviate_url: str = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    
    # Application Configuration
    data_dir: Path = Path(os.getenv("DATA_DIR", "./data/records"))
    samples_dir: Path = Path(os.getenv("SAMPLES_DIR", "./samples"))
    
    # LLM Settings (legacy - reasoning_effort replaces temperature for o4-mini)
    topic_temperature: float = float(os.getenv("TOPIC_TEMPERATURE", "0.1"))  # Deprecated
    max_topics: int = int(os.getenv("MAX_TOPICS", "10"))
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure data directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.samples_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

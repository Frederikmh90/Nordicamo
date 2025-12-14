"""Configuration settings for the NAMO backend."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).parent.parent.parent

class Settings:
    """Application settings."""
    
    # Database configuration
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_USER: str = os.getenv("DB_USER", "namo_user")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "namo_password")
    DB_NAME: str = os.getenv("DB_NAME", "namo_db")
    
    @property
    def database_url(self) -> str:
        """Get database connection URL."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # API settings
    API_TITLE: str = "NAMO API"
    API_VERSION: str = "0.1.0"  # Version 0.1 - Initial release
    API_DESCRIPTION: str = "Nordic Alternative Media Observatory API"
    
    # Data quality configuration
    MIN_ARTICLE_DATE: str = "2003-01-01"  # Use clean data from 2003+
    MAX_FUTURE_DAYS: int = 90  # Prevent scraper errors with future dates
    
    # Caching (if using Redis later)
    CACHE_TTL: int = 3600  # 1 hour default

settings = Settings()


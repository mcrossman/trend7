from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    infactory_api_key: Optional[str] = None
    infactory_api_url: str = "https://api.atlantic-archive.com/v1"
    
    # Database
    database_url: str = "sqlite:///./data/story_threads.db"
    
    # Google Trends
    trends_geo: str = "US"
    trends_timeframe: str = "now 7-d"
    
    # Analysis
    default_threshold: float = 0.10
    max_results_per_query: int = 10
    rerank_enabled: bool = True
    cache_ttl_seconds: int = 3600
    
    # Proactive Feed
    proactive_enabled: bool = True
    proactive_scan_interval_hours: int = 24
    proactive_batch_size: int = 5
    min_trend_velocity: int = 50
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


def find_env_file() -> str:
    """Find .env file - check current dir, then project root."""
    current_dir = Path.cwd()
    
    # Check current directory
    env_current = current_dir / ".env"
    if env_current.exists():
        return str(env_current)
    
    # Check project root (parent of backend/)
    project_root = current_dir
    while project_root.name and project_root.name != "atlantic-hh":
        project_root = project_root.parent
    
    env_root = project_root / ".env"
    if env_root.exists():
        return str(env_root)
    
    # Fallback to relative from this file's location
    this_file = Path(__file__).resolve()
    env_from_file = this_file.parent.parent.parent.parent / ".env"
    if env_from_file.exists():
        return str(env_from_file)
    
    # Default fallback
    return ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    infactory_api_key: Optional[str] = None
    infactory_api_url: str = "https://atlantichack-api.infactory.ai"
    
    # Database
    database_url: str = "sqlite:///./data/story_threads.db"
    
    # Google Trends
    trends_geo: str = "US"
    trends_timeframe: str = "now 7-d"
    trends_cache_ttl_minutes: int = 120
    trends_watch_interval_minutes: int = 60
    
    # Trend thresholds
    min_trend_score: int = 50
    min_match_score: float = 0.30
    trends_max_results: int = 10
    trends_threshold: float = 0.10
    
    # Proactive feed
    proactive_deduplicate_hours: int = 24
    
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
        env_file = find_env_file()
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def reload_settings() -> Settings:
    """Force reload settings - useful during development."""
    get_settings.cache_clear()
    return get_settings()

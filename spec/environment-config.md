# Environment Configuration Specification

## Overview

The environment configuration system provides flexible loading of settings from `.env` files, environment variables, and sensible defaults. It supports running the application from any directory (project root or backend/) and includes comprehensive logging configuration for development.

## Implementation

**Location**: `backend/app/config.py`

## Features

### Multi-Directory .env Loading

The configuration system automatically finds `.env` files from multiple locations:

```python
def find_env_file() -> str:
    """Find .env file - check current dir, then project root."""
    current_dir = Path.cwd()
    
    # 1. Check current directory
    env_current = current_dir / ".env"
    if env_current.exists():
        return str(env_current)
    
    # 2. Walk up to project root (atlantic-hh directory)
    project_root = current_dir
    while project_root.name and project_root.name != "atlantic-hh":
        project_root = project_root.parent
    
    env_root = project_root / ".env"
    if env_root.exists():
        return str(env_root)
    
    # 3. Fallback to file location (backend/app/config.py -> ../../..)
    this_file = Path(__file__).resolve()
    env_from_file = this_file.parent.parent.parent.parent / ".env"
    if env_from_file.exists():
        return str(env_from_file)
    
    # 4. Default fallback
    return ".env"
```

**Supported Run Locations**:
- Project root: `make backend-dev`
- Backend directory: `cd backend && uvicorn app.main:app`
- Any subdirectory within the project

### Settings Class

```python
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
        env_file = find_env_file()  # Dynamic path resolution
        env_file_encoding = "utf-8"
```

### Settings Cache Management

Settings are cached using `@lru_cache()` for performance. A reload function is available for development:

```python
@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

def reload_settings() -> Settings:
    """Force reload settings - useful during development."""
    get_settings.cache_clear()
    return get_settings()
```

**Note**: When changing environment variables (like `INFACTORY_API_URL` in mise.toml or shell), a full server restart is required as the lru_cache persists across uvicorn reloads.

## Logging Configuration

### Main Application Logging

**Location**: `backend/app/main.py`

Logging is configured with DEBUG level by default to aid development:

```python
import logging
import sys

# Configure root logger BEFORE any other imports
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True  # Override uvicorn's defaults
)

# Set all relevant loggers to DEBUG
for logger_name in ['app', 'app.integrations', 'app.integrations.infactory', 'httpx', 'httpcore']:
    logging.getLogger(logger_name).setLevel(logging.DEBUG)
```

### Infactory Client Logging

The Infactory client uses dual logging strategy:

1. **Standard logging module**: `logger.info()`, `logger.debug()`
2. **Direct stderr output**: `debug_print()` helper that always works

```python
def debug_print(msg: str):
    """Print to stderr immediately - bypasses logging config issues."""
    print(f"[INFACTORY] {msg}", file=sys.stderr, flush=True)
```

**Log Output**:
```
2026-01-31 13:40:37,836 - app.main - INFO - BACKEND STARTING - DEBUG LOGGING ENABLED
[INFACTORY] Client initialized - base_url: https://atlantichack-api.infactory.ai, api_key: YES
[INFACTORY] REQUEST: POST https://atlantichack-api.infactory.ai/v1/search
[INFACTORY] REQUEST PAYLOAD: {'query': 'test', 'mode': 'hybrid', 'rerank': True, 'limit': 10}
[INFACTORY] RESPONSE status: 200
```

## Environment Variable Precedence

1. **Environment variables** (highest priority)
2. **`.env` file** (loaded dynamically from discovered location)
3. **Default values** in Settings class (lowest priority)

**Example**: If `INFACTORY_API_URL` is set in your shell or mise.toml, it will override the value in `.env` and the default in code.

## Configuration Files

### .env (Project Root)

```bash
INFACTORY_API_KEY=ak_dVKy50Pi0X-7gcOFkey_56yIrKvNt3X0__QjzRN65-k
```

**Note**: `INFACTORY_API_URL` should NOT be in `.env` if you want to use the code default. If present in `.env`, it will be loaded. If also in mise.toml or shell, the environment variable takes precedence.

### mise.toml (Alternative)

```toml
[env]
INFACTORY_API_URL = "https://atlantichack-api.infactory.ai"
```

## Development Workflow

### Running from Project Root

```bash
make backend-dev
# Loads .env from current directory (project root)
```

### Running from Backend Directory

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
# Loads .env from project root via path resolution
```

### Troubleshooting Environment Variables

Check current environment:
```bash
env | grep INFACTORY
```

Clear cached settings:
```bash
find . -type d -name __pycache__ -exec rm -rf {} +
find . -name "*.pyc" -delete
```

## Files

- Configuration: `backend/app/config.py`
- Logging setup: `backend/app/main.py`
- Environment file: `.env` (project root)
- Alternative config: `mise.toml` (if using mise)

## Future Enhancements

- [ ] Add environment-specific config files (`.env.development`, `.env.production`)
- [ ] Add validation for required settings on startup
- [ ] Support for encrypted secrets (e.g., AWS Secrets Manager)
- [ ] Hot-reload of settings without server restart
- [ ] Configuration UI for viewing/changing settings at runtime

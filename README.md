# Story Thread Surfacing System

Proof-of-concept for identifying and resurfacing historical Atlantic stories using semantic search, clustering, and Google Trends correlation.

## Architecture

- **Backend**: Python FastAPI with modular service layer
- **Frontend**: Next.js with Block Kit renderer
- **Database**: SQLite
- **Response Format**: Slack Block Kit (works for web UI now, Slack later)

## Quick Start

### Prerequisites

- mise (runtime manager)
- Python 3.12
- Node.js 20

### Setup

```bash
# Activate mise
mise install

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Running

```bash
# Terminal 1 - Backend
make backend-dev

# Terminal 2 - Frontend
make frontend-dev
```

## Development

See `spec/` for detailed specifications.

### Using Local Article JSON

You can work with downloaded article JSON files directly:

```bash
# Place article JSON files in ./data/articles/
# Files should be named: {article_id}.json

# The Infactory API is the PRIMARY source.
# Local storage is used only when explicitly requested:
# - When the API is unavailable (offline mode)
# - When testing with known data
# - When explicitly calling local-article endpoints

# API endpoints:
# - GET /api/v1/articles - List local articles
# - POST /api/v1/articles/upload-json - Upload article JSON
# - POST /api/v1/analyze/local-article - Analyze local article ONLY
# - POST /api/v1/analyze/article - Analyze via API ONLY
# - POST /api/v1/articles/bulk-import - Import directory of JSON files

## License

Internal use only.

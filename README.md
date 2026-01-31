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

## License

Internal use only.

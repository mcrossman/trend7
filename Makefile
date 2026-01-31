.PHONY: help install backend-dev frontend-dev dev test clean

help:
	@echo "Available commands:"
	@echo "  install       - Install all dependencies"
	@echo "  backend-dev   - Run backend development server"
	@echo "  frontend-dev  - Run frontend development server"
	@echo "  dev           - Run both backend and frontend (requires tmux or similar)"
	@echo "  test          - Run tests"
	@echo "  clean         - Clean build artifacts"

install:
	@echo "Installing backend dependencies..."
	cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

backend-dev:
	cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000

frontend-dev:
	cd frontend && npm run dev

dev:
	@echo "Run 'make backend-dev' and 'make frontend-dev' in separate terminals"

test:
	cd backend && source venv/bin/activate && pytest
	cd frontend && npm test

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .next -exec rm -rf {} +
	find . -type d -name node_modules -exec rm -rf {} +
	rm -f data/*.db data/*.sqlite data/*.sqlite3

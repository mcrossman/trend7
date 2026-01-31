import logging
import sys

# Configure root logger BEFORE any other imports - this ensures uvicorn doesn't override it
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True  # Force reconfiguration even if logging was already configured
)

# Set all relevant loggers to DEBUG
for logger_name in ['app', 'app.integrations', 'app.integrations.infactory', 'httpx', 'httpcore']:
    logging.getLogger(logger_name).setLevel(logging.DEBUG)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import analyze, threads, proactive, feedback, topics, health, articles, trends

logger = logging.getLogger(__name__)
logger.info("="*60)
logger.info("BACKEND STARTING - DEBUG LOGGING ENABLED")
logger.info("="*60)

app = FastAPI(
    title="Story Thread Surfacing API",
    description="API for identifying and resurfacing historical Atlantic stories",
    version="0.1.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(analyze.router, prefix="/api/v1/analyze", tags=["analyze"])
app.include_router(threads.router, prefix="/api/v1/threads", tags=["threads"])
app.include_router(proactive.router, prefix="/api/v1/proactive", tags=["proactive"])
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["feedback"])
app.include_router(topics.router, prefix="/api/v1/topics", tags=["topics"])
app.include_router(articles.router, prefix="/api/v1/articles", tags=["articles"])
app.include_router(trends.router, prefix="/api/v1/trends", tags=["trends"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Story Thread Surfacing API",
        "version": "0.1.0",
        "docs": "/docs",
    }

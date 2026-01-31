from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import analyze, threads, proactive, feedback, topics, health

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


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Story Thread Surfacing API",
        "version": "0.1.0",
        "docs": "/docs",
    }

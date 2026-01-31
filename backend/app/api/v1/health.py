from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "story-thread-api"}


@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with dependencies status."""
    # TODO: Add database connectivity check
    # TODO: Add Infactory API connectivity check
    return {
        "status": "healthy",
        "service": "story-thread-api",
        "dependencies": {
            "database": "unknown",
            "infactory_api": "unknown",
        },
    }

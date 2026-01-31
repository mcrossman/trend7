from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_topics():
    """
    List all available topics from the archive.
    """
    # TODO: Implement topic listing from Infactory API
    return {
        "success": True,
        "data": {
            "topics": [],
        },
    }

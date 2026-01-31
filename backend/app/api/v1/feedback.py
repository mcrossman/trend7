from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class FeedbackRequest(BaseModel):
    thread_id: str
    helpful: bool
    context: Optional[str] = None
    query_id: Optional[str] = None


@router.post("/")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit feedback on a thread suggestion.
    """
    # TODO: Implement feedback storage
    return {
        "success": True,
        "data": {
            "feedback_id": "feedback_123",
            "thread_id": request.thread_id,
            "helpful": request.helpful,
        },
    }

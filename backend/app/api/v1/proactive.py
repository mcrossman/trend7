from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.database import get_db
from app.services.proactive_service import ProactiveService
from app.services.trends_watch_service import TrendsWatchService
from app.services.block_formatter import BlockFormatter
from app.models.schemas import Thread
import json

router = APIRouter()


class ProactiveSuggestionsResponse(BaseModel):
    """Response with proactive suggestions."""
    success: bool
    generated_at: str
    threads: List[dict]


class ScanTriggerResponse(BaseModel):
    """Response from scan trigger."""
    success: bool
    scan_id: str
    status: str
    trends_checked: int
    new_matches: int
    queue_entries_added: int


@router.get("/suggestions", response_model=ProactiveSuggestionsResponse)
async def get_proactive_suggestions(
    limit: int = Query(5, ge=1, le=20),
    include_trends: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    Get current proactive suggestions based on trending topics and recent content.
    
    - **limit**: Maximum number of suggestions to return
    - **include_trends**: Whether to include trend-based suggestions
    """
    try:
        service = ProactiveService(db=db)
        suggestions = await service.get_suggestions(
            limit=limit,
            include_trends=include_trends
        )
        
        # Convert threads to dict format with blocks
        formatter = BlockFormatter()
        thread_dicts = []
        
        for thread in suggestions:
            thread_dict = {
                "thread_id": thread.thread_id,
                "central_topic": thread.central_topic,
                "thread_type": thread.thread_type,
                "relevance_score": thread.relevance_score,
                "article_count": len(thread.articles),
                "blocks": [b.model_dump() for b in thread.blocks]
            }
            thread_dicts.append(thread_dict)
        
        return ProactiveSuggestionsResponse(
            success=True,
            generated_at=datetime.utcnow().isoformat(),
            threads=thread_dicts
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching suggestions: {str(e)}")


@router.post("/trigger", response_model=ScanTriggerResponse)
async def trigger_proactive_scan(
    force_refresh: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Manually trigger a proactive scan for new suggestions.
    
    This will:
    1. Fetch current Google Trends (or use cached if recent)
    2. Search Infactory for relevant Atlantic articles
    3. Score and queue matching threads
    
    - **force_refresh**: If True, ignores cache and fetches fresh trends from Google
    """
    try:
        # Use TrendsWatchService for the actual scanning
        trends_service = TrendsWatchService(db=db)
        
        # Clear cache if forcing refresh
        if force_refresh:
            from app.models.database import Trend
            db.query(Trend).filter(Trend.expires_at <= datetime.utcnow()).delete()
            db.commit()
        
        # Run the watch cycle
        queue_entries = await trends_service.watch_and_populate()
        current_trends = trends_service.get_current_trends()
        
        return ScanTriggerResponse(
            success=True,
            scan_id=f"scan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            status="completed",
            trends_checked=len(current_trends),
            new_matches=queue_entries,
            queue_entries_added=queue_entries
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering scan: {str(e)}")

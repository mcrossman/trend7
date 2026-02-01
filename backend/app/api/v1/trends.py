"""
API endpoints for Google Trends integration.

Provides:
- POST /api/v1/trends/watch - Trigger trends watch cycle
- GET /api/v1/trends/current - Get current cached trends
- GET /api/v1/trends/queue - Get proactive queue status
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.database import get_db, Trend, ProactiveFeedQueue
from app.integrations.trends import TrendsClient, Trend as TrendSchema
from app.services.trends_watch_service import TrendsWatchService
from app.config import get_settings

settings = get_settings()
router = APIRouter()


# Request/Response Models

class TriggerWatchRequest(BaseModel):
    """Request to trigger trends watch cycle."""
    force_refresh: bool = False  # Ignore cache and fetch fresh trends


class WatchResponse(BaseModel):
    """Response from watch cycle trigger."""
    success: bool
    trends_checked: int
    new_matches: int
    queue_entries_added: int


class CurrentTrendsResponse(BaseModel):
    """Response with current cached trends."""
    success: bool
    recorded_at: Optional[str]
    trends: List[dict]


class QueueItemResponse(BaseModel):
    """Single queue item response."""
    queue_id: int
    trend_keyword: str
    thread_id: str
    priority_score: float
    status: str
    created_at: str
    overall_confidence: Optional[float]
    confidence_level: Optional[str]
    sections_involved: Optional[int]
    total_articles: Optional[int]


class QueueResponse(BaseModel):
    """Response with proactive queue items."""
    success: bool
    count: int
    items: List[QueueItemResponse]


class SectionInfoResponse(BaseModel):
    """Information about a section."""
    name: str
    emoji: str
    total_matches_24h: int


class SectionsResponse(BaseModel):
    """Response with available sections."""
    success: bool
    sections: List[SectionInfoResponse]


class ConfidenceFactorsResponse(BaseModel):
    """Confidence calculation breakdown."""
    base_confidence: float
    article_count_bonus: float
    diversity_multiplier: float
    velocity_multiplier: float
    threshold_penalty: float
    final_confidence: float


class SectionGroupResponse(BaseModel):
    """Articles grouped by section."""
    section_name: str
    section_emoji: str
    article_count: int
    average_score: float
    confidence_contribution: float
    articles: List[dict]


class TrendMessageResponse(BaseModel):
    """Enhanced trend message with sections and confidence."""
    trend_keyword: str
    trend_score: int
    trend_category: str
    trend_velocity: Optional[float]
    overall_confidence: float
    confidence_level: str
    confidence_factors: ConfidenceFactorsResponse
    total_articles: int
    sections_with_matches: int
    section_groups: List[SectionGroupResponse]
    threshold_met: bool


class InterestOverTimeRequest(BaseModel):
    """Request for interest over time data."""
    keyword: str
    timeframe: str = "now 7-d"


class InterestOverTimeResponse(BaseModel):
    """Response with interest over time data."""
    success: bool
    data: Optional[dict]


# API Endpoints

class WatchWithCachedRequest(BaseModel):
    """Request to trigger watch using only cached trends."""
    max_trends: int = 10  # Limit to prevent overwhelming Infactory


@router.post("/watch", response_model=WatchResponse)
async def trigger_trends_watch(
    request: TriggerWatchRequest = TriggerWatchRequest(),
    db: Session = Depends(get_db)
):
    """
    Trigger the trends watch cycle.
    
    Fetches current trends, searches Infactory for relevant articles,
    and populates the proactive feed queue.
    
    - **force_refresh**: If True, ignores cache and fetches fresh trends from Google
    
    Note: If Google Trends returns 429 (rate limit), falls back to cached trends.
    """
    try:
        # Initialize service with fresh client if forcing refresh
        trends_client = TrendsClient() if request.force_refresh else None
        service = TrendsWatchService(db=db, trends_client=trends_client)
        
        # Clear cache if forcing refresh
        if request.force_refresh:
            # Delete expired trends from cache
            from datetime import datetime
            db.query(Trend).filter(Trend.expires_at <= datetime.utcnow()).delete()
            db.commit()
        
        # Run watch cycle (limited to 10 trends to avoid rate limits)
        queue_entries = await service.watch_and_populate(max_trends=10)
        
        # Get stats
        current_trends = service.get_current_trends()
        
        return WatchResponse(
            success=True,
            trends_checked=len(current_trends),
            new_matches=queue_entries,
            queue_entries_added=queue_entries
        )
        
    except Exception as e:
        error_str = str(e).lower()
        # Check if it's a rate limit error
        if '429' in error_str or 'rate limit' in error_str or 'too many requests' in error_str:
            print(f"Google Trends rate limited (429), falling back to cached trends...")
            try:
                # Fallback to cached-only mode
                service = TrendsWatchService(db=db)
                queue_entries = await service.watch_and_populate(use_cached_only=True, max_trends=10)
                current_trends = service.get_current_trends()
                
                return WatchResponse(
                    success=True,
                    trends_checked=len(current_trends),
                    new_matches=queue_entries,
                    queue_entries_added=queue_entries
                )
            except Exception as fallback_error:
                raise HTTPException(
                    status_code=503,
                    detail=f"Google Trends rate limited and no cached trends available. Please try again later."
                )
        
        raise HTTPException(status_code=500, detail=f"Error triggering trends watch: {str(e)}")


@router.post("/watch/cached", response_model=WatchResponse)
async def trigger_watch_cached(
    request: WatchWithCachedRequest = WatchWithCachedRequest(),
    db: Session = Depends(get_db)
):
    """
    Trigger watch cycle using only cached trends (no Google Trends API call).
    
    Use this when Google Trends is rate limiting (429 errors).
    Processes existing cached trends from the database.
    
    - **max_trends**: Maximum number of cached trends to process (default: 10)
    """
    try:
        service = TrendsWatchService(db=db)
        
        # Run watch cycle with cached trends only
        queue_entries = await service.watch_and_populate(
            use_cached_only=True,
            max_trends=request.max_trends
        )
        
        # Get stats
        current_trends = service.get_current_trends()
        
        return WatchResponse(
            success=True,
            trends_checked=len(current_trends),
            new_matches=queue_entries,
            queue_entries_added=queue_entries
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing cached trends: {str(e)}")


@router.get("/current", response_model=CurrentTrendsResponse)
async def get_current_trends(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get current cached trends from Google Trends.
    
    Returns cached trends if available and not expired.
    Trends expire after the configured TTL (default: 2 hours).
    """
    try:
        service = TrendsWatchService(db=db)
        trends = service.get_current_trends(limit=limit)
        
        if not trends:
            return CurrentTrendsResponse(
                success=True,
                recorded_at=None,
                trends=[]
            )
        
        # Get the most recent recorded_at timestamp
        recorded_at = max(t.recorded_at for t in trends if t.recorded_at)
        
        return CurrentTrendsResponse(
            success=True,
            recorded_at=recorded_at.isoformat() if recorded_at else None,
            trends=[
                {
                    "keyword": t.keyword,
                    "score": t.trend_score,
                    "category": t.trend_category,
                    "velocity": t.velocity,
                    "geo_region": t.geo_region
                }
                for t in trends
            ]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trends: {str(e)}")


@router.get("/queue", response_model=QueueResponse)
async def get_proactive_queue(
    status: str = Query("pending", regex="^(pending|sent|all)$"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get current proactive feed queue items.
    
    - **status**: Filter by status ('pending', 'sent', 'all')
    - **limit**: Maximum number of results to return
    """
    try:
        query = db.query(
            ProactiveFeedQueue,
            Trend.keyword.label("trend_keyword")
        ).join(Trend, ProactiveFeedQueue.trend_id == Trend.trend_id)
        
        if status != "all":
            query = query.filter(ProactiveFeedQueue.status == status)
        
        items = query.order_by(
            ProactiveFeedQueue.priority_score.desc()
        ).limit(limit).all()
        
        return QueueResponse(
            success=True,
            count=len(items),
            items=[
                QueueItemResponse(
                    queue_id=item.ProactiveFeedQueue.queue_id,
                    trend_keyword=item.trend_keyword or "Unknown",
                    thread_id=item.ProactiveFeedQueue.thread_id,
                    priority_score=item.ProactiveFeedQueue.priority_score,
                    status=item.ProactiveFeedQueue.status,
                    created_at=item.ProactiveFeedQueue.created_at.isoformat(),
                    overall_confidence=float(item.ProactiveFeedQueue.overall_confidence) if item.ProactiveFeedQueue.overall_confidence else None,
                    confidence_level=item.ProactiveFeedQueue.confidence_level,
                    sections_involved=item.ProactiveFeedQueue.sections_involved,
                    total_articles=item.ProactiveFeedQueue.total_articles
                )
                for item in items
            ]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching queue: {str(e)}")


@router.post("/interest", response_model=InterestOverTimeResponse)
async def get_interest_over_time(
    request: InterestOverTimeRequest,
    db: Session = Depends(get_db)
):
    """
    Get interest over time for a specific keyword.
    
    Useful for checking if a journalist's query topic is currently trending.
    """
    try:
        client = TrendsClient()
        data = await client.get_interest_over_time(
            keyword=request.keyword,
            timeframe=request.timeframe
        )
        
        return InterestOverTimeResponse(
            success=True,
            data=data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching interest data: {str(e)}")


@router.get("/sections", response_model=SectionsResponse)
async def get_sections(
    db: Session = Depends(get_db)
):
    """
    Get available Atlantic sections and their match statistics.
    
    Returns sections with emojis and recent match counts from the last 24 hours.
    """
    try:
        from datetime import datetime, timedelta
        from app.models.schemas import SECTION_EMOJIS
        from app.models.database import TrendArticleMatch
        
        # Get matches from last 24 hours
        recent_matches = db.query(TrendArticleMatch).filter(
            TrendArticleMatch.surfaced_at > datetime.utcnow() - timedelta(hours=24)
        ).all()
        
        # Count matches per section
        section_counts = {}
        for match in recent_matches:
            section = match.section or 'general'
            section_counts[section] = section_counts.get(section, 0) + 1
        
        # Build response
        sections = []
        for section_name, emoji in SECTION_EMOJIS.items():
            sections.append(SectionInfoResponse(
                name=section_name.title(),
                emoji=emoji,
                total_matches_24h=section_counts.get(section_name.lower(), 0)
            ))
        
        # Sort by match count descending
        sections.sort(key=lambda s: s.total_matches_24h, reverse=True)
        
        return SectionsResponse(
            success=True,
            sections=sections
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sections: {str(e)}")


@router.post("/queue/{queue_id}/send")
async def mark_queue_item_sent(
    queue_id: int,
    db: Session = Depends(get_db)
):
    """
    Mark a proactive queue item as sent.
    
    Used by the delivery system to track which suggestions have been surfaced.
    """
    try:
        service = TrendsWatchService(db=db)
        service.mark_queue_item_sent(queue_id)
        
        return {
            "success": True,
            "message": f"Queue item {queue_id} marked as sent"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating queue item: {str(e)}")


# Demo endpoint for frontend

class DemoTriggerResponse(BaseModel):
    """Detailed response for demo trigger showing what was found."""
    success: bool
    message: str
    trends_found: int
    trends: List[dict]
    queue_entries_added: int
    top_matches: List[dict]


@router.post("/demo-trigger", response_model=DemoTriggerResponse)
async def demo_trigger_trends_watch(
    force_refresh: bool = Query(True, description="Fetch fresh trends from Google"),
    db: Session = Depends(get_db)
):
    """
    **Demo endpoint** - Trigger trends watch cycle with detailed results.
    
    Perfect for frontend demos. Returns:
    - What trends were found
    - How many articles matched
    - Top matches with scores
    
    **Use this instead of scheduling** for testing and demos.
    
    - **force_refresh**: If True, fetches fresh trends from Google (recommended for demo)
    """
    try:
        # Initialize service with fresh client
        trends_client = TrendsClient()
        service = TrendsWatchService(db=db, trends_client=trends_client)
        
        # Clear cache if forcing refresh
        if force_refresh:
            from datetime import datetime
            db.query(Trend).filter(Trend.expires_at <= datetime.utcnow()).delete()
            db.commit()
        
        # Get fresh trends first (for demo display)
        fresh_trends = await trends_client.fetch_daily_trends(geo=settings.trends_geo)
        
        if not fresh_trends:
            return DemoTriggerResponse(
                success=True,
                message="No trends available from Google Trends",
                trends_found=0,
                trends=[],
                queue_entries_added=0,
                top_matches=[]
            )
        
        # Run watch cycle
        queue_entries = await service.watch_and_populate()
        
        # Get top matches from queue
        queue_items = service.get_pending_queue(limit=5)
        top_matches = []
        
        for item in queue_items:
            trend = db.query(Trend).filter(Trend.trend_id == item.trend_id).first()
            top_matches.append({
                "trend_keyword": trend.keyword if trend else "Unknown",
                "thread_id": item.thread_id,
                "priority_score": round(float(item.priority_score), 2) if item.priority_score else 0.0,
                "status": item.status
            })
        
        return DemoTriggerResponse(
            success=True,
            message=f"✅ Found {len(fresh_trends)} trends, added {queue_entries} queue entries",
            trends_found=len(fresh_trends),
            trends=[
                {
                    "keyword": t.keyword,
                    "score": t.trend_score,
                    "category": t.trend_category,
                    "velocity": t.velocity
                }
                for t in fresh_trends[:10]  # Top 10 for display
            ],
            queue_entries_added=queue_entries,
            top_matches=top_matches
        )
        
    except Exception as e:
        import traceback
        raise HTTPException(
            status_code=500, 
            detail=f"Error running demo trigger: {str(e)}\n{traceback.format_exc()}"
        )


class PurgeQueueResponse(BaseModel):
    """Response from queue purge operation."""
    success: bool
    deleted_count: int
    message: str


@router.post("/queue/purge", response_model=PurgeQueueResponse)
async def purge_queue(
    db: Session = Depends(get_db)
):
    """
    Purge all entries from the proactive feed queue.
    
    This deletes all pending, sent, and dismissed queue entries.
    Use this to force regeneration of trend blocks with new formatting.
    
    Note: This only removes queue entries. The underlying trend data 
    from Google Trends is preserved and will be rematched on the next watch cycle.
    """
    try:
        # Delete all queue entries
        deleted = db.query(ProactiveFeedQueue).delete()
        db.commit()
        
        return PurgeQueueResponse(
            success=True,
            deleted_count=deleted,
            message=f"✅ Purged {deleted} queue entries"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error purging queue: {str(e)}"
        )

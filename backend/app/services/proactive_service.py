from typing import List, Optional
from sqlalchemy.orm import Session
import json

from app.models.schemas import Thread, ArticleReference
from app.services.trends_watch_service import TrendsWatchService
from app.models.database import ProactiveFeedQueue


class ProactiveService:
    """
    Service for generating proactive suggestions.
    
    Integrates with TrendsWatchService to provide trend-based suggestions
    from the proactive feed queue.
    """
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self._trends_service: Optional[TrendsWatchService] = None
    
    def _get_trends_service(self) -> TrendsWatchService:
        """Lazy initialization of TrendsWatchService."""
        if self._trends_service is None:
            if self.db is None:
                raise ValueError("Database session required for TrendsWatchService")
            self._trends_service = TrendsWatchService(db=self.db)
        return self._trends_service
    
    async def get_suggestions(
        self,
        limit: int = 5,
        include_trends: bool = True
    ) -> List[Thread]:
        """
        Get current proactive suggestions based on:
        - Trending topics (from proactive feed queue)
        - Recently added archive content
        - Scheduled scans
        
        Args:
            limit: Maximum number of suggestions to return
            include_trends: Whether to include trend-based suggestions
        
        Returns:
            List of Thread objects ready for display
        """
        if not include_trends or self.db is None:
            return []
        
        try:
            # Get pending items from queue
            service = self._get_trends_service()
            queue_items = service.get_pending_queue(limit=limit)
            
            threads = []
            for item in queue_items:
                try:
                    # Parse blocks JSON
                    blocks_data = json.loads(item.blocks_json)
                    
                    # Reconstruct thread from queue item
                    # Note: In production, you might want to fetch the full thread
                    # from the database or cache
                    thread = Thread(
                        thread_id=item.thread_id,
                        central_topic=f"Trending Topic (Queue ID: {item.queue_id})",
                        thread_type="event_driven",
                        relevance_score=item.priority_score,
                        articles=[],  # Could fetch from DB if needed
                        blocks=blocks_data
                    )
                    threads.append(thread)
                except Exception as e:
                    print(f"Error parsing queue item {item.queue_id}: {e}")
                    continue
            
            return threads
            
        except Exception as e:
            print(f"Error fetching suggestions: {e}")
            return []
    
    async def trigger_scan(self) -> str:
        """
        Manually trigger a proactive scan.
        Returns scan ID.
        """
        if self.db is None:
            raise ValueError("Database session required")
        
        from datetime import datetime
        scan_id = f"scan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            service = self._get_trends_service()
            await service.watch_and_populate()
            return scan_id
        except Exception as e:
            raise RuntimeError(f"Scan failed: {e}")
    
    async def should_resurface(
        self,
        thread: Thread,
        min_trend_velocity: float = 50.0
    ) -> bool:
        """
        Determine if a thread should be resurfaced based on:
        - Trend velocity > threshold
        - Not recently surfaced
        - Relevance score > threshold
        """
        if not self.db:
            return False
        
        try:
            # Check if this thread is in the proactive queue with high priority
            from app.models.database import TrendArticleMatch, Trend
            from datetime import datetime, timedelta
            
            recent_match = self.db.query(TrendArticleMatch).join(Trend).filter(
                TrendArticleMatch.thread_id == thread.thread_id,
                TrendArticleMatch.surfaced_at > datetime.utcnow() - timedelta(hours=24)
            ).order_by(
                TrendArticleMatch.match_score.desc()
            ).first()
            
            if recent_match and recent_match.match_score >= 0.3:
                # Check trend velocity
                trend = self.db.query(Trend).filter(
                    Trend.trend_id == recent_match.trend_id
                ).first()
                
                if trend and trend.velocity and trend.velocity >= min_trend_velocity:
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error checking resurfacing eligibility: {e}")
            return False

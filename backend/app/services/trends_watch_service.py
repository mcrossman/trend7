from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.config import get_settings
from app.integrations.trends import TrendsClient, Trend
from app.integrations.infactory import InfactoryClient
from app.services.analyzer import AnalyzerService
from app.models.database import Trend as TrendModel, TrendArticleMatch, ProactiveFeedQueue
from app.models.schemas import AnalysisOptions
from app.services.block_formatter import BlockFormatter

settings = get_settings()


class TrendsWatchService:
    """
    Periodic trend watcher that searches archive and populates proactive queue.
    
    This service:
    1. Fetches current trends (from cache or Google Trends)
    2. Filters to significant trends (rising/top with score >= threshold)
    3. Searches Infactory for relevant Atlantic articles
    4. Creates thread matches with composite scoring
    5. Queues proactive suggestions for delivery
    """
    
    def __init__(
        self,
        db: Session,
        trends_client: Optional[TrendsClient] = None,
        infactory_client: Optional[InfactoryClient] = None,
        analyzer_service: Optional[AnalyzerService] = None,
        formatter: Optional[BlockFormatter] = None
    ):
        self.db = db
        self.trends = trends_client or TrendsClient()
        self.infactory = infactory_client or InfactoryClient()
        self.analyzer = analyzer_service or AnalyzerService()
        self.formatter = formatter or BlockFormatter()
    
    async def watch_and_populate(self) -> int:
        """
        Main watch cycle. Returns number of new queue entries created.
        """
        # 1. Get fresh trends (or cached if recent)
        trends = await self._get_cached_or_fetch_trends()
        
        if not trends:
            print("No trends available")
            return 0
        
        # 2. Filter to significant trends
        significant_trends = [
            t for t in trends 
            if t.trend_category in ('rising', 'top') 
            and t.trend_score >= settings.min_trend_score
        ]
        
        print(f"Found {len(significant_trends)} significant trends to process")
        
        # 3. Search Infactory for each trend
        new_entries = 0
        for trend in significant_trends:
            try:
                matches = await self._find_articles_for_trend(trend)
                if matches:
                    queued = await self._queue_proactive_suggestions(trend, matches)
                    new_entries += queued
            except Exception as e:
                print(f"Error processing trend '{trend.keyword}': {e}")
                continue
        
        print(f"Added {new_entries} new entries to proactive queue")
        return new_entries
    
    async def _get_cached_or_fetch_trends(self) -> List[Trend]:
        """Get trends from cache or fetch fresh from Google Trends."""
        # Check cache first
        cached = self._get_cached_trends()
        if cached:
            print(f"Using {len(cached)} cached trends")
            return cached
        
        # Fetch fresh from Google Trends
        print("Fetching fresh trends from Google Trends...")
        fresh_trends = await self.trends.fetch_daily_trends(geo=settings.trends_geo)
        
        if not fresh_trends:
            print("No trends fetched from Google Trends")
            return []
        
        # Cache in DB
        self._cache_trends(fresh_trends)
        
        return fresh_trends
    
    def _get_cached_trends(self) -> List[Trend]:
        """Get non-expired cached trends from database."""
        now = datetime.utcnow()
        
        db_trends = self.db.query(TrendModel).filter(
            TrendModel.expires_at > now
        ).order_by(TrendModel.trend_score.desc()).all()
        
        return [
            Trend(
                trend_id=t.trend_id,
                keyword=t.keyword,
                trend_score=t.trend_score,
                trend_category=t.trend_category,
                velocity=t.velocity,
                geo_region=t.geo_region,
                recorded_at=t.recorded_at,
                expires_at=t.expires_at
            )
            for t in db_trends
        ]
    
    def _cache_trends(self, trends: List[Trend]):
        """Cache trends in database."""
        for trend in trends:
            db_trend = TrendModel(
                keyword=trend.keyword,
                trend_score=trend.trend_score,
                trend_category=trend.trend_category,
                velocity=trend.velocity,
                geo_region=trend.geo_region,
                recorded_at=trend.recorded_at or datetime.utcnow(),
                expires_at=trend.expires_at or (datetime.utcnow() + timedelta(minutes=settings.trends_cache_ttl_minutes))
            )
            self.db.add(db_trend)
        
        self.db.commit()
    
    async def _find_articles_for_trend(self, trend: Trend) -> List[dict]:
        """
        Search Infactory for articles matching this trend.
        Returns list of scored matches.
        """
        print(f"Searching for articles related to trend: {trend.keyword}")
        
        # Search with the trend keyword
        results = await self.infactory.search(
            query=trend.keyword,
            limit=settings.trends_max_results
        )
        
        if not results or not results.get('results'):
            print(f"No Infactory results for trend: {trend.keyword}")
            return []
        
        # Create thread from results using analyzer
        try:
            analysis = await self.analyzer.analyze_text(
                text=trend.keyword,
                options=AnalysisOptions(
                    max_results=settings.trends_max_results,
                    threshold=settings.trends_threshold
                )
            )
        except Exception as e:
            print(f"Error analyzing trend '{trend.keyword}': {e}")
            return []
        
        if not analysis.threads:
            print(f"No threads created for trend: {trend.keyword}")
            return []
        
        # Score each match: trend_score * infactory_relevance
        matches = []
        for thread in analysis.threads:
            for article in thread.articles:
                match_score = (trend.trend_score / 100) * article.relevance_score
                
                if match_score >= settings.min_match_score:
                    matches.append({
                        'trend': trend,
                        'thread': thread,
                        'article': article,
                        'infactory_score': article.relevance_score,
                        'match_score': match_score
                    })
        
        # Sort by match score descending
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        print(f"Found {len(matches)} article matches for trend: {trend.keyword}")
        return matches
    
    async def _queue_proactive_suggestions(self, trend: Trend, matches: List[dict]) -> int:
        """
        Add trend matches to proactive feed queue.
        Returns number of new queue entries.
        """
        if not matches:
            return 0
        
        # Group matches by thread
        threads_dict = {}
        for match in matches:
            thread_id = match['thread'].thread_id
            if thread_id not in threads_dict:
                threads_dict[thread_id] = {
                    'thread': match['thread'],
                    'trend': match['trend'],
                    'articles': [],
                    'total_score': 0
                }
            threads_dict[thread_id]['articles'].append(match)
            threads_dict[thread_id]['total_score'] += match['match_score']
        
        # Get or create trend in DB
        db_trend = self.db.query(TrendModel).filter(
            TrendModel.keyword == trend.keyword,
            TrendModel.recorded_at > datetime.utcnow() - timedelta(hours=1)
        ).first()
        
        if not db_trend:
            db_trend = TrendModel(
                keyword=trend.keyword,
                trend_score=trend.trend_score,
                trend_category=trend.trend_category,
                velocity=trend.velocity,
                geo_region=trend.geo_region,
                recorded_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(minutes=settings.trends_cache_ttl_minutes)
            )
            self.db.add(db_trend)
            self.db.flush()  # Get trend_id
        
        new_entries = 0
        
        for thread_id, thread_data in threads_dict.items():
            # Check for duplicates (same trend + thread within deduplicate window)
            recent_match = self.db.query(TrendArticleMatch).join(TrendModel).filter(
                TrendArticleMatch.thread_id == thread_id,
                TrendModel.keyword == trend.keyword,
                TrendArticleMatch.surfaced_at > datetime.utcnow() - timedelta(hours=settings.proactive_deduplicate_hours)
            ).first()
            
            if recent_match:
                # Update existing match
                recent_match.times_surfaced += 1
                recent_match.last_surfaced_at = datetime.utcnow()
                print(f"Updated existing match for thread {thread_id}")
                continue
            
            # Create trend article matches
            for match in thread_data['articles']:
                db_match = TrendArticleMatch(
                    trend_id=db_trend.trend_id,
                    thread_id=thread_id,
                    article_id=match['article'].article_id,
                    infactory_score=match['infactory_score'],
                    match_score=match['match_score'],
                    surfaced_at=datetime.utcnow(),
                    times_surfaced=1,
                    last_surfaced_at=datetime.utcnow()
                )
                self.db.add(db_match)
            
            # Calculate priority score
            velocity_multiplier = 1.5 if trend.trend_category == 'rising' else 1.2
            priority_score = thread_data['total_score'] * velocity_multiplier
            
            # Format blocks for this trend thread
            blocks = self.formatter.format_trend_thread(
                trend=trend,
                thread=thread_data['thread'],
                articles=[m['article'] for m in thread_data['articles'][:5]]  # Top 5 articles
            )
            
            import json
            
            # Add to proactive queue
            queue_entry = ProactiveFeedQueue(
                trend_id=db_trend.trend_id,
                thread_id=thread_id,
                priority_score=priority_score,
                status='pending',
                created_at=datetime.utcnow(),
                blocks_json=json.dumps([b.model_dump() if hasattr(b, 'model_dump') else b for b in blocks])
            )
            self.db.add(queue_entry)
            new_entries += 1
            
            print(f"Queued trend thread: {trend.keyword} -> {thread_data['thread'].central_topic} (priority: {priority_score:.2f})")
        
        self.db.commit()
        return new_entries
    
    def get_pending_queue(self, limit: int = 10) -> List[ProactiveFeedQueue]:
        """Get pending items from proactive queue, ordered by priority."""
        return self.db.query(ProactiveFeedQueue).filter(
            ProactiveFeedQueue.status == 'pending'
        ).order_by(
            ProactiveFeedQueue.priority_score.desc()
        ).limit(limit).all()
    
    def mark_queue_item_sent(self, queue_id: int):
        """Mark a queue item as sent."""
        item = self.db.query(ProactiveFeedQueue).filter(
            ProactiveFeedQueue.queue_id == queue_id
        ).first()
        
        if item:
            item.status = 'sent'
            item.sent_at = datetime.utcnow()
            self.db.commit()
    
    def get_current_trends(self, limit: int = 20) -> List[Trend]:
        """Get current cached trends."""
        return self._get_cached_trends()[:limit]

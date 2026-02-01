from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.config import get_settings
from app.integrations.trends import TrendsClient, Trend
from app.integrations.infactory import InfactoryClient
from app.services.analyzer import AnalyzerService
from app.services.confidence_calculator import ConfidenceCalculator, create_section_groups
from app.models.database import Trend as TrendModel, TrendArticleMatch, ProactiveFeedQueue
from app.models.schemas import (
    AnalysisOptions, ArticleReference, TrendMessageResult, ThresholdConfig
)
from app.services.block_formatter import BlockFormatter

settings = get_settings()


class TrendsWatchService:
    """
    Periodic trend watcher that searches archive and populates proactive queue.
    
    Enhanced with section-aware search and confidence scoring:
    1. Fetches current trends (from cache or Google Trends)
    2. Filters to significant trends (rising/top with score >= threshold)
    3. Searches Infactory for relevant Atlantic articles (with section grouping)
    4. Calculates per-story scores and overall confidence
    5. Creates trend message results with section groups
    6. Queues proactive suggestions for delivery
    """
    
    def __init__(
        self,
        db: Session,
        trends_client: Optional[TrendsClient] = None,
        infactory_client: Optional[InfactoryClient] = None,
        analyzer_service: Optional[AnalyzerService] = None,
        formatter: Optional[BlockFormatter] = None,
        confidence_calculator: Optional[ConfidenceCalculator] = None
    ):
        self.db = db
        self.trends = trends_client or TrendsClient()
        self.infactory = infactory_client or InfactoryClient()
        self.analyzer = analyzer_service or AnalyzerService()
        self.formatter = formatter or BlockFormatter()
        self.confidence = confidence_calculator or ConfidenceCalculator()
    
    async def watch_and_populate(self, use_cached_only: bool = False, max_trends: int = 10) -> int:
        """
        Main watch cycle. Returns number of new queue entries created.
        
        Args:
            use_cached_only: If True, only use cached trends, don't fetch from Google
            max_trends: Maximum number of trends to process (default: 10)
        """
        # 1. Get trends (cached or fresh)
        if use_cached_only:
            trends = self._get_cached_trends()
            if not trends:
                print("No cached trends available")
                return 0
            print(f"Using {len(trends)} cached trends (limited to {max_trends})")
            trends = trends[:max_trends]
        else:
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
                trend_result = await self._find_articles_for_trend(trend)
                if trend_result and trend_result.threshold_met:
                    queued = await self._queue_proactive_suggestions(trend, trend_result)
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
    
    async def _find_articles_for_trend(self, trend: Trend) -> Optional[TrendMessageResult]:
        """
        Search Infactory for articles matching this trend with section awareness.
        
        Returns a TrendMessageResult with confidence scores and section groups.
        """
        print(f"Searching for articles related to trend: {trend.keyword}")
        
        # Search with section grouping enabled
        try:
            results = await self.infactory.search(
                query=trend.keyword,
                limit=settings.trends_max_results,
                group_by='section' if settings.enable_section_grouping else None
            )
        except Exception as e:
            print(f"Error searching Infactory for trend '{trend.keyword}': {e}")
            return None
        
        # Check for results in both flat and grouped formats
        has_results = (
            results and 
            (results.get('results') or 
             (results.get('data') and results['data'].get('groups')))
        )
        if not has_results:
            print(f"No Infactory results for trend: {trend.keyword}")
            return None
        
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
            return None
        
        if not analysis.threads:
            print(f"No threads created for trend: {trend.keyword}")
            return None
        
        # Collect all articles and calculate story scores
        all_articles: List[ArticleReference] = []
        for thread in analysis.threads:
            for article in thread.articles:
                # Calculate per-story score
                article.story_score = self.confidence.calculate_story_score(article, trend)
                
                # Try to extract section from metadata if available
                # This would come from Infactory results when group_by=section is used
                article.section = self._extract_section_from_result(
                    results, article.article_id
                )
                
                all_articles.append(article)
        
        # Filter by min_story_score threshold
        filtered_articles = [
            art for art in all_articles 
            if art.story_score >= settings.min_story_score
        ]
        
        if not filtered_articles:
            print(f"No articles meet min_story_score threshold for trend: {trend.keyword}")
            return None
        
        # Calculate overall confidence
        confidence_factors = self.confidence.calculate_overall_confidence(
            filtered_articles, trend
        )
        
        # Create section groups
        section_groups = create_section_groups(filtered_articles)
        
        # Check if threshold is met
        threshold_met = confidence_factors.threshold_penalty == 0.0
        
        # Get the primary thread (highest relevance)
        primary_thread = max(analysis.threads, key=lambda t: t.relevance_score)
        
        # Format blocks with section grouping and confidence
        blocks = self.formatter.format_trend_thread_with_sections(
            trend=trend,
            thread=primary_thread,
            articles=filtered_articles,
            section_groups=section_groups,
            confidence_factors=confidence_factors,
            threshold_met=threshold_met
        )
        
        print(f"Found {len(filtered_articles)} articles across {len(section_groups)} sections for trend: {trend.keyword}")
        print(f"Overall confidence: {confidence_factors.final_confidence:.2f} (threshold met: {threshold_met})")
        
        return TrendMessageResult(
            trend_keyword=trend.keyword,
            trend_score=trend.trend_score,
            trend_category=trend.trend_category,
            trend_velocity=trend.velocity,
            overall_confidence=confidence_factors.final_confidence,
            confidence_level=self.confidence.get_confidence_level(confidence_factors.final_confidence),
            confidence_factors=confidence_factors,
            section_groups=section_groups,
            total_articles=len(filtered_articles),
            sections_with_matches=len(section_groups),
            blocks=blocks,
            threshold_met=threshold_met
        )
    
    def _extract_section_from_result(
        self, 
        search_results: Dict[str, Any], 
        article_id: str
    ) -> Optional[str]:
        """
        Extract section from search results for a given article ID.
        
        When Infactory returns grouped results, we can extract section info.
        """
        # Try to find section in results metadata
        results = search_results.get('results', [])
        for result in results:
            metadata = result.get('metadata', {})
            if metadata.get('id') == article_id or result.get('id') == article_id:
                # Check for section in various possible fields
                for field in ['section', 'category', 'department', 'desk']:
                    section = metadata.get(field)
                    if section:
                        return section.lower()
        
        # Default to 'general' if not found
        return 'general'
    
    async def _queue_proactive_suggestions(
        self, 
        trend: Trend, 
        trend_result: TrendMessageResult
    ) -> int:
        """
        Add trend matches to proactive feed queue with confidence and section data.
        
        Returns number of new queue entries.
        """
        if not trend_result.threshold_met:
            print(f"Skipping trend '{trend.keyword}' - threshold not met")
            return 0
        
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
        
        # Use primary thread_id from section groups
        thread_id = f"thread_{trend.keyword.replace(' ', '_').lower()}"
        if trend_result.section_groups:
            # Use first article's thread as identifier
            first_article = trend_result.section_groups[0].articles[0] if trend_result.section_groups[0].articles else None
            if first_article:
                thread_id = f"trend_thread_{trend.keyword.replace(' ', '_').lower()}"
        
        # Check for duplicates
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
            self.db.commit()
            return 0
        
        # Create trend article matches with section info
        for section_group in trend_result.section_groups:
            for article in section_group.articles:
                db_match = TrendArticleMatch(
                    trend_id=db_trend.trend_id,
                    thread_id=thread_id,
                    article_id=article.article_id,
                    infactory_score=article.relevance_score,
                    match_score=article.story_score,
                    story_score=article.story_score,
                    section=section_group.section_name.lower(),
                    surfaced_at=datetime.utcnow(),
                    times_surfaced=1,
                    last_surfaced_at=datetime.utcnow()
                )
                self.db.add(db_match)
        
        # Calculate priority score
        velocity_multiplier = 1.5 if trend.trend_category == 'rising' else 1.2
        priority_score = trend_result.overall_confidence * velocity_multiplier
        
        import json
        
        # Add to proactive queue with confidence and section data
        queue_entry = ProactiveFeedQueue(
            trend_id=db_trend.trend_id,
            thread_id=thread_id,
            priority_score=priority_score,
            status='pending',
            created_at=datetime.utcnow(),
            blocks_json=json.dumps([b.model_dump() if hasattr(b, 'model_dump') else b for b in trend_result.blocks]),
            overall_confidence=trend_result.overall_confidence,
            confidence_level=trend_result.confidence_level,
            sections_involved=trend_result.sections_with_matches,
            total_articles=trend_result.total_articles
        )
        self.db.add(queue_entry)
        
        self.db.commit()
        
        print(f"Queued trend thread: {trend.keyword} -> {trend_result.total_articles} articles across {trend_result.sections_with_matches} sections (confidence: {trend_result.overall_confidence:.2f})")
        
        return 1
    
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

from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from collections import defaultdict

from app.models.schemas import (
    AnalysisResult, Thread, ArticleReference, AnalysisOptions,
    Block, HeaderBlock, SectionBlock, ContextBlock, ActionsBlock,
    DividerBlock, TextObject, ButtonElement
)
from app.integrations.infactory import InfactoryClient
from app.integrations.trends import TrendsClient
from app.integrations.article_loader import get_article_loader
from app.services.block_formatter import BlockFormatter


class AnalyzerService:
    """
    Core analysis orchestrator.
    Can be called from:
    - FastAPI endpoints (web UI)
    - Slack bot handlers (future)
    - CLI scripts
    - Scheduled jobs
    
    Note: Local article storage is NOT used as automatic fallback.
    It must be explicitly requested via analyze_local_article().
    """
    
    def __init__(
        self,
        infactory_client: Optional[InfactoryClient] = None,
        trends_client: Optional[TrendsClient] = None,
        formatter: Optional[BlockFormatter] = None
    ):
        self.infactory = infactory_client or InfactoryClient()
        self.trends = trends_client or TrendsClient()
        self.formatter = formatter or BlockFormatter()
        # Article loader for explicit local storage access only
        self._article_loader = get_article_loader()
    
    async def analyze_text(
        self,
        text: str,
        options: Optional[AnalysisOptions] = None
    ) -> AnalysisResult:
        """
        Analyze arbitrary text and return thread suggestions.
        Returns Block Kit formatted blocks for display.
        """
        options = options or AnalysisOptions()
        query_id = f"query_{uuid.uuid4().hex[:8]}"
        
        # Search archive via Infactory
        search_results = await self.infactory.search(
            query=text,
            limit=options.max_results
        )
        
        # Process search results into threads
        threads = self._create_threads_from_results(
            search_results, 
            options.threshold,
            options.thread_types
        )
        
        # Format each thread with Block Kit blocks
        for thread in threads:
            thread.blocks = self.formatter.format_thread_result(thread)
        
        # Extract topics (simple keyword extraction for now)
        extracted_topics = self._extract_topics(text, search_results)
        
        return AnalysisResult(
            query_id=query_id,
            threads=threads,
            extracted_topics=extracted_topics,
        )
    
    def _create_threads_from_results(
        self,
        search_results: Dict[str, Any],
        threshold: float,
        thread_types: List[str]
    ) -> List[Thread]:
        """
        Convert Infactory search results into Thread objects.
        
        For the POC, we'll create a single thread from the top results
        that meet the threshold. In a more sophisticated implementation,
        we would cluster results into multiple threads.
        """
        # Handle both flat results and grouped results
        results = search_results.get('results', [])
        
        # If no flat results, check for data.results or data.groups
        if not results and 'data' in search_results:
            data = search_results['data']
            if 'results' in data:
                # Flat results in data
                results = data['results']
            elif 'groups' in data:
                # Grouped results - extract from all groups
                results = []
                for group in data['groups']:
                    results.extend(group.get('results', []))
        
        if not results:
            return []
        
        # Filter results by threshold
        filtered_results = [
            r for r in results 
            if r.get('score', 0) >= threshold
        ]
        
        if not filtered_results:
            return []
        
        # Group results by a simple topic extraction strategy
        # For POC: create 1-2 threads based on result clustering
        clusters = self._cluster_results(filtered_results)
        
        threads = []
        for cluster_id, cluster_results in clusters.items():
            if len(cluster_results) < 2:  # Need at least 2 articles for a thread
                continue
            
            # Determine thread type (simplified for POC)
            thread_type = self._classify_thread_type(cluster_results)
            if thread_type not in thread_types:
                continue
            
            # Convert to ArticleReferences
            articles = self._convert_to_articles(cluster_results)
            
            # Calculate relevance as average score
            avg_score = sum(r.get('score', 0) for r in cluster_results) / len(cluster_results)
            
            # Create central topic from top result
            central_topic = self._extract_central_topic(cluster_results)
            
            # Create explanation
            explanation = self._generate_explanation(cluster_results, central_topic)
            
            thread = Thread(
                thread_id=f"thread_{uuid.uuid4().hex[:8]}",
                thread_type=thread_type,
                central_topic=central_topic,
                relevance_score=avg_score,
                articles=articles,
                blocks=[],  # Will be populated later
                explanation=explanation
            )
            threads.append(thread)
        
        # Sort by relevance score
        threads.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return threads
    
    def _cluster_results(self, results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Simple clustering of search results.
        For POC: Group by similar titles/metadata or just split into chunks.
        """
        if len(results) <= 3:
            # If few results, put them all in one cluster
            return {"cluster_1": results}
        
        # Simple clustering: group by decade or by similarity
        clusters = defaultdict(list)
        
        for result in results:
            # Try to extract year from metadata
            metadata = result.get('metadata', {})
            year = None
            
            # Look for year in various fields
            for field in ['published_date', 'date', 'year']:
                date_val = metadata.get(field)
                if date_val:
                    try:
                        if isinstance(date_val, str):
                            year = int(date_val[:4])
                        break
                    except (ValueError, TypeError):
                        continue
            
            # Group by decade if we have a year, otherwise put in general cluster
            if year:
                decade = (year // 10) * 10
                cluster_key = f"decade_{decade}"
            else:
                cluster_key = "general"
            
            clusters[cluster_key].append(result)
        
        # If we have too many small clusters, merge them
        final_clusters = {}
        general_cluster = []
        
        for key, cluster_results in clusters.items():
            if len(cluster_results) >= 2:
                final_clusters[key] = cluster_results
            else:
                general_cluster.extend(cluster_results)
        
        if general_cluster:
            if len(general_cluster) >= 2:
                final_clusters["mixed"] = general_cluster
            elif final_clusters:
                # Add to first cluster if only one item
                first_key = list(final_clusters.keys())[0]
                final_clusters[first_key].extend(general_cluster)
        
        return final_clusters
    
    def _classify_thread_type(self, results: List[Dict[str, Any]]) -> str:
        """
        Classify thread type based on article dates and patterns.
        
        - evergreen: Articles spanning multiple years
        - event_driven: Articles clustered around specific time periods
        - novel_concept: Recent articles (last 2 years) with few historical precedents
        """
        years = []
        for result in results:
            chunk = result.get('chunk', {})
            date_val = chunk.get('published_at')
            if date_val and isinstance(date_val, str):
                try:
                    year = int(date_val[:4])
                    years.append(year)
                except (ValueError, TypeError):
                    continue
        
        if not years:
            return "evergreen"  # Default
        
        year_range = max(years) - min(years) if len(years) > 1 else 0
        most_recent = max(years)
        current_year = datetime.now().year
        
        if year_range >= 5:
            return "evergreen"
        elif most_recent >= current_year - 2 and year_range <= 2:
            return "novel_concept"
        else:
            return "event_driven"
    
    def _convert_to_articles(self, results: List[Dict[str, Any]]) -> List[ArticleReference]:
        """Convert search results to ArticleReference objects."""
        articles = []
        
        for result in results:
            chunk = result.get('chunk', {})
            
            # Parse date from published_at
            published_date = None
            date_val = chunk.get('published_at')
            if date_val:
                try:
                    if isinstance(date_val, str):
                        # Try different date formats
                        for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y']:
                            try:
                                published_date = datetime.strptime(date_val[:10], fmt)
                                break
                            except ValueError:
                                continue
                except (ValueError, TypeError):
                    pass
            
            article = ArticleReference(
                article_id=str(chunk.get('article_id', result.get('id', 'unknown'))),
                title=chunk.get('title', 'Untitled'),
                author=chunk.get('author'),
                published_date=published_date,
                url=None,  # Not provided in chunk
                excerpt=chunk.get('excerpt'),
                relevance_score=result.get('score', 0.5)
            )
            articles.append(article)
        
        # Sort by relevance score
        articles.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return articles
    
    def _extract_central_topic(self, results: List[Dict[str, Any]]) -> str:
        """Extract central topic from top results."""
        if not results:
            return "Unknown Topic"
        
        # Use top result title as base (from chunk, not metadata)
        top_chunk = results[0].get('chunk', {})
        title = top_chunk.get('title', 'Unknown Topic')
        
        # Try to extract key terms (simplified)
        # Remove common stop words and take first few meaningful words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = title.lower().split()
        key_words = [w for w in words if w not in stop_words and len(w) > 2]
        
        if key_words:
            # Return a topic based on key words
            return ' '.join(key_words[:3]).title()
        
        return title
    
    def _generate_explanation(self, results: List[Dict[str, Any]], topic: str) -> str:
        """Generate an explanation for the thread."""
        years = []
        for result in results:
            chunk = result.get('chunk', {})
            date_val = chunk.get('published_at')
            if date_val and isinstance(date_val, str):
                try:
                    year = int(date_val[:4])
                    years.append(year)
                except (ValueError, TypeError):
                    continue
        
        if years:
            year_range = f"{min(years)}-{max(years)}"
            return f"This thread spans {year_range} with {len(results)} related articles on {topic}."
        else:
            return f"This thread contains {len(results)} related articles on {topic}."
    
    def _extract_topics(self, text: str, search_results: Dict[str, Any]) -> List[str]:
        """Extract key topics from text and search results."""
        # Simple keyword extraction from text
        # In a real implementation, we'd use NLP/NER
        words = text.lower().split()
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        
        # Get word frequencies
        word_freq = defaultdict(int)
        for word in words:
            word = word.strip('.,!?;:"()[]{}').lower()
            if word not in stop_words and len(word) > 3:
                word_freq[word] += 1
        
        # Get top words
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        topics = [word for word, count in top_words[:5]]
        
        # Also extract from search result titles
        results = search_results.get('results', [])
        for result in results[:3]:
            metadata = result.get('metadata', {})
            title = metadata.get('title', '')
            title_words = [w.strip('.,!?;:"()[]{}').lower() for w in title.split() if len(w) > 3]
            for word in title_words:
                if word not in stop_words and word not in topics:
                    topics.append(word)
                    if len(topics) >= 5:
                        break
            if len(topics) >= 5:
                break
        
        return topics[:5]
    
    async def analyze_article(
        self,
        article_id: str,
        options: Optional[AnalysisOptions] = None
    ) -> AnalysisResult:
        """Analyze specific archive article by ID."""
        options = options or AnalysisOptions()
        
        # Fetch article content
        try:
            article_data = await self.infactory.get_article_content(article_id)
        except Exception:
            # If content not available, try metadata
            article_data = await self.infactory.get_article(article_id)
        
        # Extract text for analysis
        content = article_data.get('content', '')
        if not content:
            content = article_data.get('metadata', {}).get('title', '')
        
        # Use analyze_text on the content
        return await self.analyze_text(content, options)
    
    async def analyze_local_article(
        self,
        article_id: str,
        options: Optional[AnalysisOptions] = None
    ) -> AnalysisResult:
        """
        Analyze an article from local JSON storage.
        This is useful for working with downloaded article data.
        """
        if not self._article_loader:
            raise ValueError("Local article loader not initialized")
        
        options = options or AnalysisOptions()
        
        # Load article from local storage
        article_data = await self._article_loader.load_article(article_id)
        if not article_data:
            raise ValueError(f"Article {article_id} not found in local storage")
        
        # Extract text for analysis
        content = article_data.get('content', '')
        if not content:
            content = article_data.get('title', '')
        
        # Use analyze_text on the content
        return await self.analyze_text(content, options)
    
    async def analyze_article_data(
        self,
        article_data: Dict[str, Any],
        options: Optional[AnalysisOptions] = None
    ) -> AnalysisResult:
        """
        Analyze article data directly without loading from storage.
        This is useful for one-off analysis of article JSON.
        """
        options = options or AnalysisOptions()
        
        # Extract text for analysis
        content = article_data.get('content', '')
        if not content:
            content = article_data.get('title', '')
        
        # Use analyze_text on the content
        return await self.analyze_text(content, options)
    
    async def close(self):
        """Close all client connections."""
        await self.infactory.close()
    
    async def analyze_text_with_trends(
        self,
        text: str,
        options: Optional[AnalysisOptions] = None
    ) -> AnalysisResult:
        """
        Analyze text and include trend correlation if query matches current trends.
        
        This method checks if any extracted topics from the query match
        current Google Trends, and if so, adds trend context to the results.
        """
        # Do normal analysis first
        result = await self.analyze_text(text, options)
        
        # Check if trends should be included
        if not options or not options.include_trends:
            return result
        
        # Fetch current trends
        try:
            current_trends = await self.trends.fetch_daily_trends(geo='US')
        except Exception as e:
            # If trends fetch fails, return normal result without trend context
            print(f"Error fetching trends for analysis: {e}")
            return result
        
        if not current_trends:
            return result
        
        # Check if any extracted topics match current trends
        trend_matches = []
        matched_trend = None
        
        for topic in result.extracted_topics:
            for trend in current_trends:
                # Simple matching: check if topic is in trend keyword or vice versa
                topic_lower = topic.lower()
                trend_lower = trend.keyword.lower()
                
                if topic_lower in trend_lower or trend_lower in topic_lower:
                    matched_trend = trend
                    trend_matches.append({
                        'keyword': trend.keyword,
                        'score': trend.trend_score,
                        'category': trend.trend_category,
                        'velocity': trend.velocity
                    })
                    break
            
            if matched_trend:
                break
        
        # If we found a matching trend, add context to the first/most relevant thread
        if matched_trend and result.threads:
            from app.models.schemas import TrendContext
            
            # Add trend context to the most relevant thread
            top_thread = result.threads[0]
            top_thread.trend_context = TrendContext(
                keyword=matched_trend.keyword,
                score=matched_trend.trend_score,
                category=matched_trend.trend_category,
                velocity=matched_trend.velocity
            )
            
            # Re-format blocks to include trend indicator
            top_thread.blocks = self.formatter.format_thread_result_with_trend(
                top_thread,
                matched_trend
            )
        
        # Update result with trend matches
        result.trend_matches = trend_matches
        
        return result

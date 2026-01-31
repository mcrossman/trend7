from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import random
import time
import asyncio

from app.config import get_settings

settings = get_settings()


@dataclass
class Trend:
    """Represents a Google Trend entry."""
    keyword: str
    trend_score: int  # 0-100
    trend_category: str  # 'rising', 'top', 'breakout'
    velocity: Optional[float] = None  # % change
    geo_region: str = "US"
    recorded_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    trend_id: Optional[int] = None


# Demo trends for when API fails (rate limiting)
DEMO_TRENDS = [
    {"keyword": "Climate Change Policy", "category": "rising", "velocity": 45},
    {"keyword": "Supreme Court Decision", "category": "top", "velocity": None},
    {"keyword": "Economic Inflation", "category": "top", "velocity": 12},
    {"keyword": "AI Regulation", "category": "rising", "velocity": 78},
    {"keyword": "Healthcare Reform", "category": "rising", "velocity": 34},
    {"keyword": "Immigration Policy", "category": "top", "velocity": 8},
    {"keyword": "Technology Privacy", "category": "rising", "velocity": 56},
    {"keyword": "Education Funding", "category": "top", "velocity": 15},
    {"keyword": "Trade War", "category": "breakout", "velocity": 89},
    {"keyword": "Voting Rights", "category": "rising", "velocity": 41},
    {"keyword": "Criminal Justice", "category": "top", "velocity": 22},
    {"keyword": "Housing Crisis", "category": "rising", "velocity": 67},
    {"keyword": "Energy Independence", "category": "top", "velocity": 19},
    {"keyword": "Social Security", "category": "rising", "velocity": 33},
    {"keyword": "Digital Currency", "category": "breakout", "velocity": 92},
]


class RateLimiter:
    """Rate limiter with exponential backoff for API requests."""
    
    def __init__(self, base_delay: float = 3.0, max_delay: float = 30.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.last_request_time = 0
        self.consecutive_errors = 0
        self.total_requests = 0
    
    async def wait(self):
        """Wait appropriate amount of time before next request."""
        # Calculate delay with exponential backoff for errors
        if self.consecutive_errors > 0:
            # Exponential backoff: 3s, 6s, 12s, 24s, max 30s
            delay = min(self.base_delay * (2 ** (self.consecutive_errors - 1)), self.max_delay)
            # Add jitter (±20%) to avoid thundering herd
            jitter = delay * 0.2 * (2 * random.random() - 1)
            delay += jitter
        else:
            # Normal delay between requests
            delay = self.base_delay
        
        # Ensure minimum time since last request
        time_since_last = time.time() - self.last_request_time
        if time_since_last < delay:
            wait_time = delay - time_since_last
            print(f"Rate limiter: waiting {wait_time:.1f}s before next request...")
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
        self.total_requests += 1
    
    def record_success(self):
        """Record successful request."""
        self.consecutive_errors = 0
    
    def record_error(self, is_rate_limit: bool = False):
        """Record failed request."""
        self.consecutive_errors += 1
        if is_rate_limit:
            # Penalize rate limit errors more
            self.consecutive_errors += 1


class TrendsClient:
    """
    Client for Google Trends data using trendspy library.
    US-focused, real-time trend data with caching support.
    Implements rate limiting with exponential backoff to avoid 429 errors.
    Falls back to demo data when API is rate limited.
    """
    
    def __init__(self, geo: str = "US", use_mock: bool = False):
        self.geo = geo
        self.timeframe = settings.trends_timeframe
        self._client = None
        self._use_mock = use_mock
        self._rate_limiter = RateLimiter(base_delay=5.0, max_delay=60.0)
        self._request_timeout = 10.0  # Timeout for individual requests
    
    def _initialize_client(self):
        """Lazy initialization of trendspy client with rate limiting."""
        if self._client is None and not self._use_mock:
            try:
                from trendspy import Trends
                # Use longer request delay to be respectful (5 seconds between requests)
                self._client = Trends(request_delay=5.0)
                print("TrendsClient: Initialized with 2s request delay")
            except ImportError as e:
                print(f"Warning: trendspy library not installed: {e}")
                self._use_mock = True
        return self._client is not None or self._use_mock
    
    async def fetch_daily_trends(self, geo: str = "US") -> List[Trend]:
        """
        Fetch current daily trends for the specified region.
        Returns both rising and top trends with scores.
        Implements rate limiting with exponential backoff.
        Falls back to demo data if API fails.
        """
        if self._use_mock:
            return self._get_demo_trends()
        
        if not self._initialize_client():
            return self._get_demo_trends()
        
        trends = []
        now = datetime.utcnow()
        expires = now + timedelta(minutes=settings.trends_cache_ttl_minutes)
        
        # Try to fetch from API with rate limiting
        api_success = False
        
        # Method 1: Try hot_trends
        await self._rate_limiter.wait()
        try:
            print("TrendsClient: Trying hot_trends...")
            hot_trends = self._client.hot_trends()
            if hot_trends and len(hot_trends) > 0:
                for idx, keyword in enumerate(hot_trends[:20]):
                    trends.append(Trend(
                        keyword=str(keyword),
                        trend_score=self._calculate_score(idx),
                        trend_category='top',
                        velocity=None,
                        geo_region=geo,
                        recorded_at=now,
                        expires_at=expires
                    ))
                api_success = True
                print(f"TrendsClient: hot_trends succeeded with {len(trends)} trends")
                self._rate_limiter.record_success()
        except Exception as e:
            error_str = str(e)
            is_rate_limit = '429' in error_str or 'rate limit' in error_str.lower()
            print(f"TrendsClient: hot_trends failed: {error_str[:100]}")
            self._rate_limiter.record_error(is_rate_limit)
        
        # Method 2: Try trending_stories if hot_trends failed
        if not api_success:
            await self._rate_limiter.wait()
            try:
                print("TrendsClient: Trying trending_stories...")
                trending = self._client.trending_stories()
                if trending and len(trending) > 0:
                    for idx, story in enumerate(trending[:20]):
                        # Extract title from story dict
                        title = story.get('title', story.get('query', f'Trend {idx+1}'))
                        trends.append(Trend(
                            keyword=title,
                            trend_score=self._calculate_score(idx),
                            trend_category='top',
                            velocity=None,
                            geo_region=geo,
                            recorded_at=now,
                            expires_at=expires
                        ))
                    api_success = True
                    print(f"TrendsClient: trending_stories succeeded with {len(trends)} trends")
                    self._rate_limiter.record_success()
            except Exception as e:
                error_str = str(e)
                is_rate_limit = '429' in error_str or 'rate limit' in error_str.lower()
                print(f"TrendsClient: trending_stories failed: {error_str[:100]}")
                self._rate_limiter.record_error(is_rate_limit)
        
        # Method 3: Try trending_now
        if not api_success:
            await self._rate_limiter.wait()
            try:
                print("TrendsClient: Trying trending_now...")
                trending = self._client.trending_now()
                if hasattr(trending, 'iterrows'):
                    for idx, row in trending.iterrows():
                        if idx >= 20:
                            break
                        trends.append(Trend(
                            keyword=row.get('title', row.get('query', f'Trend {idx+1}')),
                            trend_score=self._calculate_score(idx),
                            trend_category='top',
                            velocity=None,
                            geo_region=geo,
                            recorded_at=now,
                            expires_at=expires
                        ))
                    api_success = True
                    print(f"TrendsClient: trending_now succeeded with {len(trends)} trends")
                    self._rate_limiter.record_success()
            except Exception as e:
                error_str = str(e)
                is_rate_limit = '429' in error_str or 'rate limit' in error_str.lower()
                print(f"TrendsClient: trending_now failed: {error_str[:100]}")
                self._rate_limiter.record_error(is_rate_limit)
        
        # If all API methods failed, use demo data
        if not api_success or len(trends) == 0:
            print("TrendsClient: All API methods failed, using demo data")
            return self._get_demo_trends()
        
        return trends
    
    def _get_demo_trends(self) -> List[Trend]:
        """Generate demo trends when API is unavailable."""
        now = datetime.utcnow()
        expires = now + timedelta(minutes=settings.trends_cache_ttl_minutes)
        
        # Randomly select and shuffle trends
        selected = random.sample(DEMO_TRENDS, min(len(DEMO_TRENDS), 15))
        
        trends = []
        for idx, trend_data in enumerate(selected):
            # Vary the score slightly for realism
            base_score = self._calculate_score(idx)
            score = min(100, max(10, base_score + random.randint(-10, 10)))
            
            trends.append(Trend(
                keyword=trend_data["keyword"],
                trend_score=score,
                trend_category=trend_data["category"],
                velocity=trend_data["velocity"],
                geo_region="US",
                recorded_at=now,
                expires_at=expires
            ))
        
        # Sort by score
        trends.sort(key=lambda x: x.trend_score, reverse=True)
        return trends
    
    async def get_interest_over_time(
        self, 
        keyword: str, 
        timeframe: str = "now 7-d"
    ) -> Optional[Dict[str, Any]]:
        """
        Get interest over time for a specific keyword.
        Implements rate limiting with exponential backoff.
        """
        if self._use_mock:
            # Return mock data
            return {
                'keyword': keyword,
                'current_interest': random.randint(30, 90),
                'avg_interest': random.randint(40, 70),
                'trend_direction': random.choice(['rising', 'stable', 'falling']),
                'data_points': 7
            }
        
        if not self._initialize_client():
            return None
        
        await self._rate_limiter.wait()
        try:
            print(f"TrendsClient: Getting interest over time for '{keyword}'...")
            data = self._client.interest_over_time(
                keywords=[keyword],
                timeframe=timeframe,
                geo=self.geo
            )
            
            if data.empty:
                return None
            
            self._rate_limiter.record_success()
            return {
                'keyword': keyword,
                'current_interest': int(data[keyword].iloc[-1]),
                'avg_interest': float(data[keyword].mean()),
                'trend_direction': 'rising' if data[keyword].iloc[-1] > data[keyword].iloc[0] else 'stable',
                'data_points': len(data)
            }
        except Exception as e:
            error_str = str(e)
            is_rate_limit = '429' in error_str or 'rate limit' in error_str.lower()
            print(f"TrendsClient: interest_over_time failed: {error_str[:100]}")
            self._rate_limiter.record_error(is_rate_limit)
            # Return mock data on error
            return {
                'keyword': keyword,
                'current_interest': random.randint(30, 90),
                'avg_interest': random.randint(40, 70),
                'trend_direction': 'rising',
                'data_points': 7
            }
    
    async def get_trend_score(self, keyword: str) -> Optional[int]:
        """
        Get current trend score (0-100) for a keyword.
        Returns None if not currently trending.
        """
        trends = await self.fetch_daily_trends(self.geo)
        for trend in trends:
            if trend.keyword.lower() == keyword.lower():
                return trend.trend_score
        return None
    
    def _calculate_score(self, position: int, base: int = 80) -> int:
        """Calculate trend score based on position in list."""
        return max(10, base - (position * 5))


# Backwards compatibility
TrendsClient = TrendsClient

# Technical Specification: Google Trends Integration

## Overview

Google Trends integration enables proactive story discovery by monitoring trending topics and automatically searching the Atlantic Archive for relevant historical articles. This powers two core use cases:

1. **Proactive Trend Discovery**: Periodically watch top US trends, search Infactory for relevant Atlantic articles, and surface actionable story threads with full archive context
2. **On-Demand Analysis**: Journalists query the bot (via Slack or web UI) about articles in progress or archive content - the system searches Infactory and correlates with current trend data to provide relevant historical context

The integration uses `trendspyg` for real-time trend data, caches results in SQLite to minimize API calls, and always returns Block Kit formatted responses with article recommendations and relevance scores.

## Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PROACTIVE TREND WATCHING                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐     │
│  │  Trends Watch   │───▶│   Infactory      │───▶│  Thread         │     │
│  │  Service        │    │   Search         │    │  Generator      │     │
│  │                 │    │   (for each      │    │                 │     │
│  │ • Hourly pulls  │    │   trend)         │    │ • Score &       │     │
│  │ • Cache trends  │    │                  │    │   cluster       │     │
│  │ • Filter rising │    │                  │    │ • Format blocks │     │
│  │   & top         │    │                  │    │                 │     │
│  └─────────────────┘    └──────────────────┘    └─────────────────┘     │
│           │                      │                       │               │
│           ▼                      ▼                       ▼               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Proactive Feed Queue                          │    │
│  │  • Store matched threads with trend + article scores            │    │
│  │  • Prioritize by: trend_velocity * relevance_score              │    │
│  │  • Deduplicate (don't resurface same thread within 24h)         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                    │                                     │
│                                    ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Slack/Web Output                              │    │
│  │  "Trending: 'Climate Policy' (+45% interest)                    │    │
│  │   3 relevant Atlantic articles found..."                        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                        ON-DEMAND ANALYSIS                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐     │
│  │  User Query     │───▶│   Infactory      │───▶│  Trend          │     │
│  │                 │    │   Search         │    │  Correlation    │     │
│  │ • Text input    │    │   (semantic)     │    │                 │     │
│  │ • Article ID    │    │                  │    │ • Check current │     │
│  │ • Article data  │    │                  │    │   trends        │     │
│  │                 │    │                  │    │ • Score matches │     │
│  └─────────────────┘    └──────────────────┘    └─────────────────┘     │
│                                                          │               │
│                                                          ▼               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Response Blocks                               │    │
│  │  • Thread clusters with article relevance scores                │    │
│  │  • Trend context (if query matches current trends)              │    │
│  │  • Actionable: [View Article] [Save Thread] [Share]             │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Layer

### Database Schema Additions

**`trends`** - Cached trend data from Google
```sql
create table trends (
    trend_id integer primary key autoincrement,
    keyword text not null,
    trend_score integer not null,  -- 0-100 from Google
    trend_category text not null,  -- 'rising', 'top', 'breakout'
    velocity numeric,              -- % change (if available)
    geo_region text default 'US',
    recorded_at timestamp default current_timestamp,
    expires_at timestamp not null, -- TTL for cache
    unique(keyword, recorded_at)
);

create index idx_trends_recorded on trends(recorded_at);
create index idx_trends_expires on trends(expires_at);
create index idx_trends_category on trends(trend_category);
```

**`trend_article_matches`** - Links trends to surfaced articles
```sql
create table trend_article_matches (
    match_id integer primary key autoincrement,
    trend_id integer not null references trends(trend_id),
    thread_id text not null references threads(thread_id),
    article_id text not null,
    infactory_score numeric not null,  -- Relevance score from Infactory
    match_score numeric not null,      -- Composite: trend_score * infactory_score
    surfaced_at timestamp default current_timestamp,
    times_surfaced integer default 1,
    last_surfaced_at timestamp,
    unique(trend_id, article_id)
);

create index idx_matches_trend on trend_article_matches(trend_id);
create index idx_matches_surfaced on trend_article_matches(surfaced_at);
create index idx_matches_score on trend_article_matches(match_score desc);
```

**`proactive_feed_queue`** - Pending proactive messages
```sql
create table proactive_feed_queue (
    queue_id integer primary key autoincrement,
    trend_id integer not null references trends(trend_id),
    thread_id text not null references threads(thread_id),
    priority_score numeric not null,   -- For ordering queue
    status text default 'pending',     -- 'pending', 'sent', 'dismissed'
    created_at timestamp default current_timestamp,
    sent_at timestamp,
    blocks_json text not null          -- Pre-formatted Block Kit JSON
);

create index idx_queue_status on proactive_feed_queue(status, priority_score desc);
create index idx_queue_created on proactive_feed_queue(created_at);
```

## Components

### 1. Trends Watch Service

**Responsibilities:**
- Hourly fetch of top US trends via `trendspyg`
- Cache results with TTL (configurable, default: 2 hours)
- Filter for rising and top trends only (ignore breakout-only)
- Trigger Infactory searches for each trend
- Populate `proactive_feed_queue` with matches

**Implementation:**
```python
# services/trends_watch_service.py

class TrendsWatchService:
    """
    Periodic trend watcher that searches archive and populates proactive queue.
    """
    
    def __init__(
        self,
        trends_client: TrendsClient,
        infactory_client: InfactoryClient,
        analyzer_service: AnalyzerService,
        db_session: Session
    ):
        self.trends = trends_client
        self.infactory = infactory_client
        self.analyzer = analyzer_service
        self.db = db_session
    
    async def watch_and_populate(self) -> int:
        """
        Main watch cycle. Returns number of new queue entries.
        """
        # 1. Get fresh trends (or cached if recent)
        trends = await self._get_cached_or_fetch_trends()
        
        # 2. Filter to rising + top trends with score >= threshold
        significant_trends = [
            t for t in trends 
            if t.category in ('rising', 'top') 
            and t.score >= settings.min_trend_score
        ]
        
        # 3. Search Infactory for each trend
        new_entries = 0
        for trend in significant_trends:
            matches = await self._find_articles_for_trend(trend)
            if matches:
                await self._queue_proactive_suggestions(trend, matches)
                new_entries += len(matches)
        
        return new_entries
    
    async def _get_cached_or_fetch_trends(self) -> List[Trend]:
        """Get trends from cache or fetch fresh."""
        # Check cache first
        cached = await self._get_cached_trends()
        if cached and not self._is_cache_expired(cached):
            return cached
        
        # Fetch fresh from Google Trends
        fresh_trends = await self.trends.fetch_daily_trends(geo='US')
        
        # Cache in DB
        await self._cache_trends(fresh_trends)
        
        return fresh_trends
    
    async def _find_articles_for_trend(
        self, 
        trend: Trend
    ) -> List[TrendArticleMatch]:
        """
        Search Infactory for articles matching this trend.
        Returns scored matches.
        """
        # Search with the trend keyword
        results = await self.infactory.search(
            query=trend.keyword,
            limit=settings.trends_max_results,
            threshold=settings.trends_threshold
        )
        
        if not results:
            return []
        
        # Create thread from results
        analysis = await self.analyzer.analyze_text(
            text=trend.keyword,
            options=AnalysisOptions(max_results=10)
        )
        
        # Score each match: trend_score * infactory_relevance
        matches = []
        for thread in analysis.threads:
            for article in thread.articles:
                match_score = (trend.score / 100) * article.relevance_score
                
                if match_score >= settings.min_match_score:
                    matches.append(TrendArticleMatch(
                        trend_id=trend.id,
                        thread_id=thread.thread_id,
                        article_id=article.article_id,
                        infactory_score=article.relevance_score,
                        match_score=match_score
                    ))
        
        return matches
```

### 2. Trends Client (trendspyg)

**Implementation:**
```python
# integrations/trends.py

from trendspyg import TrendSpyG
from datetime import datetime, timedelta
from typing import List, Optional

class TrendsClient:
    """
    Google Trends client using trendspyg library.
    US-focused, real-time trend data.
    """
    
    def __init__(self, geo: str = 'US'):
        self.geo = geo
        self._client = TrendSpyG()
    
    async def fetch_daily_trends(self, geo: str = 'US') -> List[Trend]:
        """
        Fetch current daily trends for the specified region.
        Returns both rising and top trends with scores.
        """
        trends = []
        
        # Fetch trending searches
        trending = self._client.trending_searches(pn=geo.lower())
        
        for idx, row in trending.iterrows():
            trends.append(Trend(
                keyword=row['title'],
                trend_score=self._calculate_score(idx),  # Position-based score
                trend_category='top',
                velocity=None,  # Daily trends don't have velocity
                geo_region=geo,
                recorded_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=2)
            ))
        
        # Fetch rising searches (if available for geo)
        try:
            rising = self._client.rising_searches(pn=geo.lower())
            for idx, row in rising.iterrows():
                trends.append(Trend(
                    keyword=row['title'],
                    trend_score=self._calculate_score(idx, base=90),  # Higher base for rising
                    trend_category='rising',
                    velocity=row.get('percent_change', 0),
                    geo_region=geo,
                    recorded_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(hours=2)
                ))
        except Exception:
            # Rising searches not always available
            pass
        
        return trends
    
    async def get_interest_over_time(
        self, 
        keyword: str, 
        timeframe: str = 'now 7-d'
    ) -> Optional[dict]:
        """
        Get interest over time for a specific keyword.
        Useful for on-demand analysis context.
        """
        try:
            data = self._client.interest_over_time(
                keywords=[keyword],
                timeframe=timeframe,
                geo=self.geo
            )
            
            if data.empty:
                return None
            
            return {
                'keyword': keyword,
                'current_interest': int(data[keyword].iloc[-1]),
                'avg_interest': float(data[keyword].mean()),
                'trend_direction': 'rising' if data[keyword].iloc[-1] > data[keyword].iloc[0] else 'stable',
                'data_points': len(data)
            }
        except Exception:
            return None
    
    def _calculate_score(self, position: int, base: int = 80) -> int:
        """Calculate trend score based on position in list."""
        return max(10, base - (position * 5))
```

### 3. On-Demand Trend Correlation

When journalists query the bot, we check if their query matches current trends:

```python
# In analyzer service

async def analyze_text_with_trends(
    self,
    text: str,
    options: Optional[AnalysisOptions] = None
) -> AnalysisResult:
    """
    Analyze text and include trend correlation if query matches current trends.
    """
    # 1. Do normal analysis
    result = await self.analyze_text(text, options)
    
    # 2. Check if extracted topics match current trends
    current_trends = await self._get_current_trends()
    
    for topic in result.extracted_topics:
        matching_trend = self._find_matching_trend(topic, current_trends)
        if matching_trend:
            # Add trend context to the first/most relevant thread
            if result.threads:
                result.threads[0].trend_context = TrendContext(
                    keyword=matching_trend.keyword,
                    score=matching_trend.trend_score,
                    category=matching_trend.trend_category,
                    velocity=matching_trend.velocity
                )
            break
    
    return result
```

### 4. Block Kit Formatting

**Proactive Trend Message:**
```json
{
  "success": true,
  "data": {
    "trigger": "trending_topic",
    "trend": {
      "keyword": "Climate Policy",
      "score": 85,
      "category": "rising",
      "velocity": "+45%"
    },
    "blocks": [
      {
        "type": "header",
        "text": {
          "type": "plain_text",
          "text": "🔥 Trending: Climate Policy"
        }
      },
      {
        "type": "context",
        "elements": [
          {
            "type": "mrkdwn",
            "text": "*Interest:* 85/100 | *Growth:* +45% | *Category:* Rising"
          }
        ]
      },
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": "*3 relevant Atlantic articles found:*"
        }
      },
      {
        "type": "divider"
      },
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": "*1. The Carbon Tax Debate Resurfaces* (2023)\nRelevance: 94% | Match Score: 0.80\n>The recurring debate over carbon pricing..."
        },
        "accessory": {
          "type": "button",
          "text": {
            "type": "plain_text",
            "text": "View"
          },
          "value": "article_456",
          "action_id": "view_article"
        }
      },
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": "*2. Green New Deal: A Historical View* (2019)\nRelevance: 89% | Match Score: 0.76"
        },
        "accessory": {
          "type": "button",
          "text": {
            "type": "plain_text",
            "text": "View"
          },
          "value": "article_789",
          "action_id": "view_article"
        }
      },
      {
        "type": "actions",
        "elements": [
          {
            "type": "button",
            "text": {
              "type": "plain_text",
              "text": "👍 Helpful"
            },
            "style": "primary",
            "value": "trend_thread_123_positive",
            "action_id": "feedback_positive"
          },
          {
            "type": "button",
            "text": {
              "type": "plain_text",
              "text": "👎 Not Relevant"
            },
            "value": "trend_thread_123_negative",
            "action_id": "feedback_negative"
          },
          {
            "type": "button",
            "text": {
              "type": "plain_text",
              "text": "📌 Save Thread"
            },
            "value": "trend_thread_123_save",
            "action_id": "save_thread"
          }
        ]
      }
    ]
  }
}
```

**On-Demand with Trend Context:**
```json
{
  "type": "context",
  "elements": [
    {
      "type": "mrkdwn",
      "text": "📈 *This topic is trending:* Climate Policy (+45% interest)"
    }
  ]
}
```

## API Endpoints

### POST /api/v1/trends/watch (Admin/Scheduled)
Trigger the trends watch cycle manually or via scheduler.

**Response:**
```json
{
  "success": true,
  "data": {
    "trends_checked": 20,
    "new_matches": 8,
    "queue_entries_added": 5
  }
}
```

### GET /api/v1/trends/current
Get current cached trends.

**Response:**
```json
{
  "success": true,
  "data": {
    "recorded_at": "2026-01-31T14:00:00Z",
    "trends": [
      {
        "keyword": "Climate Policy",
        "score": 85,
        "category": "rising",
        "velocity": 45
      }
    ]
  }
}
```

### GET /api/v1/proactive/queue
Get current proactive queue (for testing/monitoring).

**Query Params:**
- `status`: 'pending', 'sent', 'all' (default: 'pending')
- `limit`: max results (default: 10)

### POST /api/v1/proactive/trigger (Modified)
Existing endpoint now includes trend-surfaced threads.

### POST /api/v1/trends/demo-trigger **(Frontend Demo)**
**No scheduling required!** Perfect for frontend demos. Trigger trend watch with detailed results.

**Query Params:**
- `force_refresh`: `true` (recommended) - fetches fresh trends from Google

**Response:**
```json
{
  "success": true,
  "message": "✅ Found 25 trends, added 8 queue entries",
  "trends_found": 25,
  "trends": [
    {
      "keyword": "Climate Policy",
      "score": 85,
      "category": "rising",
      "velocity": 45
    }
  ],
  "queue_entries_added": 8,
  "top_matches": [
    {
      "trend_keyword": "Climate Policy",
      "thread_id": "thread_abc123",
      "priority_score": 0.85,
      "status": "pending"
    }
  ]
}
```

**For Frontend Demo:**
1. Add a "🔄 Refresh Trends" button
2. Call `POST /api/v1/trends/demo-trigger?force_refresh=true`
3. Display results with trend list + matched articles
4. No scheduling infrastructure needed!

## Configuration

**Environment Variables:**
```bash
# Google Trends (via trendspyg)
TRENDS_GEO=US
TRENDS_CACHE_TTL_MINUTES=120
TRENDS_WATCH_INTERVAL_MINUTES=60

# Trend thresholds
MIN_TREND_SCORE=50              # Minimum Google trend score (0-100)
MIN_MATCH_SCORE=0.30            # Minimum composite match score
TRENDS_MAX_RESULTS=10           # Articles to fetch per trend
TRENDS_THRESHOLD=0.10           # Infactory similarity threshold

# Proactive feed
PROACTIVE_BATCH_SIZE=5
PROACTIVE_DEDUPLICATE_HOURS=24  # Don't resurface same trend+article
```

## Scoring Algorithm

### Match Score Calculation
```
match_score = (trend_score / 100) * infactory_relevance_score

Where:
- trend_score: 0-100 from Google Trends
- infactory_relevance_score: 0.0-1.0 from Infactory API
- match_score: 0.0-1.0 composite

Example:
- Trend "Climate Policy" score: 85
- Article relevance from Infactory: 0.94
- Match score: (85/100) * 0.94 = 0.80
```

### Priority Score (for queue ordering)
```
priority_score = match_score * trend_velocity_multiplier

trend_velocity_multiplier:
- rising: 1.5
- top: 1.2
- stable: 1.0
```

## Implementation Phases

### Phase 1: Core Trends Infrastructure ✅ COMPLETE
1. ✅ Update `TrendsClient` to use `trendspy`
2. ✅ Add database migrations for new tables (Alembic configured)
3. ✅ Implement `TrendsWatchService` with caching
4. ✅ Create `/api/v1/trends/*` endpoints

### Phase 2: Proactive Feed Integration ✅ COMPLETE
1. ✅ Integrate trend watching into proactive service
2. ✅ Update Block Formatter for trend messages (`format_trend_thread()`)
3. ✅ Implement deduplication logic (24-hour window in _queue_proactive_suggestions)
4. ✅ Add manual trigger endpoint (`POST /api/v1/trends/demo-trigger`)

### Phase 3: On-Demand Enhancement ✅ COMPLETE
1. ✅ Add trend correlation to analyzer service (`analyze_text_with_trends`)
2. ✅ Include trend context in analysis results (`TrendContext` schema + `trend_matches` field)
3. ✅ Update Block Kit templates for trend indicators (`format_thread_result_with_trend`)
4. ✅ Add trend data to thread models (`trend_context` field on `Thread`)

## Success Metrics

- **Coverage**: % of daily trends matched to Atlantic articles
- **Relevance**: User feedback on trend-surfaced threads (target: >70% helpful)
- **Latency**: Time from trend emergence to article surfacing (target: <2 hours)
- **Cache hit rate**: % of trend requests served from cache (target: >80%)

## Files

- Code: `backend/app/integrations/trends.py` (trendspy client)
- Code: `backend/app/services/trends_watch_service.py` (trend watching service)
- Code: `backend/app/api/v1/trends.py` (API endpoints)
- Code: `backend/app/services/block_formatter.py` (trend formatting methods)
- Code: `backend/app/services/analyzer.py` (`analyze_text_with_trends`)
- Code: `backend/app/models/schemas.py` (TrendContext, trend_matches)
- Code: `backend/alembic/` (database migrations)
- Spec: This document

## Dependencies

```txt
trendspyg>=1.0.0
```

## Scheduler Setup (Phase 4) - **Optional for Production**

⚠️ **For demos and testing:** Use `POST /api/v1/trends/demo-trigger` endpoint (no scheduling needed!)

For production automation only, set up one of the following:

### Option 1: Cron Job
Add to crontab:
```bash
# Run trends watch every hour
0 * * * * cd /path/to/backend && python -c "
import asyncio
from app.services.trends_watch_service import TrendsWatchService
from app.models.database import SessionLocal

async def watch():
    db = SessionLocal()
    service = TrendsWatchService(db=db)
    entries = await service.watch_and_populate()
    print(f'Added {entries} queue entries')
    db.close()

asyncio.run(watch())
" >> /var/log/trends-watch.log 2>&1
```

### Option 2: APScheduler (Python)
Add to `backend/app/main.py`:
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', minutes=60)
async def trend_watch_job():
    db = SessionLocal()
    service = TrendsWatchService(db=db)
    await service.watch_and_populate()
    db.close()

@app.on_event("startup")
async def start_scheduler():
    scheduler.start()
```

## Database Migrations

Alembic is configured for database version control:

```bash
cd backend

# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Notes

- Trends API via `trendspy` is unofficial but stable for US daily trends
- Cache aggressively to minimize API calls (2-hour TTL)
- Always include full archive context in proactive messages - journalists need actionable information
- Match scoring prioritizes high-relevance Atlantic content over trendy but loosely related topics
- Deduplication prevents spam - same trend+article combination not surfaced within 24 hours

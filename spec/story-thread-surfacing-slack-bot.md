# Technical Specification: Story Thread Surfacing Slack Bot

## Overview

A Slack-integrated system for identifying and resurfacing historical Atlantic stories relevant to current editorial work. The system uses semantic search against the Atlantic Archive API combined with Google Trends correlation to identify story threads and surface them proactively or on-demand to journalists.

## Architecture

### High-Level Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Slack UI      │────▶│  Story Processor │────▶│ Atlantic Archive│
│   (Test Harness)│     │                  │     │      API        │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │                         │
         │                       ▼                         │
         │              ┌──────────────────┐               │
         │              │  Google Trends   │               │
         │              │   (Scraping)     │               │
         │              └──────────────────┘               │
         │                       │                         │
         ▼                       ▼                         ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   SQLite DB     │◀────│ Thread Analyzer  │◀────│ Similarity/RRF  │
│ (topics, refs,  │     │  (clustering,    │     │     Search      │
│ threads, trends)│     │   lineage)       │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Slack Output Generator                   │
│  - Rich blocks with article previews                            │
│  - Timeline visualizations (text-based)                         │
│  - Relevance scores and explanations                            │
│  - Feedback collection (👍/👎)                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Data Layer (SQLite)

**Tables:**

- `story_references`: Article IDs and metadata from archive
  - `article_id` (PK)
  - `title`, `author`, `published_date`, `url`
  - `topics` (JSON array)
  - `last_analyzed_at`
  - `relevance_score` (computed)

- `threads`: Identified story clusters
  - `thread_id` (PK)
  - `thread_type` (enum: 'evergreen', 'event_driven', 'novel_concept')
  - `central_topic` (text)
  - `article_ids` (JSON array of references)
  - `created_at`, `updated_at`
  - `temporal_span` (days between oldest/newest)
  - `cluster_density` (articles per time unit)

- `topics`: Extracted topics from analysis
  - `topic_id` (PK)
  - `topic_name`
  - `frequency_count`
  - `last_seen_at`
  - `trend_velocity` (from Google Trends)

- `trend_data`: Google Trends correlations
  - `topic_id` (FK)
  - `trend_score` (0-100)
  - `recorded_at`
  - `geo_region` (default: 'US')

- `user_feedback`: Feedback on suggestions
  - `feedback_id` (PK)
  - `thread_id` (FK)
  - `was_helpful` (boolean)
  - `context` (text - what user was working on)
  - `created_at`

### 2. Atlantic Archive API Client

**Endpoints Used:**
- `POST /v1/search` - Hybrid/semantic search with RRF
- `GET /v1/articles/{id}` - Metadata retrieval
- `GET /v1/articles/{id}/content` - Full content
- `GET /v1/topics` - Reference data

**Features:**
- Configurable reranking (`rerank=true` for deep analysis)
- Hierarchical grouping (`group_by=year`, `group_by=topic`)
- Date-bounded filtering for temporal analysis
- Semantic similarity thresholds (configurable, default: 10%)

### 3. Google Trends Integration

**Implementation:**
- Use `pytrends` or similar library for unofficial API access
- Real-time topic correlation during analysis
- Rate-limited to avoid blocks
- Fallback: Skip trends if unavailable

**Process:**
1. Extract topics from user input or archive results
2. Query Google Trends for topic interest
3. Store trend velocity (rising/falling/stable)
4. Use for prioritization in proactive feed

### 4. Thread Analyzer

**Clustering Algorithm:**
- Semantic similarity matrix from archive search results
- Temporal clustering: Group by publication date proximity
- Thematic clustering: Group by shared topics/entities
- RRF (Reciprocal Rank Fusion) for hybrid ranking

**Thread Types:**
- **Evergreen**: Long temporal span (>1 year), recurring topics
- **Event-driven**: Tight temporal cluster (<30 days), spike in coverage
- **Novel concept**: Semantic outliers with weak historical precedent

**Lineage Detection:**
- Follow reference chains via semantic similarity
- Identify foundational articles (highly cited in cluster)
- Build parent-child relationships based on temporal and semantic proximity

### 5. Slack Bot (Test Harness UI)

**Interface Options:**

A. **Interactive Web UI** (for testing)
   - Text input area (paste article content)
   - "Find Connections" button
   - Article ID/URL input
   - "Trigger Proactive Scan" button
   - Results display with Slack-like formatting

B. **CLI Mode** (for automation)
   - `python bot.py analyze --text "..."`
   - `python bot.py analyze --article-id ABC123`
   - `python bot.py proactive --channel #suggestions`

**Output Format (Rich Blocks):**

```
═══════════════════════════════════════════════════════════════
🎯 Story Thread: Climate Policy Evolution
Type: Evergreen | Relevance: 87% | Articles: 12
───────────────────────────────────────────────────────────────
📊 TIMELINE:
  2019 ──●── 2021 ──●── 2023 ──●── 2024
         │        │        │        │
     [Green     [Biden   [Inflat-  [Paris
      New       Climate   ion      Agreement
      Deal]     Agenda]   Impact]  Update]

🔍 WHY SURFACED:
Your input mentioned "carbon pricing" → 3 articles match
Currently trending: +45% interest on Google Trends
───────────────────────────────────────────────────────────────
📰 TOP MATCHES:

1. "The Carbon Tax Debate Resurfaces" (2023)
   Author: Jane Doe | Relevance: 94%
   Excerpt: "The recurring debate over carbon pricing..."
   [View Full] [Add to Thread] [Dismiss]

2. "Green New Deal: A Historical Perspective" (2019)
   Author: John Smith | Relevance: 89%
   [View Full] [Add to Thread] [Dismiss]
───────────────────────────────────────────────────────────────
👍 Was this helpful? [Yes] [No] [Save Thread]
═══════════════════════════════════════════════════════════════
```

### 6. Proactive Feed Generator

**Trigger Conditions:**
1. **New Archive Content**: Scan for articles added to archive (via date search)
2. **Trending Topics**: When Google Trends shows spike in topic matching stored threads
3. **Scheduled**: Daily/weekly batch analysis

**Selection Criteria:**
- Trend velocity > 50 (rising topics)
- Thread has 3+ articles (substantial coverage)
- Not surfaced in last 7 days (avoid repetition)
- Relevance score > 10%

**Output:** Top 5 threads posted to configured Slack channel

## Configuration

**Environment Variables:**
```bash
ATLANTIC_API_KEY=xxx
ATLANTIC_API_URL=https://api.atlantic-archive.com/v1
TRENDS_GEO=US
TRENDS_TIMEFRAME=now 7-d
DB_PATH=./data/story_threads.db
RELEVANCE_THRESHOLD=0.10
RERANK_ENABLED=true
PROACTIVE_CHANNEL=#story-suggestions
SCAN_INTERVAL_HOURS=24
```

**Configurable Thresholds:**
- `RELEVANCE_THRESHOLD`: Minimum similarity score (0.0-1.0, default: 0.10)
- `CLUSTER_TIME_WINDOW_DAYS`: Days to consider for event clustering (default: 30)
- `EVERGREEN_MIN_SPAN_DAYS`: Minimum span for evergreen (default: 365)
- `MAX_RESULTS_PER_QUERY`: Cap for user queries (default: 10)
- `PROACTIVE_BATCH_SIZE`: Threads per proactive post (default: 5)

## MVP Implementation Plan

### Phase 1: Core Infrastructure (Week 1)
1. SQLite schema setup
2. Atlantic Archive API client with caching
3. Basic search pipeline (input → archive → results)
4. Simple CLI interface

### Phase 2: Analysis Engine (Week 1-2)
1. Google Trends integration (pytrends)
2. Thread clustering algorithm
3. Thread type classification
4. Lineage detection

### Phase 3: Slack Integration (Week 2)
1. Rich output formatting
2. Test harness web UI
3. Proactive feed scheduler
4. Feedback collection

### Phase 4: Polish (Week 2-3)
1. Timeline visualization
2. Explanation generation
3. Configurable thresholds
4. Documentation

## API/Interface Design

**Programmatic API (for future Slack integration):**

```python
# Core service interface
class StorySurfacingService:
    def analyze_content(self, text: str) -> ThreadResult:
        """Analyze pasted content and return thread suggestions"""
        
    def analyze_article(self, article_id: str) -> ThreadResult:
        """Analyze specific archive article"""
        
    def get_proactive_suggestions(self) -> List[ThreadResult]:
        """Get top threads for proactive feed"""
        
    def record_feedback(self, thread_id: str, helpful: bool, context: str):
        """Record user feedback for learning"""

# Data models
@dataclass
class ThreadResult:
    thread_id: str
    thread_type: ThreadType  # evergreen, event_driven, novel_concept
    central_topic: str
    relevance_score: float
    articles: List[ArticleReference]
    timeline: TimelineData
    explanation: str
    trend_data: Optional[TrendInfo]
```

## Success Metrics

**Technical:**
- Query latency < 5s (with reranking)
- Thread detection accuracy (measured via feedback)
- Proactive suggestion relevance rate (>70% thumbs up)

**Editorial:**
- Time to find relevant historical context
- Number of threads saved/bookmarked
- Articles produced with historical context

## Future Enhancements

- Real Slack bot integration (not just test harness)
- User profiles and personalized feeds
- Advanced visualization (interactive timelines)
- ML-based relevance tuning from feedback
- Integration with editorial CMS
- Multi-language support

## Files

- Code: `src/` (Python FastAPI + simple frontend)
- Database: `data/story_threads.db` (SQLite)
- Config: `.env` and `config.yaml`
- Tests: `tests/`

## Notes

- Stateless auth for MVP (no user sessions)
- Google Trends scraping is best-effort (may rate-limit)
- Archive API calls are the main cost - implement caching
- Focus on relevance over recency as specified
- Slack blocks can be rendered as HTML for testing

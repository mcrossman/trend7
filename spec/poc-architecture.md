# POC Architecture: Story Thread Surfacing System

## Overview

Architecture for the proof-of-concept implementation of the story thread surfacing system. A modular Python backend exposes REST APIs consumed by a Next.js frontend. The backend is designed to be reusable for future Slack bot integration while supporting a standalone web interface.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  ┌──────────────────────┐              ┌──────────────────────────────────┐ │
│  │   Next.js Web App    │              │   Future: Slack Bot              │ │
│  │   (POC Frontend)     │              │   (Bolt/Slack API)               │ │
│  │                      │              │                                  │ │
│  │  • Block Renderer    │              │  • Event handlers                │ │
│  │  • Query Interface   │              │  • Command parsers               │ │
│  │  • Timeline Viz      │              │  • Modal builders                │ │
│  └──────────┬───────────┘              └──────────────┬───────────────────┘ │
│             │                                         │                     │
│             │         REST API (JSON)                 │                     │
│             └─────────────────┬───────────────────────┘                     │
│                               │                                             │
└───────────────────────────────┼─────────────────────────────────────────────┘
                                │
┌───────────────────────────────┼─────────────────────────────────────────────┐
│                           SERVICE LAYER                                      │
│                               │                                             │
│  ┌────────────────────────────┴──────────────────────────────────────────┐  │
│  │                    Python Backend (FastAPI)                            │  │
│  │                                                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                      API Layer (Routers)                         │  │  │
│  │  │  • /api/v1/analyze        (POST text/article_id)                │  │  │
│  │  │  • /api/v1/threads        (GET/POST thread operations)          │  │  │
│  │  │  • /api/v1/proactive      (GET suggestions, POST trigger)       │  │  │
│  │  │  • /api/v1/feedback       (POST thumbs up/down)                 │  │  │
│  │  │  • /api/v1/topics         (GET available topics)                │  │  │
│  │  │  • /api/v1/health         (Health check)                        │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                    Service Layer                                 │  │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │  │  │
│  │  │  │  Analyzer    │  │   Thread     │  │   Proactive         │  │  │  │
│  │  │  │  Service     │  │   Service    │  │   Service           │  │  │  │
│  │  │  │              │  │              │  │                     │  │  │  │
│  │  │  │ • Semantic   │  │ • Cluster    │  │ • Schedule          │  │  │  │
│  │  │  │   search     │  │   detection  │  │   scans             │  │  │  │
│  │  │  │ • Similarity │  │ • Type       │  │ • Trend alerts      │  │  │  │
│  │  │  │   scoring    │  │   classify   │  │ • Priority queue    │  │  │  │
│  │  │  │ • Trend      │  │ • Lineage    │  │                     │  │  │  │
│  │  │  │   correlate  │  │   build      │  │                     │  │  │  │
│  │  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                 Integration Layer                                │  │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │  │  │
│  │  │  │   Infactory  │  │    Google    │  │   Article   │         │  │  │
│  │  │  │    Client    │  │    Trends    │  │   Loader    │         │  │  │
│  │  │  │              │  │    Client    │  │             │         │  │  │
│  │  │  │ • Search API │  │              │  │ • JSON I/O  │         │  │  │
│  │  │  │ • Article    │  │ • pytrends   │  │ • Local FS  │         │  │  │
│  │  │  │   metadata   │  │ • Topic      │  │ • Bulk load │         │  │  │
│  │  │  │ • Content    │  │   extract    │  │             │         │  │  │
│  │  │  └──────────────┘  └──────────────┘  └──────────────┘         │  │  │
│  │  │  ┌──────────────────────────────────────────────────────────┐  │  │  │
│  │  │  │                    Block Kit Formatter                    │  │  │
│  │  │  │  • Slack blocks → JSON                                   │  │  │
│  │  │  │  • Rich components                                       │  │  │
│  │  │  │  • Actions                                               │  │  │
│  │  │  └──────────────────────────────────────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                    Data Layer                                    │  │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │  │  │
│  │  │  │   SQLite     │  │    Cache     │  │   Config            │  │  │  │
│  │  │  │   (SQLite)   │  │   (TTLCache) │  │   (Pydantic)        │  │  │  │
│  │  │  │              │  │              │  │                     │  │  │  │
│  │  │  │ • Threads    │  │ • API        │  │ • Thresholds        │  │  │  │
│  │  │  │ • Topics     │  │   responses  │  │ • Feature flags     │  │  │  │
│  │  │  │ • Feedback   │  │ • Trend      │  │ • Secrets           │  │  │  │
│  │  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Backend Design (Python/FastAPI)

### Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Pydantic settings
│   ├── dependencies.py         # FastAPI dependencies
│   ├──
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── analyze.py      # Analysis endpoints
│   │   │   ├── articles.py     # Local article management
│   │   │   ├── threads.py      # Thread management
│   │   │   ├── proactive.py    # Proactive suggestions
│   │   │   ├── feedback.py     # User feedback
│   │   │   ├── topics.py       # Topic reference
│   │   │   └── health.py       # Health checks
│   │   └── deps.py             # Common dependencies
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── analyzer.py         # Main analysis orchestrator
│   │   ├── thread_service.py   # Thread CRUD + clustering
│   │   ├── proactive_service.py # Proactive feed logic
│   │   └── block_formatter.py  # Block Kit formatting
│   │
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── infactory.py        # Atlantic Archive API client
│   │   │   ├── article_loader.py   # Local JSON article loader
│   │   ├── trends.py           # Google Trends client
│   │   └── cache.py            # Caching utilities
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py         # SQLAlchemy models
│   │   ├── schemas.py          # Pydantic request/response models
│   │   └── blocks.py           # Block Kit type definitions
│   │
│   └── core/
│       ├── __init__.py
│       ├── clustering.py       # Thread clustering algorithms
│       ├── timeline.py         # Timeline generation
│       └── utils.py            # Utilities
│
├── tests/
├── alembic/                    # DB migrations
├── requirements.txt
├── pyproject.toml
└── Dockerfile
```

### Key Design Decisions

#### 1. Modular Service Layer

Services are designed to be reusable across different interfaces:

```python
# services/analyzer.py
class AnalyzerService:
    """
    Core analysis orchestrator.
    Can be called from:
    - FastAPI endpoints (web UI)
    - Slack bot handlers (future)
    - CLI scripts
    - Scheduled jobs
    """
    
    def __init__(
        self,
        infactory_client: InfactoryClient,
        trends_client: TrendsClient,
        thread_service: ThreadService,
        formatter: BlockFormatter
    ):
        self.infactory = infactory_client
        self.trends = trends_client
        self.threads = thread_service
        self.formatter = formatter
    
    async def analyze_text(
        self,
        text: str,
        options: AnalysisOptions
    ) -> AnalysisResult:
        """
        Analyze arbitrary text and return thread suggestions.
        Returns Block Kit formatted blocks for display.
        """
        # 1. Extract topics from text
        # 2. Search archive via Infactory
        # 3. Correlate with Google Trends
        # 4. Cluster into threads
        # 5. Format as Block Kit blocks
        pass
    
    async def analyze_local_article(
        self,
        article_id: str,
        options: AnalysisOptions
    ) -> AnalysisResult:
        """
        Analyze an article from local JSON storage.
        Falls back to API if not found locally.
        """
        pass
    
    async def analyze_article(
        self,
        article_id: str,
        options: AnalysisOptions
    ) -> AnalysisResult:
        """Analyze specific archive article by ID."""
        pass

# services/block_formatter.py  
class BlockFormatter:
    """
    Formats analysis results as Slack Block Kit blocks.
    This allows the same output to be:
    - Rendered by web UI (convert blocks to React components)
    - Sent directly to Slack (native rendering)
    - Stored for later retrieval
    """
    
    def format_thread_result(
        self,
        thread: Thread,
        include_timeline: bool = True
    ) -> List[Block]:
        """Format a thread as Block Kit blocks."""
        pass
    
    def format_proactive_feed(
        self,
        threads: List[Thread]
    ) -> List[Block]:
        """Format proactive suggestions."""
        pass
```

#### 2. Block Kit as Universal Format

Using Slack's Block Kit as the response format provides:
- **Rich UI**: Sections, dividers, buttons, images, context
- **Portability**: Same format works for web UI and Slack
- **Future-proof**: Easy Slack integration later
- **Structured**: Well-defined schema for frontend rendering

Example response structure:

```python
# Response from any endpoint
{
    "success": True,
    "data": {
        "thread_id": "thread_123",
        "blocks": [
            # Header section
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🎯 Story Thread: Climate Policy Evolution"
                }
            },
            # Context/metadata
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "*Type:* Evergreen"},
                    {"type": "mrkdwn", "text": "*Relevance:* 87%"},
                    {"type": "mrkdwn", "text": "*Articles:* 12"}
                ]
            },
            # Divider
            {"type": "divider"},
            # Timeline section
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Timeline:*\n```\n2019 ──●── 2021 ──●── 2023 ──●── 2024\n```"
                }
            },
            # Article list
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*1. The Carbon Tax Debate Resurfaces* (2023)\nAuthor: Jane Doe | Relevance: 94%\n> The recurring debate over carbon pricing..."
                },
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View"},
                    "value": "article_456"
                }
            },
            # Actions
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "👍 Helpful"},
                        "value": "feedback_positive",
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "👎 Not Helpful"},
                        "value": "feedback_negative"
                    }
                ]
            }
        ]
    }
}
```

#### 3. Client Agnostic Design

The backend doesn't care about the client:

```python
# All endpoints return Block Kit format
# Client decides how to render

# Next.js frontend: Convert blocks to React components
# Slack bot: Pass blocks directly to Slack API
# Mobile app: Custom renderer for Block Kit
# CLI: Text rendering of blocks
```

#### 4. Local Article Storage

The system supports loading article JSON files directly from local storage, which is useful for:

- **Working offline**: Analyze downloaded articles without API calls
- **Testing**: Use known article data for reproducible results
- **Bulk processing**: Import multiple articles from a directory
- **Debugging**: Inspect article data directly

**Storage Location**: `./data/articles/{article_id}.json`

**Features**:
- **Explicit access only**: Local storage is NOT automatic fallback; use specific endpoints
- Bulk import: Load all JSON files from a directory
- Direct analysis: Analyze article data without storing it
- CRUD operations: List, upload, retrieve, and delete local articles

**Design Principle**: The Infactory API is the primary source. Local storage is used only when:
1. Explicitly requested via `/api/v1/analyze/local-article`
2. The API is unavailable and you need to work offline
3. Testing with known article data

**Usage Examples**:
```bash
# Upload a single article
curl -X POST /api/v1/articles/upload-json \
  -H "Content-Type: application/json" \
  -d '{"article_id": "my_article", "data": {...}}'

# Analyze a local article
curl -X POST /api/v1/analyze/local-article \
  -H "Content-Type: application/json" \
  -d '{"article_id": "my_article"}'

# Bulk import from directory
curl -X POST /api/v1/articles/bulk-import \
  -H "Content-Type: application/json" \
  -d '{"directory": "/path/to/articles"}'
```

### API Endpoints

#### POST /api/v1/analyze/text
Analyze pasted text content.

**Request:**
```json
{
  "text": "Article content or draft...",
  "options": {
    "max_results": 10,
    "include_trends": true,
    "threshold": 0.10,
    "thread_types": ["evergreen", "event_driven", "novel_concept"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "query_id": "query_123",
    "threads": [
      {
        "thread_id": "thread_456",
        "thread_type": "evergreen",
        "relevance_score": 0.87,
        "blocks": [...]  // Block Kit blocks
      }
    ],
    "extracted_topics": ["carbon pricing", "climate policy"],
    "trend_data": {...}
  }
}
```

#### POST /api/v1/analyze/article
Analyze specific article by ID. Checks local storage first, then falls back to API.

**Request:**
```json
{
  "article_id": "atlantic_12345",
  "options": {...}
}
```

#### POST /api/v1/analyze/local-article
Analyze an article from local JSON storage (./data/articles/{article_id}.json).

**Request:**
```json
{
  "article_id": "atlantic_12345",
  "options": {...}
}
```

#### POST /api/v1/analyze/article-data
Analyze article data directly without storing it.

**Request:**
```json
{
  "article_data": { ... },
  "options": {...}
}
```

#### GET /api/v1/proactive/suggestions
Get current proactive suggestions.

**Response:**
```json
{
  "success": true,
  "data": {
    "generated_at": "2026-01-31T12:00:00Z",
    "threads": [
      {
        "thread_id": "thread_789",
        "trigger": "trending_topic",
        "trend_score": 85,
        "blocks": [...]
      }
    ]
  }
}
```

#### POST /api/v1/feedback
Submit feedback on a thread.

**Request:**
```json
{
  "thread_id": "thread_456",
  "helpful": true,
  "context": "Working on climate story",
  "query_id": "query_123"
}
```

#### GET /api/v1/articles
List all articles stored in local JSON storage.

**Response:**
```json
{
  "articles": ["article_1", "article_2", "article_3"],
  "total": 3
}
```

#### GET /api/v1/articles/{article_id}
Get a specific article from local storage.

#### POST /api/v1/articles/upload-json
Upload article data as JSON payload to local storage.

**Request:**
```json
{
  "article_id": "my_article",
  "data": { ...article_json... }
}
```

#### DELETE /api/v1/articles/{article_id}
Delete an article from local storage.

### Configuration

See detailed specs:
- [Environment Configuration](environment-config.md) - Multi-directory .env loading, DEBUG logging
- [Infactory Integration](infactory-integration.md) - API client with comprehensive logging

**Environment Variables:**
```bash
# API Keys
INFACTORY_API_KEY=ak_dVKy50Pi0X-7gcOFkey_56yIrKvNt3X0__QjzRN65-k
INFACTORY_API_URL=https://atlantichack-api.infactory.ai

# Database
DATABASE_URL=sqlite:///./data/story_threads.db

# Google Trends
TRENDS_GEO=US
TRENDS_TIMEFRAME=now 7-d

# Analysis
DEFAULT_THRESHOLD=0.10
MAX_RESULTS_PER_QUERY=10
RERANK_ENABLED=true
CACHE_TTL_SECONDS=3600

# Proactive Feed
PROACTIVE_ENABLED=true
PROACTIVE_SCAN_INTERVAL_HOURS=24
PROACTIVE_BATCH_SIZE=5
MIN_TREND_VELOCITY=50
```

**Configuration Features:**
- Automatic `.env` discovery from project root, current directory, or file-relative paths
- Environment variable override support
- DEBUG logging enabled by default for development
- Settings cache with reload capability

## Frontend Design (Next.js)

### Project Structure

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout
│   ├── page.tsx                # Main interface
│   ├──
│   ├── components/
│   │   ├── blocks/             # Block Kit renderers
│   │   │   ├── BlockRenderer.tsx
│   │   │   ├── SectionBlock.tsx
│   │   │   ├── HeaderBlock.tsx
│   │   │   ├── ContextBlock.tsx
│   │   │   ├── ActionsBlock.tsx
│   │   │   ├── DividerBlock.tsx
│   │   │   └── TimelineBlock.tsx
│   │   │
│   │   ├── query/
│   │   │   ├── TextInput.tsx      # Paste content
│   │   │   ├── ArticleInput.tsx   # Enter article ID
│   │   │   └── QueryOptions.tsx   # Thresholds, filters
│   │   │
│   │   ├── results/
│   │   │   ├── ThreadCard.tsx     # Single thread display
│   │   │   ├── ThreadList.tsx     # List of threads
│   │   │   ├── Timeline.tsx       # Timeline visualization
│   │   │   ├── ArticlePreview.tsx # Article card
│   │   │   └── FeedbackButtons.tsx # 👍/👎
│   │   │
│   │   └── proactive/
│   │       ├── ProactivePanel.tsx
│   │       └── TriggerButton.tsx
│   │
│   ├── lib/
│   │   ├── api.ts              # Backend API client
│   │   ├── blocks.ts           # Block Kit types
│   │   └── utils.ts
│   │
│   └── types/
│       ├── api.ts              # API response types
│       └── blocks.ts           # Block Kit TypeScript types
│
├── components/ui/              # shadcn/ui components
├── public/
├── next.config.js
├── tailwind.config.ts
└── package.json
```

### Block Kit Renderer

The key frontend component converts Block Kit JSON to React:

```typescript
// components/blocks/BlockRenderer.tsx
import { Block } from '@/app/types/blocks';
import { SectionBlock } from './SectionBlock';
import { HeaderBlock } from './HeaderBlock';
// ... other block components

interface BlockRendererProps {
  blocks: Block[];
  onAction?: (actionId: string, value: string) => void;
}

export function BlockRenderer({ blocks, onAction }: BlockRendererProps) {
  return (
    <div className="space-y-2">
      {blocks.map((block, index) => (
        <BlockComponent
          key={index}
          block={block}
          onAction={onAction}
        />
      ))}
    </div>
  );
}

function BlockComponent({ block, onAction }: { block: Block, onAction?: Function }) {
  switch (block.type) {
    case 'header':
      return <HeaderBlock block={block} />;
    case 'section':
      return <SectionBlock block={block} onAction={onAction} />;
    case 'context':
      return <ContextBlock block={block} />;
    case 'actions':
      return <ActionsBlock block={block} onAction={onAction} />;
    case 'divider':
      return <DividerBlock />;
    case 'timeline':  // Custom extension
      return <TimelineBlock block={block} />;
    default:
      return <div>Unknown block type: {block.type}</div>;
  }
}
```

### Main Interface Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Story Thread Surfacing System                    [Logo]        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  🔍 INPUT                                               │   │
│  │                                                          │   │
│  │  [Text] [Article ID]                              [⚙️]  │   │
│  │                                                          │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │ Paste article content or draft here...          │    │   │
│  │  │                                                  │    │   │
│  │  │                                                  │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  │                                                          │   │
│  │  [Find Connections]                               [Scan Proactive]
│   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  📊 RESULTS                                             │   │
│  │                                                          │   │
│  │  ┌───────────────────────────────────────────────────┐  │   │
│  │  │ 🎯 Story Thread: Climate Policy Evolution         │  │   │
│  │  │ ─────────────────────────────────────────────────  │  │   │
│  │  │ Type: Evergreen | Relevance: 87% | Articles: 12   │  │   │
│  │  │                                                    │  │   │
│  │  │ Timeline: 2019 ──●── 2021 ──●── 2023 ──●── 2024  │  │   │
│  │  │                                                    │  │   │
│  │  │ 📰 The Carbon Tax Debate Resurfaces (2023)       │  │   │
│  │  │    Jane Doe | Relevance: 94%                      │  │   │
│  │  │    "The recurring debate over carbon pricing..."  │  │   │
│  │  │    [View] [Add to Thread]                         │  │   │
│  │  │                                                    │  │   │
│  │  │ 👍 Was this helpful? [Yes] [No] [Save Thread]    │  │   │
│  │  └───────────────────────────────────────────────────┘  │   │
│  │                                                          │   │
│  │  [Previous] [Next]                              1 of 3  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### API Client

```typescript
// lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function analyzeText(
  text: string,
  options: AnalysisOptions
): Promise<AnalysisResponse> {
  const res = await fetch(`${API_BASE}/api/v1/analyze/text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, options }),
  });
  return res.json();
}

export async function getProactiveSuggestions(): Promise<ProactiveResponse> {
  const res = await fetch(`${API_BASE}/api/v1/proactive/suggestions`);
  return res.json();
}

export async function submitFeedback(
  threadId: string,
  helpful: boolean,
  context?: string
): Promise<void> {
  await fetch(`${API_BASE}/api/v1/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ thread_id: threadId, helpful, context }),
  });
}
```

## Block Kit Types

TypeScript definitions for Slack Block Kit:

```typescript
// types/blocks.ts

export type BlockType = 
  | 'header' 
  | 'section' 
  | 'context' 
  | 'actions' 
  | 'divider'
  | 'image'
  | 'timeline';  // Custom extension

export interface TextObject {
  type: 'plain_text' | 'mrkdwn';
  text: string;
  emoji?: boolean;
}

export interface HeaderBlock {
  type: 'header';
  text: TextObject;
}

export interface SectionBlock {
  type: 'section';
  text?: TextObject;
  fields?: TextObject[];
  accessory?: ButtonElement | ImageElement;
}

export interface ContextBlock {
  type: 'context';
  elements: (TextObject | ImageElement)[];
}

export interface ActionsBlock {
  type: 'actions';
  elements: ButtonElement[];
}

export interface ButtonElement {
  type: 'button';
  text: TextObject;
  action_id?: string;
  value?: string;
  style?: 'primary' | 'danger';
}

export interface ImageElement {
  type: 'image';
  image_url: string;
  alt_text: string;
}

export interface DividerBlock {
  type: 'divider';
}

// Custom: Timeline visualization
export interface TimelineBlock {
  type: 'timeline';
  events: TimelineEvent[];
}

export interface TimelineEvent {
  year: number;
  title: string;
  article_id: string;
}

export type Block = 
  | HeaderBlock 
  | SectionBlock 
  | ContextBlock 
  | ActionsBlock 
  | DividerBlock
  | ImageElement
  | TimelineBlock;
```

## Development Workflow

### Running Locally

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev  # Runs on localhost:3000
```

### Future Slack Integration

When ready to add Slack:

1. **Create new service** in `backend/app/integrations/slack.py`
2. **Add Bolt app** in `backend/app/slack_app.py`
3. **Reuse services**: `AnalyzerService`, `BlockFormatter` work unchanged
4. **Route events**: Map Slack events to existing API logic
5. **Deploy separately**: Slack bot can be separate service calling same backend

```python
# Future: Slack integration (separate service or same)
from slack_bolt import App
from app.services.analyzer import AnalyzerService

app = App(token=os.environ["SLACK_BOT_TOKEN"])

@app.message()
def handle_message(message, say):
    # Reuse the same service
    result = await analyzer.analyze_text(message['text'])
    # Blocks work natively in Slack
    say(blocks=result.blocks)
```

## Files

- Backend code: `backend/`
- Frontend code: `frontend/`
- Database: `backend/data/story_threads.db`
- Configuration: `.env`, `backend/app/config.py`

## Success Criteria

### Completed ✓
- [x] Backend API framework with FastAPI
- [x] Infactory API integration with search functionality
- [x] Comprehensive request/response logging (DEBUG mode)
- [x] Environment configuration with multi-directory .env support
- [x] Analyzer service calling Infactory on text analysis
- [x] Health check and basic API endpoints

### In Progress 🔄
- [ ] Article ID lookup via Infactory

### Completed ✓
- [x] Backend API framework with FastAPI
- [x] Infactory API integration with search functionality
- [x] Comprehensive request/response logging (DEBUG mode)
- [x] Environment configuration with multi-directory .env support
- [x] Analyzer service calling Infactory on text analysis
- [x] Health check and basic API endpoints
- [x] Text analysis end-to-end (Infactory connected, result processing working)
- [x] Block Kit formatted responses with full formatting
- [x] Thread clustering and classification
- [x] Article reference extraction from search results

### Pending ⏳
- [ ] Frontend Block Kit renderer
- [ ] Proactive feed generation
- [ ] Feedback collection endpoints
- [ ] Timeline visualization
- [ ] Thread type classification (evergreen/event/novel)
- [ ] Relevance scoring display
- [ ] Google Trends correlation

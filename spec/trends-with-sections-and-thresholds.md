# Technical Specification: Trends with Sections and Threshold System

## Overview

This specification extends the Google Trends integration to find stories organized by Atlantic sections (Politics, Culture, Technology, etc.) and introduces a comprehensive threshold system with per-story scores and overall message confidence scoring. This enables journalists to understand not just which stories match trends, but how confident the system is in those matches and from which editorial sections those stories originate.

## Architecture

### High-Level Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Trends Watch   │────▶│  Section-Aware   │────▶│  Confidence     │
│  Service        │     │  Search          │     │  Calculator     │
│                 │     │  (group_by=      │     │                 │
│ • Fetch trends  │     │  section)        │     │ • Story scores  │
│ • Score filter  │     │                  │     │ • Confidence    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │                       │
         │                       ▼                       ▼
         │              ┌──────────────────┐     ┌─────────────────┐
         │              │  Results by      │────▶│  Block          │
         │              │  Section         │     │  Formatter      │
         │              │                  │     │                 │
         │              │ • Politics: 3    │     │ • Group by      │
         │              │ • Culture: 2     │     │   section       │
         │              │ • Tech: 1        │     │ • Show scores   │
         │              │                  │     │ • Confidence    │
         │              └──────────────────┘     │   badge         │
         │                       │               └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Enhanced Block Output                         │
├─────────────────────────────────────────────────────────────────┤
│ 🔥 Trending: Climate Policy (Confidence: 87%)                   │
│ Interest: 85/100 | Growth: +45% | Category: Rising              │
│ ────────────────────────────────────────────────────────────────│
│ 📰 SECTIONS WITH MATCHES:                                       │
│                                                                 │
│ 🏛️ POLITICS (3 articles, avg score: 0.82)                       │
│ 1. "Carbon Tax Debate" - Relevance: 94% | Score: 0.85          │
│ 2. "Biden Climate Plan" - Relevance: 89% | Score: 0.80          │
│ 3. "Green New Deal History" - Relevance: 87% | Score: 0.82      │
│                                                                 │
│ 🎭 CULTURE (2 articles, avg score: 0.71)                        │
│ 4. "Climate in Film" - Relevance: 76% | Score: 0.71            │
│ 5. "Eco-Anxiety" - Relevance: 72% | Score: 0.71                │
│                                                                 │
│ ⚡ TECHNOLOGY (1 article, score: 0.65)                          │
│ 6. "Carbon Capture Tech" - Relevance: 81% | Score: 0.65        │
│                                                                 │
│ ────────────────────────────────────────────────────────────────│
│ Overall confidence factors:                                     │
│ • 6 articles across 3 sections (diversity score: 0.9)          │
│ • Average story score: 0.76                                     │
│ • Trend strength: 85/100                                        │
└─────────────────────────────────────────────────────────────────┘
```

## Scoring System

### Per-Story Score

Each matched article receives a composite score based on:

```
story_score = (trend_score / 100) * infactory_relevance_score * section_weight

Where:
- trend_score: 0-100 from Google Trends (normalized to 0.0-1.0)
- infactory_relevance_score: 0.0-1.0 from Infactory search
- section_weight: Optional weight for priority sections (default: 1.0)
```

### Overall Confidence Score

The overall confidence for a trend-message is calculated as:

```
confidence = base_confidence * diversity_multiplier * velocity_multiplier * threshold_passed

Where:
- base_confidence = average(story_scores) * sqrt(article_count / 10)
  (more articles increase confidence, with diminishing returns)
  
- diversity_multiplier = 1.0 + (unique_sections / 10)
  (articles across more sections = higher confidence)
  
- velocity_multiplier = 1.0 + (trend_velocity / 200) for rising trends
  (rising trends get slight confidence boost)
  
- threshold_passed = 0 if below min thresholds, 1.0 otherwise
```

### Confidence Levels

| Confidence | Badge | Description |
|------------|-------|-------------|
| 90-100% | 🔥 Very High | Strong match, highly actionable |
| 75-89% | ✅ High | Good match, recommended |
| 50-74% | ⚠️ Medium | Moderate match, review suggested |
| 25-49% | ❓ Low | Weak match, may not be relevant |
| 0-24% | ❌ Very Low | Insufficient data, not recommended |

## Configuration

### Threshold Settings

```bash
# Story-level thresholds
MIN_STORY_SCORE=0.30                    # Minimum score for individual stories
MIN_ARTICLES_PER_SECTION=1              # Min articles needed per section
MIN_SECTIONS_WITH_MATCHES=1             # Min sections that must have matches

# Message-level thresholds  
MIN_OVERALL_CONFIDENCE=0.50             # Minimum overall confidence to show message
MIN_TOTAL_ARTICLES=3                    # Minimum total articles across all sections
MAX_SECTIONS_TO_SHOW=5                  # Maximum sections to display

# Feature flags
ENABLE_SECTION_GROUPING=true            # Enable section-based grouping
ENABLE_CONFIDENCE_SCORING=true          # Enable confidence calculation
SHOW_EMPTY_SECTIONS=false               # Show sections with 0 matches
```

## Data Models

### Enhanced Schemas

```python
class ArticleReference(BaseModel):
    article_id: str
    title: str
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    url: Optional[str] = None
    excerpt: Optional[str] = None
    relevance_score: float              # Infactory score
    story_score: float                  # Composite score (trend * infactory)
    section: Optional[str] = None       # Atlantic section (Politics, Culture, etc.)


class SectionGroup(BaseModel):
    """Articles grouped by section."""
    section_name: str
    section_emoji: str                  # Emoji for section (🏛️, 🎭, ⚡)
    articles: List[ArticleReference]
    article_count: int
    average_score: float
    confidence_contribution: float      # How much this section contributes


class ConfidenceFactors(BaseModel):
    """Breakdown of confidence calculation."""
    base_confidence: float              # Average of story scores
    article_count_bonus: float          # Bonus for having more articles
    diversity_multiplier: float         # Bonus for section diversity
    velocity_multiplier: float          # Bonus for rising trends
    threshold_penalty: float            # Penalty if below thresholds
    final_confidence: float             # Final calculated confidence


class TrendMessageResult(BaseModel):
    """Complete result for a trend-surfaced message."""
    trend_keyword: str
    trend_score: int
    trend_category: str
    trend_velocity: Optional[float]
    overall_confidence: float           # 0.0-1.0
    confidence_level: str               # 'very_high', 'high', 'medium', 'low', 'very_low'
    confidence_factors: ConfidenceFactors
    section_groups: List[SectionGroup]
    total_articles: int
    sections_with_matches: int
    blocks: List[Block]                 # Block Kit formatted blocks
    threshold_met: bool                 # Whether min thresholds were met
```

### Database Schema Additions

```sql
-- Add section tracking to trend_article_matches
ALTER TABLE trend_article_matches ADD COLUMN section VARCHAR(50);
ALTER TABLE trend_article_matches ADD COLUMN story_score FLOAT NOT NULL DEFAULT 0.0;

-- Add confidence tracking to proactive_feed_queue
ALTER TABLE proactive_feed_queue ADD COLUMN overall_confidence FLOAT;
ALTER TABLE proactive_feed_queue ADD COLUMN confidence_level VARCHAR(20);
ALTER TABLE proactive_feed_queue ADD COLUMN sections_involved INTEGER;
ALTER TABLE proactive_feed_queue ADD COLUMN total_articles INTEGER;
```

## API Changes

### Enhanced Demo Trigger Response

```json
{
  "success": true,
  "message": "✅ Found 25 trends, created 3 high-confidence messages",
  "trends_found": 25,
  "messages_created": 3,
  "messages": [
    {
      "trend_keyword": "Climate Policy",
      "trend_score": 85,
      "trend_category": "rising",
      "overall_confidence": 0.87,
      "confidence_level": "very_high",
      "confidence_factors": {
        "base_confidence": 0.76,
        "article_count_bonus": 0.08,
        "diversity_multiplier": 1.09,
        "velocity_multiplier": 1.05,
        "final_confidence": 0.87
      },
      "total_articles": 6,
      "sections_with_matches": 3,
      "sections": [
        {
          "section_name": "Politics",
          "section_emoji": "🏛️",
          "article_count": 3,
          "average_score": 0.82,
          "articles": [...]
        },
        {
          "section_name": "Culture", 
          "section_emoji": "🎭",
          "article_count": 2,
          "average_score": 0.71,
          "articles": [...]
        },
        {
          "section_name": "Technology",
          "section_emoji": "⚡", 
          "article_count": 1,
          "average_score": 0.65,
          "articles": [...]
        }
      ],
      "threshold_met": true,
      "blocks": [...]
    }
  ]
}
```

### New Endpoint: GET /api/v1/trends/sections

Get available Atlantic sections and their match statistics.

```json
{
  "success": true,
  "sections": [
    {"name": "Politics", "emoji": "🏛️", "total_matches_24h": 12},
    {"name": "Culture", "emoji": "🎭", "total_matches_24h": 8},
    {"name": "Technology", "emoji": "⚡", "total_matches_24h": 5},
    {"name": "Business", "emoji": "💼", "total_matches_24h": 3},
    {"name": "Science", "emoji": "🔬", "total_matches_24h": 2}
  ]
}
```

## Block Kit Output Format

### Header with Confidence Badge

```json
{
  "type": "header",
  "text": {
    "type": "plain_text",
    "text": "🔥 Trending: Climate Policy (87% confidence)",
    "emoji": true
  }
}
```

### Confidence Context Block

```json
{
  "type": "context",
  "elements": [
    {
      "type": "mrkdwn",
      "text": "*Confidence:* 🔥 Very High (87%) | *Articles:* 6 across 3 sections"
    }
  ]
}
```

### Section Header

```json
{
  "type": "section",
  "text": {
    "type": "mrkdwn",
    "text": "🏛️ *POLITICS* (3 articles, avg: 82%)"
  }
}
```

### Article with Story Score

```json
{
  "type": "section",
  "text": {
    "type": "mrkdwn",
    "text": "*1. The Carbon Tax Debate Resurfaces* (2023)\nRelevance: 94% | Story Score: 0.85 | 🏛️ Politics\n>The recurring debate over carbon pricing..."
  },
  "accessory": {
    "type": "button",
    "text": {"type": "plain_text", "text": "View"},
    "value": "article_456",
    "action_id": "view_article"
  }
}
```

### Confidence Breakdown (Collapsible/Context)

```json
{
  "type": "context",
  "elements": [
    {
      "type": "mrkdwn",
      "text": "Confidence: Base 76% × Diversity 1.09 × Velocity 1.05 = 87%"
    }
  ]
}
```

## Implementation Phases

### Phase 1: Schema Updates
- Update `ArticleReference` with `story_score` and `section`
- Create `SectionGroup`, `ConfidenceFactors`, and `TrendMessageResult` schemas
- Add threshold configuration to settings

### Phase 2: Search Enhancement
- Modify `TrendsWatchService._find_articles_for_trend()` to search with `group_by=section`
- Parse section data from Infactory results
- Calculate per-story scores

### Phase 3: Confidence Calculation
- Implement `ConfidenceCalculator` service
- Calculate overall confidence with all factors
- Determine confidence levels and badges

### Phase 4: Block Formatting
- Update `BlockFormatter` to group by section
- Add confidence badges and context
- Include section emojis and statistics

### Phase 5: Database Migration
- Add section and confidence columns to existing tables
- Update queue storage to persist confidence data

### Phase 6: API Updates
- Update response models to include section and confidence data
- Add sections endpoint
- Update demo trigger with enhanced response

## Success Metrics

- **Accuracy**: Confidence scores correlate with user helpfulness ratings
- **Coverage**: % of trends with matches across multiple sections
- **Actionability**: Journalists can quickly identify which sections have relevant content
- **Threshold Effectiveness**: Messages below 50% confidence are rarely marked helpful

## Future Enhancements

- **Historical Confidence Tracking**: Track confidence scores over time for trend analysis
- **Section Prioritization**: Allow journalists to weight certain sections higher
- **Cross-Section Stories**: Identify stories that appear in multiple sections (high diversity)
- **Confidence Learning**: ML model to improve confidence scoring based on feedback

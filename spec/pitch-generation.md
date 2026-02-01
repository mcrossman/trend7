# Technical Specification: Story Pitch Generation

## Overview

This feature enables journalists to generate story pitches using the Infactory answer API based on trend-surfaced articles. By analyzing historical Atlantic coverage of trending topics, the system generates compelling pitch ideas with historical context, suggested angles, and source material.

## Architecture

### High-Level Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Trend Results  │────▶│  Pitch Generator │────▶│  Infactory     │
│  (with sections │     │                  │     │  Answer API    │
│   & confidence) │     │ • Build query   │     │                  │
│                 │     │ • Call API      │     │ • Retrieve      │
│ • Trend keyword │     │ • Structure     │     │   history       │
│ • Section groups│     │   response      │     │ • Suggest       │
│ • Source articles│    │                  │     │   angles        │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │
                                ▼
                    ┌─────────────────────┐
                    │    Pitch Output     │
                    ├─────────────────────┤
                    │ • Headline ideas    │
                    │ • Lead angle        │
                    │ • Historical context│
                    │ • Why now           │
                    │ • Source articles   │
                    │ • Follow-up Qs      │
                    └─────────────────────┘
```

## Components

### 1. Infactory Answer API Integration

**Endpoint:** `POST /v1/answer`

**Purpose:** Answer questions based on retrieved archive content with suggested follow-up questions.

**Request Format:**
```json
{
  "query": "What are the key historical story angles for...",
  "retrieval": {
    "top_k": 15,
    "filters": {
      "sections": ["politics", "culture"],
      "authors": [],
      "topics": [],
      "date_from": "2015-01-01",
      "date_to": "2024-12-31"
    }
  }
}
```

**Response Format:**
```json
{
  "answer": "Based on our coverage...",
  "citations": [...],
  "follow_up_questions": [...]
}
```

### 2. PitchGenerator Service

**File:** `backend/app/services/pitch_generator.py`

**Responsibilities:**
- Build contextual queries from trend + article information
- Call the Infactory answer API
- Structure pitch responses with:
  - Headline suggestions
  - Lead angle/hook
  - Historical context
  - "Why now" justification
  - Source articles
  - Follow-up questions

**Key Methods:**

```python
generate_pitch_from_trend(
    trend_keyword: str,
    section_groups: List[SectionGroup],
    overall_confidence: float,
    trend_category: str
) -> Dict[str, Any]

# Generates comprehensive pitch with full context


generate_quick_pitch(
    trend_keyword: str,
    articles: List[ArticleReference]
) -> Dict[str, Any]

# Simplified version for quick demos
```

**Query Building Strategy:**

The pitch generator builds queries that ask for:
1. Key historical story angles
2. Previous coverage context
3. Timely contexts to explore
4. Connections to past articles

Example query:
```
"What are the key historical story angles for a new article about 
'Climate Policy'? Consider our previous coverage including: 
1) "The Carbon Tax Debate Resurfaces" (2023) from Politics; 
2) "Green New Deal: A Historical Perspective" (2019) from Politics; 
3) "Climate Change in Popular Culture" (2021) from Culture.

What unique historical angles, connections to past coverage, or 
timely contexts should a journalist explore?"
```

### 3. API Endpoints

**File:** `backend/app/api/v1/pitches.py`

#### POST /api/v1/pitches/generate

Generate a comprehensive pitch from a trend.

**Request:**
```json
{
  "trend_keyword": "Climate Policy",
  "section_groups": [
    {
      "section_name": "Politics",
      "section_emoji": "🏛️",
      "articles": [...],
      "article_count": 3,
      "average_score": 0.82
    }
  ],
  "overall_confidence": 0.87,
  "trend_category": "rising",
  "quick_mode": false
}
```

**Response:**
```json
{
  "success": true,
  "pitch": {
    "headline_suggestions": [
      "The Return of Climate Policy: What History Teaches Us",
      "From Kyoto to Paris: The Evolution of Climate Politics"
    ],
    "lead_angle": "As climate policy resurfaces in the national conversation...",
    "historical_context": "Based on our coverage of carbon pricing debates since 2015...",
    "why_now": "Climate Policy is currently trending with rising interest",
    "confidence": 0.87,
    "source_articles": [
      {
        "id": "article_123",
        "title": "The Carbon Tax Debate Resurfaces",
        "author": "Jane Doe",
        "year": 2023,
        "section": "Politics",
        "relevance_score": 0.94,
        "story_score": 0.85
      }
    ],
    "citations": [...],
    "follow_up_questions": [
      "How has public opinion on carbon pricing shifted since 2019?",
      "What role do state policies play in the federal debate?"
    ],
    "sections_covered": ["Politics", "Culture", "Technology"],
    "generated_at": "2026-01-31T15:00:00Z"
  }
}
```

#### POST /api/v1/pitches/generate-from-queue

Generate a pitch from an existing queue item.

**Request:**
```json
{
  "queue_id": 123
}
```

This retrieves the trend and articles from the proactive queue and generates a pitch.

#### POST /api/v1/pitches/quick

Quick pitch generation for demos.

**Request:**
```json
{
  "trend_keyword": "Climate Policy",
  "max_articles": 5
}
```

Searches for articles on the fly and generates a basic pitch.

## Pitch Structure

### Generated Pitch Format

Each pitch includes:

**1. Headline Suggestions (3)**
- Extracted from answer text
- First 5 sentences analyzed for headline-worthiness (30-100 chars)

**2. Lead Angle**
- First substantial sentence from answer (>50 chars)
- Sets up the story hook

**3. Historical Context**
- Full answer text from Infactory
- Citations to specific archive articles
- Follow-up questions for deeper exploration

**4. Why Now**
- Trend context: "Climate Policy is currently trending with rising interest"
- Justification for timeliness

**5. Source Articles**
- Article metadata from trend results
- Relevance and story scores
- Section information

**6. Follow-up Questions**
- Suggested by Infactory answer API
- For deeper exploration

**7. Metadata**
- Confidence score
- Sections covered
- Generation timestamp

## Integration with Trend System

### Workflow

1. **Trend Discovery**
   - TrendsWatchService identifies trending topics
   - Finds related Atlantic articles
   - Groups by section
   - Calculates confidence

2. **Pitch Generation**
   - PitchGenerator receives trend + articles
   - Builds contextual query
   - Calls Infactory answer API
   - Structures response

3. **Usage**
   - Journalist reviews pitch
   - Can generate from queue item
   - Or generate on-demand from any trend keyword

### Example Workflow

```
1. System identifies: "Climate Policy" is trending (confidence: 87%)
   - 6 articles found
   - Sections: Politics (3), Culture (2), Technology (1)

2. Journalist clicks "Generate Pitch"

3. System calls Infactory answer API:
   Query: "What are the key historical story angles for 'Climate Policy' 
   based on our previous coverage?"

4. Infactory returns historical analysis with citations

5. PitchGenerator structures response:
   - Headlines: "The Carbon Tax Debate Returns"
   - Lead: "As climate policy resurfaces..."
   - Context: Historical analysis
   - Sources: 6 articles with scores
   - Follow-ups: 3 suggested questions

6. Journalist receives complete pitch package
```

## Configuration

**No additional environment variables required.**

The pitch generator uses existing configuration:
- `infactory_api_key` - For answer API calls
- `infactory_api_url` - API endpoint

## API Usage

### Example: Generate Pitch from Trend

```bash
curl -X POST http://localhost:8000/api/v1/pitches/generate \
  -H "Content-Type: application/json" \
  -d '{
    "trend_keyword": "Climate Policy",
    "overall_confidence": 0.87,
    "trend_category": "rising",
    "section_groups": [
      {
        "section_name": "Politics",
        "section_emoji": "🏛️",
        "articles": [
          {
            "article_id": "123",
            "title": "The Carbon Tax Debate Resurfaces",
            "relevance_score": 0.94,
            "story_score": 0.85,
            "section": "Politics"
          }
        ],
        "article_count": 3,
        "average_score": 0.82
      }
    ]
  }'
```

### Example: Quick Pitch

```bash
curl -X POST http://localhost:8000/api/v1/pitches/quick \
  -H "Content-Type: application/json" \
  -d '{
    "trend_keyword": "Artificial Intelligence",
    "max_articles": 5
  }'
```

## Files

- **Code:** `backend/app/integrations/infactory.py` (answer method)
- **Code:** `backend/app/services/pitch_generator.py`
- **Code:** `backend/app/api/v1/pitches.py`
- **Spec:** This document

## Future Enhancements

- **Template-based pitches:** Pre-defined templates for different story types (breaking news, evergreen, analysis)
- **Author-aware generation:** Consider specific author styles and beats
- **Multi-pitch generation:** Generate 3-5 different angle options
- **Feedback loop:** Track which pitches get developed into stories
- **Pitch scoring:** Score generated pitches based on historical success
- **Export formats:** Export pitches to Google Docs, Notion, etc.

## Dependencies

- Infactory Answer API (`/v1/answer`)
- Existing trend and section grouping system
- No additional Python packages required

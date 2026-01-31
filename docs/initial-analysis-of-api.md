# API surface analysis for product

Based on the OpenAPI specification, here's a comprehensive analysis and recommended architecture for your internal story-surfacing system.

## API Capabilities Summary

The Atlantic Archive API provides **three search modes** optimized for different discovery scenarios [^1]:
- **Semantic search**: Vector-based similarity for conceptual exploration (finding related topics, themes)
- **Keyword search**: Full-text PostgreSQL search for specific names, quotes, or exact phrases
- **Hybrid search** (default): Combines both using Reciprocal Rank Fusion (RRF) for balanced results

**Key features for journalistic research**:
- **Re-ranking support**: Cross-encoder models (Cohere/Jina) for improved relevance at ~100-300ms latency cost [^1]
- **Hierarchical grouping**: Cluster results by topic, author, year, or section via `group_by` parameter [^1]
- **Deduplication**: Automatic article-level deduplication showing only the best-matching chunk per story [^1]
- **Date-bounded filtering**: Temporal constraints via `date_from` and `date_to` [^1]
- **AI summarization**: Generate summaries with citations or answer specific questions with suggested follow-ups [^1]

## Recommended System Architecture

### Core Components

**1. Search & Discovery Service**
- **Primary endpoint**: `POST /v1/search` with hybrid mode and reranking enabled for investigative queries
- **Reference caching**: Cache responses from `/v1/topics`, `/v1/authors`, and `/v1/sections` to populate UI filter dropdowns [^1]
- **Thread detection**: Use `group_by=topic` or `group_by=year` to surface thematic clusters journalists can explore

**2. Content Resolution Layer**
- **Metadata retrieval**: `GET /v1/articles/{article_id}` for preview cards [^1]
- **Full content access**: `GET /v1/articles/{article_id}/content` when journalists need to read complete articles [^1]
- **Chunk excerpts**: `GET /v1/chunks/{chunk_id}` for quick preview of specific passages [^1]

**3. AI Analysis Pipeline**
- **Quick briefing**: `POST /v1/summarize` with `StyleConfig` (bullets/short for speed, prose/medium for depth) to generate overviews of article clusters [^1]
- **Question-driven research**: `POST /v1/answer` when journalists have specific historical questions requiring synthesized answers [^1]

### Internal Journalist Client Features

**Workflow optimization**:
- **Saved searches**: Persist filter combinations (specific authors + date ranges + topics) for beat monitoring
- **Story threads**: Use the grouping functionality to present "related coverage" views
- **Temporal exploration**: Date filtering enables "this week in history" pattern discovery
- **Citation extraction**: AI summaries include chunk citations for fact-checking and attribution [^1]

**Authentication**: API keys via `x-api-key` header; implement key rotation since keys cannot be recovered after creation [^1]

## Integration Patterns

For **story thread identification**:
1. Journalist enters seed concept (person, event, or theme)
2. System queries with hybrid mode, reranking enabled, grouped by year
3. Present timeline view showing coverage evolution
4. Allow drill-down to specific articles via content endpoint

For **"evergreen" detection**:
1. Search recent news topics against full archive using semantic mode
2. Use summarization to identify historical parallels
3. Surface top 3-5 related historical articles with full content preview

## Technical Considerations

- **Latency trade-off**: Enable reranking (`rerank=true`) for investigative research where accuracy matters more than speed; disable for exploratory browsing [^1]
- **Rate limiting**: Implement request batching for bulk operations (chunk retrieval supports up to 200 IDs per call) [^1]
- **Content boundaries**: Note that chunk excerpts are capped at `MAX_EXCERPT_CHARS` and full content may be reconstructed from chunks if stored version unavailable [^1]

[^1]: [openapi](infactory-openapi.json) (100%)


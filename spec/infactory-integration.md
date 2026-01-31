# Infactory Integration Specification

## Overview

The Infactory client provides the primary interface to the Atlantic Archive API for searching historical Atlantic stories, retrieving article metadata, and fetching full article content. It supports hybrid, semantic, and keyword search modes with configurable parameters.

## Implementation

**Location**: `backend/app/integrations/infactory.py`

## Configuration

**Environment Variables**:
```bash
INFACTORY_API_KEY=ak_dVKy50Pi0X-7gcOFkey_56yIrKvNt3X0__QjzRN65-k
INFACTORY_API_URL=https://atlantichack-api.infactory.ai  # Default in config
```

**Base URL**: `https://atlantichack-api.infactory.ai`

**Search Endpoint**: `POST /v1/search`

## Client Features

### InfactoryClient Class

```python
class InfactoryClient:
    """
    Client for Atlantic Archive (Infactory) API.
    Does NOT fall back to local storage automatically.
    """
    
    def __init__(self):
        self.api_key = settings.infactory_api_key
        self.base_url = settings.infactory_api_url
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"x-api-key": self.api_key} if self.api_key else {},
            timeout=30.0,
        )
```

### Search Method

```python
async def search(
    self,
    query: str,
    mode: str = "hybrid",      # Options: "hybrid", "semantic", "keyword"
    rerank: bool = True,
    group_by: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]
```

**Parameters**:
- `query`: Search query string
- `mode`: Search algorithm mode
- `rerank`: Whether to apply reranking
- `group_by`: Optional grouping field
- `date_from`/`date_to`: Date range filters (ISO format)
- `limit`: Maximum number of results (default: 10)

**Request Payload**:
```json
{
  "query": "climate change policy",
  "mode": "hybrid",
  "rerank": true,
  "limit": 10
}
```

### Article Retrieval

```python
async def get_article(self, article_id: str) -> Dict[str, Any]
# GET /v1/articles/{article_id}

async def get_article_content(self, article_id: str) -> Dict[str, Any]
# GET /v1/articles/{article_id}/content

async def get_topics(self) -> List[str]
# GET /v1/topics
```

## Logging

The client includes comprehensive logging at both INFO and DEBUG levels:

### Initialization Logging
```
[INFACTORY] Client initialized - base_url: https://atlantichack-api.infactory.ai, api_key: YES
```

### Request Logging
```
[INFACTORY] REQUEST: POST https://atlantichack-api.infactory.ai/v1/search
[INFACTORY] REQUEST PAYLOAD: {'query': 'test', 'mode': 'hybrid', 'rerank': True, 'limit': 10}
```

### Response Logging
```
[INFACTORY] RESPONSE status: 200
[INFACTORY] Search returned 0 results for query: test
[INFACTORY] RESPONSE DATA: {"results": [], ...}
```

**Implementation**: Uses both `logging` module and direct `print()` to stderr via `debug_print()` helper to ensure logs appear regardless of logging configuration.

## Usage in Analyzer Service

The `AnalyzerService` calls Infactory during text analysis:

```python
async def analyze_text(self, text: str, options: Optional[AnalysisOptions] = None):
    options = options or AnalysisOptions()
    
    # Search archive via Infactory
    search_results = await self.infactory.search(
        query=text,
        limit=options.max_results
    )
    
    # TODO: Process results (extract topics, correlate trends, cluster threads)
    
    return AnalysisResult(
        query_id="query_text",
        threads=[],
        extracted_topics=[],
    )
```

## Error Handling

- Raises `httpx.HTTPError` on API failures
- Uses `response.raise_for_status()` to propagate HTTP errors
- Client initialization logs API key presence (without exposing key)

## Future Enhancements

- [ ] Implement topic extraction from search results
- [ ] Add result caching layer
- [ ] Support batch/multi-query search
- [ ] Add retry logic for transient failures
- [ ] Implement result filtering by content type

## Files

- Client code: `backend/app/integrations/infactory.py`
- Configuration: `backend/app/config.py`
- API credentials: `.env` (INFACTORY_API_KEY, INFACTORY_API_URL)

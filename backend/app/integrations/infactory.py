import httpx
import logging
import sys
from typing import Optional, List, Dict, Any

from app.config import get_settings, Settings

logger = logging.getLogger(__name__)

# Debug print helper that always works
def debug_print(msg: str):
    """Print to stderr immediately - bypasses logging config issues."""
    print(f"[INFACTORY] {msg}", file=sys.stderr, flush=True)


class InfactoryClient:
    """
    Client for Atlantic Archive (Infactory) API.
    Primary API client - does NOT fall back to local storage automatically.
    Local storage is used only when explicitly requested via local-article endpoints.
    """
    
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.infactory_api_key
        self.base_url = settings.infactory_api_url
        debug_print(f"Client initialized - base_url: {self.base_url}, api_key: {'YES' if self.api_key else 'NO'}")
        logger.info(f"InfactoryClient initialized - base_url: {self.base_url}, api_key present: {bool(self.api_key)}")
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"x-api-key": self.api_key} if self.api_key else {},
            timeout=30.0,
        )
    
    async def search(
        self,
        query: str,
        mode: str = "hybrid",
        rerank: bool = True,
        group_by: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search the archive using hybrid/semantic/keyword search.
        """
        payload = {
            "query": query,
            "mode": mode,
            "rerank": rerank,
            "limit": limit,
        }
        
        if group_by:
            payload["group_by"] = group_by
        if date_from:
            payload["date_from"] = date_from
        if date_to:
            payload["date_to"] = date_to
        
        url = f"{self.base_url}/v1/search"
        debug_print(f"REQUEST: POST {url}")
        debug_print(f"REQUEST PAYLOAD: {payload}")
        logger.info(f"Infactory REQUEST: POST {url}")
        logger.info(f"Infactory REQUEST PAYLOAD: {payload}")
        
        response = await self.client.post("/v1/search", json=payload)
        debug_print(f"RESPONSE status: {response.status_code}")
        logger.info(f"Infactory RESPONSE status: {response.status_code}")
        
        response.raise_for_status()
        data = response.json()
        results_count = len(data.get('results', []))
        debug_print(f"Search returned {results_count} results for query: {query}")
        debug_print(f"RESPONSE DATA: {data}")
        logger.info(f"Infactory search returned {results_count} results for query: {query}")
        logger.info(f"Infactory RESPONSE DATA: {data}")
        return data
    
    async def get_article(self, article_id: str) -> Dict[str, Any]:
        """
        Get article metadata from API.
        Raises HTTPError on failure.
        """
        debug_print(f"Getting article: {article_id}")
        response = await self.client.get(f"/v1/articles/{article_id}")
        debug_print(f"Article response status: {response.status_code}")
        response.raise_for_status()
        return response.json()
    
    async def get_article_content(self, article_id: str) -> Dict[str, Any]:
        """
        Get full article content from API.
        Raises HTTPError on failure.
        """
        response = await self.client.get(f"/v1/articles/{article_id}/content")
        response.raise_for_status()
        return response.json()
    
    async def get_topics(self) -> List[str]:
        """Get available topics."""
        response = await self.client.get("/v1/topics")
        response.raise_for_status()
        data = response.json()
        return data.get("topics", [])
    
    async def answer(
        self,
        query: str,
        top_k: int = 12,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Answer a question based on retrieved archive content.
        
        Uses the /v1/answer endpoint which is similar to summarize but includes
        suggested follow-up questions. Perfect for generating story pitches.
        
        Args:
            query: The question to answer (max 500 chars)
            top_k: Number of chunks to retrieve (1-20, default: 12)
            filters: Optional filters dict with:
                - topics: List[str]
                - authors: List[str]
                - sections: List[str]
                - date_from: str (YYYY-MM-DD)
                - date_to: str (YYYY-MM-DD)
        
        Returns:
            Dict with answer, citations, and follow-up suggestions
        """
        payload = {
            "query": query,
            "retrieval": {
                "top_k": top_k
            }
        }
        
        if filters:
            payload["retrieval"]["filters"] = filters
        
        url = f"{self.base_url}/v1/answer"
        debug_print(f"REQUEST: POST {url}")
        debug_print(f"REQUEST PAYLOAD: {payload}")
        logger.info(f"Infactory ANSWER REQUEST: POST {url}")
        logger.info(f"Infactory ANSWER PAYLOAD: {payload}")
        
        response = await self.client.post("/v1/answer", json=payload)
        debug_print(f"RESPONSE status: {response.status_code}")
        logger.info(f"Infactory ANSWER RESPONSE status: {response.status_code}")
        
        response.raise_for_status()
        data = response.json()
        debug_print(f"ANSWER RESPONSE DATA: {data}")
        logger.info(f"Infactory ANSWER RESPONSE DATA: {data}")
        return data
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

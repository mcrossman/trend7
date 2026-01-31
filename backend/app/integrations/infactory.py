import httpx
from typing import Optional, List, Dict, Any

from app.config import get_settings

settings = get_settings()


class InfactoryClient:
    """
    Client for Atlantic Archive (Infactory) API.
    """
    
    def __init__(self):
        self.api_key = settings.infactory_api_key
        self.base_url = settings.infactory_api_url
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
        
        response = await self.client.post("/v1/search", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def get_article(self, article_id: str) -> Dict[str, Any]:
        """Get article metadata."""
        response = await self.client.get(f"/v1/articles/{article_id}")
        response.raise_for_status()
        return response.json()
    
    async def get_article_content(self, article_id: str) -> Dict[str, Any]:
        """Get full article content."""
        response = await self.client.get(f"/v1/articles/{article_id}/content")
        response.raise_for_status()
        return response.json()
    
    async def get_topics(self) -> List[str]:
        """Get available topics."""
        response = await self.client.get("/v1/topics")
        response.raise_for_status()
        data = response.json()
        return data.get("topics", [])
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

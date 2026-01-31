from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.services.analyzer import AnalyzerService
from app.models.schemas import AnalysisOptions as AnalysisOptionsSchema

router = APIRouter()


class AnalysisOptions(BaseModel):
    max_results: int = 10
    include_trends: bool = True
    threshold: float = 0.10
    thread_types: List[str] = ["evergreen", "event_driven", "novel_concept"]


class TextAnalysisRequest(BaseModel):
    text: str
    options: Optional[AnalysisOptions] = None


class ArticleAnalysisRequest(BaseModel):
    article_id: str
    options: Optional[AnalysisOptions] = None


class LocalArticleAnalysisRequest(BaseModel):
    article_id: str
    options: Optional[AnalysisOptions] = None


class DirectArticleAnalysisRequest(BaseModel):
    article_data: Dict[str, Any]
    options: Optional[AnalysisOptions] = None


def _convert_options(options: Optional[AnalysisOptions]) -> AnalysisOptionsSchema:
    """Convert API AnalysisOptions to schema AnalysisOptions."""
    if options is None:
        return AnalysisOptionsSchema()
    return AnalysisOptionsSchema(
        max_results=options.max_results,
        include_trends=options.include_trends,
        threshold=options.threshold,
        thread_types=options.thread_types
    )


@router.post("/text")
async def analyze_text(request: TextAnalysisRequest):
    """
    Analyze pasted text content and return relevant story threads.
    
    If include_trends is True, will check if query topics match current Google Trends
    and include trend context in the response.
    """
    analyzer = AnalyzerService()
    options = _convert_options(request.options)
    
    # Use analyze_text_with_trends if trends are enabled
    if options.include_trends:
        result = await analyzer.analyze_text_with_trends(request.text, options)
    else:
        result = await analyzer.analyze_text(request.text, options)
    
    await analyzer.close()
    
    return {
        "success": True,
        "data": {
            "query_id": result.query_id,
            "threads": result.threads,
            "extracted_topics": result.extracted_topics,
            "trend_matches": result.trend_matches if hasattr(result, 'trend_matches') else [],
        },
    }


@router.post("/article")
async def analyze_article(request: ArticleAnalysisRequest):
    """
    Analyze specific article by ID and return relevant story threads.
    Uses the Infactory API only. Does NOT check local storage.
    Use /analyze/local-article for local storage access.
    
    If include_trends is True, will check if article topics match current Google Trends.
    """
    analyzer = AnalyzerService()
    options = _convert_options(request.options)
    
    # First get article content
    try:
        article_data = await analyzer.infactory.get_article_content(request.article_id)
    except Exception:
        article_data = await analyzer.infactory.get_article(request.article_id)
    
    content = article_data.get('content', '')
    if not content:
        content = article_data.get('metadata', {}).get('title', '')
    
    # Use analyze_text_with_trends if trends are enabled
    if options.include_trends:
        result = await analyzer.analyze_text_with_trends(content, options)
    else:
        result = await analyzer.analyze_text(content, options)
    
    await analyzer.close()
    
    return {
        "success": True,
        "data": {
            "query_id": result.query_id,
            "article_id": request.article_id,
            "threads": result.threads,
            "extracted_topics": result.extracted_topics,
            "trend_matches": result.trend_matches if hasattr(result, 'trend_matches') else [],
        },
    }


@router.post("/local-article")
async def analyze_local_article(request: LocalArticleAnalysisRequest):
    """
    Analyze an article from local JSON storage.
    This is useful when you have downloaded article data.
    
    The article must be stored in ./data/articles/{article_id}.json
    
    If include_trends is True, will check if article topics match current Google Trends.
    """
    analyzer = AnalyzerService()
    options = _convert_options(request.options)
    
    try:
        # Load article from local storage
        article_data = await analyzer._article_loader.load_article(request.article_id)
        if not article_data:
            raise ValueError(f"Article {request.article_id} not found in local storage")
        
        content = article_data.get('content', '')
        if not content:
            content = article_data.get('title', '')
        
        # Use analyze_text_with_trends if trends are enabled
        if options.include_trends:
            result = await analyzer.analyze_text_with_trends(content, options)
        else:
            result = await analyzer.analyze_text(content, options)
        
        await analyzer.close()
        
        return {
            "success": True,
            "data": {
                "query_id": result.query_id,
                "article_id": request.article_id,
                "source": "local",
                "threads": result.threads,
                "extracted_topics": result.extracted_topics,
                "trend_matches": result.trend_matches if hasattr(result, 'trend_matches') else [],
            },
        }
    except ValueError as e:
        await analyzer.close()
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/article-data")
async def analyze_article_data(request: DirectArticleAnalysisRequest):
    """
    Analyze article data directly without storing it.
    
    This is useful for one-off analysis of article JSON that you don't want to save.
    Pass the article data as a JSON object in the request body.
    
    If include_trends is True, will check if article topics match current Google Trends.
    """
    analyzer = AnalyzerService()
    options = _convert_options(request.options)
    
    # Extract content from article data
    content = request.article_data.get('content', '')
    if not content:
        content = request.article_data.get('title', '')
    
    # Use analyze_text_with_trends if trends are enabled
    if options.include_trends:
        result = await analyzer.analyze_text_with_trends(content, options)
    else:
        result = await analyzer.analyze_text(content, options)
    
    await analyzer.close()
    
    return {
        "success": True,
        "data": {
            "query_id": result.query_id,
            "threads": result.threads,
            "extracted_topics": result.extracted_topics,
            "trend_matches": result.trend_matches if hasattr(result, 'trend_matches') else [],
        },
    }

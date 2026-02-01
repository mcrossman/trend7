"""
API endpoints for generating story pitches from trend-surfaced articles.

Provides:
- POST /api/v1/pitches/generate - Generate a pitch from a trend
- POST /api/v1/pitches/generate-from-queue - Generate from queue item
- POST /api/v1/pitches/quick - Quick pitch generation (simplified)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.database import get_db, Trend, ProactiveFeedQueue, TrendArticleMatch
from app.models.schemas import SectionGroup, ArticleReference
from app.services.pitch_generator import PitchGenerator
from app.services.trends_watch_service import TrendsWatchService
from datetime import datetime, timedelta
import json

router = APIRouter()


# Request/Response Models

class GeneratePitchRequest(BaseModel):
    """Request to generate a pitch from a trend."""
    trend_keyword: str
    section_groups: Optional[List[Dict[str, Any]]] = None
    overall_confidence: Optional[float] = None
    trend_category: str = "rising"
    quick_mode: bool = False  # Use simplified generation


class PitchSourceArticle(BaseModel):
    """Source article in a pitch."""
    id: str
    title: str
    author: Optional[str] = None
    year: Optional[int] = None
    section: str
    relevance_score: float
    story_score: float


class PitchResponseData(BaseModel):
    """Pitch data structure."""
    headline_suggestions: List[str]
    lead_angle: str
    historical_context: str
    why_now: str
    confidence: float
    source_articles: List[PitchSourceArticle]
    citations: List[Dict[str, Any]]
    follow_up_questions: List[str]
    sections_covered: List[str]
    generated_at: str


class GeneratePitchResponse(BaseModel):
    """Response from pitch generation."""
    success: bool
    pitch: Optional[PitchResponseData] = None
    error: Optional[str] = None


class GenerateFromQueueRequest(BaseModel):
    """Request to generate pitch from queue item."""
    queue_id: int


class QuickPitchRequest(BaseModel):
    """Quick pitch generation request."""
    trend_keyword: str
    max_articles: int = 5


class GeneratePitchBlockRequest(BaseModel):
    """Request to generate a pitch formatted as Slack blocks."""
    trend_keyword: str
    queue_id: Optional[int] = None  # Optional: generate from existing queue item
    custom_prompt: Optional[str] = None  # Optional: override default prompt


class PitchBlockResponse(BaseModel):
    """Response with pitch formatted as Slack blocks."""
    success: bool
    blocks: List[Dict[str, Any]] = []
    pitch_text: str = ""
    follow_up_questions: List[str] = []
    trend_keyword: str = ""
    confidence: float = 0.0
    error: Optional[str] = None


# API Endpoints

@router.post("/generate", response_model=GeneratePitchResponse)
async def generate_pitch(
    request: GeneratePitchRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a story pitch based on a trending topic.
    
    Uses the Infactory answer API to generate pitch ideas by analyzing
    historical coverage of similar topics.
    
    - **trend_keyword**: The trending topic to base the pitch on
    - **section_groups**: Optional pre-computed section groups (from trend analysis)
    - **overall_confidence**: Confidence score from trend analysis
    - **trend_category**: Type of trend (rising, top, etc.)
    - **quick_mode**: If True, uses simplified generation (faster, less detailed)
    """
    try:
        generator = PitchGenerator()
        
        if request.quick_mode:
            # Quick mode - search for articles on the fly
            from app.integrations.infactory import InfactoryClient
            
            infactory = InfactoryClient()
            search_results = await infactory.search(
                query=request.trend_keyword,
                limit=5
            )
            
            # Convert search results to ArticleReference objects
            articles = []
            for result in search_results.get('results', []):
                metadata = result.get('metadata', {})
                articles.append(ArticleReference(
                    article_id=metadata.get('id', 'unknown'),
                    title=metadata.get('title', 'Untitled'),
                    author=metadata.get('author'),
                    published_date=None,
                    url=metadata.get('url'),
                    excerpt=result.get('chunk', {}).get('excerpt'),
                    relevance_score=result.get('score', 0.5),
                    story_score=result.get('score', 0.5),
                    section=metadata.get('section', 'general')
                ))
            
            result = await generator.generate_quick_pitch(
                trend_keyword=request.trend_keyword,
                articles=articles
            )
        else:
            # Full mode - requires section_groups
            if not request.section_groups:
                # If no section groups provided, try to find from database
                # Get recent matches for this trend
                trend = db.query(Trend).filter(
                    Trend.keyword == request.trend_keyword,
                    Trend.recorded_at > datetime.utcnow() - timedelta(hours=24)
                ).first()
                
                if trend:
                    matches = db.query(TrendArticleMatch).filter(
                        TrendArticleMatch.trend_id == trend.trend_id
                    ).all()
                    
                    # Group by section
                    section_dict = {}
                    for match in matches:
                        section = match.section or 'general'
                        if section not in section_dict:
                            section_dict[section] = []
                        section_dict[section].append(match)
                    
                    # Create section groups
                    request.section_groups = []
                    for section_name, matches in section_dict.items():
                        request.section_groups.append({
                            "section_name": section_name,
                            "section_emoji": "📰",
                            "articles": [
                                {
                                    "article_id": m.article_id,
                                    "title": "Article",  # Would need to fetch actual titles
                                    "relevance_score": m.infactory_score,
                                    "story_score": m.story_score,
                                    "section": section_name
                                }
                                for m in matches[:5]
                            ]
                        })
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="No section_groups provided and no recent trend found for keyword"
                    )
            
            # Convert dict to SectionGroup objects
            section_groups = [
                SectionGroup(**sg) for sg in request.section_groups
            ]
            
            result = await generator.generate_pitch_from_trend(
                trend_keyword=request.trend_keyword,
                section_groups=section_groups,
                overall_confidence=request.overall_confidence or 0.5,
                trend_category=request.trend_category
            )
        
        await generator.close()
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        pitch_data = result["pitch"]
        
        # Convert to response format
        return GeneratePitchResponse(
            success=True,
            pitch=PitchResponseData(
                headline_suggestions=pitch_data.get("headline_suggestions", []),
                lead_angle=pitch_data.get("lead_angle", ""),
                historical_context=pitch_data.get("historical_context", ""),
                why_now=pitch_data.get("why_now", ""),
                confidence=pitch_data.get("confidence", 0.0),
                source_articles=[
                    PitchSourceArticle(**art)
                    for art in pitch_data.get("source_articles", [])
                ],
                citations=pitch_data.get("citations", []),
                follow_up_questions=pitch_data.get("follow_up_questions", []),
                sections_covered=pitch_data.get("sections_covered", []),
                generated_at=pitch_data.get("generated_at", datetime.utcnow().isoformat())
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating pitch: {str(e)}")


@router.post("/generate-from-queue", response_model=GeneratePitchResponse)
async def generate_pitch_from_queue(
    request: GenerateFromQueueRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a pitch from a proactive queue item.
    
    Retrieves the trend and articles from the queue and generates
    a story pitch based on that context.
    """
    try:
        # Get queue item
        queue_item = db.query(ProactiveFeedQueue).filter(
            ProactiveFeedQueue.queue_id == request.queue_id
        ).first()
        
        if not queue_item:
            raise HTTPException(status_code=404, detail="Queue item not found")
        
        # Get trend info
        trend = db.query(Trend).filter(Trend.trend_id == queue_item.trend_id).first()
        if not trend:
            raise HTTPException(status_code=404, detail="Trend not found for queue item")
        
        # Get article matches
        matches = db.query(TrendArticleMatch).filter(
            TrendArticleMatch.trend_id == trend.trend_id,
            TrendArticleMatch.thread_id == queue_item.thread_id
        ).all()
        
        if not matches:
            raise HTTPException(status_code=404, detail="No articles found for this queue item")
        
        # Group by section
        section_dict = {}
        for match in matches:
            section = match.section or 'general'
            if section not in section_dict:
                section_dict[section] = []
            section_dict[section].append(match)
        
        # Create section groups
        section_groups = []
        from app.models.schemas import get_section_emoji
        
        for section_name, section_matches in section_dict.items():
            articles = []
            for m in section_matches:
                articles.append(ArticleReference(
                    article_id=m.article_id,
                    title="Article",  # Would fetch actual title from Infactory
                    author=None,
                    published_date=None,
                    url=None,
                    excerpt=None,
                    relevance_score=m.infactory_score,
                    story_score=m.story_score,
                    section=section_name
                ))
            
            # Calculate average score
            scores = [m.story_score for m in section_matches]
            avg_score = sum(scores) / len(scores) if scores else 0.0
            
            section_groups.append(SectionGroup(
                section_name=section_name.title(),
                section_emoji=get_section_emoji(section_name),
                articles=articles,
                article_count=len(articles),
                average_score=avg_score,
                confidence_contribution=avg_score * len(articles) / len(matches)
            ))
        
        # Generate pitch
        generator = PitchGenerator()
        result = await generator.generate_pitch_from_trend(
            trend_keyword=trend.keyword,
            section_groups=section_groups,
            overall_confidence=queue_item.overall_confidence or 0.5,
            trend_category=trend.trend_category
        )
        await generator.close()
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        pitch_data = result["pitch"]
        
        return GeneratePitchResponse(
            success=True,
            pitch=PitchResponseData(
                headline_suggestions=pitch_data.get("headline_suggestions", []),
                lead_angle=pitch_data.get("lead_angle", ""),
                historical_context=pitch_data.get("historical_context", ""),
                why_now=pitch_data.get("why_now", ""),
                confidence=pitch_data.get("confidence", 0.0),
                source_articles=[
                    PitchSourceArticle(**art)
                    for art in pitch_data.get("source_articles", [])
                ],
                citations=pitch_data.get("citations", []),
                follow_up_questions=pitch_data.get("follow_up_questions", []),
                sections_covered=pitch_data.get("sections_covered", []),
                generated_at=pitch_data.get("generated_at", datetime.utcnow().isoformat())
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating pitch: {str(e)}")


@router.post("/quick", response_model=GeneratePitchResponse)
async def generate_quick_pitch(
    request: QuickPitchRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a quick pitch from a trend keyword.
    
    Simplified version that searches for articles on the fly and
    generates a basic pitch. Useful for quick demos.
    
    - **trend_keyword**: The trending topic to base the pitch on
    - **max_articles**: Maximum number of articles to consider (default: 5)
    """
    try:
        # Search for articles
        from app.integrations.infactory import InfactoryClient
        
        infactory = InfactoryClient()
        search_results = await infactory.search(
            query=request.trend_keyword,
            limit=request.max_articles
        )
        
        # Convert to ArticleReference
        articles = []
        for result in search_results.get('results', []):
            metadata = result.get('metadata', {})
            
            # Parse date if available
            published_date = None
            date_val = metadata.get('published_date') or metadata.get('date')
            if date_val and isinstance(date_val, str):
                try:
                    published_date = datetime.strptime(date_val[:10], '%Y-%m-%d')
                except ValueError:
                    pass
            
            articles.append(ArticleReference(
                article_id=metadata.get('id', result.get('id', 'unknown')),
                title=metadata.get('title', 'Untitled'),
                author=metadata.get('author'),
                published_date=published_date,
                url=metadata.get('url'),
                excerpt=result.get('chunk', {}).get('excerpt'),
                relevance_score=result.get('score', 0.5),
                story_score=result.get('score', 0.5),
                section=metadata.get('section', 'general')
            ))
        
        if not articles:
            return GeneratePitchResponse(
                success=False,
                error="No articles found for this trend keyword",
                pitch=None
            )
        
        # Generate pitch
        generator = PitchGenerator()
        result = await generator.generate_quick_pitch(
            trend_keyword=request.trend_keyword,
            articles=articles
        )
        await generator.close()
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        pitch_data = result["pitch"]
        
        return GeneratePitchResponse(
            success=True,
            pitch=PitchResponseData(
                headline_suggestions=pitch_data.get("headline_suggestions", []),
                lead_angle=pitch_data.get("lead_angle", ""),
                historical_context=pitch_data.get("historical_context", ""),
                why_now=pitch_data.get("why_now", ""),
                confidence=pitch_data.get("confidence", 0.5),
                source_articles=[
                    PitchSourceArticle(**art)
                    for art in pitch_data.get("source_articles", [])
                ],
                citations=pitch_data.get("citations", []),
                follow_up_questions=pitch_data.get("follow_up_questions", []),
                sections_covered=pitch_data.get("sections_covered", []),
                generated_at=pitch_data.get("generated_at", datetime.utcnow().isoformat())
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating pitch: {str(e)}")


@router.post("/block", response_model=PitchBlockResponse)
async def generate_pitch_block(
    request: GeneratePitchBlockRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a story pitch formatted as Slack blocks using the answers endpoint.

    This endpoint uses the editable prompt from `app/prompts.py` to generate
    a pitch via the Infactory answers API, then formats it as Slack blocks.

    - **trend_keyword**: The trending topic to base the pitch on
    - **queue_id**: Optional - generate from an existing queue item
    - **custom_prompt**: Optional - override the default prompt template

    The prompt can be easily edited in `backend/app/prompts.py`.
    """
    try:
        from app.services.pitch_generator import PitchGenerator
        from app.models.schemas import SectionGroup, ArticleReference
        from app.models.database import Trend, ProactiveFeedQueue, TrendArticleMatch

        generator = PitchGenerator()

        # If queue_id provided, get trend and articles from queue
        if request.queue_id:
            queue_item = db.query(ProactiveFeedQueue).filter(
                ProactiveFeedQueue.queue_id == request.queue_id
            ).first()

            if not queue_item:
                raise HTTPException(status_code=404, detail="Queue item not found")

            trend = db.query(Trend).filter(Trend.trend_id == queue_item.trend_id).first()
            if not trend:
                raise HTTPException(status_code=404, detail="Trend not found")

            # Get article matches
            matches = db.query(TrendArticleMatch).filter(
                TrendArticleMatch.trend_id == trend.trend_id,
                TrendArticleMatch.thread_id == queue_item.thread_id
            ).all()

            # Group by section
            section_dict = {}
            for match in matches:
                section = match.section or 'general'
                if section not in section_dict:
                    section_dict[section] = []
                section_dict[section].append(match)

            # Create section groups with proper ArticleReference objects
            section_groups = []
            for section_name, section_matches in section_dict.items():
                articles = []
                for m in section_matches:
                    articles.append(ArticleReference(
                        article_id=str(m.article_id),
                        title=f"Article {m.article_id}",  # Would fetch actual title
                        relevance_score=float(m.infactory_score) if m.infactory_score else 0.0,
                        story_score=float(m.story_score) if m.story_score else 0.0,
                        section=section_name
                    ))

                section_groups.append(SectionGroup(
                    section_name=section_name.title(),
                    section_emoji="📰",
                    articles=articles,
                    article_count=len(articles),
                    average_score=sum(a.story_score for a in articles) / len(articles) if articles else 0.0,
                    confidence_contribution=0.0
                ))

            trend_keyword = trend.keyword
            confidence = float(queue_item.overall_confidence) if queue_item.overall_confidence else 0.5
            trend_category = trend.trend_category
        else:
            # Use provided trend keyword - search for articles
            from app.integrations.infactory import InfactoryClient

            infactory = InfactoryClient()
            search_results = await infactory.search(
                query=request.trend_keyword,
                limit=10
            )

            # Convert results to ArticleReference objects
            articles = []
            for result in search_results.get('results', []):
                chunk = result.get('chunk', {})
                metadata = result.get('metadata', {})
                articles.append(ArticleReference(
                    article_id=str(chunk.get('article_id', 'unknown')),
                    title=chunk.get('title', 'Untitled'),
                    author=chunk.get('author'),
                    excerpt=chunk.get('excerpt'),
                    relevance_score=result.get('score', 0.0),
                    section=metadata.get('section') or chunk.get('section', 'general')
                ))

            # Group by section
            section_dict = {}
            for art in articles:
                section = art.section or 'general'
                if section not in section_dict:
                    section_dict[section] = []
                section_dict[section].append(art)

            section_groups = []
            for section_name, section_articles in section_dict.items():
                section_groups.append(SectionGroup(
                    section_name=section_name.title(),
                    section_emoji="📰",
                    articles=section_articles,
                    article_count=len(section_articles),
                    average_score=sum(a.relevance_score for a in section_articles) / len(section_articles) if section_articles else 0.0,
                    confidence_contribution=0.0
                ))

            trend_keyword = request.trend_keyword
            confidence = 0.5  # Default for ad-hoc queries
            trend_category = "rising"

            await infactory.close()

        # Generate pitch block using the answers endpoint
        result = await generator.generate_pitch_block(
            trend_keyword=trend_keyword,
            section_groups=section_groups,
            overall_confidence=confidence,
            trend_category=trend_category,
            custom_prompt=request.custom_prompt
        )

        await generator.close()

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))

        # Convert blocks to dict for JSON serialization
        blocks = []
        for block in result["blocks"]:
            if hasattr(block, 'model_dump'):
                blocks.append(block.model_dump())
            else:
                blocks.append(block)

        return PitchBlockResponse(
            success=True,
            blocks=blocks,
            pitch_text=result["pitch_text"],
            follow_up_questions=result["follow_up_questions"],
            trend_keyword=result["trend_keyword"],
            confidence=result["confidence"]
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Error generating pitch block: {str(e)}\n{traceback.format_exc()}")

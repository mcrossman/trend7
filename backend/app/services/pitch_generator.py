"""Pitch Generator service for creating story pitches from trend-surfaced articles."""

from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.schemas import (
    ArticleReference, SectionGroup, TrendMessageResult, ArticleReference
)
from app.integrations.infactory import InfactoryClient
from app.config import get_settings
from app.prompts import build_pitch_prompt, PITCH_BLOCK_PROMPT

settings = get_settings()


class PitchGenerator:
    """
    Generates story pitches using the Infactory answer API.
    
    Takes trend-surfaced articles and generates pitch ideas by:
    1. Building contextual queries from trend + article information
    2. Calling the Infactory answer API for historical context
    3. Synthesizing pitch ideas with historical angles
    """
    
    def __init__(self, infactory_client: Optional[InfactoryClient] = None):
        """Initialize with optional Infactory client."""
        self.infactory = infactory_client or InfactoryClient()
    
    async def generate_pitch_from_trend(
        self,
        trend_keyword: str,
        section_groups: List[SectionGroup],
        overall_confidence: float,
        trend_category: str = "rising"
    ) -> Dict[str, Any]:
        """
        Generate a story pitch based on trend-surfaced articles.
        
        Args:
            trend_keyword: The trending topic/keyword
            section_groups: Articles grouped by section
            overall_confidence: Confidence score for this trend match
            trend_category: Type of trend (rising, top, etc.)
        
        Returns:
            Dict with pitch text, historical context, and suggested angles
        """
        # Build pitch query
        query = self._build_pitch_query(trend_keyword, section_groups)
        
        # Get sections for filtering
        sections = [sg.section_name.lower() for sg in section_groups if sg.section_name]
        
        # Build filters
        filters = {}
        if sections:
            filters["sections"] = sections[:3]  # Limit to top 3 sections
        
        # Call answer API
        try:
            answer_result = await self.infactory.answer(
                query=query,
                top_k=15,
                filters=filters if filters else None
            )
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate pitch: {str(e)}",
                "pitch": None
            }
        
        # Extract and structure the response
        pitch_data = self._structure_pitch_response(
            trend_keyword=trend_keyword,
            section_groups=section_groups,
            answer_result=answer_result,
            overall_confidence=overall_confidence,
            trend_category=trend_category
        )
        
        return {
            "success": True,
            "pitch": pitch_data
        }
    
    def _build_pitch_query(
        self,
        trend_keyword: str,
        section_groups: List[SectionGroup]
    ) -> str:
        """
        Build a contextual query for the answer API.
        
        Creates a query that asks for story angles based on the trend
        and the sections where related content has been found.
        """
        # Get top articles from each section
        top_articles = []
        for sg in section_groups[:3]:  # Top 3 sections
            if sg.articles:
                top_article = sg.articles[0]
                top_articles.append({
                    "title": top_article.title,
                    "section": sg.section_name,
                    "year": top_article.published_date.year if top_article.published_date else None
                })
        
        # Build query
        query = f"What are the key historical story angles for a new article about '{trend_keyword}'?"
        
        if top_articles:
            query += " Consider our previous coverage including:"
            for i, article in enumerate(top_articles[:3], 1):
                year_str = f" ({article['year']})" if article['year'] else ""
                query += f" {i}) \"{article['title']}\"{year_str} from {article['section']};"
        
        query += " What unique historical angles, connections to past coverage, or timely contexts should a journalist explore?"
        
        return query
    
    def _structure_pitch_response(
        self,
        trend_keyword: str,
        section_groups: List[SectionGroup],
        answer_result: Dict[str, Any],
        overall_confidence: float,
        trend_category: str
    ) -> Dict[str, Any]:
        """
        Structure the answer API response into a pitch format.
        """
        # Extract key information from answer result
        answer_text = answer_result.get("answer", "")
        citations = answer_result.get("citations", [])
        follow_up_questions = answer_result.get("follow_up_questions", [])
        
        # Get article metadata from our results
        article_summaries = []
        for sg in section_groups:
            for article in sg.articles[:2]:  # Top 2 per section
                article_summaries.append({
                    "id": article.article_id,
                    "title": article.title,
                    "author": article.author,
                    "year": article.published_date.year if article.published_date else None,
                    "section": sg.section_name,
                    "relevance_score": article.relevance_score,
                    "story_score": article.story_score
                })
        
        # Calculate trend context
        trend_context = f"{trend_keyword} is currently trending"
        if trend_category == "rising":
            trend_context += " with rising interest"
        elif trend_category == "top":
            trend_context += " as a top topic"
        
        # Structure the pitch
        pitch = {
            "headline_suggestions": self._extract_headlines(answer_text),
            "lead_angle": self._extract_lead_angle(answer_text),
            "historical_context": answer_text,
            "why_now": trend_context,
            "confidence": overall_confidence,
            "source_articles": article_summaries[:6],  # Top 6 sources
            "citations": citations[:5],  # Top 5 citations
            "follow_up_questions": follow_up_questions[:3],  # Top 3 follow-ups
            "sections_covered": [sg.section_name for sg in section_groups],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return pitch
    
    def _extract_headlines(self, answer_text: str) -> List[str]:
        """
        Extract potential headline suggestions from the answer text.
        
        This is a simple extraction - in production, we might use NLP
        or ask the API specifically for headlines.
        """
        # For now, return a generic structure
        # In the future, this could parse the answer for specific suggestions
        headlines = []
        
        # Look for sentences that might be headline-worthy
        sentences = answer_text.split('.')
        for sentence in sentences[:5]:  # Check first 5 sentences
            sentence = sentence.strip()
            # If sentence is reasonable headline length (30-100 chars)
            if 30 <= len(sentence) <= 100:
                headlines.append(sentence)
        
        return headlines[:3]  # Return top 3
    
    def _extract_lead_angle(self, answer_text: str) -> str:
        """
        Extract the lead angle/hook from the answer text.
        
        Returns the first substantial sentence as the lead.
        """
        sentences = answer_text.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 50:  # Substantial sentence
                return sentence + "."
        
        # Fallback to first sentence
        return sentences[0].strip() + "." if sentences else ""
    
    async def generate_quick_pitch(
        self,
        trend_keyword: str,
        articles: List[ArticleReference]
    ) -> Dict[str, Any]:
        """
        Generate a quick pitch without full section grouping.
        
        Simplified version for quick demos.
        """
        if not articles:
            return {
                "success": False,
                "error": "No articles provided for pitch generation",
                "pitch": None
            }
        
        # Build simple query
        query = f"What are the key story angles for '{trend_keyword}' based on previous Atlantic coverage?"
        
        # Add article titles as context
        if articles:
            query += " Previous articles include: "
            query += "; ".join([f"\"{art.title}\"" for art in articles[:3]])
        
        try:
            answer_result = await self.infactory.answer(
                query=query,
                top_k=10
            )
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate pitch: {str(e)}",
                "pitch": None
            }
        
        # Create simple pitch structure
        pitch = {
            "headline_suggestions": [f"The return of {trend_keyword}", f"Understanding {trend_keyword} through history"],
            "lead_angle": answer_result.get("answer", "")[:200] + "...",
            "why_now": f"{trend_keyword} is currently trending",
            "source_articles": [
                {
                    "id": art.article_id,
                    "title": art.title,
                    "relevance_score": art.relevance_score
                }
                for art in articles[:5]
            ],
            "follow_up_questions": answer_result.get("follow_up_questions", [])[:3],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "pitch": pitch
        }
    
    async def generate_pitch_block(
        self,
        trend_keyword: str,
        section_groups: List[SectionGroup],
        overall_confidence: float,
        trend_category: str = "rising",
        custom_prompt: str = None
    ) -> Dict[str, Any]:
        """
        Generate a story pitch formatted as Slack blocks.
        
        Uses the editable prompt from app/prompts.py for easy customization.
        
        Args:
            trend_keyword: The trending topic/keyword
            section_groups: Articles grouped by section
            overall_confidence: Confidence score for this trend match
            trend_category: Type of trend (rising, top, etc.)
            custom_prompt: Optional custom prompt template (defaults to PITCH_BLOCK_PROMPT)
        
        Returns:
            Dict with Slack blocks and pitch data
        """
        # Build article list for prompt
        articles_data = []
        sections_list = []
        
        for sg in section_groups:
            sections_list.append(sg.section_name)
            for article in sg.articles[:2]:  # Top 2 per section
                articles_data.append({
                    "title": article.title,
                    "year": article.published_date.year if article.published_date else None,
                    "section": sg.section_name
                })
        
        # Build query using the prompt from app/prompts.py
        query = build_pitch_prompt(
            trend_keyword=trend_keyword,
            articles=articles_data,
            sections=sections_list,
            confidence=overall_confidence,
            trend_category=trend_category,
            prompt_template=custom_prompt or PITCH_BLOCK_PROMPT
        )
        
        # Call answer API
        try:
            answer_result = await self.infactory.answer(
                query=query,
                top_k=10
            )
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate pitch: {str(e)}",
                "blocks": []
            }
        
        # Build Slack blocks from the answer
        from app.services.block_formatter import BlockFormatter
        formatter = BlockFormatter()
        
        blocks = formatter.format_pitch_block(
            trend_keyword=trend_keyword,
            pitch_text=answer_result.get("answer", ""),
            section_groups=section_groups,
            confidence=overall_confidence
        )
        
        return {
            "success": True,
            "blocks": blocks,
            "pitch_text": answer_result.get("answer", ""),
            "follow_up_questions": answer_result.get("follow_up_questions", [])[:3],
            "trend_keyword": trend_keyword,
            "confidence": overall_confidence,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def close(self):
        """Close Infactory client connection."""
        await self.infactory.close()

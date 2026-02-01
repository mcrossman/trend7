from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# Block Kit Types
class TextObject(BaseModel):
    type: Literal["plain_text", "mrkdwn"]
    text: str
    emoji: Optional[bool] = None


# Section emoji mapping
SECTION_EMOJIS = {
    "politics": "🏛️",
    "culture": "🎭",
    "technology": "⚡",
    "business": "💼",
    "science": "🔬",
    "health": "🏥",
    "education": "📚",
    "environment": "🌍",
    "general": "📰",
}


def get_section_emoji(section_name: str) -> str:
    """Get emoji for a section name."""
    return SECTION_EMOJIS.get(section_name.lower(), "📰")


class ButtonElement(BaseModel):
    type: Literal["button"] = "button"
    text: TextObject
    action_id: Optional[str] = None
    value: Optional[str] = None
    style: Optional[Literal["primary", "danger"]] = None


class ImageElement(BaseModel):
    type: Literal["image"] = "image"
    image_url: str
    alt_text: str


class HeaderBlock(BaseModel):
    type: Literal["header"] = "header"
    text: TextObject


class SectionBlock(BaseModel):
    type: Literal["section"] = "section"
    text: Optional[TextObject] = None
    fields: Optional[List[TextObject]] = None
    accessory: Optional[ButtonElement] = None


class ContextBlock(BaseModel):
    type: Literal["context"] = "context"
    elements: List[TextObject]


class ActionsBlock(BaseModel):
    type: Literal["actions"] = "actions"
    elements: List[ButtonElement]


class DividerBlock(BaseModel):
    type: Literal["divider"] = "divider"


class TimelineEvent(BaseModel):
    year: int
    title: str
    article_id: str


class TimelineBlock(BaseModel):
    type: Literal["timeline"] = "timeline"
    events: List[TimelineEvent]


Block = HeaderBlock | SectionBlock | ContextBlock | ActionsBlock | DividerBlock | TimelineBlock


# API Models
class ArticleReference(BaseModel):
    article_id: str
    title: str
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    url: Optional[str] = None
    excerpt: Optional[str] = None
    relevance_score: float
    story_score: float = Field(default=0.0, description="Composite score: trend_score * infactory_relevance")
    section: Optional[str] = Field(default=None, description="Atlantic section (Politics, Culture, Technology, etc.)")


class TrendContext(BaseModel):
    """Trend context for a thread when query matches current trends."""
    keyword: str
    score: int  # 0-100 trend score
    category: str  # 'rising', 'top', 'breakout'
    velocity: Optional[float] = None  # % change


class Thread(BaseModel):
    thread_id: str
    thread_type: Literal["evergreen", "event_driven", "novel_concept"]
    central_topic: str
    relevance_score: float
    articles: List[ArticleReference]
    blocks: List[Block]
    explanation: Optional[str] = None
    trend_context: Optional[TrendContext] = None  # Set if thread matches a current trend


class AnalysisOptions(BaseModel):
    max_results: int = 10
    include_trends: bool = True
    threshold: float = 0.10
    thread_types: List[str] = ["evergreen", "event_driven", "novel_concept"]


class AnalysisResult(BaseModel):
    query_id: str
    threads: List[Thread]
    extracted_topics: List[str]
    trend_matches: List[TrendContext] = []  # Any trends that matched the query


# Threshold and Confidence Schemas

class ThresholdConfig(BaseModel):
    """Configuration for threshold-based filtering."""
    min_story_score: float = Field(default=0.30, description="Minimum score for individual stories")
    min_articles_per_section: int = Field(default=1, description="Minimum articles per section")
    min_sections_with_matches: int = Field(default=1, description="Minimum sections with matches")
    min_overall_confidence: float = Field(default=0.50, description="Minimum overall confidence (0.0-1.0)")
    min_total_articles: int = Field(default=3, description="Minimum total articles across all sections")
    max_sections_to_show: int = Field(default=5, description="Maximum sections to display")
    enable_section_grouping: bool = Field(default=True, description="Enable section-based grouping")
    enable_confidence_scoring: bool = Field(default=True, description="Enable confidence calculation")
    show_empty_sections: bool = Field(default=False, description="Show sections with 0 matches")


class SectionGroup(BaseModel):
    """Articles grouped by section."""
    section_name: str
    section_emoji: str = Field(default="📰", description="Emoji representing the section")
    articles: List[ArticleReference]
    article_count: int = Field(default=0, description="Number of articles in this section")
    average_score: float = Field(default=0.0, description="Average story score in this section")
    confidence_contribution: float = Field(default=0.0, description="How much this section contributes to confidence")


class ConfidenceFactors(BaseModel):
    """Breakdown of confidence calculation."""
    base_confidence: float = Field(default=0.0, description="Average of story scores")
    article_count_bonus: float = Field(default=0.0, description="Bonus for having more articles")
    diversity_multiplier: float = Field(default=1.0, description="Bonus for section diversity")
    velocity_multiplier: float = Field(default=1.0, description="Bonus for rising trends")
    threshold_penalty: float = Field(default=0.0, description="Penalty if below thresholds")
    final_confidence: float = Field(default=0.0, description="Final calculated confidence (0.0-1.0)")


class TrendMessageResult(BaseModel):
    """Complete result for a trend-surfaced message."""
    trend_keyword: str
    trend_score: int
    trend_category: str
    trend_velocity: Optional[float] = None
    overall_confidence: float = Field(default=0.0, description="Overall confidence score (0.0-1.0)")
    confidence_level: str = Field(default="very_low", description="very_high, high, medium, low, very_low")
    confidence_factors: ConfidenceFactors
    section_groups: List[SectionGroup]
    total_articles: int = Field(default=0, description="Total articles across all sections")
    sections_with_matches: int = Field(default=0, description="Number of sections with matches")
    blocks: List[Block]  # Block Kit formatted blocks
    threshold_met: bool = Field(default=False, description="Whether min thresholds were met")


class SectionInfo(BaseModel):
    """Information about an Atlantic section."""
    name: str
    emoji: str
    total_matches_24h: int = Field(default=0, description="Total matches in last 24 hours")


class SectionsResponse(BaseModel):
    """Response with available sections and their statistics."""
    success: bool
    sections: List[SectionInfo]

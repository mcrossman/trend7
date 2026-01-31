from typing import List, Optional, Literal
from pydantic import BaseModel
from datetime import datetime


# Block Kit Types
class TextObject(BaseModel):
    type: Literal["plain_text", "mrkdwn"]
    text: str
    emoji: Optional[bool] = None


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


class Thread(BaseModel):
    thread_id: str
    thread_type: Literal["evergreen", "event_driven", "novel_concept"]
    central_topic: str
    relevance_score: float
    articles: List[ArticleReference]
    blocks: List[Block]
    explanation: Optional[str] = None


class AnalysisOptions(BaseModel):
    max_results: int = 10
    include_trends: bool = True
    threshold: float = 0.10
    thread_types: List[str] = ["evergreen", "event_driven", "novel_concept"]


class AnalysisResult(BaseModel):
    query_id: str
    threads: List[Thread]
    extracted_topics: List[str]

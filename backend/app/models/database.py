from sqlalchemy import create_engine, Column, String, DateTime, Float, Integer, JSON, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class StoryReference(Base):
    __tablename__ = "story_references"
    
    article_id = Column(String, primary_key=True)
    title = Column(String)
    author = Column(String)
    published_date = Column(DateTime)
    url = Column(String)
    topics = Column(JSON)
    last_analyzed_at = Column(DateTime, default=datetime.utcnow)
    relevance_score = Column(Float)


class Thread(Base):
    __tablename__ = "threads"
    
    thread_id = Column(String, primary_key=True)
    thread_type = Column(String)  # evergreen, event_driven, novel_concept
    central_topic = Column(String)
    article_ids = Column(JSON)  # List of article IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    temporal_span = Column(Integer)  # Days
    cluster_density = Column(Float)


class Topic(Base):
    __tablename__ = "topics"
    
    topic_id = Column(String, primary_key=True)
    topic_name = Column(String, unique=True)
    frequency_count = Column(Integer, default=0)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    trend_velocity = Column(Float)


class TrendData(Base):
    __tablename__ = "trend_data"
    
    id = Column(Integer, primary_key=True)
    topic_id = Column(String, ForeignKey("topics.topic_id"))
    trend_score = Column(Float)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    geo_region = Column(String, default="US")


class UserFeedback(Base):
    __tablename__ = "user_feedback"
    
    feedback_id = Column(String, primary_key=True)
    thread_id = Column(String, ForeignKey("threads.thread_id"))
    was_helpful = Column(Boolean)
    context = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class Trend(Base):
    __tablename__ = "trends"
    
    trend_id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String, nullable=False)
    trend_score = Column(Integer, nullable=False)  # 0-100 from Google
    trend_category = Column(String, nullable=False)  # 'rising', 'top', 'breakout'
    velocity = Column(Float)  # % change (if available)
    geo_region = Column(String, default="US")
    recorded_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)  # TTL for cache


class TrendArticleMatch(Base):
    __tablename__ = "trend_article_matches"
    
    match_id = Column(Integer, primary_key=True, autoincrement=True)
    trend_id = Column(Integer, ForeignKey("trends.trend_id"))
    thread_id = Column(String, ForeignKey("threads.thread_id"))
    article_id = Column(String, nullable=False)
    infactory_score = Column(Float, nullable=False)  # Relevance score from Infactory
    match_score = Column(Float, nullable=False)  # Composite: trend_score * infactory_score
    surfaced_at = Column(DateTime, default=datetime.utcnow)
    times_surfaced = Column(Integer, default=1)
    last_surfaced_at = Column(DateTime)


class ProactiveFeedQueue(Base):
    __tablename__ = "proactive_feed_queue"
    
    queue_id = Column(Integer, primary_key=True, autoincrement=True)
    trend_id = Column(Integer, ForeignKey("trends.trend_id"))
    thread_id = Column(String, ForeignKey("threads.thread_id"))
    priority_score = Column(Float, nullable=False)  # For ordering queue
    status = Column(String, default="pending")  # 'pending', 'sent', 'dismissed'
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime)
    blocks_json = Column(String, nullable=False)  # Pre-formatted Block Kit JSON


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

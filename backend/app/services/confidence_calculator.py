"""Confidence calculation service for trend-surfaced stories."""

from typing import List, Dict, Any
import math

from app.models.schemas import (
    ArticleReference, SectionGroup, ConfidenceFactors, ThresholdConfig
)
from app.integrations.trends import Trend
from app.config import get_settings

settings = get_settings()


class ConfidenceCalculator:
    """
    Calculates confidence scores for trend-surfaced stories.
    
    Implements the scoring algorithm defined in the specification:
    - Per-story scores based on trend and infactory relevance
    - Overall confidence with base score, diversity, and velocity multipliers
    - Threshold checking for quality filtering
    """
    
    def __init__(self, config: ThresholdConfig = None):
        """Initialize with optional custom threshold configuration."""
        self.config = config or ThresholdConfig(
            min_story_score=settings.min_story_score,
            min_articles_per_section=settings.min_articles_per_section,
            min_sections_with_matches=settings.min_sections_with_matches,
            min_overall_confidence=settings.min_overall_confidence,
            min_total_articles=settings.min_total_articles,
            max_sections_to_show=settings.max_sections_to_show,
            enable_section_grouping=settings.enable_section_grouping,
            enable_confidence_scoring=settings.enable_confidence_scoring,
            show_empty_sections=settings.show_empty_sections,
        )
    
    def calculate_story_score(
        self,
        article: ArticleReference,
        trend: Trend
    ) -> float:
        """
        Calculate per-story score.
        
        Formula: (trend_score / 100) * infactory_relevance_score
        """
        if not article.relevance_score or not trend.trend_score:
            return 0.0
        
        # Normalize trend score to 0.0-1.0
        trend_normalized = trend.trend_score / 100.0
        
        # Calculate composite score
        story_score = trend_normalized * article.relevance_score
        
        return round(story_score, 3)
    
    def calculate_overall_confidence(
        self,
        articles: List[ArticleReference],
        trend: Trend
    ) -> ConfidenceFactors:
        """
        Calculate overall confidence for a set of articles matching a trend.
        
        Returns a ConfidenceFactors object with all calculation components.
        """
        if not articles:
            return ConfidenceFactors(
                base_confidence=0.0,
                article_count_bonus=0.0,
                diversity_multiplier=1.0,
                velocity_multiplier=1.0,
                threshold_penalty=0.0,
                final_confidence=0.0
            )
        
        # Calculate base confidence from average story scores
        story_scores = [art.story_score for art in articles if art.story_score]
        avg_score = sum(story_scores) / len(story_scores) if story_scores else 0.0
        
        # Article count bonus: sqrt(article_count / 10) with diminishing returns
        # More articles increase confidence, but with diminishing returns
        article_count_normalized = len(articles) / 10.0
        count_bonus = math.sqrt(min(article_count_normalized, 1.0))  # Cap at 1.0
        
        base_confidence = avg_score * (0.8 + 0.2 * count_bonus)
        
        # Diversity multiplier: bonus for articles across multiple sections
        sections = set(art.section for art in articles if art.section)
        unique_sections = len(sections)
        diversity_multiplier = 1.0 + (unique_sections / 10.0)
        diversity_multiplier = min(diversity_multiplier, 1.5)  # Cap at 1.5
        
        # Velocity multiplier: bonus for rising trends
        velocity_multiplier = 1.0
        if trend.trend_category == 'rising' and trend.velocity:
            # Rising trends get up to 1.05 boost
            velocity_multiplier = 1.0 + min(trend.velocity / 200.0, 0.05)
        
        # Check thresholds
        threshold_met = self._check_thresholds(articles, unique_sections)
        threshold_penalty = 0.0 if threshold_met else 1.0  # 1.0 = 100% penalty
        
        # Calculate final confidence
        if threshold_penalty > 0:
            final_confidence = 0.0
        else:
            final_confidence = base_confidence * diversity_multiplier * velocity_multiplier
            final_confidence = min(final_confidence, 1.0)  # Cap at 1.0
        
        return ConfidenceFactors(
            base_confidence=round(base_confidence, 3),
            article_count_bonus=round(count_bonus * 0.2 * avg_score, 3),
            diversity_multiplier=round(diversity_multiplier, 3),
            velocity_multiplier=round(velocity_multiplier, 3),
            threshold_penalty=threshold_penalty,
            final_confidence=round(final_confidence, 3)
        )
    
    def _check_thresholds(
        self,
        articles: List[ArticleReference],
        unique_sections: int
    ) -> bool:
        """
        Check if results meet minimum thresholds.
        
        Returns True if all thresholds are met, False otherwise.
        """
        # Check total articles
        if len(articles) < self.config.min_total_articles:
            return False
        
        # Check sections with matches
        if unique_sections < self.config.min_sections_with_matches:
            return False
        
        # Check min articles per section
        section_counts: Dict[str, int] = {}
        for art in articles:
            section = art.section or 'general'
            section_counts[section] = section_counts.get(section, 0) + 1
        
        min_count = min(section_counts.values()) if section_counts else 0
        if min_count < self.config.min_articles_per_section:
            return False
        
        # Check min story scores
        story_scores = [art.story_score for art in articles if art.story_score]
        if story_scores and min(story_scores) < self.config.min_story_score:
            return False
        
        return True
    
    def get_confidence_level(self, confidence: float) -> str:
        """
        Map confidence score to confidence level.
        
        Returns: 'very_high', 'high', 'medium', 'low', 'very_low'
        """
        if confidence >= 0.90:
            return 'very_high'
        elif confidence >= 0.75:
            return 'high'
        elif confidence >= 0.50:
            return 'medium'
        elif confidence >= 0.25:
            return 'low'
        else:
            return 'very_low'
    
    def get_confidence_badge(self, confidence: float) -> str:
        """Get emoji badge for confidence level."""
        level = self.get_confidence_level(confidence)
        badges = {
            'very_high': '🔥',
            'high': '✅',
            'medium': '⚠️',
            'low': '❓',
            'very_low': '❌'
        }
        return badges.get(level, '❓')
    
    def get_confidence_label(self, confidence: float) -> str:
        """Get human-readable label for confidence level."""
        level = self.get_confidence_level(confidence)
        labels = {
            'very_high': 'Very High',
            'high': 'High',
            'medium': 'Medium',
            'low': 'Low',
            'very_low': 'Very Low'
        }
        return labels.get(level, 'Unknown')


def create_section_groups(
    articles: List[ArticleReference]
) -> List[SectionGroup]:
    """
    Group articles by section.
    
    Returns a list of SectionGroup objects sorted by average score descending.
    """
    from app.models.schemas import get_section_emoji
    
    # Group articles by section
    section_dict: Dict[str, List[ArticleReference]] = {}
    for article in articles:
        section = article.section or 'general'
        if section not in section_dict:
            section_dict[section] = []
        section_dict[section].append(article)
    
    # Create SectionGroup objects
    groups = []
    for section_name, section_articles in section_dict.items():
        scores = [art.story_score for art in section_articles if art.story_score]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        # Sort articles by story score descending
        sorted_articles = sorted(
            section_articles,
            key=lambda a: a.story_score or 0,
            reverse=True
        )
        
        groups.append(SectionGroup(
            section_name=section_name.title(),
            section_emoji=get_section_emoji(section_name),
            articles=sorted_articles,
            article_count=len(sorted_articles),
            average_score=round(avg_score, 3),
            confidence_contribution=round(avg_score * len(sorted_articles) / len(articles), 3)
        ))
    
    # Sort by average score descending
    groups.sort(key=lambda g: g.average_score, reverse=True)
    
    return groups

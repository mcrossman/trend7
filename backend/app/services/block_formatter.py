from typing import Any, List, Optional
from datetime import datetime
from app.models.schemas import (
    Thread, Block, HeaderBlock, SectionBlock, ContextBlock, ActionsBlock,
    DividerBlock, TimelineBlock, TextObject, ButtonElement, TimelineEvent,
    ArticleReference, AnalysisResult
)
from app.integrations.trends import Trend

# Configuration constants for block formatting
MAX_ARTICLES_PER_THREAD = 10  # Max articles to show in a thread
MAX_ARTICLES_PER_SECTION = 10  # Max articles per section in trend view
MAX_SECTIONS_TO_SHOW = 5  # Max sections to display
MAX_BLOCKS_TOTAL = 50  # Slack allows up to 50 blocks per message


class BlockFormatter:
    """
    Formats analysis results as Slack Block Kit blocks.
    This allows the same output to be:
    - Rendered by web UI (convert blocks to React components)
    - Sent directly to Slack (native rendering)
    - Stored for later retrieval
    """
    
    def format_thread_result(self, thread: Thread) -> List[Block]:
        """Format a single thread as Block Kit blocks."""
        blocks: List[Block] = []
        
        # Header with thread title
        blocks.append(HeaderBlock(
            text=TextObject(
                type="plain_text",
                text=f"🎯 {thread.central_topic}",
                emoji=True
            )
        ))
        
        # Context with metadata (type, relevance, article count)
        context_elements = [
            TextObject(type="mrkdwn", text=f"*Type:* {thread.thread_type.replace('_', ' ').title()}"),
            TextObject(type="mrkdwn", text=f"*Relevance:* {int(thread.relevance_score * 100)}%"),
            TextObject(type="mrkdwn", text=f"*Articles:* {len(thread.articles)}")
        ]
        blocks.append(ContextBlock(elements=context_elements))
        
        # Explanation if available
        if thread.explanation:
            blocks.append(SectionBlock(
                text=TextObject(
                    type="mrkdwn",
                    text=f"_{thread.explanation}_"
                )
            ))
        
        # Divider
        blocks.append(DividerBlock())
        
        # Month+Year distribution if we have articles with dates
        dated_articles = [a for a in thread.articles if a.published_date]
        if dated_articles:
            distribution = self._create_month_year_distribution(dated_articles)
            if distribution:
                blocks.append(distribution)

        # Article sections (show up to 10, or more if we have room)
        max_articles = min(MAX_ARTICLES_PER_THREAD, len(thread.articles))
        for i, article in enumerate(thread.articles[:max_articles], 1):
            blocks.append(self._format_article_section(article, i))

        # Show more indicator if there are more articles
        remaining = len(thread.articles) - max_articles
        if remaining > 0:
            blocks.append(SectionBlock(
                text=TextObject(
                    type="mrkdwn",
                    text=f"_... and {remaining} more articles_"
                )
            ))
        
        # Action buttons
        action_buttons = [
            ButtonElement(
                text=TextObject(type="plain_text", text="👍 Helpful"),
                action_id="feedback_positive",
                value=f"{thread.thread_id}",
                style="primary"
            ),
            ButtonElement(
                text=TextObject(type="plain_text", text="👎 Not Helpful"),
                action_id="feedback_negative",
                value=f"{thread.thread_id}"
            ),
            ButtonElement(
                text=TextObject(type="plain_text", text="💾 Save Thread"),
                action_id="save_thread",
                value=f"{thread.thread_id}"
            )
        ]
        blocks.append(ActionsBlock(elements=action_buttons))
        
        return blocks
    
    def _create_month_year_distribution(self, articles: List[ArticleReference]) -> Optional[SectionBlock]:
        """Create a month+year distribution histogram as a section block."""
        from collections import Counter
        
        # Group articles by month+year
        month_year_counts = Counter()
        for article in articles:
            if article.published_date:
                key = article.published_date.strftime("%b %Y")  # e.g., "Jan 2024"
                month_year_counts[key] += 1
        
        if not month_year_counts:
            return None
        
        # Sort chronologically
        sorted_items = sorted(
            month_year_counts.items(),
            key=lambda x: datetime.strptime(x[0], "%b %Y")
        )
        
        # Build distribution text
        max_count = max(count for _, count in sorted_items)
        distribution_text = "*Coverage over time:*\n```\n"
        
        for month_year, count in sorted_items:
            # Create a simple bar chart using block characters
            bar_length = int((count / max_count) * 10) if max_count > 0 else 0
            bar = "█" * bar_length + "░" * (10 - bar_length)
            distribution_text += f"{month_year:>8} │{bar}│ {count}\n"
        
        distribution_text += "```"
        
        return SectionBlock(
            text=TextObject(type="mrkdwn", text=distribution_text)
        )
    
    def _format_article_section(self, article: ArticleReference, index: int) -> SectionBlock:
        """Format a single article as a section block."""
        # Build article text
        date_str = ""
        if article.published_date:
            date_str = f" ({article.published_date.year})"
        
        author_str = f" | {article.author}" if article.author else ""
        
        text = f"*{index}. {article.title}*{date_str}\n"
        text += f"Author: {article.author or 'Unknown'}{author_str} | Relevance: {int(article.relevance_score * 100)}%\n"
        
        if article.excerpt:
            excerpt = article.excerpt[:280] + "..." if len(article.excerpt) > 280 else article.excerpt
            text += f"> {excerpt}"
        
        # Create view button
        view_button = ButtonElement(
            text=TextObject(type="plain_text", text="View"),
            action_id="view_article",
            value=article.article_id
        )
        
        return SectionBlock(
            text=TextObject(type="mrkdwn", text=text),
            accessory=view_button
        )
    
    def format_analysis_result(self, result: AnalysisResult) -> List[Block]:
        """Format a complete analysis result with multiple threads."""
        blocks: List[Block] = []
        
        if not result.threads:
            # No threads found
            blocks.append(HeaderBlock(
                text=TextObject(
                    type="plain_text",
                    text="🔍 No relevant threads found"
                )
            ))
            blocks.append(SectionBlock(
                text=TextObject(
                    type="mrkdwn",
                    text="Try adjusting your search terms or try a different article."
                )
            ))
            return blocks
        
        # Summary header
        thread_count = len(result.threads)
        topic_text = ", ".join(result.extracted_topics[:5]) if result.extracted_topics else "general topics"
        
        blocks.append(HeaderBlock(
            text=TextObject(
                type="plain_text",
                text=f"📊 Found {thread_count} thread{'s' if thread_count > 1 else ''}"
            )
        ))
        
        if result.extracted_topics:
            blocks.append(ContextBlock(
                elements=[
                    TextObject(type="mrkdwn", text=f"*Topics:* {topic_text}")
                ]
            ))
        
        blocks.append(DividerBlock())
        
        # Format each thread
        for i, thread in enumerate(result.threads):
            thread_blocks = self.format_thread_result(thread)
            blocks.extend(thread_blocks)
            
            # Add divider between threads (except after the last one)
            if i < len(result.threads) - 1:
                blocks.append(DividerBlock())
        
        return blocks
    
    def format_proactive_suggestions(self, threads: List[Thread]) -> List[Block]:
        """Format proactive thread suggestions."""
        blocks: List[Block] = []
        
        blocks.append(HeaderBlock(
            text=TextObject(
                type="plain_text",
                text="📰 Trending Story Threads"
            )
        ))
        
        blocks.append(ContextBlock(
            elements=[
                TextObject(type="mrkdwn", text=f"*{len(threads)} trending topics found*")
            ]
        ))
        
        blocks.append(DividerBlock())
        
        for thread in threads:
            # Compact format for proactive feed
            blocks.append(SectionBlock(
                text=TextObject(
                    type="mrkdwn",
                    text=f"*🎯 {thread.central_topic}*\n"
                         f"Type: {thread.thread_type.replace('_', ' ').title()} | "
                         f"Relevance: {int(thread.relevance_score * 100)}% | "
                         f"Articles: {len(thread.articles)}"
                ),
                accessory=ButtonElement(
                    text=TextObject(type="plain_text", text="View"),
                    action_id="view_thread",
                    value=thread.thread_id
                )
            ))
        
        return blocks
    
    def format_error_message(self, error: str) -> List[Block]:
        """Format an error message as Block Kit blocks."""
        return [
            HeaderBlock(
                text=TextObject(
                    type="plain_text",
                    text="❌ Error"
                )
            ),
            SectionBlock(
                text=TextObject(
                    type="mrkdwn",
                    text=f"An error occurred: {error}"
                )
            )
        ]

    def format_thread_result_with_trend(
        self,
        thread: Thread,
        trend: Trend
    ) -> List[Block]:
        """
        Format a thread with trend context included.

        Adds a trend indicator block at the beginning to show that
        this topic is currently trending.
        """
        # Get base blocks from normal formatting
        blocks = self.format_thread_result(thread)

        # Insert trend indicator after header (position 0) and context (position 1)
        # Find the right position - after header and context blocks
        insert_position = 0
        for i, block in enumerate(blocks):
            if hasattr(block, 'type') and block.type in ['header', 'context']:
                insert_position = i + 1

        # Create trend indicator block
        velocity_str = ""
        if trend.velocity:
            velocity_str = f" (+{trend.velocity}% interest)"

        trend_block = ContextBlock(
            elements=[
                TextObject(
                    type="mrkdwn",
                    text=f"📈 *This topic is trending:* {trend.keyword}{velocity_str}"
                )
            ]
        )

        # Insert trend block
        blocks.insert(insert_position, trend_block)

        return blocks
    
    def format_trend_thread(
        self,
        trend: Trend,
        thread: Thread,
        articles: List[ArticleReference]
    ) -> List[Block]:
        """
        Format a trend-surfaced thread as Block Kit blocks.
        
        Includes trend context (score, velocity, category) along with
        the thread and article information.
        """
        blocks: List[Block] = []
        
        # Header with trending indicator
        blocks.append(HeaderBlock(
            text=TextObject(
                type="plain_text",
                text=f"🔥 Trending: {trend.keyword}",
                emoji=True
            )
        ))
        
        # Trend context
        velocity_str = ""
        if trend.velocity:
            velocity_str = f" | *Growth:* +{trend.velocity}%"
        
        blocks.append(ContextBlock(
            elements=[
                TextObject(
                    type="mrkdwn",
                    text=f"*Interest:* {trend.trend_score}/100 | *Category:* {trend.trend_category.title()}{velocity_str}"
                )
            ]
        ))
        
        # Thread topic
        blocks.append(SectionBlock(
            text=TextObject(
                type="mrkdwn",
                text=f"*Thread:* {thread.central_topic}\n"
                     f"Type: {thread.thread_type.replace('_', ' ').title()} | "
                     f"Relevance: {int(thread.relevance_score * 100)}%"
            )
        ))
        
        blocks.append(DividerBlock())
        
        # Article sections (top articles)
        if articles:
            blocks.append(SectionBlock(
                text=TextObject(
                    type="mrkdwn",
                    text=f"*{len(articles)} relevant Atlantic article{'s' if len(articles) > 1 else ''} found:*"
                )
            ))
            
            for i, article in enumerate(articles[:MAX_ARTICLES_PER_SECTION], 1):
                blocks.append(self._format_trend_article_section(article, i, trend))
            
            # "More" indicator if there are additional articles
            if len(articles) > MAX_ARTICLES_PER_SECTION:
                blocks.append(SectionBlock(
                    text=TextObject(
                        type="mrkdwn",
                        text=f"_... and {len(articles) - 6} more articles_"
                    )
                ))
        
        # Action buttons
        action_buttons = [
            ButtonElement(
                text=TextObject(type="plain_text", text="👍 Helpful"),
                action_id="feedback_positive",
                value=f"{thread.thread_id}",
                style="primary"
            ),
            ButtonElement(
                text=TextObject(type="plain_text", text="👎 Not Relevant"),
                action_id="feedback_negative",
                value=f"{thread.thread_id}"
            ),
            ButtonElement(
                text=TextObject(type="plain_text", text="📌 Save Thread"),
                action_id="save_thread",
                value=f"{thread.thread_id}"
            )
        ]
        blocks.append(ActionsBlock(elements=action_buttons))
        
        return blocks

    def format_trend_thread_with_sections(
        self,
        trend: Trend,
        thread: Thread,
        articles: List[ArticleReference],
        section_groups: List,
        confidence_factors,
        threshold_met: bool = True
    ) -> List[Block]:
        """
        Format a trend-surfaced thread with section-based grouping and confidence scores.
        
        This is the enhanced version that includes:
        - Overall confidence badge and score
        - Articles grouped by Atlantic section
        - Per-story scores for each article
        - Confidence factors breakdown
        """
        from app.models.schemas import get_section_emoji, ConfidenceFactors
        from app.services.confidence_calculator import ConfidenceCalculator
        
        blocks: List[Block] = []
        
        # Get confidence calculator for badges/labels
        calc = ConfidenceCalculator()
        overall_confidence = confidence_factors.final_confidence
        confidence_badge = calc.get_confidence_badge(overall_confidence)
        confidence_label = calc.get_confidence_label(overall_confidence)
        
        # Header with confidence badge
        blocks.append(HeaderBlock(
            text=TextObject(
                type="plain_text",
                text=f"{confidence_badge} Trending: {trend.keyword} ({int(overall_confidence * 100)}% confidence)",
                emoji=True
            )
        ))
        
        # Confidence context line
        velocity_str = ""
        if trend.velocity:
            velocity_str = f" | Growth: +{trend.velocity}%"
        
        blocks.append(ContextBlock(
            elements=[
                TextObject(
                    type="mrkdwn",
                    text=f"*Confidence:* {confidence_badge} {confidence_label} ({int(overall_confidence * 100)}%) | "
                         f"*Articles:* {len(articles)} across {len(section_groups)} sections | "
                         f"*Interest:* {trend.trend_score}/100{velocity_str}"
                )
            ]
        ))
        
        # Threshold warning if not met
        if not threshold_met:
            blocks.append(SectionBlock(
                text=TextObject(
                    type="mrkdwn",
                    text="⚠️ *Note:* This trend does not meet all quality thresholds. Results may be less reliable."
                )
            ))
        
        blocks.append(DividerBlock())
        
        # Section headers and articles
        if section_groups:
            blocks.append(SectionBlock(
                text=TextObject(
                    type="mrkdwn",
                    text=f"📰 *SECTIONS WITH MATCHES:*"
                )
            ))
            
            for section_group in section_groups[:MAX_SECTIONS_TO_SHOW]:  # Max sections
                # Section header with emoji
                section_header = f"{section_group.section_emoji} *{section_group.section_name.upper()}* "
                section_header += f"({section_group.article_count} article{'s' if section_group.article_count > 1 else ''}, "
                section_header += f"avg: {int(section_group.average_score * 100)}%)"
                
                blocks.append(SectionBlock(
                    text=TextObject(
                        type="mrkdwn",
                        text=section_header
                    )
                ))
                
                # Articles in this section (top 6 per section)
                for i, article in enumerate(section_group.articles[:MAX_ARTICLES_PER_SECTION], 1):
                    blocks.append(self._format_section_article(article, i, trend))
                
                # "More" indicator if there are additional articles
                if len(section_group.articles) > MAX_ARTICLES_PER_SECTION:
                    blocks.append(ContextBlock(
                        elements=[
                            TextObject(
                                type="mrkdwn",
                                text=f"_{len(section_group.articles) - 6} more articles in this section..._"
                            )
                        ]
                    ))
                
                blocks.append(DividerBlock())
        
        # Confidence breakdown (collapsible context)
        if isinstance(confidence_factors, ConfidenceFactors):
            breakdown = f"*Confidence breakdown:* Base {int(confidence_factors.base_confidence * 100)}%"
            if confidence_factors.diversity_multiplier > 1.0:
                breakdown += f" × Diversity {confidence_factors.diversity_multiplier:.2f}"
            if confidence_factors.velocity_multiplier > 1.0:
                breakdown += f" × Velocity {confidence_factors.velocity_multiplier:.2f}"
            breakdown += f" = {int(confidence_factors.final_confidence * 100)}%"
            
            blocks.append(ContextBlock(
                elements=[
                    TextObject(
                        type="mrkdwn",
                        text=breakdown
                    )
                ]
            ))
        
        # Action buttons
        action_buttons = [
            ButtonElement(
                text=TextObject(type="plain_text", text="👍 Helpful"),
                action_id="feedback_positive",
                value=f"{thread.thread_id}",
                style="primary"
            ),
            ButtonElement(
                text=TextObject(type="plain_text", text="👎 Not Relevant"),
                action_id="feedback_negative",
                value=f"{thread.thread_id}"
            ),
            ButtonElement(
                text=TextObject(type="plain_text", text="📌 Save Thread"),
                action_id="save_thread",
                value=f"{thread.thread_id}"
            )
        ]
        blocks.append(ActionsBlock(elements=action_buttons))
        
        return blocks

    def _format_section_article(
        self,
        article: ArticleReference,
        index: int,
        trend: Trend
    ) -> SectionBlock:
        """Format a single article within a section context."""
        # Build article text
        date_str = ""
        if article.published_date:
            date_str = f" ({article.published_date.year})"
        
        # Use story_score if available, otherwise calculate
        story_score = article.story_score if article.story_score else (trend.trend_score / 100) * article.relevance_score
        
        text = f"*{index}. {article.title}*{date_str}\n"
        text += f"Relevance: {int(article.relevance_score * 100)}% | Story Score: {story_score:.2f}\n"
        
        if article.excerpt:
            excerpt = article.excerpt[:280] + "..." if len(article.excerpt) > 280 else article.excerpt
            text += f"> {excerpt}"
        
        # Create view button
        view_button = ButtonElement(
            text=TextObject(type="plain_text", text="View"),
            action_id="view_article",
            value=article.article_id
        )
        
        return SectionBlock(
            text=TextObject(type="mrkdwn", text=text),
            accessory=view_button
        )
    
    def _format_trend_article_section(
        self,
        article: ArticleReference,
        index: int,
        trend: Trend
    ) -> SectionBlock:
        """Format a single article in a trend context."""
        # Build article text
        date_str = ""
        if article.published_date:
            date_str = f" ({article.published_date.year})"
        
        # Calculate match score
        match_score = (trend.trend_score / 100) * article.relevance_score
        
        text = f"*{index}. {article.title}*{date_str}\n"
        text += f"Relevance: {int(article.relevance_score * 100)}% | Match Score: {match_score:.2f}\n"
        
        if article.excerpt:
            excerpt = article.excerpt[:280] + "..." if len(article.excerpt) > 280 else article.excerpt
            text += f"> {excerpt}"
        
        # Create view button
        view_button = ButtonElement(
            text=TextObject(type="plain_text", text="View"),
            action_id="view_article",
            value=article.article_id
        )
        
        return SectionBlock(
            text=TextObject(type="mrkdwn", text=text),
            accessory=view_button
        )
    
    def format_pitch_block(
        self,
        trend_keyword: str,
        pitch_text: str,
        section_groups: List[Any],
        confidence: float
    ) -> List[Block]:
        """
        Format a story pitch as Slack blocks.
        
        Args:
            trend_keyword: The trending topic
            pitch_text: The generated pitch text from the answers API
            section_groups: Articles grouped by section
            confidence: Overall confidence score
        
        Returns:
            List of Block objects for Slack
        """
        blocks: List[Block] = []
        
        # Header
        blocks.append(HeaderBlock(
            text=TextObject(
                type="plain_text",
                text=f"📝 Story Pitch: {trend_keyword}",
                emoji=True
            )
        ))
        
        # Confidence context
        confidence_pct = int(confidence * 100)
        blocks.append(ContextBlock(
            elements=[
                TextObject(
                    type="mrkdwn",
                    text=f"*Confidence:* {confidence_pct}% | Based on {len(section_groups)} section{'s' if len(section_groups) > 1 else ''} of coverage"
                )
            ]
        ))
        
        blocks.append(DividerBlock())
        
        # Main pitch content
        # Split pitch text into sections if it contains headers
        if "**" in pitch_text:
            # Parse markdown-style headers
            sections = pitch_text.split("\n\n")
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                    
                # Check if it's a header (starts with **)
                if section.startswith("**") and section.endswith("**"):
                    header_text = section[2:-2]  # Remove ** markers
                    blocks.append(SectionBlock(
                        text=TextObject(
                            type="mrkdwn",
                            text=f"*{header_text}*"
                        )
                    ))
                else:
                    # Regular content
                    # Truncate if too long for Slack
                    if len(section) > 2900:
                        section = section[:2900] + "..."
                    
                    blocks.append(SectionBlock(
                        text=TextObject(
                            type="mrkdwn",
                            text=section
                        )
                    ))
        else:
            # Plain text - just add as section
            if len(pitch_text) > 2900:
                pitch_text = pitch_text[:2900] + "..."
            
            blocks.append(SectionBlock(
                text=TextObject(
                    type="mrkdwn",
                    text=pitch_text
                )
            ))
        
        blocks.append(DividerBlock())
        
        # Source articles section
        if section_groups:
            blocks.append(SectionBlock(
                text=TextObject(
                    type="mrkdwn",
                    text="*📰 Source Articles by Section:*"
                )
            ))

            article_count = 0
            for sg in section_groups:
                # Add section header with emoji
                section_header = f"{sg.section_emoji} *{sg.section_name}* ({sg.article_count} article{'s' if sg.article_count > 1 else ''})"
                blocks.append(SectionBlock(
                    text=TextObject(type="mrkdwn", text=section_header)
                ))

                for article in sg.articles[:2]:  # Top 2 per section
                    article_count += 1
                    if article_count > 6:  # Max 6 articles total
                        break

                    date_str = f" ({article.published_date.year})" if article.published_date else ""
                    text = f"• *{article.title}*{date_str}"
                    if article.author:
                        text += f" — {article.author}"

                    blocks.append(SectionBlock(
                        text=TextObject(type="mrkdwn", text=text)
                    ))

                if article_count > 6:
                    break
        
        # Action buttons
        action_buttons = [
            ButtonElement(
                text=TextObject(type="plain_text", text="👍 Good Pitch"),
                action_id="pitch_helpful",
                value=f"pitch_{trend_keyword}",
                style="primary"
            ),
            ButtonElement(
                text=TextObject(type="plain_text", text="👎 Not Useful"),
                action_id="pitch_not_helpful",
                value=f"pitch_{trend_keyword}"
            ),
            ButtonElement(
                text=TextObject(type="plain_text", text="🔄 Regenerate"),
                action_id="regenerate_pitch",
                value=f"regenerate_{trend_keyword}"
            )
        ]
        blocks.append(ActionsBlock(elements=action_buttons))
        
        return blocks

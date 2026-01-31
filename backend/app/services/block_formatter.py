from typing import List, Optional
from datetime import datetime
from app.models.schemas import (
    Thread, Block, HeaderBlock, SectionBlock, ContextBlock, ActionsBlock,
    DividerBlock, TimelineBlock, TextObject, ButtonElement, TimelineEvent,
    ArticleReference, AnalysisResult
)
from app.integrations.trends import Trend


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
        
        # Timeline if we have articles with dates
        dated_articles = [a for a in thread.articles if a.published_date]
        if dated_articles:
            timeline_events = []
            for article in sorted(dated_articles, key=lambda x: x.published_date or datetime.min)[:5]:
                year = article.published_date.year if article.published_date else 0
                timeline_events.append(TimelineEvent(
                    year=year,
                    title=article.title,
                    article_id=article.article_id
                ))
            if timeline_events:
                blocks.append(self._create_timeline_section(timeline_events))
        
        # Article sections (top 3)
        for i, article in enumerate(thread.articles[:3], 1):
            blocks.append(self._format_article_section(article, i))
        
        # Show more indicator if there are more articles
        if len(thread.articles) > 3:
            blocks.append(SectionBlock(
                text=TextObject(
                    type="mrkdwn",
                    text=f"_... and {len(thread.articles) - 3} more articles_"
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
    
    def _create_timeline_section(self, events: List[TimelineEvent]) -> SectionBlock:
        """Create a timeline visualization as a section block."""
        # Sort events by year
        sorted_events = sorted(events, key=lambda x: x.year)
        
        # Create timeline text
        timeline_text = "*Timeline:*\n```\n"
        for i, event in enumerate(sorted_events):
            if i > 0:
                timeline_text += " ── "
            timeline_text += f"{event.year} ●"
        timeline_text += "\n```"
        
        return SectionBlock(
            text=TextObject(type="mrkdwn", text=timeline_text)
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
            excerpt = article.excerpt[:150] + "..." if len(article.excerpt) > 150 else article.excerpt
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
            
            for i, article in enumerate(articles[:3], 1):
                blocks.append(self._format_trend_article_section(article, i, trend))
        
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
            excerpt = article.excerpt[:150] + "..." if len(article.excerpt) > 150 else article.excerpt
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

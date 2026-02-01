"""Story Pitch Prompts Configuration

This file contains all the prompts used for generating story pitches via the Infactory answers API.
Edit these prompts to customize the pitch generation behavior.

Prompts support the following variables:
- {trend_keyword}: The trending topic/keyword
- {article_titles}: List of previous article titles
- {sections}: List of Atlantic sections with relevant coverage
- {confidence}: Overall confidence score (0.0-1.0)
- {trend_category}: Type of trend (rising, top, breakout)
"""

# Main pitch generation prompt - used for full pitch generation
PITCH_GENERATION_PROMPT = """You are a senior Atlantic editor helping a journalist develop a story pitch about "{trend_keyword}".

This topic is currently {trend_category} with a confidence score of {confidence:.0%}.

Previous Atlantic coverage includes:
{article_list}

Based on this historical coverage and current trends, provide:

1. **Headline Suggestions** (3 options): Compelling headlines that connect the trend to Atlantic's voice
2. **Lead Angle**: A strong opening paragraph or hook (2-3 sentences)
3. **Historical Context**: How this connects to previous Atlantic coverage and what new angles emerge
4. **Why Now**: What's timely about this story
5. **Follow-up Questions** (3): Questions the journalist should explore

Keep your response concise but substantive. Focus on angles that would resonate with Atlantic readers."""

# Quick pitch prompt - used for rapid pitch generation
QUICK_PITCH_PROMPT = """Generate a story pitch about "{trend_keyword}" for The Atlantic.

Previous coverage: {article_titles}

Provide:
- 2-3 headline suggestions
- A 2-sentence lead/hook
- Why this matters now
- 2 follow-up questions to explore"""

# Block-specific pitch prompt - generates content formatted for Slack blocks
PITCH_BLOCK_PROMPT = """Generate a concise story pitch about "{trend_keyword}" for a Slack message.

Context: This relates to previous coverage in {sections}.

Format your response as:

**Suggested Headlines:**
• [Headline 1]
• [Headline 2]

**The Angle:**
[1-2 sentence hook explaining the story]

**Historical Context:**
[1-2 sentences connecting to Atlantic's coverage]

**Next Steps:**
• [Question 1]
• [Question 2]

Keep it brief and punchy - this will appear in a Slack block."""

# Follow-up questions prompt - generates questions for further exploration
FOLLOW_UP_PROMPT = """Based on the trend "{trend_keyword}" and Atlantic's previous coverage, what are 3-5 essential questions a journalist should answer to develop a comprehensive story?

Format as a numbered list with brief context for each question."""


def format_article_list(articles: list) -> str:
    """Format a list of articles for prompt insertion."""
    if not articles:
        return "No previous coverage found."
    
    lines = []
    for i, art in enumerate(articles[:5], 1):  # Top 5 articles
        year = f" ({art.get('year')})" if art.get('year') else ""
        section = f" [{art.get('section', 'general')}]"
        lines.append(f"{i}. \"{art.get('title', 'Untitled')}\"{year}{section}")
    
    return "\n".join(lines)


def format_sections_list(sections: list) -> str:
    """Format sections list for prompt insertion."""
    if not sections:
        return "various sections"
    
    if len(sections) == 1:
        return sections[0]
    
    return ", ".join(sections[:-1]) + " and " + sections[-1]


def build_pitch_prompt(
    trend_keyword: str,
    articles: list,
    sections: list,
    confidence: float,
    trend_category: str,
    prompt_template: str = None
) -> str:
    """
    Build a pitch prompt with variables substituted.
    
    Args:
        trend_keyword: The trending topic
        articles: List of article dicts with title, year, section
        sections: List of section names
        confidence: Overall confidence score (0.0-1.0)
        trend_category: Type of trend
        prompt_template: Optional custom prompt template
    
    Returns:
        Formatted prompt string ready for the answers API
    """
    template = prompt_template or PITCH_GENERATION_PROMPT
    
    return template.format(
        trend_keyword=trend_keyword,
        article_list=format_article_list(articles),
        article_titles=", ".join([a.get('title', 'Untitled') for a in articles[:3]]),
        sections=format_sections_list(sections),
        confidence=confidence,
        trend_category=trend_category
    )

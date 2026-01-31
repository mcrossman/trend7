from typing import List
from app.models.schemas import Thread, Block, HeaderBlock, TextObject, AnalysisResult


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
        
        # Header
        blocks.append(HeaderBlock(
            text=TextObject(
                type="plain_text",
                text=f"🎯 Story Thread: {thread.central_topic}"
            )
        ))
        
        # TODO: Add more block types
        # - Context with metadata
        # - Timeline visualization
        # - Article sections
        # - Action buttons
        
        return blocks
    
    def format_analysis_result(self, result: AnalysisResult) -> List[Block]:
        """Format a complete analysis result with multiple threads."""
        blocks: List[Block] = []
        
        # Summary header
        blocks.append(HeaderBlock(
            text=TextObject(
                type="plain_text",
                text=f"Found {len(result.threads)} relevant threads"
            )
        ))
        
        # Format each thread
        for thread in result.threads:
            thread_blocks = self.format_thread_result(thread)
            blocks.extend(thread_blocks)
        
        return blocks

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import aiofiles

from app.config import get_settings

settings = get_settings()


class ArticleLoader:
    """
    Load and manage article JSON files from local storage.
    This allows working with downloaded article data without API calls.
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or "./data/articles")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    async def load_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a single article from JSON file.
        
        Args:
            article_id: The article ID (filename without .json extension)
            
        Returns:
            Article data dict or None if not found
        """
        file_path = self.data_dir / f"{article_id}.json"
        
        if not file_path.exists():
            return None
        
        async with aiofiles.open(file_path, 'r') as f:
            content = await f.read()
            return json.loads(content)
    
    def load_article_sync(self, article_id: str) -> Optional[Dict[str, Any]]:
        """Synchronous version of load_article."""
        file_path = self.data_dir / f"{article_id}.json"
        
        if not file_path.exists():
            return None
        
        with open(file_path, 'r') as f:
            return json.load(f)
    
    async def save_article(self, article_id: str, data: Dict[str, Any]) -> None:
        """
        Save article data to JSON file.
        
        Args:
            article_id: The article ID (will be used as filename)
            data: Article data to save
        """
        file_path = self.data_dir / f"{article_id}.json"
        
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(json.dumps(data, indent=2))
    
    def save_article_sync(self, article_id: str, data: Dict[str, Any]) -> None:
        """Synchronous version of save_article."""
        file_path = self.data_dir / f"{article_id}.json"
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def list_articles(self) -> List[str]:
        """
        List all available article IDs from local storage.
        
        Returns:
            List of article IDs (filenames without .json extension)
        """
        if not self.data_dir.exists():
            return []
        
        articles = []
        for file_path in self.data_dir.glob("*.json"):
            articles.append(file_path.stem)
        
        return sorted(articles)
    
    async def load_all_articles(self) -> List[Dict[str, Any]]:
        """
        Load all articles from local storage.
        
        Returns:
            List of article data dicts
        """
        article_ids = await self.list_articles()
        articles = []
        
        for article_id in article_ids:
            article = await self.load_article(article_id)
            if article:
                articles.append(article)
        
        return articles
    
    async def delete_article(self, article_id: str) -> bool:
        """
        Delete an article from local storage.
        
        Args:
            article_id: The article ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        file_path = self.data_dir / f"{article_id}.json"
        
        if not file_path.exists():
            return False
        
        file_path.unlink()
        return True
    
    async def bulk_load_from_directory(self, directory: str) -> int:
        """
        Load all JSON files from a directory into local storage.
        
        Args:
            directory: Path to directory containing article JSON files
            
        Returns:
            Number of articles loaded
        """
        source_dir = Path(directory)
        if not source_dir.exists():
            return 0
        
        count = 0
        for file_path in source_dir.glob("*.json"):
            try:
                async with aiofiles.open(file_path, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                
                # Use filename as article_id if not specified in data
                article_id = data.get('id') or data.get('article_id') or file_path.stem
                await self.save_article(article_id, data)
                count += 1
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        return count
    
    def get_article_path(self, article_id: str) -> Path:
        """Get the file path for an article."""
        return self.data_dir / f"{article_id}.json"
    
    async def article_exists(self, article_id: str) -> bool:
        """Check if an article exists in local storage."""
        file_path = self.data_dir / f"{article_id}.json"
        return file_path.exists()


# Global loader instance
_article_loader: Optional[ArticleLoader] = None


def get_article_loader() -> ArticleLoader:
    """Get or create global article loader instance."""
    global _article_loader
    if _article_loader is None:
        _article_loader = ArticleLoader()
    return _article_loader

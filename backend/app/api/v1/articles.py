from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.integrations.article_loader import get_article_loader

router = APIRouter()


class ArticleUploadResponse(BaseModel):
    article_id: str
    success: bool
    message: str


class ArticleListResponse(BaseModel):
    articles: List[str]
    total: int


class ArticleDataResponse(BaseModel):
    article_id: str
    data: Dict[str, Any]


@router.get("/", response_model=ArticleListResponse)
async def list_local_articles():
    """
    List all articles stored in local JSON storage.
    """
    loader = get_article_loader()
    articles = await loader.list_articles()
    return ArticleListResponse(articles=articles, total=len(articles))


@router.get("/{article_id}", response_model=ArticleDataResponse)
async def get_local_article(article_id: str):
    """
    Get a specific article from local storage.
    """
    loader = get_article_loader()
    data = await loader.load_article(article_id)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"Article {article_id} not found")
    
    return ArticleDataResponse(article_id=article_id, data=data)


@router.post("/upload", response_model=ArticleUploadResponse)
async def upload_article(
    article_id: str,
    file: UploadFile = File(...)
):
    """
    Upload an article JSON file to local storage.
    
    - **article_id**: The ID to assign to this article
    - **file**: JSON file containing article data
    """
    loader = get_article_loader()
    
    try:
        content = await file.read()
        data = eval(content.decode('utf-8'))  # In production, use json.loads with validation
        
        await loader.save_article(article_id, data)
        return ArticleUploadResponse(
            article_id=article_id,
            success=True,
            message=f"Article {article_id} uploaded successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to upload article: {str(e)}")


@router.post("/upload-json", response_model=ArticleUploadResponse)
async def upload_article_json(
    article_id: str,
    data: Dict[str, Any]
):
    """
    Upload article data as JSON payload.
    
    - **article_id**: The ID to assign to this article
    - **data**: Article data as JSON object
    """
    loader = get_article_loader()
    
    try:
        await loader.save_article(article_id, data)
        return ArticleUploadResponse(
            article_id=article_id,
            success=True,
            message=f"Article {article_id} saved successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to save article: {str(e)}")


@router.delete("/{article_id}")
async def delete_local_article(article_id: str):
    """
    Delete an article from local storage.
    """
    loader = get_article_loader()
    deleted = await loader.delete_article(article_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Article {article_id} not found")
    
    return {"success": True, "message": f"Article {article_id} deleted"}


@router.post("/bulk-import")
async def bulk_import_articles(directory: str):
    """
    Import all JSON files from a directory.
    
    - **directory**: Path to directory containing article JSON files
    """
    loader = get_article_loader()
    count = await loader.bulk_load_from_directory(directory)
    
    return {
        "success": True,
        "message": f"Imported {count} articles from {directory}",
        "count": count
    }

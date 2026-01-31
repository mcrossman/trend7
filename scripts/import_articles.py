import json
import asyncio
from pathlib import Path

# Simple import without backend dependencies
async def import_articles():
    data_dir = Path('./data/articles')
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Load the Atlantic articles
    with open('data/Atlantic_hackathon_articles.json', 'r') as f:
        articles = json.load(f)
    
    print(f"Found {len(articles)} articles to import")
    
    imported = 0
    skipped = 0
    for article in articles:
        article_id = str(article['article_id'])
        file_path = data_dir / f"{article_id}.json"
        
        # Check if already exists
        if file_path.exists():
            skipped += 1
            continue
        
        # Save the article
        with open(file_path, 'w') as f:
            json.dump(article, f, indent=2)
        imported += 1
        
        if imported % 500 == 0:
            print(f"Imported {imported}/{len(articles)} articles...")
    
    print(f"\nDone!")
    print(f"  Imported: {imported} new articles")
    print(f"  Skipped: {skipped} existing articles")
    
    # Count total
    existing = list(data_dir.glob('*.json'))
    print(f"  Total in storage: {len(existing)} articles")

if __name__ == "__main__":
    asyncio.run(import_articles())

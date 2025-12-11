import asyncio
import os
from platforms.bilibili import BilibiliPlatform

def test_bilibili_search():
    print("Initializing Bilibili Platform...")
    # Ensure SESSDATA is available (mock if needed or rely on env)
    # The user has SESSDATA exported in the terminal, so os.getenv should pick it up if running in same env context.
    # If not, I'll print a warning.
    sess = os.getenv("SESSDATA")
    if not sess:
        print("WARNING: SESSDATA not found in env. Search might fail or return limited results.")
    
    bili = BilibiliPlatform()
    keyword = "AI"
    print(f"Searching Bilibili for: {keyword}")
    
    try:
        results = bili.search_users(keyword)
        print(f"Found {len(results)} users:")
        for u in results[:3]:
            # The search returns video objects with 'author', 'mid', 'title'
            print(f" - Author: {u.get('author')} (mid={u.get('mid')}) - Title: {u.get('title')[:30]}...")
            
        if len(results) == 0:
            print("ERROR: No results found.")
            
    except Exception as e:
        print(f"EXCEPTION during search: {e}")

if __name__ == "__main__":
    test_bilibili_search()

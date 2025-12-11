import asyncio
from platforms.douyin import DouyinPlatform

async def test_link_parsing():
    platform = DouyinPlatform()
    # A random popular video or search result link (need a real one to test)
    # Using a typical format example. Use a real ID if possible.
    # If I don't have a real ID, I might fail.
    # Let's try to search first to get a video ID? No search fails.
    # I'll try to find a known public video ID from recent noise or valid URL pattern.
    # Example video ID: 731000000... (need a valid one).
    # Ill try to hit the API with a made-up ID to see if it 404s or 403s. 
    # If 403/Shark -> Cookie needed. If 404/Success -> Cookie not strictly needed for access.
    
    # Actually, better to test Playwright Cookie Fetch immediately since Search is the main goal.
    pass

if __name__ == "__main__":
    asyncio.run(test_link_parsing())

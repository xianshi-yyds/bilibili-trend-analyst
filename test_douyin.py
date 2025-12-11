import asyncio
from douyin_tiktok_scraper.scraper import Scraper

async def test():
    scraper = Scraper()
    # Test User Search or Info
    # Note: API methods are likely named 'hybrid_parsing', 'get_user_info' etc.
    # Without docs, I'll try to dir(scraper) or use common names found in search results.
    # Search result said: "parsing videos", "get_douyin_video_id"
    
    print("Scraper initialized")
    print("Methods:", dir(scraper))

if __name__ == "__main__":
    asyncio.run(test())

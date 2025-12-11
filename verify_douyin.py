import asyncio
from platforms.douyin import DouyinPlatform

async def test_search():
    platform = DouyinPlatform()
    keyword = "AI"
    print(f"Searching Douyin for: {keyword}")
    
    results = platform.search_users(keyword)
    print(f"DEBUG: Found {len(results)} users.")
    
    for u in results[:3]:
        print(f" - {u['name']} (mid={u['mid']})")
        print(f"   Matches: {u}")
        
        # Test Get Recent Posts for first user
        print(f"   Fetching posts for {u['name']}...")
        posts = platform.get_recent_posts(u['mid'], limit=5)
        print(f"   Found {len(posts)} posts.")
        if posts:
            print(f"   Latest: {posts[0]['title']}")

if __name__ == "__main__":
    # DouyinPlatform is synchronous (requests based) but we wrap in asyncio if needed or just run
    # platform methods are sync in my implementation.
    asyncio.run(test_search())

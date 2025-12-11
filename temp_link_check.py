from platforms.douyin import DouyinPlatform
import json

print("Initializing DouyinPlatform...")
dy = DouyinPlatform()
try:
    with open("douyin_cookie.txt", "r") as f:
        cookie = f.read().strip()
    dy.update_cookies(cookie)
except:
    print("Failed to load cookie file")

# Sample Video ID
vid = "7069979868804418851"
print(f"Fetching detail via scraper.get_douyin_video_data for ID: {vid}")

import asyncio

async def test():
    try:
        detail = await dy.scraper.get_douyin_video_data(vid)
        print("SUCCESS! Video Detail Fetched via SCRAPER:")
        print(json.dumps(detail, indent=2, ensure_ascii=False)[:1000])
    except Exception as e:
        print(f"Scraper Method Failed: {e}")

asyncio.run(test())

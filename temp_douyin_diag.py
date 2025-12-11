from platforms.douyin import DouyinPlatform
import json
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

print("Initializing DouyinPlatform...")
dy = DouyinPlatform()
try:
    with open("douyin_cookie.txt", "r") as f:
        cookie = f.read().strip()
    dy.update_cookies(cookie)
except:
    print("Failed to load cookie file")

print(f"Cookie Length: {len(dy.cookie)}")

keyword = "ai"
print(f"Searching for '{keyword}'...")
results = dy.search_users(keyword)

print(f"Results Found: {len(results)}")
if len(results) > 0:
    print("First Result:")
    print(json.dumps(results[0], indent=2, ensure_ascii=False))
else:
    print("No results found. Check logs for API errors.")

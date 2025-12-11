import asyncio
import os
from playwright.async_api import async_playwright

async def fetch_douyin_cookies():
    """
    Launches a headless browser to visit Douyin and capture the initial cookies (ttwid).
    """
    print("[CookieManager] Launching Playwright to fetch Douyin cookies...")
    try:
        async with async_playwright() as p:
            # Check if chromium is installed, if not, might fail. 
            # Assuming widely available or installed via previous step.
            browser = await p.chromium.launch(headless=True)
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = await context.new_page()
            
            # Go to Douyin Search page directly to trigger ttwid
            # Using a harmless search to ensure search-related cookies are primed?
            # Or just home. Search page seems to trigger 'hit_shark' checks which sets cookies.
            target_url = "https://www.douyin.com/search/AI"
            
            print(f"[CookieManager] Navigating to {target_url}...")
            try:
                # Wait until network is idle or just commit
                await page.goto(target_url, wait_until="networkidle", timeout=20000)
            except Exception as e:
                print(f"[CookieManager] Notification: Navigation timeout/warning: {e}")

            # Wait a bit for JS to execute and cookies to set
            await asyncio.sleep(2)
            
            # Get cookies
            cookies = await context.cookies()
            cookie_str = ""
            ttwid_found = False
            for c in cookies:
                cookie_str += f"{c['name']}={c['value']}; "
                if c['name'] == "ttwid":
                    ttwid_found = True
            
            await browser.close()
            
            if ttwid_found:
                print("[CookieManager] Success: ttwid found.")
                return cookie_str
            else:
                print("[CookieManager] Warning: ttwid NOT found in captured cookies.")
                # Return what we have anyway, might work for some things
                return cookie_str
                
    except Exception as e:
        print(f"[CookieManager] Failed to fetch cookies: {e}")
        return None

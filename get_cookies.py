import asyncio
from playwright.async_api import async_playwright
import time

async def get_douyin_cookies():
    print("Launching Playwright to fetch cookies...")
    async with async_playwright() as p:
        # Launch headless
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        
        # Go to Douyin Search page directly to trigger ttwid
        print("Navigating to Douyin...")
        try:
            await page.goto("https://www.douyin.com/search/AI", wait_until="networkidle", timeout=15000)
        except Exception as e:
            print(f"Navigation warning: {e}")

        # Wait a bit for JS to execute and cookies to set
        await asyncio.sleep(2)
        
        # Get cookies
        cookies = await context.cookies()
        cookie_str = ""
        for c in cookies:
            cookie_str += f"{c['name']}={c['value']}; "
        
        print(f"Captured Cookie Length: {len(cookie_str)}")
        await browser.close()
        
        if "ttwid" in cookie_str:
            print("Success: ttwid found.")
            return cookie_str
        else:
            print("Warning: ttwid to found.")
            return cookie_str

if __name__ == "__main__":
    cookies = asyncio.run(get_douyin_cookies())
    print("\n--- COOKIES ---\n")
    print(cookies)

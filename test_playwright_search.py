from playwright.sync_api import sync_playwright
import time
import urllib.parse

def test_search(keyword):
    # Load cookies
    cookies = []
    try:
        with open('douyin_cookie.txt', 'r') as f:
            cookie_str = f.read().strip()
            # Parse standard cookie string (k=v; k=v;) into list of dicts
            for item in cookie_str.split(';'):
                if '=' in item:
                    name, value = item.split('=', 1)
                    cookies.append({
                        "name": name.strip(),
                        "value": value.strip(),
                        "domain": ".douyin.com",
                        "path": "/"
                    })
    except Exception as e:
        print(f"Cookie Load Error: {e}")

    with sync_playwright() as p:
        # Launch Headful (Visible) to pass fingerprinting
        browser = p.chromium.launch(
            headless=False, # Visible Browser
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        
        # Inject Cookies
        if cookies:
            context.add_cookies(cookies)
            print(f"Injected {len(cookies)} cookies.")
            
        page = context.new_page()
        
        # Hack to remove 'navigator.webdriver' property
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """)

        encoded = urllib.parse.quote(keyword)
        url = f"https://www.douyin.com/search/{encoded}?source=normal_search&type=video"
        
        print(f"Navigating to: {url}")
        page.goto(url)
        
        # Wait for results
        print("Waiting for results...")
        try:
            # Wait for search cards
            page.wait_for_selector('div[data-e2e="search_card"]', timeout=20000)
            print("Results Loaded!")
            
            cards = page.query_selector_all('div[data-e2e="search_card"]')
            print(f"Found {len(cards)} cards.")
            
            for i, card in enumerate(cards[:3]):
                text = card.inner_text()
                print(f"Card {i}: {text[:100]}...")
                
        except Exception as e:
            print(f"Timeout/Error: {e}")
            print(f"Title: {page.title()}")
            # Screenshot for debug (can't see it but useful if I could fetch it)
            # page.screenshot(path="debug_error.png")
        
        browser.close()

if __name__ == "__main__":
    test_search("开箱")

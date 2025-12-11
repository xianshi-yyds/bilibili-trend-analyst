from playwright.sync_api import sync_playwright
import time
import urllib.parse

def test_capture():
    print("Launching Browser for Capture Diagnosis...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = browser.new_page()
        
        url = "https://www.douyin.com/search/%E5%BC%80%E7%AE%B1?source=normal_search&type=video"
        print(f"Navigating to {url}")
        
        try:
            page.goto(url, timeout=30000)
            print("Navigation returned.")
        except Exception as e:
            print(f"Navigation error: {e}")
            
        print("Waiting 5s...")
        time.sleep(5)
        
        title = page.title()
        print(f"Page Title: '{title}'")
        
        page.screenshot(path="diag_status.png")
        print("Saved diag_status.png")
        
        # Check for captcha frames
        frames = page.frames
        print(f"Frame Count: {len(frames)}")
        for f in frames:
            print(f"Frame: {f.name} | {f.url}")
            
        browser.close()

if __name__ == "__main__":
    test_capture()

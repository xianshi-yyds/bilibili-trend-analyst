import asyncio
from playwright.async_api import async_playwright
try:
    from playwright_stealth import stealth_async
except ImportError:
    stealth_async = None

import urllib.parse
import json
import os
import random
import cv2
import numpy as np
import requests

class DouyinBrowser:
    def __init__(self, cookie_file="douyin_cookie.txt", headless=False):
        self.cookie_file = cookie_file
        self.headless = headless

    def _bezier_curve(self, points, steps):
        """Calculate Bezier curve points"""
        n = len(points) - 1
        curve = []
        for t in np.linspace(0, 1, steps):
            x, y = 0, 0
            for i, (px, py) in enumerate(points):
                binom = np.math.factorial(n) / (np.math.factorial(i) * np.math.factorial(n - i))
                term = binom * ((1 - t) ** (n - i)) * (t ** i)
                x += term * px
                y += term * py
            curve.append((x, y))
        return curve

    async def _human_drag(self, page, slider_box, target_x):
        """Simulate human-like drag with Bezier Curve and Overshoot"""
        print("[DouyinBrowser] Generating Human-like Bezier Trajectory...")
        
        # Start center of slider
        start_x = slider_box['x'] + slider_box['width'] / 2
        start_y = slider_box['y'] + slider_box['height'] / 2
        
        end_x = start_x + target_x
        end_y = start_y + random.randint(-5, 5) # Slight Y drift
        
        # Control points for Bezier (Randomized)
        c1_x = start_x + (target_x / 3) + random.randint(-20, 20)
        c1_y = start_y + random.randint(-50, 50)
        c2_x = start_x + (2 * target_x / 3) + random.randint(-20, 20)
        c2_y = start_y + random.randint(-50, 50)
        
        points = [(start_x, start_y), (c1_x, c1_y), (c2_x, c2_y), (end_x, end_y)]
        
        steps = random.randint(40, 60)
        trajectory = self._bezier_curve(points, steps)
        
        await page.mouse.move(start_x, start_y)
        await page.mouse.down()
        
        for tx, ty in trajectory:
             await page.mouse.move(tx, ty)
             # Random sleep (faster in middle)
             dist_remain = abs(end_x - tx)
             if dist_remain < 10:
                 sleep_t = random.uniform(0.05, 0.1) 
             else:
                 sleep_t = random.uniform(0.005, 0.02)
             await asyncio.sleep(sleep_t)
             
        # Overshoot correction (Occasionally)
        if random.random() > 0.3:
            overshoot = random.randint(2, 5)
            await page.mouse.move(end_x + overshoot, end_y)
            await asyncio.sleep(0.1)
            await page.mouse.move(end_x, end_y)
            
        await asyncio.sleep(random.uniform(0.2, 0.5)) 
        await page.mouse.up()

    async def _solve_captcha(self, page):
        print("[DouyinBrowser] Attempting Auto-Solve Captcha (Scanning Frames)...")
        try:
             # Find the Captcha Frame
             target_frame = None
             for frame in page.frames:
                 if "captcha" in frame.url or "verify" in frame.url:
                     target_frame = frame
                     print(f"[DouyinBrowser] Found Captcha Frame: {frame.url[:50]}...")
                     break
            
             # Fallback: Scrape main page if no frame found
             search_context = target_frame if target_frame else page
             
             # 1. Get Images
             bg_selectors = ['.captcha_verify_img_slide', '#captcha-verify-image', '.img_block', 'img[src*="captcha"]', '.captcha_bg_img']
             bg_el = None
             
             # Wait a bit for frame content
             await asyncio.sleep(2)
             
             # Try to find the image with WAITING
             for sel in bg_selectors:
                 try:
                    if target_frame:
                         print(f"[DouyinBrowser] Waiting for selector '{sel}' in captcha frame...")
                         bg_el = await target_frame.wait_for_selector(sel, timeout=3000)
                    else:
                         print(f"[DouyinBrowser] Waiting for selector '{sel}' in page...")
                         bg_el = await page.wait_for_selector(sel, timeout=3000)
                    if bg_el: 
                        print(f"[DouyinBrowser] Locked on image: {sel}")
                        break
                 except: pass

             if not bg_el: 
                 # Final attempt: Find ANY large image
                 print("[DouyinBrowser] Selectors failed. Scanning for large images...")
                 try:
                     images = await (target_frame if target_frame else page).query_selector_all('img')
                     for img in images:
                         box = await img.bounding_box()
                         if box and box['width'] > 200 and box['height'] > 100:
                             bg_el = img
                             print(f"[DouyinBrowser] Found heuristic image (w={box['width']})")
                             break
                 except Exception as err:
                     print(f"Heuristic scan error: {err}")

             if not bg_el:
                 print("[DouyinBrowser] Could not find captcha image in any frame.")
                 # Capture full frame for debug
                 try:
                    await (target_frame if target_frame else page).screenshot(path="debug_captcha_failed_frame.png")
                 except: 
                    await page.screenshot(path="debug_captcha_failed_page.png")
                 return False
             
             # Screenshot form the element handle (works even in frame)
             await bg_el.screenshot(path="captcha_bg.png")
             print("[DouyinBrowser] Captured captcha_bg.png from frame.")
             
             # 2. Logic: Process Image
             img_rgb = cv2.imread('captcha_bg.png')
             img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
             edges = cv2.Canny(img_gray, 100, 200)
             contours, _ = cv2.findContours(edges, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
             target_x = 0
             for cnt in contours:
                 x, y, w, h = cv2.boundingRect(cnt)
                 if 30 < w < 80 and 30 < h < 80 and x > 50:
                     target_x = x
                     cv2.rectangle(img_rgb, (x, y), (x+w, y+h), (0, 255, 0), 2)
                     break
             cv2.imwrite("debug_captcha_detected.png", img_rgb)
             
             if target_x == 0:
                 print("[DouyinBrowser] CV failed to find gap.")
                 return False
             print(f"[DouyinBrowser] Gap found at X={target_x}")

             # 3. Drag (Context aware)
             slider_selectors = ['.secsdk-captcha-drag-icon', '.btn', '.captcha_drag_btn', '.slide_btn']
             slider_el = None
             for sel in slider_selectors:
                 slider_el = await search_context.query_selector(sel)
                 if slider_el: break
             
             if slider_el:
                 box = await slider_el.bounding_box()
                 if box:
                     await self._human_drag(page, box, target_x)
                     return True
        except Exception as e:
            print(f"[DouyinBrowser] Solver Exception: {e}")
        return False

    def _parse_cookies(self):
        cookies = []
        if os.path.exists(self.cookie_file):
            try:
                with open(self.cookie_file, 'r') as f:
                    cookie_str = f.read().strip()
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
                print(f"[DouyinBrowser] Cookie Parse Error: {e}")
        return cookies

    async def search(self, keyword):
        print(f"[DouyinBrowser] Converting keyword '{keyword}' to Playwright Search...")
        print(f"[DouyinBrowser] Launching Browser (Visible={not self.headless})...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
            )
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            
            cookies = self._parse_cookies()
            if cookies:
                await context.add_cookies(cookies)

            page = await context.new_page()
            
            if stealth_async:
                print("[DouyinBrowser] Applying Playwright Stealth...")
                await stealth_async(page)
            else:
                await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            encoded = urllib.parse.quote(keyword)
            url = f"https://www.douyin.com/search/{encoded}?source=normal_search&type=video"
            
            results = []
            try:
                print(f"[DouyinBrowser] Navigating to {url}")
                await page.goto(url, timeout=60000)
                
                # Frame Detection Loop (Robust)
                print("[DouyinBrowser] Scanning for Security Frames...")
                captcha_detected = False
                
                for i in range(15):
                    # Method 1: Page Frames loop
                    for frame in page.frames:
                        if "verify" in frame.url or "captcha" in frame.url:
                            print(f"[DouyinBrowser] Detected Frame URL: {frame.url}")
                            captcha_detected = True
                            break
                    # Method 2: Selector check
                    if not captcha_detected:
                        if await page.query_selector('iframe[src*="verify"]'):
                            print("[DouyinBrowser] Detected iframe via Selector!")
                            captcha_detected = True
                            
                    if captcha_detected: break
                    if i % 2 == 0: print(f"[DouyinBrowser] Scanning... {i}/15")
                    await asyncio.sleep(1)
                
                if captcha_detected:
                    print(f"[DouyinBrowser] !!! DETECTED CAPTCHA IFRAME !!!")
                    print(f"[DouyinBrowser] Attempting AUTO-SOLVE...")
                    solved = await self._solve_captcha(page)
                    if solved:
                         print("[DouyinBrowser] Auto-Solve apparently successful. Waiting...")
                         await asyncio.sleep(3)
                         
                # Verify and Wait for Results (with manual fallback loop)
                print("[DouyinBrowser] Waiting for result cards (or Manual Solve)...")
                cards_found = False
                
                # Wait for ANY text content or specific video links
                # We relax the check to just look for links with /video/
                for i in range(30):
                    # Check for video links directly
                    if await page.query_selector('a[href*="/video/"]'):
                        print("[DouyinBrowser] Video links detected!")
                        cards_found = True
                        break
                    if i % 5 == 0: print(f"[DouyinBrowser] Waiting... {30-i}s")
                    await asyncio.sleep(1)

                if cards_found:
                    # Find all video links directly
                    video_links = await page.query_selector_all('a[href*="/video/"]')
                    print(f"[DouyinBrowser] Found {len(video_links)} potential video links.")
                    
                    seen_urls = set()
                    
                    for link in video_links:
                        try:
                            href = await link.get_attribute('href')
                            if not href: continue
                            
                            print(f"[DouyinBrowser] Checking Link: {href[:60]}...")
                            
                            if href.startswith("//"): href = "https:" + href
                            elif href.startswith("/"): href = "https://www.douyin.com" + href
                            
                            # Deduplicate
                            if href in seen_urls: continue
                            seen_urls.add(href)
                            
                            # Extract ID
                            import re
                            vid_match = re.search(r'video/(\d+)', href)
                            if not vid_match: 
                                print(f"[DouyinBrowser] X No video ID in: {href}")
                                continue
                            vid = vid_match.group(1)
                            
                            # Try to get text/title from the link itself or parent
                            text = await link.inner_text()
                            if not text:
                                # Try parent text
                                parent = await link.evaluate_handle('el => el.parentElement')
                                text = await parent.inner_text()
                                
                            print(f"[DouyinBrowser] -> ADDING VIDEO: {vid} | {text[:20]}")
                            
                            # Try to get image (recursive search)
                            img_el = await link.query_selector('img')
                            if not img_el:
                                # Try slightly deeper or wait? Usually just 'img' works if present.
                                # Check for style background?
                                pass
                                
                            src = ""
                            if img_el:
                                src = await img_el.get_attribute('src')
                                # Douyin sometimes uses data-src
                                if not src:
                                    src = await img_el.get_attribute('data-src')
                            
                            # Fallback if src is relative or protocol-less
                            if src and src.startswith("//"): src = "https:" + src
                            
                            print(f"[DouyinBrowser] -> Image: {src[:40]}...")

                            results.append({
                                "id": vid,
                                "title": text.split('\n')[0][:50] if text else f"Video {vid}", 
                                "cover": src,
                                "author": "Douyin User", 
                                "play": 0, 
                                "link": href
                            })
                        except Exception as e:
                            print(f"Link Parse Error: {e}")
                            
            except Exception as e:
                print(f"[DouyinBrowser] Search Error: {e}")
                import traceback
                traceback.print_exc()
            
            await browser.close()
            return results
            # Singleton instance
print("----------------------------------------------------------------")
print("[DouyinBrowser] MODULE RELOADED SUCCESSFULLY.")
print("[DouyinBrowser] Features Active: Stealth, Bezier, Iframe-Scan.")
print("----------------------------------------------------------------")
douyin_browser = DouyinBrowser(headless=False) # Visual Mode Enabled


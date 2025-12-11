import requests
import re
import json
import urllib.parse

keyword = "开箱"
encoded_keyword = urllib.parse.quote(keyword)
url = f"https://www.douyin.com/search/{encoded_keyword}?source=normal_search&type=video"

headers = {
    # Desktop UA often gets the SSR page
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Cookie": "s_v_web_id=verify_...;" # Ideally uses the cookie file, but let's try guest/minimal first or load from file
}

# Load real cookies if available to avoid immediate captcha
try:
    with open('douyin_cookie.txt', 'r') as f:
        cookie_str = f.read().strip()
        if cookie_str:
            headers['Cookie'] = cookie_str
except:
    pass

print(f"Fetching Search Page: {url}")
try:
    res = requests.get(url, headers=headers, timeout=10)
    html = res.text
    print(f"Content Length: {len(html)}")
    
    # Check for _ROUTER_DATA
    if "window._ROUTER_DATA" in html:
        print("FOUND _ROUTER_DATA!")
        
        # Extract JSON
        json_match = re.search(r'window\._ROUTER_DATA\s*=\s*(\{.+?\});', html, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            try:
                data = json.loads(json_str)
                loader_data = data.get('loaderData', {})
                print(f"Loader Keys: {list(loader_data.keys())}")
                
                # Look for search results key
                # Provide a dump of keys to find the right path
                for k, v in loader_data.items():
                    print(f"Key: {k}")
                    if isinstance(v, dict):
                         print(f"  Subkeys: {list(v.keys())}")
                         
            except Exception as e:
                print(f"JSON Parse Error: {e}")
    else:
        print("NO _ROUTER_DATA found.")
        # Check for title to see if we got a captcha page
        title = re.search(r'<title>(.*?)</title>', html)
        if title:
            print(f"Page Title: {title.group(1)}")
            
        if "captcha" in html or "verify" in html or "验证" in html:
            print("DETECTED CAPTCHA/VERIFICATION PAGE")
            
        print(f"First 500 chars: {html[:500]}")

except Exception as e:
    print(f"Request Error: {e}")

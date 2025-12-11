import requests
import re
import json

short_url = "https://v.douyin.com/XE29evc41EE/"
headers = {
    # Use generic iPhone UA to get the mobile share page
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
}

print(f"1. Resolving: {short_url}")
try:
    session = requests.Session()
    res = session.get(short_url, headers=headers, allow_redirects=True)
    final_url = res.url
    print(f"2. Final URL: {final_url}")
    
    print("3. Fetching Content...")
    # Sometimes Douyin checks Referer
    headers["Referer"] = final_url
    res = session.get(final_url, headers=headers)
    html = res.text
    
    print(f"   Content Length: {len(html)}")
    
    # Check for Title
    title_match = re.search(r'<title>(.*?)</title>', html)
    if title_match:
        print(f"   Page Title: {title_match.group(1)}")
        
    # Check for JSON data (RENDER_DATA or similar)
    # Often in <script id="RENDER_DATA" type="application/json">
    # Check for JSON data (RENDER_DATA or similar)
    if "window._ROUTER_DATA" in html:
        print("   FOUND _ROUTER_DATA!")
        idx = html.find("window._ROUTER_DATA")
        print(f"   Context: {html[idx:idx+200]}")
        
        try:
            # Extract the JSON string - handle newlines with re.DOTALL and optional semicolon
            json_match = re.search(r'window\._ROUTER_DATA\s*=\s*(\{.+?\});', html, re.DOTALL)
            if not json_match:
                 # Try without semicolon
                 json_match = re.search(r'window\._ROUTER_DATA\s*=\s*(\{.+?\})\s*</script>', html, re.DOTALL)

            if json_match:
                json_str = json_match.group(1)
                # Remove trailing semicolon if captured
                if json_str.endswith(';'): json_str = json_str[:-1]
                
                print(f"   Captured JSON Length: {len(json_str)}")
                data = json.loads(json_str)
                
                loader_data = data.get('loaderData', {})
                print(f"   Loader Keys: {list(loader_data.keys())}")
                
                # Find key like "video_(id)/page"
                # It might be unicode encoded in the HTML source key but json.loads decoded it?
                # We simply search for a key containing 'video_' and 'page'
                video_key = next((k for k in loader_data.keys() if 'video_' in k and 'page' in k), None)
                
                if video_key:
                    print(f"   Found Video Key: {video_key}")
                    # Path: key -> videoInfoRes -> item_list -> [0]
                    video_info_res = loader_data[video_key].get('videoInfoRes', {})
                    item_list = video_info_res.get('item_list', [])
                    
                    if item_list:
                        video_info = item_list[0]
                        print("\n   --- EXTRACTED DATA ---")
                        print(f"   Title: {video_info.get('desc')}")
                        print(f"   Create Time: {video_info.get('create_time')}")
                        
                        stats = video_info.get('statistics', {})
                        print(f"   Plays: {stats.get('play_count')}")
                        print(f"   Likes: {stats.get('digg_count')}")
                        
                        author = video_info.get('author', {})
                        print(f"   Author: {author.get('nickname')}")
                        print(f"   Fans: {author.get('follower_count')}")
                        
                        video = video_info.get('video', {})
                        cover = video.get('cover', {}).get('url_list', [''])[0]
                        print(f"   Cover: {cover}")
                    else:
                        print("   item_list is empty!")
                else:
                    print("   Could not find video key in loaderData!")

        except Exception as e:
            print(f"   JSON Parse Error: {e}")

except Exception as e:
    print(f"Error: {e}")

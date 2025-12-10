import requests
import time
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get SESSDATA from env (Secure)
SESSDATA = os.getenv("SESSDATA", "")
# Fallback for open source usage: If no SESSDATA, use empty/dummy (but warn user)
if not SESSDATA:
    print("WARNING: No SESSDATA found in environment. Some features may be rate limited.")

COOKIE_STR = f"buvid3=infoc; SESSDATA={SESSDATA};"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
    "Origin": "https://www.bilibili.com",
    "Cookie": COOKIE_STR
}

import re

def clean_text(text):
    """Remove HTML tags like <em class="keyword">."""
    if not text:
        return ""
    return re.sub(r'<[^>]+>', '', text)

def search_raw_videos(keyword, limit=50):
    """Search Bilibili for videos to aggregate creators."""
    url = "https://api.bilibili.com/x/web-interface/search/type"
    params = {
        "keyword": keyword,
        "search_type": "video",
        "order": "totalrank", # Use 'totalrank' for better relevance/recency balance
        "page": 1,
        "page_size": limit
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code != 200:
            print(f"API Request Failed: {response.status_code}")
            return []
            
        data = response.json()
        if data['code'] == 0:
            return data['data']['result']
        else:
            print(f"Search API Error: {data['message']}")
            return []
    except Exception as e:
        print(f"Search failed: {e}")
        return []

def get_creator_info(mid):
    """Get detailed user info for a specific creator."""
    return get_user_card(mid)


def get_user_stats(mid):
    """Get user stats (fans) using the more robust relation API."""
    url = "https://api.bilibili.com/x/relation/stat"
    params = {"vmid": mid}
    try:
        # This API is much more lenient and often works without cookies
        response = requests.get(url, headers=HEADERS, params=params)
        data = response.json()
        if data['code'] == 0:
            return data['data'] # Contains 'follower'
    except Exception as e:
        print(f"Stats failed: {e}")
    return None

def get_user_card(mid):
    """Get basic user info (fans, intro)."""
    # ... legacy function, heavily rate limited ...
    url = "https://api.bilibili.com/x/web-interface/card"
    params = {"mid": mid}
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        data = response.json()
        if data['code'] == 0:
            card = data['data']['card']
            return {
                "mid": mid,
                "name": card['name'],
                "fans": card['fans'],
                "sign": card['sign'],
                "avatar": card['face'],
                # "level": data['data']['card'].get('level_info', {}).get('current_level', 0)
            }
        return None
    except Exception as e:
        print(f"Get User Card failed: {e}")
        return None

def get_space_feed_videos(mid, limit=10):
    """Fallback: Get user videos via 'feed/space' (Dynamic) endpoint."""
    url = "https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space"
    params = {
        "host_mid": mid,
        "offset": "",
        "timezone_offset": -480
    }
    
    try:
        print(f"Requesting Feed Fallback for {mid}...")
        response = requests.get(url, headers=HEADERS, params=params)
        data = response.json()
        
        if data['code'] == 0 and 'items' in data['data']:
            items = data['data']['items']
            processed = []
            for item in items:
                if item['type'] == "DYNAMIC_TYPE_AV": # Only Video types
                    module_dynamic = item['modules']['module_dynamic']['major']['archive']
                    pub_ts = item['modules']['module_author']['pub_ts']
                    processed.append({
                        "bvid": module_dynamic['bvid'],
                        "title": clean_text(module_dynamic['title']),
                        "play": int(module_dynamic['stat']['play']),
                        "created": pub_ts,
                        "pic": module_dynamic['cover'],
                        "length": module_dynamic['duration_text'] # Text format "01:23"
                    })
            # Feed might yield mixed results, but it's better than nothing
            return processed[:limit]
        return []
    except Exception as e:
        print(f"Feed Fallback failed: {e}")
        return []

def get_recent_videos(mid, limit=5):
    """Get recent videos using Search API -> Feed Fallback."""
    url = "https://api.bilibili.com/x/space/arc/search"
    params = {
        "mid": mid,
        "ps": limit,
        "tid": 0,
        "pn": 1,
        "order": "pubdate",
        "jsonp": "jsonp"
    }
    
def get_search_videos_fallback(mid, limit=10):
    """Ultimate Fallback: Search for videos by creator name."""
    try:
        # 1. We need the creator's name first
        card = get_user_card(mid)
        if not card: return []
        name = card['name']
        
        print(f"Trying Search Fallback for {name} (mid={mid})...")
        url = "https://api.bilibili.com/x/web-interface/search/type"
        params = {
            "keyword": name,
            "search_type": "video",
            "order": "pubdate",
            "page": 1,
            "page_size": 20
        }
        res = requests.get(url, headers=HEADERS, params=params)
        data = res.json()
        
        if data['code'] == 0:
            result = data['data'].get('result', [])
            processed = []
            for item in result:
                # IMPORTANT: Filter by MID to ensure we don't get other people's videos
                if item['mid'] == mid:
                    processed.append({
                        "bvid": item['bvid'],
                        "title": clean_text(item['title']),
                        "play": item['play'], # Search API returns Int or Str? usually Int
                        "created": item['pubdate'],
                        "pic": "https:" + item['pic'] if item['pic'].startswith("//") else item['pic'],
                        "length": item['duration']
                    })
            return processed[:limit]
        return []
    except Exception as e:
        print(f"Search Fallback Failed: {e}")
        return []

def get_recent_videos(mid, limit=5):
    """Get recent videos using Search API -> Feed Fallback -> Name Search Fallback."""
    url = "https://api.bilibili.com/x/space/arc/search"
    params = {
        "mid": mid,
        "ps": limit,
        "tid": 0,
        "pn": 1,
        "order": "pubdate",
        "jsonp": "jsonp"
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        data = response.json()
        if data['code'] == 0:
            vlist = data['data']['list']['vlist']
            processed_videos = []
            for v in vlist:
                processed_videos.append({
                    "bvid": v['bvid'],
                    "title": clean_text(v['title']),
                    "play": v['play'],
                    "created": v['created'],
                    "pic": v['pic'],
                    "length": v['length']
                })
            return processed_videos
        else:
            print(f"Space Search API Error (Code {data['code']}): {data.get('message')}")
    except Exception as e:
        print(f"Get Recent Videos Exception: {e}")

    # Fallback 1: Feed
    print(f"Trying Feed fallback for mid={mid}...")
    feed_res = get_space_feed_videos(mid, limit)
    if feed_res: return feed_res
    
    # Fallback 2: Search by Name
    print(f"Trying Search fallback for mid={mid}...")
    return get_search_videos_fallback(mid, limit)

def get_video_comments(bvid):
    """Fetch top comments for a video."""
    # First get AID
    try:
        view_url = "https://api.bilibili.com/x/web-interface/view"
        res = requests.get(view_url, params={"bvid": bvid}, headers=HEADERS)
        data = res.json()
        if data['code'] != 0: return []
        aid = data['data']['aid']
        
        # Get Replies
        # type=1 (video), sort=1 (hot)
        reply_url = "https://api.bilibili.com/x/v2/reply"
        params = {"type": 1, "oid": aid, "sort": 1, "ps": 20}
        res = requests.get(reply_url, params=params, headers=HEADERS)
        data = res.json()
        
        comments = []
        if data['code'] == 0:
            replies = data['data'].get('replies', [])
            if replies:
                for r in replies:
                    content = r['content']['message']
                    like = r['like']
                    comments.append(f"[{like} likes] {content}")
        return comments
    except Exception as e:
        print(f"Fetch Comments Error: {e}")
        return []

def get_video_subtitles(bvid):
    """
    Robust Subtitle Fetcher:
    1. Try 'web-interface/view' (CC)
    2. Try 'player/v2' (CC) - often needs Wbi
    3. Return None if truly missing
    """
    print(f"Using Robust Fetcher for {bvid}")
    
    # 1. Standard View API
    url = "https://api.bilibili.com/x/web-interface/view"
    params = {"bvid": bvid}
    
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        data = response.json()
        if data['code'] != 0: return f"Metadata Error: {data['message']}"
        
        data_data = data['data']
        # Try finding subtitle
        subtitle_data = data_data.get('subtitle', {})
        subtitle_list = subtitle_data.get('list', [])
        
        if subtitle_list:
             sub_url = subtitle_list[0].get('url')
             if sub_url.startswith('//'): sub_url = 'https:' + sub_url
             res = requests.get(sub_url, headers=HEADERS)
             if res.status_code == 200:
                 sub_json = res.json()
                 body = sub_json.get('body', [])
                 return " ".join([line.get('content', '') for line in body])
        
        # If no CC, fallback to description
        print(f"No CC found (or error). Using Title/Desc fallback.")
        # Return a clean formatted string for the UI/Prompt
        title = data_data.get('title', '')
        desc = data_data.get('desc', '')
        return f"【视频内容】\n标题：{clean_text(title)}\n\n简介：{desc[:500]}..."

    except Exception as e:
        return f"Fetch Error: {e}"

def calculate_stats(videos):
    """Calculate avg views and frequency."""
    if not videos:
        # Debug why no videos
        print("DEBUG: No videos to calculate stats.")
        return {"avg_views_5": 0, "weekly_freq": 0}
    
    # Avg views of last 5
    last_5 = videos[:5]
    total_views = sum(v['play'] for v in last_5)
    avg_views = total_views / len(last_5) if last_5 else 0
    
    # Weekly frequency
    if len(videos) < 2:
        weekly_freq = 1 # Assume at least 1 if lists exists
    else:
        subset = videos[:5] # Look at recent behavior
        first = subset[0]['created']
        last = subset[-1]['created']
        days = (first - last) / (24 * 3600)
        if days > 0:
            weekly_freq = round((len(subset) / days) * 7, 1)
        else:
            weekly_freq = len(subset)

    return {
        "avg_views_5": int(avg_views),
        "weekly_freq": weekly_freq
    }

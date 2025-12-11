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
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
    "Origin": "https://www.bilibili.com",
    "Cookie": COOKIE_STR,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
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
    """Get detailed user info for a specific creator (Robust)."""
    return get_user_info_robust(mid)


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

def get_user_info_via_search(mid):
    """
    Fallback: Get user info by searching for their MID.
    This often bypasses the -352 Risk Check on direct profile lookup.
    """
    url = "https://api.bilibili.com/x/web-interface/search/type"
    params = {
        "keyword": str(mid),
        "search_type": "bili_user",
        "page": 1,
        "page_size": 1
    }
    try:
        res = requests.get(url, headers=HEADERS, params=params)
        data = res.json()
        print(f"DEBUG SEARCH: Code={data.get('code')}, Data={str(data.get('data'))[:100]}")
        if data['code'] == 0:
            results = data['data'].get('result', [])
            if results:
                # The first result should be the user if searching by MID
                # Verify MID to be safe
                user = results[0]
                # print(f"DEBUG SEARCH: Found user mid={user['mid']}")
                if str(user['mid']) == str(mid):
                    return {
                        "mid": mid,
                        "name": user['uname'],
                        "fans": user['fans'], # formatting might be needed? Usually int or str
                        "sign": user['usign'],
                        "avatar": "https:" + user['upic'] if user['upic'].startswith("//") else user['upic']
                    }
                else:
                    print(f"DEBUG SEARCH: Mismatch MID {user['mid']} != {mid}")
            else:
                 print("DEBUG SEARCH: No results found.")
        else:
            print(f"DEBUG SEARCH: API Error {data['message']}")
    except Exception as e:
        print(f"Search User Info Fallback Failed: {e}")

    # Fallback 2: Search for Video (to extract author)
    # This is useful if the user is hidden from 'bili_user' search but has videos.
    try:
        print(f"Trying Video Search Fallback for {mid}...")
        video_params = {
            "keyword": str(mid),
            "search_type": "video",
            "page": 1
        }
        res = requests.get(url, headers=HEADERS, params=video_params)
        data = res.json()
        print(f"DEBUG VIDEO SEARCH: Code={data.get('code')}")
        if data['code'] == 0:
            results = data['data'].get('result', [])
            print(f"DEBUG VIDEO SEARCH: Found {len(results)} results.")
            if results:
                # Use the first video's author info
                v = results[0]
                print(f"DEBUG VIDEO SEARCH: First result mid={v.get('mid')}, author={v.get('author')}")
                
                # 'mid' in video result should match
                # Relaxed check: If mid matches OR if author is '账号已注销' (Account Deleted)
                msg_mid = str(v.get('mid'))
                if msg_mid == str(mid) or v.get('author') == '账号已注销':
                    print(f"DEBUG VIDEO SEARCH: Match! Returning info.")
                    return {
                        "mid": mid,
                        "name": v['author'], # or v['uname']
                        "fans": 0, # Video search doesn't give fans
                        "sign": "Found via Video Search",
                        "avatar": "https:" + v['upic'] if v['upic'].startswith("//") else v['upic']
                    }
                else:
                    print(f"DEBUG VIDEO SEARCH: Mismatch MID {msg_mid} != {mid}")
    except Exception as e:
        print(f"Search Video Fallback Failed: {e}")

    return None

def get_user_info_robust(mid):
    """
    Robust User Info Fetcher:
    1. Try standard `get_user_card`
    2. Try `get_space_feed_videos` (extract author info)
    3. Try `get_user_stats` (fans only) and return minimal info
    """
    # 1. Standard
    card = get_user_card(mid)
    if card: return card
    
    print(f"Card API failed for {mid}. Trying robust fallback...")
    
    # 2. Priority Fallback: Search (Most reliable when blocked)
    print(f"Trying Search Fallback for user info {mid}...")
    search_info = get_user_info_via_search(mid)
    if search_info:
        return search_info

    # 3. Feed Fallback (Extract name/avatar from video items)
    # We ask for limit=1 just to get the author module
    feed_items = get_space_feed_videos(mid, limit=1)
    
    if feed_items:
        # Note: get_space_feed_videos returns simplified list. 
        # But we need the RAW response to get author info properly if we didn't save it.
        # WAIT: get_space_feed_videos returns processed "processed" list.
        # We need to hack it OR fetch again? 
        # Actually, get_space_feed_videos helper in this file filters everything out.
        # Let's write a targeted "get_feed_author" helper or just inline the request here for robustness.
        pass

    # Let's do a raw request here to be sure
    url = "https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space"
    params = {"host_mid": mid, "timezone_offset": -480}
    
    name = "Unknown"
    avatar = "https://via.placeholder.com/80"
    sign = "Profile Unavailable (Rate Limit)"
    
    # Try Acc Info Fallback first (often better than feed)
    try:
        acc_url = "https://api.bilibili.com/x/space/wbi/acc/info"
        acc_res = requests.get(acc_url, headers=HEADERS, params={"mid": mid})
        acc_data = acc_res.json()
        if acc_data['code'] == 0:
            info = acc_data['data']
            return {
                "mid": mid,
                "name": info['name'],
                "fans": get_user_stats(mid)['follower'] if get_user_stats(mid) else 0, # Acc info doesn't have fans, need stats
                "sign": info['sign'],
                "avatar": info['face']
            }
    except Exception as e:
        print(f"Acc Info Fallback failed: {e}")



    try:
        res = requests.get(url, headers=HEADERS, params=params)
        data = res.json()
        if data['code'] == 0 and 'items' in data['data']:
            items = data['data']['items']
            for item in items:
                # Try to find author module
                if 'modules' in item and 'module_author' in item['modules']:
                    author = item['modules']['module_author']
                    name = author.get('name', name)
                    avatar = author.get('face', avatar)
                    # sign isn't usually in feed author module, but that's fine
                    break
    except Exception as e:
        print(f"Feed Author Fallback failed: {e}")
        
    # 3. Fans Fallback
    stats = get_user_stats(mid)
    fans = stats['follower'] if stats else 0
    
    # If we still have "Unknown" name, we might be truly blocked or ID invalid.
    # But return what we have.
    return {
        "mid": mid,
        "name": name,
        "fans": fans,
        "sign": sign,
        "avatar": avatar
    }

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

                    play_str = module_dynamic['stat']['play']
                    play_count = 0
                    try:
                        if '万' in str(play_str):
                            play_count = int(float(play_str.replace('万', '')) * 10000)
                        elif '亿' in str(play_str):
                            play_count = int(float(play_str.replace('亿', '')) * 100000000)
                        else:
                            play_count = int(play_str)
                    except:
                        play_count = 0

                    processed.append({
                        "bvid": module_dynamic['bvid'],
                        "title": clean_text(module_dynamic['title']),
                        "play": play_count,
                        "created": int(pub_ts),
                        "pic": module_dynamic['cover'],
                        "length": module_dynamic['duration_text'] # Text format "01:23"
                    })
            # Feed might yield mixed results, but it's better than nothing
            return processed[:limit]
        return []
    except Exception as e:
        print(f"Feed Fallback failed: {e}")
        return []


    
def get_search_videos_fallback(mid, limit=10, known_name=None):
    """Ultimate Fallback: Search for videos by creator name."""
    try:
        # 1. We need the creator's name first
        if known_name:
            name = known_name
        else:
            card = get_user_card(mid)
            if not card: return []
            name = card['name']
            
        if not name or name in ["Unknown", "Unknown User"]:
            print(f"Skipping Search Fallback for invalid name: {name}")
            return []
        
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
                        "created": int(item['pubdate']),
                        # Force HTTPS for clarity and referrer handling
                        "pic": item['pic'].replace("http://", "https://") if item['pic'].startswith("http") else ("https:" + item['pic'] if item['pic'].startswith("//") else item['pic']),
                        "length": item['duration']
                    })
            return processed[:limit]
        return []
    except Exception as e:
        print(f"Search Fallback Failed: {e}")
        return []

def get_recent_videos(mid, limit=5, known_name=None):
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
                    "created": int(v['created']),
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
    return get_search_videos_fallback(mid, limit, known_name=known_name)

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
        first = int(subset[0]['created'])
        last = int(subset[-1]['created'])
        days = (first - last) / (24 * 3600)
        if days > 0:
            weekly_freq = round((len(subset) / days) * 7, 1)
        else:
            weekly_freq = len(subset)

    return {
        "avg_views_5": int(avg_views),
        "weekly_freq": weekly_freq
    }

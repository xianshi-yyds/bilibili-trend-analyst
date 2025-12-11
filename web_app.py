from fastapi import FastAPI, Request, Form, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
import uvicorn
import sys
import os
import asyncio
import requests
import io
from pathlib import Path
from platforms.bilibili import BilibiliPlatform
from platforms.douyin import DouyinPlatform
from mcp_client import MCPConnector
from cookie_manager import fetch_douyin_cookies
from analyzer import generate_analysis_prompt
from market_analyzer import generate_market_report

# 计算根路径，避免从其他目录启动时找不到静态/模板文件
BASE_DIR = Path(__file__).parent
static_dir = BASE_DIR / "static"
if not static_dir.exists():
    # 当前项目未提供 static 目录，回退到 assets 以保证 FastAPI 正常启动
    static_dir = BASE_DIR / "assets"

app = FastAPI()
app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Initialize Platform
# Initialize Platform
bili = BilibiliPlatform()
douyin = DouyinPlatform()

@app.on_event("startup")
async def startup_event():
    # Auto-fetch Douyin Cookies if not provided
    if not os.getenv("DOUYIN_COOKIE"):
        # FALLBACK: Check for local cookie text file (from user manual input via UI or upload)
        cookie_file = Path("douyin_cookie.txt")
        if cookie_file.exists():
            print(">> Found local 'douyin_cookie.txt'. Using it.")
            with open(cookie_file, "r") as f:
                cookies = f.read().strip()
            douyin.update_cookies(cookies)
        else:
            print(">> No DOUYIN_COOKIE env or local file. Attempting automatic fetch...")
            cookies = await fetch_douyin_cookies()
            if cookies:
                douyin.update_cookies(cookies)
            else:
                print(">> Failed to auto-fetch cookies. Douyin search may be limited.")
    else:
        print(">> DOUYIN_COOKIE present in env.")

# --- IMAGE PROXY ---
@app.get("/img_proxy")
async def img_proxy(url: str = Query(..., description="Target Image URL")):
    """Proxies images to bypass Bilibili Referer blocks."""
    if not url or url == "None":
         # Return a transparent 1x1 pixel or 404
         return StreamingResponse(io.BytesIO(b""), media_type="image/png")
    
    try:
        # Request with browser headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.bilibili.com/" 
        }
        # Use stream=True to save memory
        r = requests.get(url, headers=headers, stream=True, timeout=5)
        return StreamingResponse(r.raw, media_type=r.headers.get("content-type", "image/jpeg"))
    except Exception as e:
        print(f"Proxy Error: {e}")
        return StreamingResponse(io.BytesIO(b""), media_type="image/png")

# Robust Placeholder (Data URI)
PLACEHOLDER_IMG = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2MDAiIGhlaWdodD0iNDAwIiB2aWV3Qm94PSIwIDAgNjAwIDQwMCI+CiAgPHJlY3Qgd2lkdGg9IjYwMCIgaGVpZ2h0PSI0MDAiIGZpbGw9IiMxZTFlMWUiIC8+CiAgPHRleHQgeD0iNTAlIiB5PSI1MCUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjI0IiBmaWxsPSIjZmZmZmZmIj5JbWFnZSBVbmF2YWlsYWJsZTwvdGV4dD4KPC9zdmc+"

def format_fans(fans):
    if not fans: return "0"
    if isinstance(fans, str) and 'w' in fans: return fans
    try:
        f = int(fans)
        if f >= 10000: return f"{f/10000:.1f}w"
        return str(f)
    except:
        return str(fans)

import datetime # Fix UnboundLocalError by importing at top level

MCP_SERVER_URL = "https://mcp.api-inference.modelscope.net/360783e5932148/mcp"

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

from typing import Optional
@app.get("/creator/{mid}", response_class=HTMLResponse)
@app.get("/creator/{mid}", response_class=HTMLResponse)
async def creator_detail(request: Request, mid: str, name: Optional[str] = None, avatar: Optional[str] = None, platform: str = "bilibili"):
    # 1. Get User Info (Robust)
    api = douyin if platform == "douyin" else bili
    user_card = api.get_user_info(mid)
    
    warning = None
    if not user_card or user_card['name'] == "Unknown":
        warning = "API 请求受限 (Rate Limited)。部分数据无法显示。建议稍后再试。"
        # Fallback if params provided
        if name:
            user_card = {
                "mid": mid,
                "name": name,
                "fans": "未知",
                "sign": "API Limit - Fallback Mode",
                "avatar": avatar or "https://via.placeholder.com/80"
            }
        elif not user_card:
             # Minimal dummy
             user_card = {
                "mid": mid,
                "name": "Unknown User",
                "fans": 0,
                "sign": "Data unavailable due to API limits",
                "avatar": "https://via.placeholder.com/80"
             }

    # 2. Get Recent Videos
    # Pass known name to help searching if needed
    # Pass known name to help searching if needed
    known_name = name or (user_card.get('name') if user_card else None)
    raw_videos = api.get_recent_posts(mid, limit=20) #, known_name=known_name) - Douyin might not need known_name fallback logic yet
    try:
        if platform == 'bilibili':
             raw_videos = api.get_recent_videos(mid, limit=20, known_name=known_name)
    except: pass
    
    videos_10 = raw_videos[:10] if raw_videos else []
    
    # 3. Calculate Stats
    if videos_10:
        plays = [v['play'] for v in videos_10]
        max_play = max(plays) if plays else 1
        avg_play = int(sum(plays) / len(plays)) if plays else 0
        if platform == 'bilibili':
             stats = bili.calculate_stats(videos_10)
        else:
             # Basic stats for Douyin
             stats = {"weekly_freq": 1, "avg_views_5": avg_play}
    else:
        plays = []
        max_play = 0
        avg_play = 0
        stats = {"weekly_freq": 0}
        if not warning:
             warning = "未找到最近视频，可能是 API 限制或博主无公开视频。"
    
    # Process for Template
    processed_videos = []

    for v in videos_10:
        dt = datetime.datetime.fromtimestamp(v['created'])
        processed_videos.append({
            "bvid": v['bvid'],
            "title": v['title'],
            "play": v['play'],
            "play_percent": int((v['play'] / max_play) * 100) if max_play > 0 else 0,
            "length": v['length'],
            "date": dt.strftime("%Y-%m-%d")
        })
        
    # Map 'avatar' to 'face' for template compatibility if needed
    # But template uses {{ user.face }}?
    # get_user_card returns 'avatar'. 
    # Let's standardize on 'face' for template or change template.
    # Changing template to accept 'avatar' (standard in this app) is better but current template has 'face'.
    # Let's fix the user object to have 'face' = 'avatar'
    user_card['face'] = user_card.get('avatar', user_card.get('face', ''))
    if user_card['face'] and user_card['face'].startswith('//'):
        user_card['face'] = 'https:' + user_card['face']
    user_card['fans'] = format_fans(user_card['fans'])

    return templates.TemplateResponse("creator.html", {
        "request": request,
        "user": user_card,
        "videos": processed_videos,
        "avg_views": avg_play,
        "max_views": max_play,
        "weekly_freq": stats.get('weekly_freq', 0),
        "warning": warning,
        "platform": platform
    })

@app.post("/analyze", response_class=HTMLResponse)
async def analyze_track(request: Request, track: str = Form(...), platform_input: str = Form("bilibili")):
    track = track.strip()
    print(f"Analyzing input: {track} on {platform_input}")
    
    api = douyin if platform_input == "douyin" else bili
    analyzed_creators = []
    
    # --- QUERY TYPE DETECTION (Quick Hack for Bilibili Video Links) ---
    # TODO: abstract this into api.detect_query_type(track)
    is_video_url = False
    if platform_input == "bilibili" and ("bilibili.com/video/BV" in track or track.startswith("BV")):
        is_video_url = True
    elif platform_input == "douyin" and "douyin.com/video/" in track:
        # TODO: Douyin Video Link Analysis
        pass 

    if is_video_url and platform_input == "bilibili":
        print("  > Detected Single Video Analysis")
        # Extract BVID
        import re
        bvid_match = re.search(r'(BV\w+)', track)
        if not bvid_match:
            return templates.TemplateResponse("index.html", {"request": request, "error": "Invalid BVID/URL"})
        bvid = bvid_match.group(1)
        
        # Helper to get video info (Should be in API)
        # Using raw request for now to reuse legacy logic quickly, or strictly use API
        # Let's use the API if possible, but BilibiliPlatform.get_post_detail returns simplified dict.
        # We need extensive info for the single video view.
        # For now, let's keep the legacy logic for Bilibili Video Analysis but routed cleanly.
        
        import requests
        res = requests.get("https://api.bilibili.com/x/web-interface/view", params={"bvid": bvid}, headers=bili.headers)
        if res.status_code == 200:
            vdata = res.json().get('data', {})
            mid = vdata.get('owner', {}).get('mid')
            if mid:
                 user_card = bili.get_user_info(mid)
                 recent_videos = [{
                    "bvid": vdata['bvid'],
                    "title": bili.clean_text(vdata['title']),
                    "play": vdata['stat']['view'],
                    "created": vdata['pubdate'],
                    "pic": vdata['pic'],
                    "length": vdata['duration']
                 }]
                 user_stats = bili.calculate_stats(recent_videos)
                 latest_video = recent_videos[0]
                 latest_date_str = datetime.datetime.fromtimestamp(latest_video['created']).strftime("%Y-%m-%d") if latest_video['created'] else "N/A"
                 
                 content_context = bili.get_video_subtitles(latest_video['bvid']) or "No content available"
                 comments = bili.get_video_comments(latest_video['bvid'])
                 comments_str = "\n".join(comments[:5])
                 analysis_prompt = f"【内容摘要】{content_context[:120]}...\n\n【观众热评】\n{comments_str}"
                 
                 item = {
                    "mid": mid,
                    "author": user_card['name'] if user_card else "Unknown Author",
                    "avatar": user_card['avatar'] if user_card else "https://via.placeholder.com/80",
                    "fans": format_fans(user_card['fans']) if user_card else 0,
                    "intro": user_card['sign'] if user_card else "Info unavailable",
                    "latest_date": latest_date_str,
                    "weekly_freq": user_stats['weekly_freq'],
                    "avg_views": user_stats['avg_views_5'],
                    "latest_video_title": latest_video['title'],
                    "latest_video_cover": latest_video['pic'],
                    "latest_video_url": f"https://www.bilibili.com/video/{latest_video['bvid']}",
                    "analysis_prompt": analysis_prompt,
                    "subtitles_snippet": content_context[:200] + "...",
                    "comments_snippet": comments_str
                 }
                 analyzed_creators.append(item)
                 
        return templates.TemplateResponse("results.html", {"request": request, "track": f"Video: {bvid}", "results": analyzed_creators, "platform": platform_input})

    # --- NORMAL TRACK SEARCH ---
    print("  > Detected Track Search")

    # 1. Search Users/Creators (Generic)
    print(f"  > Searching {platform_input} for: {track}")
    candidates = api.search_users(track) # Returns list of user dicts
    print(f"  > Found {len(candidates)} potential candidates.")
    # DEBUG DIAGNOSTICS
    print(f"DEBUG: API Instance: {api}")
    if hasattr(api, 'sessdata'):
        print(f"DEBUG: API Sessdata len: {len(api.sessdata)}")
    else:
        print("DEBUG: API has no sessdata attr")
    
    print(f"  > Processing {len(candidates)} raw results...")

    seen_mids = set()
    # Phase 1: Collect Candidates & Basic filtering
    for user in candidates:
        mid = str(user['mid'])
        if mid in seen_mids: continue
        seen_mids.add(mid)
        
        # For Douyin, we got decent info from search. For Bilibili search_raw_videos returned videos, not users.
        # BilibiliPlatform.search_users returns video results. We need to adapt it?
        # WAIT: BilibiliPlatform.search_users returns raw_videos list!
        # This is an Interface mismatch. 'search_users' should return USERS.
        # DouyinPlatform.search_users returns USERS.
        # I need to fix BilibiliPlatform.search_users to return USERS or handle the difference here.
        # To minimize disruption on this step, I will handle the difference:
        
        if platform_input == 'bilibili':
            # 'user' is actually a video dict here
            # We need to fetch the user card
             real_mid = user['mid']
             user_card = bili.get_user_info(real_mid)
             if not user_card: continue
        else:
             # Douyin: 'user' is already a user dict
             real_mid = mid
             user_card = user # Already has name, avatar, etc.

        # 2. Get Recent Posts
        clean_name = user_card.get('name')
        print(f"  > Analyzing Candidate: {clean_name} ({real_mid})")

        recent_posts = api.get_recent_posts(real_mid, limit=10)
        
        # Fallback Check
        if not recent_posts:
             print(f"    - Skipped: No recent posts found.")
             continue
             
        # 3. Relevance/Stats/Filtering
        # (Simplified filtering for now to ensure Douyin works)
        
        # Stats
        if platform_input == 'bilibili':
             user_stats = bili.calculate_stats(recent_posts)
        else:
             # Basic Douyin stats
             plays = [p['play'] for p in recent_posts]
             avg_play = int(sum(plays)/len(plays)) if plays else 0
             user_stats = {"weekly_freq": 1, "avg_views_5": avg_play} # TODO: Real stats
        
        # Prepare Item
        latest_post = recent_posts[0]
        latest_date_str = "N/A"
        if latest_post.get('created'):
             # Handle TS vs ISO string if needed. Bili is TS. Douyin is TS.
             try:
                 dt = datetime.datetime.fromtimestamp(int(latest_post['created']))
                 latest_date_str = dt.strftime("%Y-%m-%d")
             except: pass

        # Content/Comments
        # Douyin details are hard to get without specific API, use defaults
        detail = api.get_post_detail(latest_post['bvid']) # bvid is aweme_id
        content_context = detail.get('subtitles', '') if detail else ""
        comments_str = "\n".join(detail.get('comments', [])) if detail else ""
        
        analysis_prompt = f"【内容摘要】{content_context[:120]}...\n\n【观众热评】\n{comments_str}"

        # Fans formatting
        raw_fans = user_card.get('fans', 0)
        # Handle 'N/A' from Douyin Search
        fans_display = format_fans(raw_fans) if raw_fans != "N/A" else "未知"

        # Avatar Proxy
        avatar_url = user_card.get('avatar', "")
        if platform_input == 'bilibili':
             # Ensure HTTPS if missing (though API usually provides it)
             if avatar_url and avatar_url.startswith('//'):
                  avatar_url = 'https:' + avatar_url
        
        cover_url = latest_post.get('pic', "")
        if platform_input == 'bilibili' and cover_url and cover_url.startswith('//'):
             cover_url = 'https:' + cover_url

        item = {
            "mid": real_mid,
            "author": user_card['name'],
            "avatar": avatar_url or PLACEHOLDER_IMG,
            "fans": fans_display,
            "intro": user_card.get('sign', ''),
            "latest_date": latest_date_str,
            "weekly_freq": user_stats.get('weekly_freq', 0),
            "avg_views": user_stats.get('avg_views_5', 0),
            "latest_video_title": latest_post.get('title', ''),
            "latest_video_cover": cover_url or PLACEHOLDER_IMG,
            "latest_video_url": f"https://www.douyin.com/video/{latest_post['bvid']}" if platform_input == 'douyin' else f"https://www.bilibili.com/video/{latest_post['bvid']}",
            "analysis_prompt": analysis_prompt,
            "subtitles_snippet": content_context[:200] + "...",
            "comments_snippet": comments_str
        }
        analyzed_creators.append(item)

    # Sort
    analyzed_creators.sort(key=lambda x: x['avg_views'], reverse=True)
    
    # --- STEP 4: GENERATE MARKET REPORT ---
    try:
        if analyzed_creators:
            market_report = generate_market_report(analyzed_creators)
            # Inject analysis into creators for easy access in template
            if market_report and 'details' in market_report:
                for c in analyzed_creators:
                    c['market_analysis'] = market_report['details'].get(c['mid'], {})
        else:
             market_report = {}
    except Exception as e:
        print(f"Market Report Error: {e}")
        market_report = {}

    return templates.TemplateResponse("results.html", {
        "request": request, 
        "track": track, 
        "results": analyzed_creators,
        "market_report": market_report,
        "platform": platform_input
    })

if __name__ == "__main__":
    uvicorn.run("web_app:app", host="127.0.0.1", port=8000, reload=True)

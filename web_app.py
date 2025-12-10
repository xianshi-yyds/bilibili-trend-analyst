from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import asyncio
from bilibili_api import search_raw_videos, get_user_card, get_creator_info, get_recent_videos, get_user_stats, calculate_stats, clean_text, get_video_subtitles, get_video_comments
from mcp_client import MCPConnector
from analyzer import generate_analysis_prompt
from market_analyzer import generate_market_report

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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
async def creator_detail(request: Request, mid: int, name: Optional[str] = None, avatar: Optional[str] = None):
    # 1. Get User Info (Robust)
    user_card = get_creator_info(mid) # Helper now calls get_user_info_robust
    
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
    known_name = user_card.get('name') if user_card.get('name') != "Unknown User" else name
    raw_videos = get_recent_videos(mid, limit=20, known_name=known_name)
    videos_10 = raw_videos[:10]
    
    # 3. Calculate Stats
    if videos_10:
        plays = [v['play'] for v in videos_10]
        max_play = max(plays) if plays else 1
        avg_play = int(sum(plays) / len(plays)) if plays else 0
        stats = calculate_stats(videos_10)
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
    user_card['fans'] = format_fans(user_card['fans'])

    return templates.TemplateResponse("creator.html", {
        "request": request,
        "user": user_card,
        "videos": processed_videos,
        "avg_views": avg_play,
        "max_views": max_play,
        "weekly_freq": stats['weekly_freq'],
        "warning": warning
    })

@app.post("/analyze", response_class=HTMLResponse)
async def analyze_track(request: Request, track: str = Form(...)):
    track = track.strip()
    print(f"Analyzing input: {track}")
    
    mcp = MCPConnector(MCP_SERVER_URL)
    analyzed_creators = []
    
    # --- QUERY TYPE DETECTION ---
    is_video_url = "bilibili.com/video/BV" in track or track.startswith("BV")
    
    if is_video_url:
        print("  > Detected Single Video Analysis")
        # Extract BVID
        import re
        bvid_match = re.search(r'(BV\w+)', track)
        if not bvid_match:
            return templates.TemplateResponse("index.html", {"request": request, "error": "Invalid BVID/URL"})
        bvid = bvid_match.group(1)
        
        # Fetch Video Details directly
        # effectively treating this as a "Creator" list of size 1 for reuse of UI
        # OR render a specific page. Let's reuse UI but with 1 card.
        
        # We need 'mid' to get user card
        # get_video_subtitles(bvid) logic can be reused but we need 'view' data first
        import requests
        res = requests.get("https://api.bilibili.com/x/web-interface/view", params={"bvid": bvid}, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code == 200:
            vdata = res.json().get('data', {})
            mid = vdata.get('owner', {}).get('mid')
            if mid:
                 user_card = get_user_card(mid)
                 # Mock a "recent video" list containing just this one
                 recent_videos = [{
                    "bvid": vdata['bvid'],
                    "title": clean_text(vdata['title']),
                    "play": vdata['stat']['view'],
                    "created": vdata['pubdate'],
                    "pic": vdata['pic'],
                    "length": vdata['duration']
                 }]
                 # Calculate stats (will be just this video)
                 user_stats = calculate_stats(recent_videos)
                 
                 # Prepare Analysis
                 latest_video = recent_videos[0]
                 latest_date_str = "N/A"

                 if latest_video['created']:
                     latest_date_str = datetime.datetime.fromtimestamp(latest_video['created']).strftime("%Y-%m-%d")

                 content_context = get_video_subtitles(latest_video['bvid']) or "No content available"
                 subtitles_snippet = content_context[:200] + "..."
                 
                 comments = get_video_comments(latest_video['bvid'])
                 comments_str = "\n".join(comments[:5])
                 
                # Format for UI Display (Clean Summary)
                 analysis_prompt = f"【内容摘要】{content_context[:120]}...\n\n【观众热评】\n{comments_str}"
                 
                 item = {
                    "mid": mid, # ADDED MID
                    "author": user_card['name'],
                    "avatar": user_card['avatar'],
                    "fans": user_card['fans'],
                    "intro": user_card['sign'],
                    "latest_date": latest_date_str,
                    "weekly_freq": user_stats['weekly_freq'],
                    "avg_views": user_stats['avg_views_5'],
                    "latest_video_title": latest_video['title'],
                    "latest_video_cover": latest_video['pic'],
                    "latest_video_url": f"https://www.bilibili.com/video/{latest_video['bvid']}",
                    "analysis_prompt": analysis_prompt,
                    "subtitles_snippet": subtitles_snippet,
                    "comments_snippet": comments_str
                 }
                 analyzed_creators.append(item)
                 
        return templates.TemplateResponse("results.html", {"request": request, "track": f"Video: {bvid}", "results": analyzed_creators})

    # --- NORMAL TRACK SEARCH ---
    print("  > Detected Track Search")
    # --- NORMAL TRACK SEARCH ---
    print("  > Detected Track Search")
    
    # 1. Search Raw Videos (Fetch MORE to create a pool)
    limit_pool = 50 # Maximize fallback pool
    raw_videos = search_raw_videos(track, limit=limit_pool) 
    
    seen_mids = set()
    candidates = []

    print(f"  > Processing {len(raw_videos)} raw results...")

    # Phase 1: Collect Candidates & Basic filtering
    for video in raw_videos:
        mid = video['mid']
        if mid in seen_mids:
            continue
        seen_mids.add(mid)
        candidates.append(mid)
        if len(candidates) >= 20: # Limit efficient scanning to top 20 unique creators
            break
            
    analyzed_creators = []
    
    # Phase 2: Process Candidates
    for mid in candidates:
        if len(analyzed_creators) >= 10:
            break
            
        print(f"  > Analyzing Candidate: {mid}")
        
        # 1. Get User Info
        user_card = get_user_card(mid)
        if not user_card:
            continue
            
        # FILTER: Fan Count (Ignore very small creators < 500 fans for "Trend" analysis)
        if user_card['fans'] < 500:
             print(f"    - Skipped: Too few fans ({user_card['fans']})")
             continue

        # 2. Get Recent Videos
        recent_videos = get_recent_videos(mid, limit=10)
        
        # Fallback Check
        if not recent_videos:
             # Try to find the specific video from search results as fallback
             # (Simplified for candidate logic: if no recent vids, skip or minimal check)
             print(f"    - Skipped: No recent videos found")
             continue

        # --- RELEVANCE CHECK ---
        keywords = track.split()
        relevant_count = 0
        total_checked = len(recent_videos)
        
        if total_checked > 0:
            for rv in recent_videos:
                rv_title = rv['title'].lower()
                if any(k.lower() in rv_title for k in keywords):
                    relevant_count += 1
            
            is_relevant = False
            # Relaxed: Only require 1 match in recent history to confirm relevance.
            # (Strict >1 was killing valid creators who use variation in titles)
            if relevant_count >= 1: 
                is_relevant = True
            
            if not is_relevant:
                print(f"    - Skipped: Low Content Relevance ({relevant_count}/{total_checked})")
                # SOFT FALLBACK: If we are starving for results, valid search candidates might be saved later.
                continue

        # --- RECENCY CHECK (Latest video) ---
        import time
        latest_video = recent_videos[0]
        if latest_video['created'] < (time.time() - 180 * 86400):
             print(f"    - Skipped: Inactive (Latest video > 180 days)")
             continue

        # Valid Creator! Calculate Stats
        user_stats = calculate_stats(recent_videos)
        
        # Prepare Analysis Data
        latest_date_str = "N/A"
        if latest_video['created']:
             dt = datetime.datetime.fromtimestamp(latest_video['created'])
             latest_date_str = dt.strftime("%Y-%m-%d")

        # Fetch Content/Comments
        content_context = get_video_subtitles(latest_video['bvid']) or "No content available"
        subtitles_snippet = content_context[:200] + "..."
        comments = get_video_comments(latest_video['bvid'])
        comments_str = "\n".join(comments[:5])

        # Format for UI Display (Clean Summary)
        analysis_prompt = f"【内容摘要】{content_context[:120]}...\n\n【观众热评】\n{comments_str}"

        # Helper for fan formatting
        raw_fans = user_card['fans']
        if raw_fans >= 10000:
            fans_str = f"{raw_fans/10000:.1f}w"
        else:
            fans_str = str(raw_fans)

        item = {
            "mid": mid,
            "author": user_card['name'],
            "avatar": user_card['avatar'],
            "fans": fans_str, # Use formatted string
            "intro": user_card['sign'],
            "latest_date": latest_date_str,
            "weekly_freq": user_stats['weekly_freq'],
            "avg_views": user_stats['avg_views_5'],
            "latest_video_title": latest_video['title'],
            "latest_video_cover": latest_video['pic'],
            "latest_video_url": f"https://www.bilibili.com/video/{latest_video['bvid']}",
            "analysis_prompt": analysis_prompt,
            "subtitles_snippet": subtitles_snippet,
            "comments_snippet": comments_str
        }
        analyzed_creators.append(item)

    # Phase 3: Sort by Quality (Avg Views)
    analyzed_creators.sort(key=lambda x: x['avg_views'], reverse=True)
    
    # EMERGENCY FALLBACK: If filtering killed everyone, show at least the search results
    if not analyzed_creators and raw_videos:
        print("  > WARNING: Strict filters blocked all candidates. Enforcing Fallback Mode.")
        # Just process the top 12 items ensuring we show SOMETHING
        
        # We need to map raw_videos back to a usable format.
        # Since raw_videos is a list of dicts, we can iterate it.
        count = 0
        seen_fallback_mids = set()
        
        for v in raw_videos:
            if count >= 12: break
            mid = v['mid']
            if mid in seen_fallback_mids: continue
            seen_fallback_mids.add(mid)
            count += 1
            
            print(f"  > Fallback Processing (Search Data): {mid}")
            
            # Fallback 1: Try robust Relation API for fans
            user_stats = get_user_stats(mid)
            
            # Fallback 2: Basic 'card' (often fails -352)
            user_card = None 
            if not user_stats:
                 user_card = get_user_card(mid)
            
            # Name
            author_name = v['author'] # Search result author is reliable
            
            # Avatar: Use 'upic' from search result (Most reliable)
            if 'upic' in v:
                avatar = "https:" + v['upic'] if v['upic'].startswith("//") else v['upic']
            elif user_card:
                avatar = user_card['avatar']
            else:
                 avatar = "https://via.placeholder.com/80?text=Unknown"
            
            # Fans: Use stats API > Card API > None
            raw_fans = None
            if user_stats:
                 raw_fans = user_stats['follower']
            elif user_card:
                 raw_fans = user_card['fans']
            if raw_fans is not None:
                if raw_fans >= 10000:
                    fans_str = f"{raw_fans/10000:.1f}w"
                else:
                    fans_str = str(raw_fans)
            else:
                fans_str = "未知" # Unknown if API fails
                
            sign = user_card['sign'] if user_card else "API Limit: Details Unavailable"
            
            # Fallback 3: Try to get recent videos to calculate REAL stats (freq, avg views)
            # Now that get_recent_videos is robust (with search fallback), we can try it.
            recent_videos = get_recent_videos(mid, limit=10)
            
            if recent_videos:
                user_stats_video = calculate_stats(recent_videos)
                weekly_freq = user_stats_video['weekly_freq']
                avg_views = user_stats_video['avg_views_5']
                latest_video = recent_videos[0]
            else:
                 # Original strict fallback if fetch fails
                 weekly_freq = 0
                 avg_views = int(v.get('play', 0))
                 latest_video = {
                    "title": clean_text(v['title']),
                    "pic": "https:" + v['pic'] if v['pic'].startswith("//") else v['pic'],
                    "bvid": v['bvid'],
                    "created": v.get('pubdate', 0),
                    "play": v.get('play', 0),
                    "length": v.get('duration', "")
                }
            
            latest_date_str = "N/A"
            if latest_video['created']:
                 dt = datetime.datetime.fromtimestamp(latest_video['created'])
                 latest_date_str = dt.strftime("%Y-%m-%d")

            # Try content fetch, but don't die on it
            content_context = get_video_subtitles(latest_video['bvid']) or "Content analysis unavailable due to API limit."
            subtitles_snippet = content_context[:200]
            
            # Stats are now handled in the block above
            # weekly_freq and avg_views are already set

            # Format for UI Display (Clean Summary)
            analysis_prompt = f"【内容摘要】{subtitles_snippet[:120]}...\n\n【观众热评】Comments unavailable in fallback."

            analyzed_creators.append({
                "mid": mid,
                "author": author_name,
                "avatar": avatar,
                "fans": fans_str,
                "intro": sign,
                "latest_date": latest_date_str,
                "weekly_freq": weekly_freq,
                "avg_views": avg_views,
                "latest_video_title": latest_video['title'],
                "latest_video_cover": latest_video['pic'],
                "latest_video_url": f"https://www.bilibili.com/video/{latest_video['bvid']}",
                "analysis_prompt": analysis_prompt,
                "subtitles_snippet": subtitles_snippet,
                "comments_snippet": "Comments unavailable"
            })

    # --- STEP 4: GENERATE MARKET REPORT ---
    market_report = generate_market_report(analyzed_creators)

    # Inject analysis into creators for easy access in template
    for c in analyzed_creators:
        if c['mid'] in market_report.get('details', {}):
            c['market_analysis'] = market_report['details'][c['mid']]

    return templates.TemplateResponse("results.html", {
        "request": request, 
        "track": track, 
        "results": analyzed_creators,
        "market_report": market_report 
    })

if __name__ == "__main__":
    uvicorn.run("web_app:app", host="0.0.0.0", port=8000, reload=True)

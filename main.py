import asyncio
import argparse
import json
import os
from bilibili_api import search_by_keyword, get_user_card, get_recent_videos, calculate_stats
from mcp_client import MCPConnector
from analyzer import generate_analysis_prompt, mock_visual_analysis

# Configuration
MCP_SERVER_URL = "https://mcp.api-inference.modelscope.net/360783e5932148/mcp"

async def analyze_track(track_name):
    print(f"=== Starting Analysis for Track: {track_name} ===")
    
    # 1. Search for top videos/accounts
    print(f"Searching for top videos in '{track_name}'...")
    results = search_by_keyword(track_name, limit=3)
    
    if not results:
        print("No results found.")
        return

    mcp = MCPConnector(MCP_SERVER_URL)
    
    report = []

    for video in results:
        print(f"\nProcessing Video: {video['title']} ({video['bvid']})...")
        
        # Basic Info
        bvid = video['bvid']
        mid = video['mid']
        video_url = f"https://www.bilibili.com/video/{bvid}"
        
        # Get User Info
        print(f"  Fetching User Info for mid={mid}...")
        user_card = get_user_card(mid)
        user_videos = get_recent_videos(mid, limit=10) # For avg views
        user_stats = calculate_stats(user_videos)
        
        # Deep Content (MCP)
        print(f"  Fetching Subtitles via MCP...")
        subtitles = await mcp.get_video_subtitles(video_url)
        
        # Prepare Data Object
        item_data = {
            "1. Benchmarking Account": video['author'],
            "2. Link": video_url,
            "3. Fan Count": user_card['fans'] if user_card else "N/A",
            "4. Avg Views (Last 5)": user_stats['avg_views_5'],
            "5. Cover URL": video['pic'], # Visual analysis placeholder
            "6. Weekly Update Freq": user_stats['weekly_freq'],
            "7. Homepage Intro": user_card['sign'] if user_card else "N/A",
            "8. Video Title": video['title'],
            "9-13. Content Analysis Prompt": generate_analysis_prompt(
                {"title": video['title'], "play": video['play'], "bvid": bvid, "owner_name": video['author']},
                subtitles,
                None # Comments not implemented in this loop yet
            )
        }
        
        report.append(item_data)
        print("  > Done.")

    # Save Report
    output_file = f"report_{track_name}.json"
    with open(output_file, "w", encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== Analysis Complete ===")
    print(f"Report saved to {output_file}")
    print("You can copy the 'Content Analysis Prompt' from the JSON to an LLM to get the final qualitative insights.")

def main():
    parser = argparse.ArgumentParser(description="Bilibili Trend Analyst")
    parser.add_argument("track", help="The track/category to analyze (e.g. 'AI', '美妆')")
    args = parser.parse_args()
    
    asyncio.run(analyze_track(args.track))

if __name__ == "__main__":
    main()

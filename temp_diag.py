from platforms.bilibili import BilibiliPlatform
import sys

# Force stdout buffering to be unbuffered
sys.stdout.reconfigure(line_buffering=True)

print("Starting checks...")
bili = BilibiliPlatform()
print("Searching for mid=456664753 (CCTV News)...")
videos = bili.get_recent_videos("456664753")
print(f"Videos found: {len(videos)}")
print("Done.")

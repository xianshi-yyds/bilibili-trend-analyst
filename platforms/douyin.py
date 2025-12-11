from typing import Dict, List, Optional
from .base import BasePlatform
import requests
import json
import time
import os
from douyin_tiktok_scraper.scraper import Scraper

class DouyinPlatform(BasePlatform):
    """Douyin Platform Implementation"""
    
    def __init__(self):
        self.scraper = Scraper()
        # Load Cookie from Env
        self.cookie = os.getenv("DOUYIN_COOKIE", "s_v_web_id=verify_lya5; tt_webid=1;")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.douyin.com/",
            "Cookie": self.cookie,
        }

    def update_cookies(self, cookie_str: str):
        """Update the cookie used for requests"""
        self.cookie = cookie_str
        self.headers['Cookie'] = cookie_str
        print(f"[DouyinPlatform] Cookies updated. Length: {len(cookie_str)}")


    def search_users(self, keyword: str) -> List[Dict]:
        """Search Douyin Users"""
        # Douyin General Search API
        base_url = "https://www.douyin.com/aweme/v1/web/general/search/single/"
        params = {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "search_channel": "aweme_general",
            "sort_type": "0",
            "publish_time": "0",
            "keyword": keyword,
            "search_source": "normal_search",
            "query_correct_type": "1",
            "is_filter_search": "0",
            "offset": "0",
            "count": "10"
        }
        
        # Construct full URL for signing
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{base_url}?{query_string}"
        
        try:
            signed_url = self.scraper.generate_x_bogus_url(full_url)
            res = requests.get(signed_url, headers=self.headers)
            print(f"Douyin Search URL: {signed_url}")
            data = res.json()
            
            # Parse result
            users = []
            if 'data' in data:
                for item in data['data']:
                    if 'aweme_info' in item: # Video result
                        # Extract author from video
                        author = item['aweme_info']['author']
                        user_info = {
                            "mid": author['sec_uid'], # Use sec_uid as Douyin ID
                            "name": author['nickname'],
                            "fans": "N/A", # Search result might not have fans count
                            "sign": author.get('signature', ''),
                            "avatar": author['avatar_thumb']['url_list'][0]
                        }
                        users.append(user_info)
                    elif 'user_list' in item: # Direct user result?
                         # Douyin search structure varies. Assuming video search primarily.
                         pass
            
            # Simple dedup based on mid
            unique_users = {}
            for u in users:
                unique_users[u['mid']] = u
            return list(unique_users.values())

        except Exception as e:
            print(f"Douyin Search Failed: {e}")
            return []

    def get_user_info(self, sec_uid: str) -> Optional[Dict]:
        # Need user profile API. 
        # https://www.douyin.com/aweme/v1/web/user/profile/other/
        base_url = "https://www.douyin.com/aweme/v1/web/user/profile/other/"
        params = {
             "device_platform": "webapp",
             "aid": "6383",
             "channel": "channel_pc_web",
             "sec_user_id": sec_uid
        }
        # Sign
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{base_url}?{query_string}"
         
        try:
             signed_url = self.scraper.generate_x_bogus_url(full_url)
             res = requests.get(signed_url, headers=self.headers)
             data = res.json()
             if 'user' in data:
                 user = data['user']
                 return {
                     "mid": sec_uid,
                     "name": user['nickname'],
                     "fans": user['follower_count'],
                     "sign": user['signature'],
                     "avatar": user['avatar_thumb']['url_list'][0]
                 }
        except Exception as e:
            print(f"Get User Info Failed: {e}")
        return None

    def get_recent_posts(self, sec_uid: str, limit: int = 10) -> List[Dict]:
        # User Post API
        # https://www.douyin.com/aweme/v1/web/aweme/post/
        base_url = "https://www.douyin.com/aweme/v1/web/aweme/post/"
        params = {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "sec_user_id": sec_uid,
            "max_cursor": "0",
            "count": str(limit)
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{base_url}?{query_string}"

        try:
            signed_url = self.scraper.generate_x_bogus_url(full_url)
            res = requests.get(signed_url, headers=self.headers)
            data = res.json()
            
            posts = []
            if 'aweme_list' in data:
                for item in data['aweme_list']:
                    posts.append({
                        "bvid": item['aweme_id'],
                        "title": item['desc'],
                        "play": item['statistics']['play_count'],
                        "created": item['create_time'],
                        "pic": item['video']['cover']['url_list'][0],
                        "length": f"{item['duration']//1000}s"
                    })
            return posts
        except Exception as e:
             print(f"Get Posts Failed: {e}")
             return []

    def get_post_detail(self, aweme_id: str) -> Optional[Dict]:
        return {
            "id": aweme_id,
            "subtitles": "No subtitles (Douyin)",
            "comments": ["Comments unavailable (Douyin)"]
        }

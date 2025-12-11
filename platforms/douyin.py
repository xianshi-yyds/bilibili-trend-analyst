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
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
        """Fetch video detail by ID"""
        base_url = "https://www.douyin.com/aweme/v1/web/aweme/detail/"
        params = {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "aweme_id": aweme_id
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{base_url}?{query_string}"

        try:
            signed_url = self.scraper.generate_x_bogus_url(full_url)
            # Use headers with cookie (crucial)
            res = requests.get(signed_url, headers=self.headers) 
            try:
                data = res.json()
            except:
                print(f"JSON Parse Error. Raw: {res.text[:500]}")
                return None
            
            if 'aweme_detail' in data and data['aweme_detail']:
                item = data['aweme_detail']
                # Extract owner info if possible
                author = item.get('author', {})
                
                return {
                    "id": aweme_id,
                    "title": item.get('desc', ''),
                    "pic": item.get('video', {}).get('cover', {}).get('url_list', [''])[0],
                    "created": item.get('create_time', 0),
                    "play": item.get('statistics', {}).get('play_count', 0),
                    "author": {
                        "mid": author.get('sec_uid', ''),
                        "name": author.get('nickname', 'Unknown'),
                        "face": author.get('avatar_thumb', {}).get('url_list', [''])[0],
                        "fans": author.get('follower_count', 0)
                    },
                    "subtitles": "No subtitles available", # Douyin subtitles harder to get
                    "comments": [] # Comments require separate API
                }
            print(f"Detail API returned no data: {data.keys()}")
            return None
        except Exception as e:
            print(f"Get Post Detail Failed: {e}")
            return None

    def get_video_via_html(self, share_url: str) -> Optional[Dict]:
        """Fetch video info by scraping the Share Page HTML (Bypasses API Block)"""
        try:
            import re
            import json
            session = requests.Session()
            # Use Mobile UA for Share Page
            headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
            }
            # 1. Follow Redirects to get final ID/URL
            res = session.get(share_url, headers=headers, allow_redirects=True, timeout=10)
            final_url = res.url
            html = res.text
            
            video_data = {}
            
            # 2. Robust JSON extraction from _ROUTER_DATA
            # Douyin embeds data in window._ROUTER_DATA = {...};
            json_match = re.search(r'window\._ROUTER_DATA\s*=\s*(\{.+?\});', html, re.DOTALL)
            if not json_match:
                 json_match = re.search(r'window\._ROUTER_DATA\s*=\s*(\{.+?\})\s*</script>', html, re.DOTALL)

            if json_match:
                try:
                    json_str = json_match.group(1)
                    if json_str.endswith(';'): json_str = json_str[:-1]
                    data = json.loads(json_str)
                    
                    loader_data = data.get('loaderData', {})
                    # Find key like "video_(id)/page"
                    video_key = next((k for k in loader_data.keys() if 'video_' in k and 'page' in k), None)
                    
                    if video_key:
                        info = loader_data[video_key].get('videoInfoRes', {}).get('item_list', [{}])[0]
                        stats = info.get('statistics', {})
                        author = info.get('author', {})
                        video = info.get('video', {})
                        
                        video_data = {
                            "title": info.get('desc'),
                            "created": info.get('create_time'),
                            "play": stats.get('play_count', 0),
                            "likes": stats.get('digg_count', 0),
                            "author_name": author.get('nickname'),
                            "author_id": author.get('sec_uid'),
                            "author_fans": author.get('follower_count'), # Often None in share page
                            "cover": video.get('cover', {}).get('url_list', [''])[0],
                            "author_avatar": author.get('avatar_thumb', {}).get('url_list', [''])[0]
                        }
                except Exception as e:
                    print(f"JSON Parsing Logic Failed: {e}")

            # Fallback to Regex if JSON failed or fields missing
            if not video_data.get('title'):
                desc_match = re.search(r'"desc":"(.*?)"', html)
                if desc_match:
                    title = desc_match.group(1)
                    try: title = title.encode('utf-8').decode('unicode_escape')
                    except: pass
                    video_data['title'] = title

            # Extract ID from URL
            vid_match = re.search(r'video/(\d+)', final_url)
            vid = vid_match.group(1) if vid_match else "unknown"
            
            # Use Likes as Proxy for Plays if Plays is 0 (Common in Share Page)
            play_count = video_data.get('play', 0)
            if play_count == 0 and video_data.get('likes'):
                play_count = video_data.get('likes') # Proxy

            return {
                "id": vid,
                "title": video_data.get('title', "Douyin Video"),
                "pic": video_data.get('cover') or "https://via.placeholder.com/150",
                "created": video_data.get('created', 0),
                "play": play_count,
                "author": {
                    "mid": video_data.get('author_id', 'unknown'),
                    "name": video_data.get('author_name', 'Douyin Creator'),
                    "face": video_data.get('author_avatar', ''),
                    "fans": video_data.get('author_fans') or "Unknown"
                },
                "subtitles": f"Likes: {video_data.get('likes', 0)} (No subtitles via Link)",
                "comments": []
            }
        except Exception as e:
            print(f"HTML Scrape Failed: {e}")
            return None

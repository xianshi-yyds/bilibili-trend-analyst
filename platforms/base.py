from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class BasePlatform(ABC):
    """Abstract Base Class for Social Media Platforms"""

    @abstractmethod
    def search_users(self, keyword: str) -> List[Dict]:
        """
        Search for users by keyword.
        Returns: List of dicts with keys: mid, name, avatar, fans, sign
        """
        pass

    @abstractmethod
    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """
        Get detailed user info.
        Returns: Dict with keys: mid, name, avatar, fans, sign, etc.
        """
        pass

    @abstractmethod
    def get_recent_posts(self, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Get recent posts/videos.
        Returns: List of dicts with keys: bvid/id, title, play, created, pic, length
        """
        pass
    
    @abstractmethod
    def get_post_detail(self, post_id: str) -> Optional[Dict]:
         """
         Get detail for a single post (including subtitles/comments if possible).
         """
         pass

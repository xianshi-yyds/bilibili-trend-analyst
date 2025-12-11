import re

track = "9.97 11/09 e@O.kC QkP:/ 我从中国买了一堆奇葩玩意：真的有人用吗？ # 开箱评测# 英语口语# 老外看中国# 网购# 神器  https://v.douyin.com/XE29evc41EE/ 复制此链接，打开Dou音搜索，直接观看视频！"

print(f"Testing regex on: {track}")

url_match = re.search(r'https?://(?:v\.douyin\.com|www\.douyin\.com|www\.iesdouyin\.com)/[a-zA-Z0-9/]+', track)
if url_match:
    print(f"MATCH FOUND: {url_match.group(0)}")
else:
    print("NO MATCH")

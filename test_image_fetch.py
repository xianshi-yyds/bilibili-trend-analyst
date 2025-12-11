import requests

url = "https://p3-pc-sign.douyinpic.com/image-cut-tos-priv/9bf5a5b560c3ccbdb29f7e132387acdb~tplv-dy-resize-origshort-autoq-75:330.jpeg?biz_tag=pcweb_cover&from=327834062&lk3s=138a59ce&s=PackSourceEnum_SEARCH&sc=cover&se=false&x-expires=2080803600&x-signature=B86NYab%2BLmFDYgYrDpkC62%2BileE%3D"

headers_options = [
    {"User-Agent": "Mozilla/5.0", "Referer": "https://www.douyin.com/"},
    {"User-Agent": "Mozilla/5.0", "Referer": "https://www.bilibili.com/"},
    {"User-Agent": "Mozilla/5.0", "Referer": ""}, # Empty
    {"User-Agent": "Mozilla/5.0"}, # No Referer key
]

print(f"Testing URL: {url[:50]}...")

for h in headers_options:
    try:
        r = requests.get(url, headers=h, timeout=5)
        print(f"Headers: {h}")
        print(f"Status: {r.status_code}, Length: {len(r.content)}")
    except Exception as e:
        print(f"Error with {h}: {e}")

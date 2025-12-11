import requests

short_url = "https://v.douyin.com/XE29evc41EE/"
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
}

print(f"Resolving: {short_url}")
try:
    res = requests.get(short_url, headers=headers, allow_redirects=True)
    print(f"Final URL: {res.url}")
except Exception as e:
    print(f"Error: {e}")

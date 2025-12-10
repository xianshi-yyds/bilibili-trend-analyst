import requests
import json
import os

# Inject SESSDATA
os.environ["SESSDATA"] = "ad9345bb%2C1778221336%2Cf1eea%2Ab1CjDdhRLznDE0c3AjHIy597Xv3JuyuTdsRiPSyEvvysFWxVDxCrmkllFxADn74qNqTJ8SVmFQNlFVZHVTOHlvbDhYZzZGQjN2YXVWWjhFbXhLOUJCOENaSnlueS1GNjdidlBnaWFiSm9vVUV5ZmlQbFpvbktBM1FQY0FkNU1ENlhySjRsRUNnOHVRIIEC"

SESSDATA = os.getenv("SESSDATA", "")
COOKIE = f"SESSDATA={SESSDATA};"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
    "Cookie": COOKIE
}

mid = 3493298436049525
print(f"Testing Search User by MID: {mid}")

url = "https://api.bilibili.com/x/web-interface/search/type"
params = {
    "keyword": str(mid),
    "search_type": "bili_user",
    "page": 1,
    "page_size": 1
}

try:
    res = requests.get(url, headers=HEADERS, params=params)
    print(f"Status: {res.status_code}")
    data = res.json()
    if data['code'] == 0:
        results = data['data'].get('result', [])
        if results:
            print("Found User:")
            print(json.dumps(results[0], indent=2, ensure_ascii=False))
        else:
            print("No user found.")
    else:
        print(f"API Error: {data}")
except Exception as e:
    print(f"Crash: {e}")

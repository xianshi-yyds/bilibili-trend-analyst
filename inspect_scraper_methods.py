from douyin_tiktok_scraper.scraper import Scraper
import inspect

s = Scraper()
print("Methods of Scraper:")
for method_name in dir(s):
    if not method_name.startswith("_"):
        print(method_name)

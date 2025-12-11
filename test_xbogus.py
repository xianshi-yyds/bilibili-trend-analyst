import asyncio
from douyin_tiktok_scraper.scraper import Scraper

async def test():
    scraper = Scraper()
    url = "https://www.douyin.com/aweme/v1/web/general/search/single/?keyword=test"
    try:
        # Check signature generation
        signed_url = scraper.generate_x_bogus_url(url)
        print(f"Signed URL: {signed_url}")
    except Exception as e:
        print(f"Signing failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())

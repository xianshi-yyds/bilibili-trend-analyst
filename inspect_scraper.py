try:
    import douyin_tiktok_scraper
    print("Module found:", douyin_tiktok_scraper)
    print("Dir:", dir(douyin_tiktok_scraper))
    
    # Try submodules commonly used
    try:
        from douyin_tiktok_scraper.scraper import Scraper
        print("Scraper class found")
    except ImportError:
        print("No Scraper class at top level")
        
except ImportError as e:
    print(f"Import failed: {e}")

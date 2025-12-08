from tsdr_scraper import TSDRScraper
import logging
import sys

# Configure logging to see everything
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

def debug():
    serial = 99534546
    print(f"Debug fetching {serial}...")
    
    scraper = TSDRScraper()
    
    # 1. Fetch raw response to check status code
    # url = scraper.session.get(f"https://tsdr.uspto.gov/statusview/sn{serial}")
    # ... code commented out ...
    
    # 2. Try the parser
    print(f"Calling fetch_trademark({serial})...")
    tm = scraper.fetch_trademark(serial)
    if tm:
        print("✅ Success!")
        print(tm)
    else:
        print("❌ Failed parser")


if __name__ == "__main__":
    debug()

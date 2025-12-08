from tsdr_scraper import TSDRScraper
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

def verify():
    print("Testting Scraper Reliability with Session Rotation...")
    scraper = TSDRScraper(rate_limit_delay=2.0)
    
    # Use a known recent serial to test (from previous run)
    start_serial = 99535061 
    count = 10
    
    success = 0
    
    for i in range(count):
        serial = start_serial - i
        print(f"[{i+1}/{count}] Fetching {serial}...")
        tm = scraper.fetch_trademark(serial)
        if tm:
            print(f"✅ Success: {tm.get('mark_name', 'N/A')}")
            success += 1
        else:
            print(f"❌ Failed: {serial}")
            
    print(f"\nResult: {success}/{count} ({success/count*100}%)")

if __name__ == "__main__":
    verify()

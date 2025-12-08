import logging
import time
from datetime import datetime, timedelta
from tsdr_scraper import TSDRScraper
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def analyze_daily_volume():
    """
    Analyzes the number of trademark filings per day.
    """
    print("\n📊 USPTO Trademark Volume Analysis")
    print("=================================")
    
    scraper = TSDRScraper(rate_limit_delay=1.5)
    
    # 1. Find the absolute latest serial
    print("\n1. Finding latest serial number...")
    latest_serial = scraper.find_latest_serial()
    print(f"👉 Latest Serial: {latest_serial}")
    
    if not latest_serial:
        print("❌ Could not find latest serial. Aborting.")
        return

    # Get details of the latest serial
    latest_tm = scraper.fetch_trademark(latest_serial)
    if not latest_tm:
        print("❌ Could not fetch details for latest serial.")
        return
        
    latest_date_str = latest_tm.get('filing_date')
    print(f"📅 Latest Filing Date: {latest_date_str} (Serial: {latest_serial})")
    
    if not latest_date_str:
        print("❌ Latest trademark has no filing date.")
        return

    latest_date = datetime.strptime(latest_date_str, "%Y-%m-%d").date()
    
    # 2. Estimate volume by going back X serials
    # Let's check 2000 serials ago and 5000 serials ago
    checkpoints = [1000, 2000, 3000, 5000]
    
    print("\n2. Sampling past serials to estimate density...")
    
    results = []
    
    for offset in checkpoints:
        target_serial = latest_serial - offset
        tm = scraper.fetch_trademark(target_serial)
        
        if tm and tm.get('filing_date'):
            tm_date = datetime.strptime(tm.get('filing_date'), "%Y-%m-%d").date()
            days_diff = (latest_date - tm_date).days
            
            print(f"   - Serial {target_serial} (-{offset}): Filed {tm.get('filing_date')} ({days_diff} days ago)")
            
            results.append({
                'offset': offset,
                'days_diff': days_diff,
                'serial': target_serial,
                'date': tm_date
            })
            
            # Use the first checkpoint that is >= 1 day ago to simple estimate
            if days_diff >= 1:
                daily_volume_est = offset / days_diff
                print(f"   💡 Rough Estimate: ~{int(daily_volume_est)} filings/day")
                
        else:
            print(f"   - Serial {target_serial} (-{offset}): Failed to fetch or no date")
            
    # 3. Precise check for "yesterday" boundary (optional but good)
    # Binary search for the start of the latest_date
    print("\n3. Verifying Scraper Quality with 10 sequential records...")
    
    # Fetch 10 records from latest backwards
    failures = 0
    successes = 0
    
    for i in range(10):
        s = latest_serial - i
        tm = scraper.fetch_trademark(s)
        if tm:
            status = "✅"
            successes += 1
            print(f"   {status} {s}: {tm.get('mark_name', 'N/A')[:30]:<30} | {tm.get('owner', 'N/A')[:20]}")
        else:
            status = "❌"
            failures += 1
            print(f"   {status} {s}: Failed to fetch")
            
    print(f"\n✅ Success Rate: {successes}/10")
    
    return latest_serial

if __name__ == "__main__":
    analyze_daily_volume()

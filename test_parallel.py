from tsdr_scraper import TSDRScraper
import logging
import time

# Logging ayarla
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def test_parallel():
    scraper = TSDRScraper()
    
    print("\n🚀 Testing Parallel Scanning (3 Workers)...")
    start_time = time.time()
    
    # Bilinen bir aralığı tara (örneğin botun az önce taradığı yerler)
    # Bu aralıkta veriler cache'de olmayabilir ama server'da vardır.
    results = scraper.scan_range(99538000, 99538020, workers=3)
    
    elapsed = time.time() - start_time
    print(f"\n✅ Finished in {elapsed:.2f} seconds.")
    print(f"Found: {len(results)} items.")

if __name__ == "__main__":
    test_parallel()

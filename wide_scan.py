#!/usr/bin/env python3
"""
Geniş tarama - Son 2000 trademark'ı çek
"""
from tsdr_scraper import TSDRScraper
import json
import sys

def main():
    scraper = TSDRScraper(rate_limit_delay=0.2)
    
    print('🔍 Son 2000 trademark taranıyor...')
    print('   Bu ~7-10 dakika sürecek')
    print()
    sys.stdout.flush()
    
    latest = scraper.find_latest_serial()
    print(f'En son serial: {latest}')
    
    start_serial = latest - 2000
    print(f'Tarama aralığı: {start_serial} - {latest}')
    print()
    sys.stdout.flush()
    
    trademarks = scraper.scan_range(start_serial, latest)
    print(f'\n✅ {len(trademarks)} trademark bulundu')
    
    with open('wide_scan.json', 'w') as f:
        json.dump(trademarks, f, ensure_ascii=False, indent=2)
    print('💾 wide_scan.json dosyasına kaydedildi')
    
    # Özet istatistik
    print('\n📊 Özet:')
    print(f'   Toplam: {len(trademarks)} trademark')
    
    # İlginç olanları say
    ai_count = sum(1 for t in trademarks if t.get('mark_name') and 'AI' in t['mark_name'].upper())
    tech_count = sum(1 for t in trademarks if t.get('mark_name') and any(w in t['mark_name'].upper() for w in ['TECH', 'DIGITAL', 'SMART', 'CLOUD']))
    
    print(f'   AI içeren: {ai_count}')
    print(f'   Tech içeren: {tech_count}')

if __name__ == "__main__":
    main()

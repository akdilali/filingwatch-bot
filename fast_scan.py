#!/usr/bin/env python3
"""
HIZLI Geniş Tarama - Paralel requests ile 2000 trademark çek
~2-3 dakikada tamamlanır (7-10 yerine)
"""
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import time
import sys

TSDR_URL = "https://tsdr.uspto.gov/statusview/sn{serial}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def parse_trademark(html: str, serial: int) -> dict:
    """HTML'den trademark bilgisi çıkar - YENİ FORMAT"""
    soup = BeautifulSoup(html, 'lxml')
    
    def get_text(label):
        # Yeni format: div.key içinde label, div.value içinde değer
        key_div = soup.find('div', class_='key', string=lambda t: t and label in t)
        if key_div:
            value_div = key_div.find_next_sibling('div', class_='value')
            if value_div:
                # markText class'ı varsa özellikle onu al
                mark_text = value_div.find(class_='markText')
                if mark_text:
                    return mark_text.get_text(strip=True)
                return value_div.get_text(strip=True)
        return None
    
    mark_name = get_text('Mark:')
    if not mark_name or mark_name.lower() in ['none', 'n/a', '']:
        return None
    
    return {
        'serial_number': serial,
        'mark_name': mark_name,
        'filing_date': get_text('Filing Date:'),
        'status': get_text('Status:'),
        'owner': get_text('Owner:'),
        'attorney': get_text('Attorney:'),
        'goods_services': get_text('Description:') or get_text('Goods/Services:'),
    }

def fetch_one(serial: int) -> dict:
    """Tek trademark çek"""
    try:
        resp = requests.get(TSDR_URL.format(serial=serial), headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            return parse_trademark(resp.text, serial)
    except:
        pass
    return None

def find_latest_serial() -> int:
    """En son geçerli serial'ı bul - güncel başlangıç noktasıyla"""
    print("🔍 En son serial aranıyor...")
    
    # Daha güncel başlangıç noktası
    low, high = 99532000, 99540000
    
    while low < high:
        mid = (low + high + 1) // 2
        result = fetch_one(mid)
        if result:
            low = mid
        else:
            high = mid - 1
    
    print(f"✅ En son serial: {low}")
    return low

def scan_fast(start: int, end: int, workers: int = 30) -> list:
    """
    Paralel tarama - ÇOK HIZLI!
    workers=30 ile ~1-2 dakikada 2000 trademark
    """
    serials = list(range(start, end + 1))
    results = []
    found = 0
    
    print(f"⚡ {len(serials)} serial taranıyor ({workers} paralel worker)...")
    print()
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fetch_one, s): s for s in serials}
        
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            if result:
                results.append(result)
                found += 1
            
            # Progress her 200'de bir
            if (i + 1) % 200 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                eta = (len(serials) - i - 1) / rate
                print(f"   {i+1}/{len(serials)} ({found} bulundu) - {rate:.0f}/s - ETA: {eta:.0f}s")
                sys.stdout.flush()
    
    elapsed = time.time() - start_time
    print(f"\n✅ {found} trademark, {elapsed:.1f}s ({found/elapsed:.1f} tm/s)")
    
    return results

def main():
    print("=" * 60)
    print("⚡ HIZLI TARAMA - Paralel Requests")
    print("=" * 60)
    print()
    
    latest = find_latest_serial()
    
    # Günde ~2000 trademark için ~15000 serial tara
    # (her ~8 serial'da 1 trademark var)
    SERIAL_RANGE = 15000
    start = latest - SERIAL_RANGE
    
    print(f"\n📊 Tarama: {start} → {latest} ({SERIAL_RANGE} serial)")
    print(f"   Beklenen: ~{SERIAL_RANGE // 8} trademark")
    print()
    
    # 50 paralel worker ile tara - ÇOK HIZLI
    trademarks = scan_fast(start, latest, workers=50)
    
    # Kaydet
    with open('wide_scan.json', 'w') as f:
        json.dump(trademarks, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 {len(trademarks)} trademark → wide_scan.json")
    
    # Quick stats
    print("\n📊 Hızlı İstatistik:")
    ai_count = sum(1 for t in trademarks if t.get('mark_name') and 'AI' in t['mark_name'].upper())
    tech_count = sum(1 for t in trademarks if t.get('mark_name') and any(w in t['mark_name'].upper() for w in ['TECH', 'DIGITAL', 'SMART', 'CLOUD', 'CYBER']))
    crypto_count = sum(1 for t in trademarks if t.get('mark_name') and any(w in t['mark_name'].upper() for w in ['CRYPTO', 'COIN', 'TOKEN', 'CHAIN', 'NFT', 'WEB3']))
    
    print(f"   🤖 AI içeren: {ai_count}")
    print(f"   ⚡ Tech içeren: {tech_count}")
    print(f"   🪙 Crypto içeren: {crypto_count}")

if __name__ == "__main__":
    main()

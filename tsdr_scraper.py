"""
TSDR (Trademark Status & Document Retrieval) Scraper
Gerçek zamanlı USPTO trademark verisi çeker
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import json
import os
from datetime import datetime
from typing import Optional, Dict, List
import logging

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
TSDR_BASE_URL = "https://tsdr.uspto.gov/statusview/sn{serial}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# State file
STATE_FILE = "scraper_state.json"


class TSDRScraper:
    """USPTO TSDR Scraper - Gerçek zamanlı trademark verisi"""
    
    # User Agents to rotate
    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:126.0) Gecko/20100101 Firefox/126.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"
    ]
    
    def __init__(self, rate_limit_delay: float = 1.0):
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        self.state = self._load_state()
        self._reset_session()

    def _reset_session(self):
        """Create a fresh session with a random User-Agent"""
        import random
        self.session = requests.Session()
        ua = random.choice(self.USER_AGENTS)
        self.session.headers.update({
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })
        logger.debug(f"New session created with UA: {ua[:30]}...")
        
    def _load_state(self) -> dict:
        """Scraper durumunu yükle"""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            "last_serial": 99530000,  # Başlangıç noktası
            "highest_valid_serial": 99530000,
            "last_scan_time": None
        }
    
    def _save_state(self):
        """Scraper durumunu kaydet"""
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def _rate_limit(self):
        """Rate limiting - USPTO'yu aşırı yüklemeden"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def fetch_trademark(self, serial: int, retries: int = 3) -> Optional[Dict]:
        """Tek bir trademark'ın detaylarını çek (Retry mekanizmalı)"""
        
        for attempt in range(retries + 1):
            self._rate_limit()
            
            url = TSDR_BASE_URL.format(serial=serial)
            try:
                response = self.session.get(url, timeout=20)
                
                # Rate limit handling
                if response.status_code == 429:
                    wait_time = (attempt + 1) * 5
                    logger.warning(f"Rate limit (429) serial {serial}. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                if response.status_code == 403:
                    logger.warning(f"HTTP 403 (Forbidden) on serial {serial}. Resetting session...")
                    self._reset_session()
                    time.sleep(2) # Extra wait after reset
                    continue

                if response.status_code != 200:
                    logger.warning(f"HTTP {response.status_code} requesting serial {serial}")
                    return None
                
                data = self._parse_trademark_page(response.text, serial)
                if data:
                    return data
                
                # If parsing failed, it might be a partial page due to server load
                # Log it, but don't retry immediately unless we are sure it's a server error
                # For now, return None if parser fails (valid page but data missing)
                return None
                
            except requests.RequestException as e:
                logger.error(f"Error fetching serial {serial} (Attempt {attempt+1}): {e}")
                if attempt < retries:
                    time.sleep((attempt + 1) * 2)
                else:
                    return None
        return None
    
    def _parse_trademark_page(self, html: str, serial: int) -> Optional[Dict]:
        """TSDR HTML sayfasını parse et"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Mark adını bul
        mark_name = self._extract_value(soup, "Mark Literal Elements:")
        if not mark_name:
            mark_name = self._extract_value(soup, "Mark:")
        
        if not mark_name:
            return None  # Geçersiz/boş trademark
        
        # Diğer alanları çek
        filing_date = self._extract_value(soup, "Application Filing Date:")
        status = self._extract_value(soup, "Status:")
        status_date = self._extract_value(soup, "Status Date:")
        mark_type = self._extract_value(soup, "Mark Type:")
        
        # Owner bilgisi
        owner = self._extract_owner(soup)
        
        # Goods/Services
        goods_services = self._extract_goods_services(soup)
        
        # International Class
        int_class = self._extract_value(soup, "International Class:")
        
        # Drawing Type
        drawing_type = self._extract_value(soup, "Mark Drawing Type:")

        # Image URL
        image_url = self._extract_image_url(soup)
        
        return {
            "serial_number": str(serial),
            "mark_name": mark_name.strip() if mark_name else None,
            "filing_date": self._parse_date(filing_date),
            "filing_date_raw": filing_date.strip() if filing_date else None,
            "status": status.strip() if status else None,
            "status_date": status_date.strip() if status_date else None,
            "mark_type": mark_type.strip() if mark_type else None,
            "owner": owner,
            "goods_services": goods_services,
            "international_class": int_class.strip() if int_class else None,
            "drawing_type": drawing_type.strip() if drawing_type else None,
            "image_url": image_url,
            "tsdr_url": f"https://tsdr.uspto.gov/caseviewer/SNUM/{serial}",
            "scraped_at": datetime.now().isoformat()
        }
    
    def _extract_value(self, soup: BeautifulSoup, key: str) -> Optional[str]:
        """Key-value pair'den value'yu çıkar"""
        key_div = soup.find('div', class_='key', string=re.compile(re.escape(key)))
        if key_div:
            value_div = key_div.find_next_sibling('div', class_='value')
            if value_div:
                return value_div.get_text(strip=True)
        return None
    
    def _extract_owner(self, soup: BeautifulSoup) -> Optional[str]:
        """Owner bilgisini çıkar"""
        # Owner section'ını bul
        owner_section = soup.find('div', id='ownerSection')
        if owner_section:
            name_div = owner_section.find('div', class_='value')
            if name_div:
                return name_div.get_text(strip=True)
        
        # Alternatif yol
        owner = self._extract_value(soup, "Owner Name:")
        if owner:
            return owner
        
        return None
    
    def _extract_goods_services(self, soup: BeautifulSoup) -> Optional[str]:
        """Goods/Services bilgisini çıkar"""
        # 1. Yöntem: 'Goods/Services:' veya 'For:' label'ı
        keys = [r'Goods/Services:', r'For:', r'International Class:']
        
        for key in keys:
             gs_div = soup.find('div', class_='key', string=re.compile(key, re.IGNORECASE))
             if gs_div:
                 value_div = gs_div.find_next_sibling('div', class_='value')
                 if value_div:
                     text = value_div.get_text(strip=True)
                     # Eğer 'For:' ise bazen class bilgisini de içerir, temizleyelim
                     return text[:500]

        # 2. Yöntem: Section ID
        gs_section = soup.find('div', id='goodsServicesSection')
        if gs_section:
            value_div = gs_section.find('div', class_='value')
            if value_div:
                return value_div.get_text(strip=True)[:500]  # İlk 500 karakter
        
        return None
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Tarih string'ini ISO formatına çevir"""
        if not date_str:
            return None
        
        date_str = date_str.strip()
        
        # Format: "Dec. 05, 2025" veya "Nov. 17, 2025"
        try:
            dt = datetime.strptime(date_str, "%b. %d, %Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
        
        # Format: "December 05, 2025"
        try:
            dt = datetime.strptime(date_str, "%B %d, %Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

        return None

    def _extract_image_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Marka görselinin URL'sini bul"""
        img = soup.find('img', id='markImage')
        if img and img.get('src'):
            src = img['src']
            if src.startswith('http'):
                return src
            # Relative path ise full URL yap (Gerekirse)
            return src
        return None

    def download_image(self, url: str, serial: str) -> Optional[str]:
        """Görseli indir ve kaydet"""
        if not url: return None
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                filename = f"temp_{serial}.jpg"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                return filename
        except Exception as e:
            logger.error(f"Image download error {serial}: {e}")
            
        return None
    
    def find_latest_serial(self) -> int:
        """En son geçerli serial numarasını bul (binary search)"""
        logger.info("En son serial numarası aranıyor...")
        
        low = self.state.get("highest_valid_serial", 99530000)
        high = low + 50000  # Makul bir üst sınır
        
        # Önce üst sınırı bul
        while self.fetch_trademark(high) is not None:
            low = high
            high += 10000
        
        # Binary search
        while low < high - 1:
            mid = (low + high) // 2
            if self.fetch_trademark(mid) is not None:
                low = mid
            else:
                high = mid
        
        logger.info(f"En son geçerli serial: {low}")
        self.state["highest_valid_serial"] = low
        self._save_state()
        
        return low
    
    def scan_new_trademarks(self, count: int = 100) -> List[Dict]:
        """Yeni trademark'ları tara"""
        logger.info(f"Son {count} trademark taranıyor...")
        
        latest = self.find_latest_serial()
        start = latest - count + 1
        
        trademarks = []
        for serial in range(start, latest + 1):
            tm = self.fetch_trademark(serial)
            if tm:
                trademarks.append(tm)
                logger.info(f"✓ {serial}: {tm['mark_name'][:50] if tm['mark_name'] else 'N/A'}")
        
        self.state["last_scan_time"] = datetime.now().isoformat()
        self._save_state()
        
        return trademarks
    
    def scan_range(self, start: int, end: int, workers: int = 1) -> List[Dict]:
        """Belirli bir aralıktaki trademark'ları tara (Sıralı ve güvenli)"""
        # Not: Parallel scanning WAF block yediği için sıralı yapıyoruz.
        # workers parametresi şimdilik yoksayılıyor.
        
        logger.info(f"Taranıyor: {start} - {end} (Sıralı/Güvenli)")
        
        serials = list(range(start, end + 1))
        trademarks = []
        start_time = time.time()
        
        for i, serial in enumerate(serials):
            tm = self.fetch_trademark(serial)
            if tm:
                trademarks.append(tm)
                logger.info(f"✓ {serial}: {tm['mark_name'][:30]}")
            
            # Progress log
            if (i + 1) % 10 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                logger.info(f"İlerleme: {i+1}/{len(serials)} ({len(trademarks)} bulundu) - {rate:.2f}/s")
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Tamamlandı: {len(trademarks)} trademark, {elapsed:.1f}s")
        
        return trademarks

    def scan_range_slow(self, start: int, end: int) -> List[Dict]:
        """Eski sıralı tarama (yedek olarak)"""
        logger.info(f"Taranıyor (yavaş): {start} - {end}")
        
        trademarks = []
        for serial in range(start, end + 1):
            tm = self.fetch_trademark(serial)
            if tm:
                trademarks.append(tm)
                if len(trademarks) % 10 == 0:
                    logger.info(f"İlerleme: {len(trademarks)} trademark bulundu")
        
        return trademarks
    
    def get_trademarks_since_last_scan(self) -> List[Dict]:
        """Son taradan bu yana yeni trademark'ları al"""
        last_serial = self.state.get("last_serial", 99530000)
        latest = self.find_latest_serial()
        
        if latest <= last_serial:
            logger.info("Yeni trademark yok")
            return []
        
        logger.info(f"Yeni trademark'lar taranıyor: {last_serial + 1} - {latest}")
        trademarks = self.scan_range(last_serial + 1, latest)
        
        self.state["last_serial"] = latest
        self._save_state()
        
        return trademarks


# Filtreleme fonksiyonları
class TrademarkFilter:
    """Trademark filtreleme sınıfı"""
    
    # İlginç şirketler
    INTERESTING_OWNERS = [
        "apple", "google", "meta", "microsoft", "amazon", "nvidia", "tesla",
        "openai", "anthropic", "alphabet", "facebook", "instagram", "whatsapp",
        "netflix", "disney", "warner", "sony", "samsung", "huawei", "xiaomi",
        "tiktok", "bytedance", "twitter", "spacex", "uber", "airbnb", "stripe",
        "coinbase", "binance", "palantir", "snowflake", "databricks", "figma"
    ]
    
    # İlginç keyword'ler (tam kelime olarak aranacak)
    INTERESTING_KEYWORDS = [
        " ai ", " ai", "ai ", "-ai", "ai-",  # AI kelimeleri
        "gpt", "llm", "neural", "quantum", "blockchain", "crypto", "nft",
        "metaverse", "robot", "autonomous", "drone",
        "chatbot", "copilot", "autopilot", "self-driving", "machine learning",
        "deep learning", "generative", "virtual reality", "augmented reality",
        "artificial intelligence", "smart", "bot", "assistant", "vision pro"
    ]
    
    # Büyük international class'lar (tech/software)
    INTERESTING_CLASSES = ["009", "035", "042", "038", "041"]  # Software, business, tech
    
    @classmethod
    def is_interesting(cls, trademark: Dict) -> tuple[bool, str]:
        """Trademark ilginç mi kontrol et, neden ilginç olduğunu döndür"""
        
        mark_name = (trademark.get("mark_name") or "").lower()
        owner = (trademark.get("owner") or "").lower()
        goods = (trademark.get("goods_services") or "").lower()
        int_class = trademark.get("international_class") or ""
        
        # Owner kontrolü
        for company in cls.INTERESTING_OWNERS:
            if company in owner:
                return True, f"🏢 {company.title()} şirketinden"
        
        # Keyword kontrolü (mark name'de)
        for keyword in cls.INTERESTING_KEYWORDS:
            if keyword in mark_name:
                return True, f"🔑 '{keyword}' keyword'ü içeriyor"
        
        # Keyword kontrolü (goods/services'de)
        for keyword in cls.INTERESTING_KEYWORDS:
            if keyword in goods:
                return True, f"📦 '{keyword}' ürün/hizmetinde"
        
        # Class kontrolü
        if int_class in cls.INTERESTING_CLASSES:
            # Sadece class yeterli değil, en az bir ilginç özellik daha olmalı
            if len(mark_name) <= 3 or any(c.isdigit() for c in mark_name):
                return True, f"🏷️ Tech class ({int_class}) + kısa/unique isim"
        
        return False, ""
    
    @classmethod
    def filter_interesting(cls, trademarks: List[Dict]) -> List[Dict]:
        """İlginç trademark'ları filtrele"""
        interesting = []
        for tm in trademarks:
            is_interesting, reason = cls.is_interesting(tm)
            if is_interesting:
                tm["interest_reason"] = reason
                interesting.append(tm)
        return interesting


def test_scraper():
    """Scraper'ı test et"""
    scraper = TSDRScraper(rate_limit_delay=0.5)
    
    # Tek bir trademark test et
    print("\n=== Tek Trademark Test ===")
    tm = scraper.fetch_trademark(99530000)
    if tm:
        print(json.dumps(tm, indent=2, ensure_ascii=False))
    
    # Son 20 trademark'ı tara
    print("\n=== Son 20 Trademark ===")
    trademarks = scraper.scan_new_trademarks(count=20)
    
    print(f"\nToplam: {len(trademarks)} trademark bulundu")
    
    # Filtreleme test
    print("\n=== İlginç Olanlar ===")
    interesting = TrademarkFilter.filter_interesting(trademarks)
    for tm in interesting:
        print(f"- {tm['mark_name']}: {tm.get('interest_reason', 'N/A')}")
    
    print(f"\nİlginç: {len(interesting)} / {len(trademarks)}")


if __name__ == "__main__":
    test_scraper()

"""
FilingWatch - USPTO Trademark Filing Bot
RapidAPI USPTO Trademark API kullanarak trademark başvurularını çeker ve tweet atar.
"""

import os
import requests
import tweepy
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
import time
import logging
import hashlib

# Logging ayarları - Detaylı
logging.basicConfig(
    filename='filingwatch.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
)

# Console handler ekle
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
logging.getLogger().addHandler(console_handler)

# .env dosyasından API key'leri yükle
load_dotenv()

# X (Twitter) API credentials
X_API_KEY = os.getenv("X_API_KEY")
X_API_SECRET = os.getenv("X_API_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")

# RapidAPI credentials
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "uspto-trademark.p.rapidapi.com"

# Cache ayarları
CACHE_FILE = "trademark_cache.json"
CACHE_EXPIRY_HOURS = 6  # Cache 6 saat geçerli
POSTED_TWEETS_FILE = "posted_tweets.json"  # Daha önce atılan tweetler

# İzlenecek büyük şirketler
BIG_COMPANIES = [
    "apple", "google", "microsoft", "amazon", "meta", "facebook",
    "tesla", "nvidia", "netflix", "spotify", "uber", "airbnb",
    "openai", "anthropic", "adobe", "salesforce", "oracle", "ibm",
    "samsung", "sony", "nintendo", "disney", "warner", "paramount",
    "coca-cola", "pepsi", "nike", "adidas", "mcdonald", "starbucks",
    "visa", "mastercard", "paypal", "stripe", "coinbase", "binance",
    "tiktok", "bytedance", "snapchat", "twitter", "linkedin",
    "walmart", "target", "costco", "ford", "gm", "toyota", "honda",
    "pfizer", "moderna", "merck", "boeing", "spacex",
    "intel", "amd", "qualcomm", "cisco", "zoom", "dropbox",
    "robinhood", "square", "block", "rivian", "lucid",
    "palantir", "snowflake", "databricks", "mongodb"
]

# İlginç keyword'ler (trademark adında aranacak)
INTERESTING_KEYWORDS = [
    "ai", "gpt", "llm", "neural", "machine learning", "copilot",
    "metaverse", "virtual reality", "vr", "ar", "mixed reality",
    "crypto", "blockchain", "nft", "web3", "defi", "bitcoin",
    "quantum", "robotics", "autonomous", "self-driving",
    "space", "satellite", "rocket", "mars", "lunar",
    "biotech", "gene", "therapeutic",
    "gaming", "esports", "streaming",
    "fintech", "neobank", "wallet",
    "cloud", "saas", "electric", "ev", "battery"
]


# ============== CACHE FONKSİYONLARI ==============

def load_cache():
    """Cache dosyasını yükle"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
                logging.debug(f"Cache yüklendi: {len(cache.get('data', {}))} kayıt")
                return cache
    except Exception as e:
        logging.error(f"Cache yükleme hatası: {e}")
    return {"timestamp": None, "data": {}}


def save_cache(cache):
    """Cache'i dosyaya kaydet"""
    try:
        cache["timestamp"] = datetime.now().isoformat()
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        logging.debug(f"Cache kaydedildi: {len(cache.get('data', {}))} kayıt")
    except Exception as e:
        logging.error(f"Cache kaydetme hatası: {e}")


def is_cache_valid(cache):
    """Cache'in hala geçerli olup olmadığını kontrol et"""
    if not cache.get("timestamp"):
        return False
    
    try:
        cache_time = datetime.fromisoformat(cache["timestamp"])
        expiry_time = cache_time + timedelta(hours=CACHE_EXPIRY_HOURS)
        is_valid = datetime.now() < expiry_time
        logging.debug(f"Cache geçerliliği: {is_valid} (Son güncelleme: {cache_time})")
        return is_valid
    except Exception as e:
        logging.error(f"Cache geçerlilik kontrolü hatası: {e}")
        return False


def get_cache_key(keywords):
    """Arama için benzersiz cache key oluştur"""
    key_str = json.dumps(sorted(keywords) if isinstance(keywords, list) else [keywords])
    return hashlib.md5(key_str.encode()).hexdigest()


def load_posted_tweets():
    """Daha önce atılan tweetlerin serial number'larını yükle"""
    try:
        if os.path.exists(POSTED_TWEETS_FILE):
            with open(POSTED_TWEETS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logging.debug(f"Posted tweets yüklendi: {len(data.get('serial_numbers', []))} kayıt")
                return data
    except Exception as e:
        logging.error(f"Posted tweets yükleme hatası: {e}")
    return {"serial_numbers": [], "tweets": []}


def save_posted_tweet(serial_number, tweet_text, tweet_id):
    """Atılan tweet'i kaydet"""
    try:
        data = load_posted_tweets()
        data["serial_numbers"].append(serial_number)
        data["tweets"].append({
            "serial_number": serial_number,
            "tweet_id": tweet_id,
            "tweet_text": tweet_text[:100],
            "posted_at": datetime.now().isoformat()
        })
        
        # Max 1000 kayıt tut
        if len(data["serial_numbers"]) > 1000:
            data["serial_numbers"] = data["serial_numbers"][-1000:]
            data["tweets"] = data["tweets"][-1000:]
        
        with open(POSTED_TWEETS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info(f"Tweet kaydedildi: {serial_number}")
    except Exception as e:
        logging.error(f"Posted tweet kaydetme hatası: {e}")


def is_already_posted(serial_number):
    """Bu trademark için daha önce tweet atılmış mı?"""
    data = load_posted_tweets()
    return serial_number in data.get("serial_numbers", [])


# ============== API FONKSİYONLARI ==============

def get_x_client():
    """Twitter API v2 client oluştur"""
    client = tweepy.Client(
        bearer_token=X_BEARER_TOKEN,
        consumer_key=X_API_KEY,
        consumer_secret=X_API_SECRET,
        access_token=X_ACCESS_TOKEN,
        access_token_secret=X_ACCESS_TOKEN_SECRET
    )
    return client


def batch_trademark_search(keywords, use_cache=True):
    """
    RapidAPI üzerinden batch trademark ara (POST /v1/batchTrademarkSearch)
    keywords: list of strings
    use_cache: Cache kullan mı?
    Returns: list of trademark results
    """
    
    # Cache kontrolü
    cache_key = get_cache_key(keywords)
    cache = load_cache()
    
    if use_cache and is_cache_valid(cache):
        cached_data = cache.get("data", {}).get(cache_key)
        if cached_data:
            logging.debug(f"Cache hit: {keywords}")
            print(f"      📦 Cache'den alındı ({len(cached_data)} sonuç)")
            return cached_data
    
    logging.debug(f"Cache miss, API çağrılıyor: {keywords}")
    
    url = "https://uspto-trademark.p.rapidapi.com/v1/batchTrademarkSearch"

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # keywords JSON array olarak gönderilmeli
    keywords_json = json.dumps(keywords if isinstance(keywords, list) else [keywords])
    data = f"keywords={keywords_json}"

    all_results = []
    
    try:
        # İlk istek
        logging.debug(f"API Request: POST {url} - keywords: {keywords}")
        start_time = time.time()
        response = requests.post(url, headers=headers, data=data, timeout=30)
        elapsed = time.time() - start_time
        logging.debug(f"API Response: {response.status_code} in {elapsed:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            count = result.get('count', 0)
            scroll_id = result.get('scroll_id', '')
            print(f"      ✅ {count} sonuç bulundu")
            logging.info(f"API batch search [{keywords}]: {count} sonuç, {elapsed:.2f}s")
            
            # Scroll ile sonuçları çek
            if scroll_id and count > 0:
                scroll_data = f"keywords={keywords_json}&scroll_id={scroll_id}"
                logging.debug(f"Scroll request yapılıyor...")
                scroll_response = requests.post(url, headers=headers, data=scroll_data, timeout=30)
                
                if scroll_response.status_code == 200:
                    scroll_result = scroll_response.json()
                    if isinstance(scroll_result, list):
                        all_results = scroll_result
                    elif isinstance(scroll_result, dict):
                        all_results = scroll_result.get('items', scroll_result.get('results', []))
                        # Eğer dönen verinin içinde liste varsa
                        if not all_results and any(isinstance(v, list) for v in scroll_result.values()):
                            for v in scroll_result.values():
                                if isinstance(v, list) and len(v) > 0:
                                    all_results = v
                                    break
                    logging.debug(f"Scroll sonucu: {len(all_results)} kayıt")
            
            # Cache'e kaydet
            final_results = all_results[:50]  # Max 50 sonuç
            if final_results:
                if "data" not in cache:
                    cache["data"] = {}
                cache["data"][cache_key] = final_results
                save_cache(cache)
                logging.debug(f"Cache güncellendi: {cache_key}")
            
            return final_results
        else:
            print(f"      ❌ HTTP {response.status_code}: {response.text[:100]}")
            logging.warning(f"API hatası [{keywords}]: {response.status_code} - {response.text[:200]}")
            return []
            
    except requests.exceptions.Timeout:
        print(f"      ❌ Timeout!")
        logging.error(f"API timeout [{keywords}]")
        return []
    except requests.exceptions.ConnectionError as e:
        print(f"      ❌ Bağlantı hatası!")
        logging.error(f"API connection error [{keywords}]: {e}")
        return []
    except Exception as e:
        print(f"      ❌ Exception: {str(e)[:50]}")
        logging.error(f"API hatası [{keywords}]: {e}", exc_info=True)
        return []


def search_trademarks_by_owner(owner_name):
    """
    RapidAPI üzerinden şirket adına göre trademark ara
    """
    return batch_trademark_search([owner_name])


def search_trademarks_by_keyword(keyword):
    """
    RapidAPI üzerinden keyword'e göre trademark ara
    """
    return batch_trademark_search([keyword])


def get_recent_filings_by_company(company_name):
    """
    Belirli bir şirketin son trademark başvurularını getir
    """
    print(f"   🔍 {company_name} araması yapılıyor...")
    
    results = batch_trademark_search([company_name])
    
    if not results:
        return []
    
    trademarks = []
    
    for item in results[:10]:  # Her şirketten max 10 sonuç
        try:
            # Sadece aktif/yeni başvuruları al
            status = str(item.get('status_label', item.get('status', ''))).lower()
            if 'dead' in status or 'abandoned' in status or 'cancelled' in status:
                continue
            
            # Yeni API yapısına göre field'ları al
            tm = {
                'serial_number': item.get('serial_number', item.get('serialNumber', '')),
                'mark_name': item.get('keyword', item.get('wordMark', item.get('mark_name', ''))),
                'owner': get_owner_name(item),
                'filing_date': item.get('filing_date', item.get('filingDate', '')),
                'status': item.get('status_label', item.get('status', '')),
                'class': '',
                'description': item.get('description', '')[:200] if item.get('description') else ''
            }
            
            if tm['mark_name']:
                trademarks.append(tm)
                
        except Exception as e:
            logging.error(f"Trademark parse hatası: {e}")
            continue
    
    return trademarks


def get_owner_name(item):
    """API sonucundan owner adını çıkar"""
    # Önce owners listesine bak
    owners = item.get('owners', [])
    if owners and isinstance(owners, list) and len(owners) > 0:
        return owners[0].get('name', 'Unknown')
    
    # Alternatif field'lara bak
    return item.get('ownerName', item.get('owner', 'Unknown'))


def fetch_recent_trademarks():
    """
    Büyük şirketlerin son trademark başvurularını çek
    """
    all_trademarks = []
    
    print("🔍 Büyük şirketlerin trademark'ları aranıyor...")
    
    # En popüler şirketleri ara (API limitini aşmamak için)
    priority_companies = [
        "Apple", "Google", "Microsoft", "Amazon", "Meta",
        "Tesla", "OpenAI", "Nvidia", "Netflix", "Disney",
        "Nike", "Coinbase", "SpaceX", "Adobe", "Salesforce"
    ]
    
    for company in priority_companies:
        trademarks = get_recent_filings_by_company(company)
        all_trademarks.extend(trademarks)
        
        # Rate limit için kısa bekle
        time.sleep(0.5)
    
    # Ayrıca ilginç keyword'leri ara
    print("\n🔍 İlginç keyword'ler aranıyor...")
    
    interesting_searches = ["AI", "GPT", "metaverse", "crypto", "quantum"]
    
    for keyword in interesting_searches:
        print(f"   🔍 '{keyword}' araması yapılıyor...")
        results = batch_trademark_search([keyword])
        
        if results:
            for item in results[:5]:
                try:
                    status = str(item.get('status_label', item.get('status', ''))).lower()
                    if 'dead' in status or 'abandoned' in status:
                        continue
                    
                    tm = {
                        'serial_number': item.get('serial_number', ''),
                        'mark_name': item.get('keyword', item.get('wordMark', '')),
                        'owner': get_owner_name(item),
                        'filing_date': item.get('filing_date', ''),
                        'status': item.get('status_label', ''),
                        'class': '',
                        'description': item.get('description', '')[:200] if item.get('description') else ''
                    }
                    
                    if tm['mark_name']:
                        all_trademarks.append(tm)
                        
                except Exception as e:
                    continue
        
        time.sleep(0.5)
    
    # Duplikasyonları kaldır
    seen = set()
    unique_trademarks = []
    for tm in all_trademarks:
        key = (tm.get('serial_number'), tm.get('mark_name'))
        if key not in seen and tm.get('mark_name'):
            seen.add(key)
            unique_trademarks.append(tm)
    
    return unique_trademarks


def filter_interesting_trademarks(trademarks):
    """İlginç trademark'ları filtrele"""
    interesting = []
    skipped_already_posted = 0
    
    logging.info(f"Filtreleme başlıyor: {len(trademarks)} trademark")
    
    for tm in trademarks:
        serial_number = tm.get("serial_number", "")
        
        # Daha önce tweet atılmış mı?
        if serial_number and is_already_posted(serial_number):
            skipped_already_posted += 1
            logging.debug(f"Atlandı (zaten paylaşıldı): {tm.get('mark_name')} - {serial_number}")
            continue
        
        owner_lower = tm.get("owner", "").lower()
        mark_lower = tm.get("mark_name", "").lower()
        
        # Büyük şirket mi?
        is_big_company = any(company in owner_lower for company in BIG_COMPANIES)
        
        # İlginç keyword var mı?
        has_keyword = any(kw in mark_lower for kw in INTERESTING_KEYWORDS)
        
        if is_big_company or has_keyword:
            tm["reason"] = []
            if is_big_company:
                tm["reason"].append("big_company")
                logging.debug(f"Big company match: {tm.get('mark_name')} - Owner: {tm.get('owner')}")
            if has_keyword:
                tm["reason"].append("interesting_keyword")
                logging.debug(f"Keyword match: {tm.get('mark_name')}")
            interesting.append(tm)
    
    logging.info(f"Filtreleme tamamlandı: {len(interesting)} ilginç, {skipped_already_posted} daha önce paylaşılmış")
    
    return interesting


def format_tweet(trademark):
    """Trademark bilgisini tweet formatına çevir"""
    
    mark_name = trademark.get("mark_name", "Unknown")
    owner = trademark.get("owner", "Unknown")
    filing_date = trademark.get("filing_date", "")
    tm_class = trademark.get("class", "")
    
    # Class bilgisini düzenle
    if tm_class:
        tm_class = f"Class {tm_class}" if not str(tm_class).startswith("Class") else tm_class
    
    # Tarih formatını düzenle
    if filing_date and len(filing_date) >= 10:
        filing_date = filing_date[:10]
    
    tweet = f"""👀 New trademark filed

🏢 {owner}
📝 "{mark_name}"
🏷️ {tm_class}
📅 Filed: {filing_date}

What could this be? 🤔

#Trademark #USPTO #Tech"""

    # Tweet 280 karakter limitine uygun mu kontrol et
    if len(tweet) > 280:
        tweet = f"""👀 New trademark filed

🏢 {owner}
📝 "{mark_name}"
📅 {filing_date}

#Trademark #USPTO"""
    
    return tweet


def post_tweet(client, tweet_text, serial_number=None):
    """Tweet at ve kaydet"""
    try:
        logging.debug(f"Tweet gönderiliyor: {tweet_text[:50]}...")
        response = client.create_tweet(text=tweet_text)
        tweet_id = response.data['id']
        print(f"✅ Tweet atıldı! ID: {tweet_id}")
        logging.info(f"Tweet atıldı: {tweet_id} - {tweet_text[:50]}...")
        
        # Atılan tweet'i kaydet
        if serial_number:
            save_posted_tweet(serial_number, tweet_text, tweet_id)
        
        return True, tweet_id
    except tweepy.errors.TooManyRequests as e:
        print(f"❌ Rate limit aşıldı! Biraz bekleyin.")
        logging.error(f"Tweet rate limit: {e}")
        return False, None
    except tweepy.errors.Forbidden as e:
        print(f"❌ Tweet izni yok: {e}")
        logging.error(f"Tweet forbidden: {e}")
        return False, None
    except Exception as e:
        print(f"❌ Tweet hatası: {e}")
        logging.error(f"Tweet hatası: {e}", exc_info=True)
        return False, None


def preview_mode(trademarks):
    """Tweet atmadan önce kullanıcıya göster"""
    print("\n" + "="*50)
    print("📋 BULUNAN İLGİNÇ TRADEMARK'LAR")
    print("="*50)
    
    approved = []
    
    for i, tm in enumerate(trademarks, 1):
        tweet = format_tweet(tm)
        
        print(f"\n--- #{i}/{len(trademarks)} ---")
        print(f"Şirket: {tm.get('owner', 'N/A')}")
        print(f"Marka: {tm.get('mark_name', 'N/A')}")
        print(f"Sebep: {', '.join(tm.get('reason', []))}")
        print("-" * 30)
        print(tweet)
        print(f"\n[Karakter: {len(tweet)}/280]")
        
        while True:
            choice = input("\n✅ Tweet at (y) | ❌ Atla (n) | 🛑 Çık (q): ").lower().strip()
            if choice in ['y', 'n', 'q']:
                break
            print("Geçersiz seçim. y/n/q girin.")
        
        if choice == 'y':
            approved.append(tm)
            print("→ Listeye eklendi")
        elif choice == 'q':
            print("Çıkılıyor...")
            break
        else:
            print("→ Atlandı")
    
    return approved


def main():
    print("""
    ╔═══════════════════════════════════════╗
    ║     🔍 FilingWatch - USPTO Bot        ║
    ║     Trademark Filing Tracker          ║
    ╚═══════════════════════════════════════╝
    """)
    
    logging.info("FilingWatch başlatıldı")
    
    # API credentials kontrolü
    if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET]):
        print("❌ X API credentials eksik! .env dosyasını kontrol et.")
        return
    
    if not RAPIDAPI_KEY:
        print("❌ RapidAPI key eksik! .env dosyasına RAPIDAPI_KEY ekle.")
        return
    
    # X client oluştur
    print("🔗 X API'ye bağlanılıyor...")
    x_client = get_x_client()
    
    # USPTO'dan veri çek
    print("\n📥 USPTO trademark verileri çekiliyor (RapidAPI)...\n")
    all_trademarks = fetch_recent_trademarks()
    print(f"\n   📊 Toplam {len(all_trademarks)} kayıt bulundu")
    
    if not all_trademarks:
        print("\n😕 Trademark bulunamadı. API key'i kontrol et.")
        return
    
    # Filtrele
    print("\n🔎 İlginç trademark'lar filtreleniyor...")
    interesting = filter_interesting_trademarks(all_trademarks)
    print(f"   {len(interesting)} ilginç kayıt bulundu")
    
    if not interesting:
        print("\n😕 İlginç trademark bulunamadı.")
        return
    
    # Kullanıcıya göster ve onay al
    approved = preview_mode(interesting)
    
    if not approved:
        print("\n👋 Hiçbir tweet onaylanmadı. Çıkılıyor.")
        return
    
    # Onaylananları tweetle
    print(f"\n🚀 {len(approved)} tweet atılacak...")
    
    success_count = 0
    for i, tm in enumerate(approved, 1):
        tweet_text = format_tweet(tm)
        print(f"\n[{i}/{len(approved)}] Tweet atılıyor...")
        
        serial_number = tm.get("serial_number", "")
        success, tweet_id = post_tweet(x_client, tweet_text, serial_number)
        if success:
            success_count += 1
        
        if success and i < len(approved):
            print("⏳ 30 saniye bekleniyor (rate limit)...")
            time.sleep(30)
    
    print(f"\n✅ Tamamlandı! {success_count}/{len(approved)} tweet başarılı.")
    logging.info(f"Tamamlandı: {success_count}/{len(approved)} tweet")


def clear_cache():
    """Cache'i temizle (debug için)"""
    try:
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
            print("✅ Cache temizlendi")
            logging.info("Cache temizlendi")
    except Exception as e:
        print(f"❌ Cache temizleme hatası: {e}")


def show_stats():
    """İstatistikleri göster"""
    print("\n📊 İSTATİSTİKLER")
    print("="*40)
    
    # Cache durumu
    cache = load_cache()
    if cache.get("timestamp"):
        print(f"📦 Cache: {len(cache.get('data', {}))} arama sonucu")
        print(f"   Son güncelleme: {cache['timestamp']}")
        print(f"   Geçerli: {'✅ Evet' if is_cache_valid(cache) else '❌ Hayır'}")
    else:
        print("📦 Cache: Boş")
    
    # Tweet durumu
    tweets = load_posted_tweets()
    print(f"\n🐦 Atılan tweetler: {len(tweets.get('serial_numbers', []))}")
    if tweets.get('tweets'):
        last_tweet = tweets['tweets'][-1]
        print(f"   Son tweet: {last_tweet.get('posted_at', 'N/A')}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--clear-cache":
            clear_cache()
        elif sys.argv[1] == "--stats":
            show_stats()
        elif sys.argv[1] == "--no-cache":
            # Cache kullanmadan çalıştır
            print("⚠️ Cache devre dışı bırakıldı")
            main()
        elif sys.argv[1] == "--help":
            print("""
FilingWatch - USPTO Trademark Bot

Kullanım:
  python main.py              Normal çalıştır (cache kullanır)
  python main.py --no-cache   Cache kullanmadan çalıştır
  python main.py --clear-cache  Cache'i temizle
  python main.py --stats      İstatistikleri göster
  python main.py --help       Bu yardımı göster
            """)
        else:
            print(f"Bilinmeyen parametre: {sys.argv[1]}")
            print("Yardım için: python main.py --help")
    else:
        main()
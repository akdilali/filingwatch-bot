"""
FilingWatch v2.1 - USPTO Trademark Filing Bot
============================================
- TSDR Scraping ile gerçek zamanlı veri (1-2 gün gecikme)
- Günlük cache - aynı gün tekrar indirmez
- Akıllı filtreleme - sıkıcıları çıkarır, ilginçleri önceliklendirir
- Günde 3-4 tweet için optimize edilmiş
"""

import os
import sys
import tweepy
from dotenv import load_dotenv
from datetime import datetime, date
import json
import time
import logging
import logging
import random
import re
from typing import Optional, List, Dict

from tsdr_scraper import TSDRScraper
from visuals import generate_trademark_card
from history_manager import HistoryManager
from analyzer import Analyzer
from weird_filter import WeirdFilter
from openai import OpenAI

# ============== LOGGING ==============
logging.basicConfig(
    filename='filingwatch.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
logging.getLogger().addHandler(console)

load_dotenv()

# ============== CONFIG ==============
X_API_KEY = os.getenv("X_API_KEY")
X_API_SECRET = os.getenv("X_API_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")

X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")

# Company Handles Tracking
KNOWN_COMPANIES = {
    "APPLE": "@Apple",
    "GOOGLE": "@Google",
    "AMAZON": "@amazon",
    "MICROSOFT": "@Microsoft",
    "META PLATFORMS": "@Meta",
    "FACEBOOK": "@Meta",
    "TESLA": "@Tesla",
    "SPACEX": "@SpaceX",
    "NETFLIX": "@netflix",
    "DISNEY": "@Disney",
    "NVIDIA": "@nvidia",
    "SAMSUNG": "@Samsung",
    "SONY": "@Sony",
    "NIKE": "@Nike",
    "ADIDAS": "@adidas",
    "INTEL": "@intel",
    "AMD": "@AMD",
    "IBM": "@IBM",
    "ORACLE": "@Oracle",
    "UBER": "@Uber",
    "AIRBNB": "@Airbnb",
    "SPOTIFY": "@Spotify",
    "PAYPAL": "@PayPal",
    "SNAP INC": "@Snap",
    "REDDIT": "@Reddit",
    "ZOOM VIDEO": "@Zoom",
    "SALESFORCE": "@Salesforce",
    "ADOBE": "@Adobe",
    
    # AUTO
    "FORD": "@Ford",
    "GENERAL MOTORS": "@GM",
    "TOYOTA": "@Toyota",
    "HONDA": "@Honda",
    "BMW": "@BMW",
    "MERCEDES": "@MercedesBenz",
    "PORSCHE": "@Porsche",
    "FERRARI": "@Ferrari",
    "HYUNDAI": "@Hyundai_Global",
    "RIVIAN": "@Rivian",
    "LUCID": "@LucidMotors",
    
    # FOOD & BEV
    "COCA-COLA": "@CocaCola",
    "PEPSICO": "@PepsiCo",
    "MCDONALD'S": "@McDonalds",
    "STARBUCKS": "@Starbucks",
    "BURGER KING": "@BurgerKing",
    "KFC": "@kfc",
    "TACO BELL": "@tacobell",
    "NESTLE": "@Nestle",
    "DANONE": "@Danone",
    "RED BULL": "@redbull",
    
    # RETAIL & FASHION
    "WALMART": "@Walmart",
    "TARGET": "@Target",
    "HOME DEPOT": "@HomeDepot",
    "COSTCO": "@Costco",
    "LOUIS VUITTON": "@LouisVuitton",
    "GUCCI": "@gucci",
    "PRADA": "@Prada",
    "ROLEX": "@ROLEX",
    "LEGO": "@LEGO_Group",
    "IKEA": "@IKEA",
    
    # FINANCE
    "VISA": "@Visa",
    "MASTERCARD": "@Mastercard",
    "AMERICAN EXPRESS": "@AmericanExpress",
    "JPMORGAN": "@jpmorgan",
    "GOLDMAN SACHS": "@GoldmanSachs",
    "COINBASE": "@coinbase",
    "BINANCE": "@binance",
    "BLOCK INC": "@blocks", # Square
    
    # MEDIA & GAMES
    "WARNER BROS": "@wbd",
    "UNIVERSAL": "@UniversalPics",
    "NINTENDO": "@NintendoAmerica",
    "ACTIVISION": "@Activision",
    "ELECTRONIC ARTS": "@EA",
    "EPIC GAMES": "@EpicGames",
    "ROBLOX": "@Roblox",
    "OPENAI": "@OpenAI",
}

# Stock Tickers (Cashtags) - Public Companies Only
KNOWN_TICKERS = {
    "APPLE": "$AAPL",
    "GOOGLE": "$GOOGL",
    "AMAZON": "$AMZN",
    "MICROSOFT": "$MSFT",
    "META PLATFORMS": "$META",
    "FACEBOOK": "$META",
    "TESLA": "$TSLA",
    "NETFLIX": "$NFLX",
    "DISNEY": "$DIS",
    "NVIDIA": "$NVDA",
    "SAMSUNG": "$SSNLF",
    "SONY": "$SONY",
    "NIKE": "$NKE",
    "ADIDAS": "$ADDYY",
    "INTEL": "$INTC",
    "AMD": "$AMD",
    "IBM": "$IBM",
    "ORACLE": "$ORCL",
    "UBER": "$UBER",
    "AIRBNB": "$ABNB",
    "SPOTIFY": "$SPOT",
    "PAYPAL": "$PYPL",
    "SNAP INC": "$SNAP",
    "REDDIT": "$RDDT",
    "ZOOM VIDEO": "$ZM",
    "SALESFORCE": "$CRM",
    "ADOBE": "$ADBE",
    "FORD": "$F",
    "GENERAL MOTORS": "$GM",
    "TOYOTA": "$TM",
    "HONDA": "$HMC",
    "BMW": "$BMWYY",
    "MERCEDES": "$MBGYY",
    "PORSCHE": "$DRPRY",
    "FERRARI": "$RACE",
    "RIVIAN": "$RIVN",
    "LUCID": "$LCID",
    "COCA-COLA": "$KO",
    "PEPSICO": "$PEP",
    "MCDONALD'S": "$MCD",
    "STARBUCKS": "$SBUX",
    "BURGER KING": "$QSR",
    "KFC": "$YUM",
    "TACO BELL": "$YUM",
    "NESTLE": "$NSRGY",
    "DANONE": "$DANOY",
    "WALMART": "$WMT",
    "TARGET": "$TGT",
    "HOME DEPOT": "$HD",
    "COSTCO": "$COST",
    "LOUIS VUITTON": "$LVMUY",
    "GUCCI": "$PPRUY",
    "VISA": "$V",
    "MASTERCARD": "$MA",
    "AMERICAN EXPRESS": "$AXP",
    "JPMORGAN": "$JPM",
    "GOLDMAN SACHS": "$GS",
    "COINBASE": "$COIN",
    "BLOCK INC": "$SQ",
    "WARNER BROS": "$WBD",
    "UNIVERSAL": "$CMCSA",
    "NINTENDO": "$NTDOY",
    "ELECTRONIC ARTS": "$EA",
    "ROBLOX": "$RBLX"
}

# Dosyalar
DAILY_CACHE_FILE = "daily_cache.json"  # Günlük cache
POSTED_FILE = "posted_tweets.json"     # Atılan tweetler
STATE_FILE = "bot_state.json"          # Bot durumu

# Rate limit - Daha hızlı çekmek için düşürdük (USPTO'yu zorlamayalım ama)
RATE_LIMIT_DELAY = 0.15  # 0.15 saniye = ~7 istek/saniye
MAX_TWEETS_PER_RUN = 2   # Her çalışmada max 2 tweet (User isteği)


# ============== GÜNLÜK CACHE ==============

def get_today_str() -> str:
    """Bugünün tarihini YYYY-MM-DD formatında döndür"""
    return date.today().isoformat()


def load_daily_cache() -> Dict:
    """Günlük cache'i yükle - last_serial'ı her zaman koru!"""
    try:
        if os.path.exists(DAILY_CACHE_FILE):
            with open(DAILY_CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
                # Bugünün cache'i mi kontrol et
                if cache.get('date') == get_today_str():
                    logging.info(f"📦 Cache yüklendi: {len(cache.get('trademarks', []))} trademark")
                    return cache
                else:
                    # Yeni gün ama last_serial'ı koru!
                    old_serial = cache.get('last_serial')
                    logging.info(f"📅 Cache eski, yeni gün - son serial {old_serial}'den devam edilecek")
                    return {'date': None, 'trademarks': [], 'last_serial': old_serial}
    except Exception as e:
        logging.error(f"Cache yükleme hatası: {e}")
    
    return {'date': None, 'trademarks': [], 'last_serial': None}


def save_daily_cache(trademarks: List[Dict], last_serial: int):
    """Günlük cache'i kaydet"""
    try:
        cache = {
            'date': get_today_str(),
            'trademarks': trademarks,
            'last_serial': last_serial,
            'saved_at': datetime.now().isoformat()
        }
        with open(DAILY_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False)
        logging.info(f"💾 Cache kaydedildi: {len(trademarks)} trademark")
    except Exception as e:
        logging.error(f"Cache kaydetme hatası: {e}")


def get_trademarks_for_today() -> List[Dict]:
    """
    Bugünkü trademark'ları al - AKILLI TARAMA (Incremental)
    
    1. Cache'i yükle (varsa)
    2. USPTO'dan en son serial'i kontrol et
    3. Cache'deki son serial ile USPTO arasındaki farkı kapat
    4. Sadece YENİ olanları listeye ve cache'e ekle
    """
    cache = load_daily_cache()
    cached_trademarks = []
    last_known_serial = None

    # Cache varsa yükle
    if cache.get('date') == get_today_str():
        cached_trademarks = cache.get('trademarks', [])
        last_known_serial = cache.get('last_serial')
        print(f"📦 Cache'de {len(cached_trademarks)} kayıt var (Son serial: {last_known_serial})")
    else:
        # Cache yoksa veya tarih eskiyse last_serial'ı koru (dünden kalan) ama listeyi sıfırla
        last_known_serial = cache.get('last_serial')
        print(f"🔄 Günlük liste sıfır (Dünden kalan serial: {last_known_serial})")

    # TSDR Scraper Başlat
    scraper = TSDRScraper(rate_limit_delay=RATE_LIMIT_DELAY)
    
    # Şu anki en son serial kaç?
    latest_serial = scraper.find_latest_serial()
    
    # Initialize History Manager
    history_manager = HistoryManager()

    # Eğer hiç last_known yoksa (ilk kurulum), simülasyon için son 200'ü al
    if not last_known_serial:
        # İLK ÇALIŞMA: Son 200 serial'ı tara (~3 saatlik güncel veri)
        INITIAL_SERIAL_RANGE = 200
        start_serial = latest_serial - INITIAL_SERIAL_RANGE
        print(f"\n📡 İlk tarama (Sıfırdan): {start_serial} → {latest_serial}")
        print(f"   {INITIAL_SERIAL_RANGE} serial taranacak (~3 saatlik güncel veri)")
        new_trademarks = scraper.scan_range(start_serial, latest_serial)
        
        # Save to History (PERSISTENCE)
        if new_trademarks:
            history_manager.append_to_history(new_trademarks)
        
        # Hepsini ekle
        cached_trademarks.extend(new_trademarks)
        
    else:
        # INCREMENTAL TARAMA: Aradaki farkı bul
        diff = latest_serial - last_known_serial
        
        if diff > 0:
            print(f"\n📡 Incremental tarama: {last_known_serial} → {latest_serial}")
            print(f"🆕 {diff} yeni başvuru var, taranıyor...")
            
            # Güvenlik: Çok fazlaysa sınır koy (örn: 2000 - yaklaşık 1 günlük veri)
            MAX_CATCHUP = 2000
            if diff > MAX_CATCHUP:
                 print(f"⚠️ Çok fazla fark ({diff}), güvenlik için son {MAX_CATCHUP} başvuru taranacak (Max 1 Gün)")
                 last_known_serial = latest_serial - MAX_CATCHUP
            
            new_trademarks = scraper.scan_range(last_known_serial + 1, latest_serial)
            
            # Save to History (PERSISTENCE)
            if new_trademarks:
                history_manager.append_to_history(new_trademarks)
            
            # Yenileri ekle
            if new_trademarks:
                cached_trademarks.extend(new_trademarks)
                print(f"✅ {len(new_trademarks)} yeni trademark eklendi.")
        else:
            print("😴 Yeni başvuru yok, her şey güncel.")
    
    # Cache'i güncelle
    if cached_trademarks:
        # En büyük serial'ı bul (garanti olsun)
        all_serials = [int(tm.get('serial_number', 0)) for tm in cached_trademarks]
        final_last_serial = max(all_serials) if all_serials else latest_serial
        save_daily_cache(cached_trademarks, final_last_serial)
    else:
        # Hiçbir şey yoksa bile latest_serial'ı kaydet ki bir dahakine baştan başlamasın
        save_daily_cache([], latest_serial)
        
    return cached_trademarks


# ============== FİLTRELEME ==============

# 🔴 SIKICI - Bunları çıkar
BORING_PATTERNS = [
    # Eğitim
    'elementary school', 'high school', 'middle school', 'university', 'college', 'academy',
    # Din
    'church', 'ministry', 'chapel', 'cathedral', 'baptist', 'methodist', 'lutheran',
    # Kurumsal sıkıcı
    'foundation', 'association', 'society', 'federation', 'council', 'committee',
    # Hukuk
    'law office', 'law firm', 'attorney', 'legal services', 'lawyers', 'law group',
    # Emlak
    'realty', 'real estate', 'properties', 'mortgage', 'title company', 'homes',
    # Finans sıkıcı
    'insurance', 'accounting', 'tax service', 'bookkeeping', 'cpa',
    # Danışmanlık
    'consulting group', 'advisory', 'management consulting', 'solutions group',
    # Yatırım
    'holdings', 'investments', 'capital group', 'asset management', 'equity',
    # Cenaze
    'funeral', 'cemetery', 'memorial', 'mortuary',
    # Ev hizmetleri
    'plumbing', 'hvac', 'roofing', 'landscaping', 'lawn care', 'pest control',
    # Sağlık sıkıcı
    'dental', 'dentistry', 'orthodontic', 'chiropractic', 'physical therapy',
]

# 🟢 İLGİNÇ - Bunlara öncelik ver
INTERESTING_PATTERNS = [
    # Tech/AI - En önemli
    ' ai', 'ai ', '-ai', 'a.i.', 'gpt', 'llm', 'neural', 'quantum',
    'cyber', 'crypto', 'bitcoin', 'ethereum', 'nft', 'web3', 'defi',
    'blockchain', 'metaverse', 'virtual reality', 'vr', 'augmented',
    'machine learning', 'deep learning', 'artificial intelligence',
    'robot', 'automation', 'autonomous', 'self-driving', 'drone',
    'cloud', 'saas', 'fintech', 'biotech', 'cleantech', 'healthtech',
    'chatbot', 'copilot', 'assistant', 'smart',
    
    # Gaming/Entertainment
    'game', 'gaming', 'esport', 'streamer', 'twitch', 'discord',
    'anime', 'manga', 'cosplay', 'comic', 'superhero',
    
    # Lifestyle/Trendy
    'vibe', 'zen', 'mindful', 'wellness', 'organic', 'sustainable',
    'plant-based', 'vegan', 'eco-', 'green',
    
    # Fun/Creative
    'ninja', 'wizard', 'dragon', 'phoenix', 'cosmic', 'stellar', 'galaxy',
    'pixel', 'neon', 'retro', 'vintage', 'artisan', 'craft',
    'hustle', 'grind', 'boss', 'empire', 'kingdom', 'squad',
    
    # Trendy Food
    'brew', 'coffee', 'boba', 'matcha', 'acai', 'kombucha', 'sushi',
]




# 🟢 SCORE WEIGHTS
SCORE_RULES = {
    'known_company': 50,    # Apple, Google vs
    'ai_keyword': 25,       # AI, GPT, Neural
    'tech_keyword': 15,     # Crypto, Cloud, Cyber
    'cool_keyword': 10,     # Game, Vibe, Zen
    'tech_class': 10,       # Software, Electronics classes
    'boring_match': -100,   # Furniture, Law firm
    'short_name': 5         # < 6 chars
}

# 🏷️ INTERESTING CLASSES (International Class)
TECH_CLASSES = ['009', '035', '036', '038', '041', '042']

def calculate_importance_score(tm: Dict) -> tuple[int, List[str]]:
    """
    Trademark'a puan ver
    Returns: (score, reasons)
    """
    score = 0
    reasons = []
    
    name = (tm.get('mark_name') or '').lower().strip()
    owner = (tm.get('owner') or '').lower()
    goods = (tm.get('goods_services') or '').lower()
    int_class = str(tm.get('international_class', '')).zfill(3)
    
    # 0. Geçersiz isimler
    if not name or name == 'none' or len(name) < 2:
        return -999, ['❌ Geçersiz isim']
    
    # 1. Bilinen Şirketler (+50)
    for company in KNOWN_COMPANIES:
        # Regex ile tam kelime eşleşmesi (örn: "Intel" -> "Intelligent" eşleşmesin)
        pattern = r'\b' + re.escape(company.lower()) + r'\b'
        if re.search(pattern, owner):
            score += SCORE_RULES['known_company']
            reasons.append(f"🏢 {company.title()}")
            break
            
    # 2. Sıkıcı mı? (-100)
    for pattern in BORING_PATTERNS:
        if pattern in name or pattern in owner:
            score += SCORE_RULES['boring_match']
            reasons.append(f"❌ {pattern}")
            return score, reasons # Direkt dön, boşa işlem yapma
    
    # 3. AI Keywords (+25)
    # Regex ile tam kelime kontrolü (Cleaner AIR vs AI karışmaması için)
    ai_keywords = ['ai', 'gpt', 'llm', 'neural', 'machine learning', 'deep learning']
    for kw in ai_keywords:
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, name):
            score += SCORE_RULES['ai_keyword']
            reasons.append(f"🤖 {kw.upper()}")
            break
            
    # 4. Tech Keywords (+15)
    tech_keywords = ['crypto', 'metaverse', 'quantum', 'cyber', 'web3', 'blockchain', 'robot', 'drone', 'autonomous']
    for kw in tech_keywords:
        if kw in name or kw in goods:
            score += SCORE_RULES['tech_keyword']
            reasons.append(f"💡 {kw.title()}")
            break

    # 5. Cool/Trendy Keywords (+10)
    cool_keywords = ['game', 'gaming', 'studio', 'lab', 'labs', 'future', 'space', 'star', 'hyper', 'super']
    for kw in cool_keywords:
        if kw in name:
            score += SCORE_RULES['cool_keyword']
            reasons.append(f"✨ {kw.title()}")
            break
            
    # 6. Tech Classes (+10)
    if int_class in TECH_CLASSES:
        score += SCORE_RULES['tech_class']
        reasons.append(f"🏷️ Tech Class ({int_class})")
        
    # 7. Kısa İsim (+5)
    if len(name) <= 5 and name.isalpha():
        score += SCORE_RULES['short_name']
        reasons.append("📝 Short Name")
        
    return score, reasons


def filter_and_select(trademarks: List[Dict], max_tweets: int = 4) -> List[Dict]:
    """
    Puanlama sistemine göre en iyileri seç + 1 Tane Weird Candidate (Opsiyonel)
    """
    # Daha önce paylaşılanları yükle
    posted = load_posted()
    posted_serials = set(posted.get('serial_numbers', []))
    
    scored_items = []
    
    # --- PHASE 7: Weird Filter (with 24h Cooldown) ---
    weird_filter = WeirdFilter()
    weird_candidate = None
    
    # Son atılan weird tweet zamanını kontrol et
    last_weird_time_str = posted.get('last_weird_time')
    can_post_weird = True
    
    if last_weird_time_str:
        try:
            last_weird = datetime.fromisoformat(last_weird_time_str)
            if datetime.now() - last_weird < timedelta(hours=24):
                can_post_weird = False
                logging.info(f"⏳ Weird Tweet Cooldown: Son atılandan beri 24 saat geçmedi.")
        except:
            pass # Tarih bozuksa yoksay, izin ver

    for tm in trademarks:
        serial = tm.get('serial_number', '')
        
        if serial in posted_serials:
            continue
            
        score, reasons = calculate_importance_score(tm)
        
        # WEIRD CHECK (Sadece izin varsa)
        if can_post_weird:
            w_res = weird_filter.check_weirdness(tm.get('mark_name', ''), tm.get('goods_services', ''))
            if w_res['is_weird']:
                tm['weird_score'] = w_res['score']
                tm['weird_reason'] = w_res['reason']
                # En komiğini sakla
                if not weird_candidate or tm['weird_score'] > weird_candidate['weird_score']:
                    weird_candidate = tm
        
        # Normal Puanlama
        if score > 0:
            tm['score'] = score
            tm['reasons'] = reasons
            tm['category'] = 'must_post' if score >= 50 else 'interesting'
            tm['interest_reason'] = ', '.join(reasons[:2])
            scored_items.append(tm)
            
    # Puana göre sırala (Büyükten küçüğe)
    scored_items.sort(key=lambda x: x['score'], reverse=True)
    
    logging.info(f"📊 Puanlama sonucu: {len(scored_items)} aday tweet")
    
    final_selection = []
    
    # 1. Weird Candidate Ekle (ALTIN VURUŞ - Max 1)
    if weird_candidate:
        logging.info(f"🤪 Weird USPTO Bulundu: {weird_candidate['mark_name']} (Puan: {weird_candidate['weird_score']})")
        weird_candidate['category'] = 'weird'
        # Listede varsa çıkar (tekrar etmesin)
        scored_items = [item for item in scored_items if item['serial_number'] != weird_candidate['serial_number']]
        final_selection.append(weird_candidate)
    
    # 2. Geriye kalan boşlukları normal iyilerle doldur
    remaining = max_tweets - len(final_selection)
    if remaining > 0:
        final_selection.extend(scored_items[:remaining])
        
    return final_selection


# ============== TWEET ==============

def load_posted() -> Dict:
    try:
        if os.path.exists(POSTED_FILE):
            with open(POSTED_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {"serial_numbers": [], "tweets": []}


def save_posted(serial: str, text: str, tweet_id: str, category: str = ''):
    data = load_posted()
    data["serial_numbers"].append(serial)
    data["tweets"].append({
        "serial": serial,
        "tweet_id": tweet_id,
        "text": text[:80],
        "category": category, # Kategori bilgisini de tut
        "time": datetime.now().isoformat()
    })
    
    # WEIRD TIMESTAMPS
    if category == 'weird':
        data['last_weird_time'] = datetime.now().isoformat()
        
    # Max 500 kayıt tut
    data["serial_numbers"] = data["serial_numbers"][-500:]
    data["tweets"] = data["tweets"][-500:]
    with open(POSTED_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_x_client():
    return tweepy.Client(
        bearer_token=X_BEARER_TOKEN,
        consumer_key=X_API_KEY,
        consumer_secret=X_API_SECRET,
        access_token=X_ACCESS_TOKEN,
        access_token_secret=X_ACCESS_TOKEN_SECRET
    )


# ============== TWEET FORMATTING (AI & CLASSIC) ==============

def generate_ai_commentary(mark: str, goods: str, owner: str) -> str:
    """OpenAI kullanarak tweeti gazeteci gibi yorumla"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
        
    try:
        client = OpenAI(api_key=api_key)
        
        prompt = f"""
        Act as a snarky, cynical tech journalist (like TechCrunch or The Verge style).
        Write a SHORT tweet hook (max 130 chars) about this new trademark filing.
        Don't include the trademark name or owner in the hook unless necessary for the joke.
        Don't write the link. Don't use hashtags.
        Be opinionated. Speculate (responsibly). Use 1 emoji.
        
        Trademark: "{mark}"
        Owner: "{owner}"
        Description: "{goods[:200]}..."
        
        Output only the tweet text. No quotes.
        """
        
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60, # Restrict token output
            temperature=0.8
        )
        
        return resp.choices[0].message.content.strip()
        logging.error(f"AI Generation Error: {e}")
        return None

def generate_ai_weird_commentary(mark: str, goods: str, owner: str) -> str:
    """OpenAI ile garip markaları komedyen gibi yorumla"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key: return None
        
    try:
        client = OpenAI(api_key=api_key)
        
        prompt = f"""
        Act as a stand-up comedian or a confused internet user.
        We found a very weird/funny trademark filing. Roast it gently or express your confusion.
        Keep it SHORT (max 130 chars).
        Don't include the trademark name if possible (it's shown below).
        Use 1 funny emoji (like 💀, 😭, 🤨, 🤡).
        
        Trademark: "{mark}"
        Description: "{goods[:200]}..."
        
        Output only the tweet text.
        """
        
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.9 # Biraz daha yaratıcı olsun
        )
        
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"AI Weird Gen Error: {e}")
        return None

def format_tweet(tm: Dict) -> str:
    """Tweet formatla - AI destekli hibrit yapı"""
    mark = (tm.get('mark_name') or 'Unknown')[:40]
    serial = tm.get('serial_number', '')
    date_str = tm.get('filing_date_raw', '')
    owner = (tm.get('owner') or '')[:40]
    desc = (tm.get('goods_services') or '').strip()
    url = f"https://tsdr.uspto.gov/caseviewer/SNUM/{serial}"

    # 1. AI YORUMU DENE (Graceful Fallback)
    try:
        # Kategoriye göre prompt seç
        if tm.get('category') == 'weird':
            ai_text = generate_ai_weird_commentary(mark, desc, owner)
        else:
            ai_text = generate_ai_commentary(mark, desc, owner)
            
        if ai_text:
            # Başarılı! Hibrid Formatı Oluştur
                # Başarılı! Hibrid Formatı Oluştur
                # AI Hook + Structured Data Block
                
                # Description Truncate (Kısa tut)
                short_desc = (desc[:60] + '...') if len(desc) > 60 else desc
                
                data_block = f"📌 {mark}\n📝 {short_desc}\n🏢 {owner}"
                
                tweet = f"{ai_text}\n\n{data_block}\n\n🔗 {url}"
                
                # Hashtag ekle (AI genelde eklemez)
                hashtags = []
                text_lower = (mark + " " + desc).lower()
                if 'ai' in text_lower or 'gpt' in text_lower: hashtags.append("#AI")
                if 'crypto' in text_lower: hashtags.append("#Crypto")
                if 'game' in text_lower: hashtags.append("#Gaming")
                
                # Ticker check
                owner_lower = owner.lower()
                for company, ticker in KNOWN_TICKERS.items():
                    if company.lower() in owner_lower:
                        hashtags.append(ticker)
                        break
                        
                if hashtags:
                    tweet += "\n\n" + " ".join(hashtags)
                    
                return tweet[:280] # Garantile
    except:
        pass # Fallback to classic

    # 2. KLASİK FORMAT (Yedek)
    # Description (Goods/Services) - max 110 karakter (Optimize edildi)
    # desc = (tm.get('goods_services') or '').strip() # Already defined above
    # Gereksiz boşlukları ve satır sonlarını temizle
    desc = ' '.join(desc.split())
    if len(desc) > 110:
        desc = desc[:107] + "..."
    
    url = f"https://tsdr.uspto.gov/caseviewer/SNUM/{serial}"
    
    # Emoji
    # Emoji & Header Logic
    cat = tm.get('category', '')
    header_text = "NEW TRADEMARK FILED"
    
    if cat == 'weird':
        emoji = '🤪'
        header_text = "WEIRD TRADEMARK ALERT"
    elif cat == 'must_post':
        emoji = '🏢'
    elif 'ai' in mark.lower() or 'gpt' in mark.lower():
        emoji = '🤖'
    elif 'crypto' in mark.lower() or 'nft' in mark.lower():
        emoji = '🔗'
    elif 'game' in mark.lower():
        emoji = '🎮'
    elif 'food' in mark.lower() or 'drink' in mark.lower():
        emoji = '☕'
    else:
        emoji = '📝'
    
    # Replace Owner with Twitter Handle if known
    # Regex ile güvenli değişim
    owner_lower = owner.lower()
    for company, handle in KNOWN_COMPANIES.items():
        pattern = r'\b' + re.escape(company.lower()) + r'\b'
        if re.search(pattern, owner_lower):
             owner = f"{handle} ({owner})"
             break
             
    # Insider Text / Intro
    intro = ""
    score = tm.get('score', 0)
    
    if cat == 'weird':
        intros = [
            "🤯 You can't make this up...",
            "😵 Go Home USPTO, You're Drunk...",
            "🤨 Seriously?",
            "🤣 Best filing of the day:"
        ]
        intro = random.choice(intros) + "\n\n"
    elif cat == 'must_post' or score >= 50:
         intros = [
             "🚨 It hasn't hit the press yet...",
             "👀 Just In from USPTO...",
             "⚡ Breaking: New filing detected...",
             "💎 Hidden Gem Discovered..."
         ]
         intro = random.choice(intros) + "\n\n"
             
    # Tweet oluştur
    tweet = f"{intro}{emoji} {header_text}\n\n📌 {mark}"
    
    if desc:
        tweet += f"\n📝 {desc}"
        
    if owner:
         # Şirket ismi çok uzunsa ve handle yoksa kısalt
        if len(owner) > 40 and '@' not in owner:
            owner = owner[:37] + "..."
        tweet += f"\n🏢 {owner}"
        
    tweet += f"\n📅 {date_str}"
    
    # Dynamic Hashtags
    hashtags = [] # Temiz görünüm için default hashtag yok
    
    # Add category-specific hashtags
    text_lower = (mark + " " + desc).lower()
    
    if cat == 'weird':
        hashtags.append("#WeirdUSPTO")
        hashtags.append("#Funny")
        hashtags.append("#Marketing")
    elif 'ai' in text_lower or 'gpt' in text_lower or 'intelligence' in text_lower:
        hashtags.append("#AI")
        hashtags.append("#ArtificialIntelligence")
    elif 'crypto' in text_lower or 'blockchain' in text_lower or 'nft' in text_lower:
        hashtags.append("#Crypto")
        hashtags.append("#Web3")
    elif 'game' in text_lower or 'gaming' in text_lower:
        hashtags.append("#Gaming")
    elif 'metaverse' in text_lower:
        hashtags.append("#Metaverse")
    elif 'tech' in text_lower or 'software' in text_lower:
        hashtags.append("#Tech")

    # Stock Ticker Logic ($CASHTAGS)
    found_ticker = None
    for company, ticker in KNOWN_TICKERS.items():
        pattern = r'\b' + re.escape(company.lower()) + r'\b'
        if re.search(pattern, owner_lower):
             hashtags.append(ticker) # $AAPL vb ekle
             found_ticker = ticker
             break
        
    tags_str = " ".join(hashtags)
    tweet += f"\n\n🔗 {url}\n\n{tags_str}"
    
    return tweet[:280]


def get_x_api_v1():
    """Media upload için v1.1 API client"""
    auth = tweepy.OAuthHandler(X_API_KEY, X_API_SECRET)
    auth.set_access_token(X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)
    return tweepy.API(auth)


def post_tweet(text: str, media_path: Optional[str] = None) -> Optional[str]:
    """Tweet at (Opsiyonel görsel ile)"""
    try:
        client = get_x_client() # v2.0
        media_id = None
        
        # 1. Görsel yükle (varsa)
        if media_path and os.path.exists(media_path):
            try:
                api_v1 = get_x_api_v1()
                media = api_v1.media_upload(media_path)
                media_id = media.media_id
                print(f"🖼️ Görsel yüklendi: {media_path} (ID: {media_id})")
            except Exception as e:
                logging.error(f"Görsel yükleme hatası: {e}")
                print(f"⚠️ Görsel yüklenemedi, twistsiz devam ediliyor...")
        
        # 2. Tweet at
        if media_id:
            response = client.create_tweet(text=text, media_ids=[media_id])
        else:
            response = client.create_tweet(text=text)
            
        tweet_id = str(response.data['id'])
        print(f"✅ https://twitter.com/i/status/{tweet_id}")
        return tweet_id
    except Exception as e:
        error_msg = f"Tweet hatası: {e}"
        if hasattr(e, 'response') and e.response is not None:
             # Headerları yazdır (Rate limit için)
             headers = e.response.headers
             if headers:
                 limit = headers.get('x-rate-limit-remaining')
                 reset = headers.get('x-rate-limit-reset')
                 error_msg += f" | Limit: {limit} | Reset: {reset}"
                 
             # Gövdeyi yazdır (Detaylı hata mesajı için)
             try:
                error_msg += f" | Body: {e.response.text}"
             except:
                pass
                
        logging.error(error_msg)
        print(f"❌ {error_msg}")

def tweet_candidates(candidates: List[Dict], dry_run: bool = False):
    """
    Seçilen adayları tweet at (veya preview yap)
    """
    print(f"\n📢 Tweet atılıyor{'(DRY RUN)' if dry_run else ''}...")
    
    # Görsel indirmek için scraper (sadece download methodu için)
    scraper = TSDRScraper()
    
    for i, tm in enumerate(candidates, 1):
        print(f"\n[{i}/{len(candidates)}] {tm.get('mark_name')} (Score: {tm.get('score', 0)})")
        print(f"   Reasons: {', '.join(tm.get('reasons', []))}")
        
        tweet_text = format_tweet(tm)
        
        # --- GÖRSEL HAZIRLIĞI ---
        media_path = None
        try:
            # 1. Önce resmi var mı bak (Drawing)
            if tm.get('image_url'):
                print(f"   📥 Görsel indiriliyor: {tm['image_url']}")
                media_path = scraper.download_image(tm['image_url'], tm.get('serial_number'))
            
            # 2. Yoksa Kart Oluştur (Card Gen)
            if not media_path:
                print(f"   🎨 Kartvizit oluşturuluyor...")
                media_path = generate_trademark_card(
                    mark_name=tm.get('mark_name', 'UNKNOWN'),
                    owner=tm.get('owner', 'Unknown'),
                    date_str=tm.get('filing_date_raw', '2025'),
                    serial=tm.get('serial_number'),
                    description=tm.get('goods_services', '') # Görselde açıklama göster
                )
        except Exception as e:
            logging.error(f"Görsel hazırlama hatası: {e}")
            print(f"⚠️ Görsel hatası: {e}")
            
        
        if dry_run:
            print(f"\n--- PREVIEW ---\n{tweet_text}")
            if media_path:
                print(f"[Görsel Eklendi: {media_path}]")
            print("---------------")
            
        else:
            tweet_id = post_tweet(tweet_text, media_path)
            if tweet_id:
                save_posted(tm.get('serial_number'), tweet_text, tweet_id, category=tm.get('category', ''))
            
            # Temizlik
            if media_path and os.path.exists(media_path):
                os.remove(media_path)
                
            # Tweetler arası rastgele bekleme (3-7 dk) - Bot Detection Önlemi
            wait_time = random.randint(180, 420)
            print(f"⏳ Bekleniyor: {wait_time // 60} dakika ({wait_time} sn)...")
            time.sleep(wait_time)
    
    print(f"\n✅ Tamamlandı!")


# ============== ANA FONKSİYONLAR ==============

def run_bot(max_tweets: int = 4, dry_run: bool = False):
    """
    Bot'u çalıştır (Eski Yöntem - Geriye dönük uyumluluk için)
    """
    # Bu fonksiyon artık ana akışın bir parçası değil,
    # ancak kodun diğer yerlerinde çağrılıyor olabilir diye tutuyoruz.
    # Asıl akış main() içindedir.
    trademarks = get_trademarks_for_today()
    if not trademarks:
        print("❌ Trademark bulunamadı!")
        return
    
    # DÜZELTME: Doğru fonksiyon ismi filter_and_select
    candidates = filter_and_select(trademarks, max_tweets)
    # filter_and_select zaten max_tweets kadar döndürüyor ama yine de slicing yapalım ne olur ne olmaz
    selected = candidates[:max_tweets]

    tweet_candidates(selected, dry_run)


def parse_arguments():
    if len(sys.argv) < 2:
        return 'run', False, False # default
    
    command = sys.argv[1] # run, preview, clear
    
    # Flags
    dry_run = '--dry-run' in sys.argv
    no_scan = '--no-scan' in sys.argv  # New flag
    
    return command, dry_run, no_scan

def print_banner():
    print("""
    ╔═══════════════════════════════════════════╗
    ║   FilingWatch v2.1 - USPTO Trademark Bot  ║
    ║   Günlük Cache + Akıllı Filtreleme        ║
    ╚═══════════════════════════════════════════╝
    """)

def main():
    print_banner()
    command, dry_run, no_scan = parse_arguments()
    
    if command == 'clear':
        clear_cache()
        return
    
    elif command == 'stats-weekly':
        analyzer = Analyzer()
        report = analyzer.generate_weekly_report()
        print(report)
        
        # Tweet at (Eğer --tweet argümanı varsa)
        if '--tweet' in sys.argv:
            print("📢 Rapor tweetleniyor...")
            client = get_x_client() # Client init
            # Rapor zaten kısa (280 char kontrolü analyzer içinde yapılmalı veya burada)
            # Analyzer raporu biraz uzun olabilir, kontrol edelim
            if len(report) > 280:
                report = report[:277] + "..."
            
            post_tweet(report)
        return

    elif command == 'stats':
        # --- İYİLEŞTİRİLMİŞ STATS (JSON + GÖRSEL) ---
        print("\n📊 --- BUGÜNÜN DETAYLI İSTATİSTİKLERİ ---")
        # For simplicity, we can load cache and print basic info
        cache = load_daily_cache()
        print(f"📦 Cache: {len(cache.get('trademarks', []))} trademarks")
        # ... (Any additional stats logic could go here)
        return
        return

    # 1. Scrape / Load Data
    if no_scan:
        # Load ONLY from cache, no update
        cache = load_daily_cache()
        trademarks = cache.get('trademarks', [])
        print(f"⏩ Taramayı atla (--no-scan). Cache'den {len(trademarks)} kayıt kullanılıyor.")
    else:
        # Normal flow (Load cache + Scan new)
        trademarks = get_trademarks_for_today()
    
    print(f"\n📦 Toplam: {len(trademarks)} trademark\n")
    
    if not trademarks:
        print("❌ İşlenecek trademark bulunamadı.")
        return

    # 2. Filter & Score
    print("🔍 Filtreleniyor...")
    # filter_and_select hem puanlar hem de en iyileri seçer
    selected = filter_and_select(trademarks, MAX_TWEETS_PER_RUN)
    print(f"INFO - 📊 Puanlama sonucu ve seçim: {len(selected)} aday tweet")
    
    # Top N selection (filter_and_select zaten yaptı ama değişken adı uyumu için)
    # selected = candidates[:MAX_TWEETS_PER_RUN]
    print(f"🎯 Seçilen: {len(selected)} trademark")
    
    if not selected:
        print("📭 Paylaşılacak kriterde trademark yok.")
        return

    # 3. Tweet / Preview
    if command == 'preview':
        print("\n📢 Tweet atılıyor(DRY RUN)...\n")
        tweet_candidates(selected, dry_run=True) # Preview is essentially a dry run
        print("\n✅ Tamamlandı!")
    
    elif command == 'run':
        # Production mode
        logging.info(f"Yayın modu: {len(selected)} tweet atılacak.")
        tweet_candidates(selected, dry_run=False)
        logging.info("Run finished.")





if __name__ == "__main__":
    main()

import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import os
import json
import time
import re
import logging
from datetime import datetime
from main_v2 import post_tweet, get_x_client, KNOWN_TICKERS

# --- CONFIG ---
SEC_RSS_URL = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=D&output=atom"
USER_AGENT = "FilingWatch Bot (bot@filingwatch.com)" # SEC requires this!
STATE_FILE = "sec_state.json"
MIN_AMOUNT = 20_000_000 # $20 Million Whale Filter

# --- LOGGING ---
logging.basicConfig(
    filename='sec_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logger.addHandler(console)

class SECMonitor:
    def __init__(self):
        self.headers = {'User-Agent': USER_AGENT}
        self.last_link = self.load_state()

    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('last_link')
            except:
                pass
        return None

    def save_state(self, link):
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump({'last_link': link, 'updated_at': datetime.now().isoformat()}, f)
        except Exception as e:
            logger.error(f"State save error: {e}")

    def get_filings(self):
        """RSS feedinden son formları çeker"""
        try:
            resp = requests.get(SEC_RSS_URL, headers=self.headers, timeout=20)
            if resp.status_code != 200:
                logger.error(f"SEC RSS Error: {resp.status_code}")
                return []
            
            # Atom Feed Parsing
            # XML namespace sorunu yaşamamak için basit string işlemi veya feedparser kullanılabilir
            # Burada ElementTree ile namespace'i handle ederek gidelim
            root = ET.fromstring(resp.content)
            entries = []
            
            # Atom namespace usually: {http://www.w3.org/2005/Atom}
            # Basitçe taglerde 'entry' arayalım
            for child in root:
                if 'entry' in child.tag:
                    entries.append(child)
                    
            filings = []
            for entry in entries:
                f = {}
                for node in entry:
                    if 'title' in node.tag: f['title'] = node.text
                    if 'link' in node.tag: f['link'] = node.attrib.get('href')
                    if 'summary' in node.tag: f['summary'] = node.text
                    if 'updated' in node.tag: f['date'] = node.text
                
                # Sadece Form D (zaten URL filter var ama teyit edelim)
                if 'D' in f.get('title', ''):
                    filings.append(f)
            
            return filings # En eskiden yeniye veya tam tersi. RSS genelde Yeni->Eski verir.
            
        except Exception as e:
            logger.error(f"RSS Parse Error: {e}")
            return []

    def get_details(self, filing_link):
        """Detay sayfasına gidip Miktarı çeker"""
        # filing_link şuna benzer: https://www.sec.gov/Archives/edgar/data/123/000123...-index.htm
        # Bizim asıl XML/HTML dokümanına ihtiyacımız var.
        # Index sayfasını scrape edip "Primary Document" tablosundan ilk linki alacağız.
        
        try:
            # 1. Index Sayfası
            resp = requests.get(filing_link, headers=self.headers, timeout=10)
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # Primary Document linkini bul
            # Tablo class="tableFile"
            doc_link = None
            for row in soup.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) > 3:
                    # Column 3 = Document (index 2), Column 4 = Type (index 3)
                    doc_type = cols[3].get_text().strip()
                    if doc_type == 'D':
                        # Link index 2
                        a_tag = cols[2].find('a')
                        if a_tag:
                            href = a_tag['href']
                            # Öncelik XML, yoksa HTML
                            current_link = "https://www.sec.gov" + href
                            if not doc_link or href.endswith('.xml'):
                                doc_link = current_link
                                if href.endswith('.xml'): 
                                    break # XML bulduk, tamamdır
            
            if not doc_link:
                return None, 0

            # 2. Dokümanı Çek
            time.sleep(0.2) # Rate limit nezaketi
            resp_doc = requests.get(doc_link, headers=self.headers, timeout=10)
            content = resp_doc.text
            
            # 3. Regex ile "Total Amount Sold" bul
            # XML pattern: <totalAmountSold>1000000</totalAmountSold>
            # HTML pattern: "Total Amount Sold" ... "$ 1,000,000"
            
            amount = 0
            
            # Pattern 1: XML
            m_xml = re.search(r'<totalAmountSold>[^<]*\$?([0-9,]+)[^<]*</totalAmountSold>', content, re.IGNORECASE)
            if m_xml:
                clean_str = m_xml.group(1).replace(',', '')
                try: amount = float(clean_str)
                except: pass
            
            # Pattern 2: Text Search (Fallback)
            if amount == 0:
                # "Total Amount Sold" yazısını bul
                idx = content.find("Total Amount Sold")
                if idx != -1:
                    snippet = content[idx:idx+200]
                    # "$ 350,000" veya "350000"
                    # Basit regex: $ ve rakamlar
                    nums = re.findall(r'\$?\s?([0-9,]{4,})', snippet)
                    if nums:
                        try: amount = float(nums[0].replace(',', ''))
                        except: pass

            return doc_link, amount

        except Exception as e:
            logger.error(f"Details Parse Error: {e}")
            return None, 0

    def format_amount(self, amount):
        if amount >= 1_000_000_000:
            return f"${amount/1_000_000_000:.1f} Billion"
        elif amount >= 1_000_000:
            return f"${amount/1_000_000:.1f} Million"
        else:
            return f"${amount:,.0f}"

    def run(self):
        logger.info("SEC Bot taraması başladı...")
        filings = self.get_filings()
        
        # Yeni -> Eski geliyor. Terse çevirelim ki eskiden yeniye tweet atalım (kronolojik)
        filings.reverse()
        
        new_last_link = self.last_link
        processed_count = 0
        
        # Eğer ilk çalıştırışsa, hepsini tweet atma, sadece sonuncuyu işaretle
        if not self.last_link and filings:
            self.save_state(filings[-1]['link'])
            logger.info("İlk kurulum: State kaydedildi, tweet atılmadı.")
            return

        for f in filings:
            link = f['link']
            title = f['title'] # Örn: "Form D - OPENAI INC (000...)"
            
            # State kontrolü: Eğer bu link daha önce işlendiyse (veya ondan öncekilerse) atla
            # Basit mantık: Link eşitse dur (yeniye doğru gidiyorduk... actually reverse ettik)
            # Logic: We process everything NEWER than last_link.
            # RSS linkleri unique id gibidir.
            
            # Ancak RSS listesinde last_link'i bulup sonrasını almak daha güvenli.
            # Biz basitçe: Eğer link == last_link ise, bu noktaya kadar olanları zaten işledik (reverse listede).
            # Hayır, reverse listede: [Eski .... Last ... Yeni ... Yeni]
            # Flag mantığı kuralım.
            pass 
        
        # Daha sağlam mantık:
        # RSS'teki sırayı (Yeni->Eski) kullanalım. Last_link'i görene kadar toplayalım.
        # Sonra toplananları (Yenileri) ters çevirip tweet atalım.
        
        filings = self.get_filings() # Tekrar al (Yeni -> Eski)
        new_entries = []
        
        for f in filings:
            if f['link'] == self.last_link:
                break
            new_entries.append(f)
            
        if not new_entries:
            logger.info("Yeni SEC bildirimi yok.")
            return

        logger.info(f"{len(new_entries)} yeni bildirim var. Detaylar çekiliyor...")
        
        # Eskiden yeniye işle
        for f in reversed(new_entries):
            # Şirket ismini al: "D - Company Name (CIK)" -> "Company Name"
            # Title format: "D - OpenAI, Inc. (0001956665) (Filer)"
            company_name = "Unknown Company"
            try:
                parts = f['title'].split('-')
                if len(parts) > 1:
                    raw_name = parts[1].strip()
                    # Parantezleri temizle (CIK kodu vs)
                    company_name = re.sub(r'\s*\(.*?\)', '', raw_name).strip()
            except:
                pass
                
            doc_link, amount = self.get_details(f['link'])
            
            if amount < MIN_AMOUNT:
                logger.info(f"Skipped {company_name}: ${amount:,.0f} < ${MIN_AMOUNT:,.0f}")
                new_last_link = f['link'] # Yine de ilerle
                continue
                
            # WHALE ALERT! 🐋
            emoji = "💰"
            if amount >= 100_000_000:
                emoji = "🐋"

            tweet = f"{emoji} NEW SEC FILING ALERT\n\n🏢 {company_name}\n💵 {self.format_amount(amount)} Raised\n\n📄 Form D (Private Placement)\n🔗 {doc_link}"
            
            # Ticker check?
            # Özel şirketlerde ticker olmaz ama yine de check edelim
            
            logger.info(f"Yayınlanıyor: {company_name} - {amount}")
            try:
                post_tweet(tweet)
                time.sleep(5) # Flood yapma
            except Exception as e:
                logger.error(f"Tweet error: {e}")
                
            new_last_link = f['link']
            
        # En son işlenen linki kaydet
        self.save_state(new_last_link)
        logger.info("SEC taraması tamamlandı.")

if __name__ == "__main__":
    bot = SECMonitor()
    bot.run()

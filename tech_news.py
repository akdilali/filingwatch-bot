import requests
from bs4 import BeautifulSoup
import logging
import sys
import os
# Import existing Twitter client
from main_v2 import post_tweet, get_x_client

# Config
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('TechNews')

class TechNewsBot:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def scrape_techmeme(self):
        """Techmeme ana manşeti çeker (RSS üzerinden)"""
        url = "https://www.techmeme.com/feed.xml"
        try:
            import xml.etree.ElementTree as ET
            resp = requests.get(url, headers=self.headers, timeout=10)
            root = ET.fromstring(resp.content)
            
            # İlk öğe her zaman manşettir
            item = root.find('./channel/item')
            if not item:
                logger.error("Techmeme RSS boş.")
                return None
            
            title = item.find('title').text
            link = item.find('link').text
            
            # Description HTML içeriyor, metni ayıklayalım
            description_html = item.find('description').text
            soup = BeautifulSoup(description_html, 'html.parser')
            clean_desc = soup.get_text().strip()
            
            # Tweet Formatla
            tweet = f"📰 TECHMEME MANŞET\n\n🚨 {title}\n\n{clean_desc[:100]}...\n\n🔗 {link}\n\n#TechNews #Breaking #Technology"
            logger.info(f"Techmeme bulundu: {title}")
            return tweet
            
        except Exception as e:
            logger.error(f"Techmeme Scrape Hatası: {e}")
            return None

    def scrape_producthunt(self):
        """Product Hunt günün ürününü çeker (RSS üzerinden)"""
        url = "https://www.producthunt.com/feed"
        try:
            import xml.etree.ElementTree as ET
            resp = requests.get(url, headers=self.headers, timeout=10)
            root = ET.fromstring(resp.content)
            
            # İlk öğe (En güncel/popüler)
            # RSS namespace kullanabilir, basit find ile deneyelim
            item = root.find('./channel/item')
            if not item:
                logger.error("Product Hunt RSS boş.")
                return None
                
            title = item.find('title').text
            link = item.find('link').text
            description = item.find('description').text
            
            # HTML tagleri temizle (basitçe)
            soup = BeautifulSoup(description, 'html.parser')
            clean_desc = soup.get_text().strip()
            
            tweet = f"🚀 PRODUCT HUNT GÜNÜN ÜRÜNÜ\n\n✨ {title}\n\n💡 {clean_desc[:120]}...\n\n🔗 {link}\n\n#ProductHunt #NewTool #Startup"
            logger.info(f"PH bulundu: {title}")
            return tweet
            
        except Exception as e:
            logger.error(f"Product Hunt Scrape Hatası: {e}")
            return None

    def scrape_github_trending(self):
        """GitHub Trending #1 reposunu çeker"""
        url = "https://github.com/trending"
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # İlk Article (Box-row)
            article = soup.find('article', class_='Box-row')
            if not article:
                logger.error("GitHub Trending yapısı değişmiş.")
                return None
                
            # Repo Name (h2 > a) -> "user / repo"
            h2 = article.find('h2')
            if not h2: return None
            
            repo_link_tag = h2.find('a')
            repo_name = repo_link_tag.get_text().strip().replace('\n', '').replace(' ', '')
            repo_path = repo_link_tag['href']
            link = f"https://github.com{repo_path}"
            
            # Description (p)
            p = article.find('p')
            desc = p.get_text().strip() if p else "No description."
            
            # Stars Today (En sondaki span)
            # Yapı: <span class="d-inline-block float-sm-right"> <svg>...</svg> 123 stars today </span>
            # Basitçe metin içinde "stars today" arayalım
            all_text = article.get_text()
            stars_today = "Unknown"
            if "stars today" in all_text:
                # Satırlara böl ve bul
                for line in all_text.split('\n'):
                     if "stars today" in line:
                         stars_today = line.strip().replace(' stars today', '')
                         break
            
            # Tweet
            tweet = f"🔥 GITHUB TRENDING #1\n\n📦 {repo_name}\n⭐ {stars_today} stars today\n\n💡 {desc[:100]}...\n\n🔗 {link}\n\n#OpenSource"
            
            # Dinamik Etiketler (İçeriğe göre)
            desc_lower = desc.lower()
            if any(x in desc_lower for x in ['llm', 'gpt', 'ai ', 'artificial intelligence', 'model', 'neural']):
                tweet += " #AI"
            if 'game' in desc_lower:
                tweet += " #GameDev"
            if 'web' in desc_lower or 'css' in desc_lower or 'react' in desc_lower:
                 tweet += " #WebDev"
                
            logger.info(f"GitHub Trending bulundu: {repo_name}")
            return tweet
            
        except Exception as e:
            logger.error(f"GitHub Scrape Hatası: {e}")
            return None

    def run(self, source: str):
        logger.info(f"Bot çalışıyor... Kaynak: {source}")
        tweet_text = None
        
        if source == 'techmeme':
            tweet_text = self.scrape_techmeme()
        elif source == 'producthunt':
            tweet_text = self.scrape_producthunt()
        elif source == 'github':
            tweet_text = self.scrape_github_trending()
        else:
            logger.error("Geçersiz kaynak. Seçenekler: techmeme, producthunt, github")
            return

        if tweet_text:
            # Tweet at
            try:
                # post_tweet fonksiyonunu main_v2'den çağırıyoruz
                # Not: post_tweet içinde 'print' var, loglama için yeterli.
                # Safe check for length
                if len(tweet_text) > 280:
                    tweet_text = tweet_text[:277] + "..."
                    
                logger.info(f"Tweetleniyor:\n{tweet_text}")
                post_tweet(tweet_text) # Gerçek tweet
            except Exception as e:
                logger.error(f"Tweet atma hatası: {e}")
        else:
            logger.warning("İçerik bulunamadı, tweet atılmadı.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python tech_news.py [techmeme|producthunt]")
        sys.exit(1)
        
    source_arg = sys.argv[1]
    bot = TechNewsBot()
    bot.run(source_arg)

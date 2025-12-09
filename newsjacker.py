
import os
import time
import random
import logging
from typing import Optional
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Load credentials
load_dotenv()

BURNER_USER = os.getenv("BURNER_USER")
BURNER_PASS = os.getenv("BURNER_PASS")

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [NewsJacker] - %(message)s')

class NewsJacker:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None

    def _setup_driver(self):
        """Setup Chrome Driver with stealth options"""
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_window_size(1920, 1080)

    def login(self):
        """Login to Twitter with Burner Account"""
        if not BURNER_USER or not BURNER_PASS:
            logging.error("❌ Burner credentials missing in .env")
            return False

        try:
            if not self.driver:
                self._setup_driver()
            
            logging.info("🕵️‍♂️ Logging in...")
            self.driver.get("https://twitter.com/i/flow/login")
            time.sleep(random.uniform(5, 7))

            # 1. Enter Email / User Identifier
            logging.info("Step 1: Entering User/Email...")
            try:
                # Try multiple selectors for robustness
                username_input = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='username' or @name='text']"))
                )
                username_input.send_keys(BURNER_USER)
                username_input.send_keys(Keys.RETURN)
                time.sleep(random.uniform(3, 5))
            except Exception as e:
                logging.error(f"❌ Failed at Email step: {e}")
                return False

            # 2. Check for "Enter your phone number or username" (Unusual Activity Check)
            try:
                logging.info("Step 2: Checking for verification...")
                time.sleep(3)
                
                # Check for input field
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                text_inputs = [i for i in inputs if i.get_attribute("type") == "text"]
                
                if text_inputs:
                    logging.info("⚠️ Twitter asking for Handle...")
                    handle_input = text_inputs[0]
                    burner_handle = os.getenv("BURNER_HANDLE")
                    if not burner_handle:
                        logging.error("❌ Handle required but not found in .env")
                        return False
                    
                    handle_input.send_keys(burner_handle)
                    time.sleep(1)
                    # Try clicking "Next" button
                    try:
                        next_buttons = self.driver.find_elements(By.XPATH, "//span[text()='Next']")
                        if next_buttons:
                            next_buttons[0].click()
                        else:
                            handle_input.send_keys(Keys.RETURN)
                    except:
                        handle_input.send_keys(Keys.RETURN)
                        
                    time.sleep(random.uniform(3, 5))
                else:
                    logging.info("ℹ️ No extra verification field detected.")

            except Exception as e:
                logging.warning(f"ℹ️ Verification check ignored: {e}")

            # 3. Enter Password
            logging.info("Step 3: Entering Password...")
            try:
                password_input = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.NAME, "password"))
                )
                password_input.send_keys(BURNER_PASS)
                time.sleep(1)
                
                # Try clicking "Log in" button
                try:
                    login_buttons = self.driver.find_elements(By.XPATH, "//span[text()='Log in']")
                    if login_buttons:
                        login_buttons[0].click()
                    else:
                        password_input.send_keys(Keys.RETURN)
                except:
                    password_input.send_keys(Keys.RETURN)
                    
                time.sleep(random.uniform(8, 10))
            except Exception as e:
                logging.error(f"❌ Failed at Password step: {e}")
                self.driver.save_screenshot("login_fail_pwd.png")
                return False
            
            # Check login success
            if "login" in self.driver.current_url:
                 logging.warning("⚠️ Url still contains 'login'. Possible failure.")
                 return False
            
            logging.info("✅ Login SUCCESS")
            return True

        except Exception as e:
            logging.error(f"❌ Login Critical Error: {e}")
            if self.driver:
                self.driver.save_screenshot("login_error_crit.png")
            return False

    def find_viral_tweet(self, query: str) -> Optional[str]:
        """Find the top viral tweet for a query"""
        if not self.driver:
            if not self.login():
                return None

        try:
            logging.info(f"🔎 Searching for: {query}")
            search_url = f"https://twitter.com/search?q={query}&src=typed_query&f=top"
            self.driver.get(search_url)
            time.sleep(random.uniform(5, 8))

            # Find first tweet article
            tweets = self.driver.find_elements(By.TAG_NAME, "article")
            if not tweets:
                logging.warning("No tweets found.")
                self.driver.save_screenshot("search_error.png")
                return None
            
            # Get the first one (Top Tweet)
            top_tweet = tweets[0]
            
            # Extract Link
            # Usually inside a time element or the main link
            try:
                # Try to find date link which is the permalink
                link_elem = top_tweet.find_element(By.XPATH, ".//time/..")
                tweet_url = link_elem.get_attribute("href")
                logging.info(f"🎯 Found Viral Tweet: {tweet_url}")
                return tweet_url
            except:
                logging.warning("Could not extract URL from tweet.")
                return None

        except Exception as e:
            logging.error(f"❌ Search Error: {e}")
            self.driver.save_screenshot("search_exception.png")
            return None

    def close(self):
        if self.driver:
            self.driver.quit()

if __name__ == "__main__":
    # Test Run
    nj = NewsJacker(headless=True)
    if nj.login():
        link = nj.find_viral_tweet("Tesla Robot")
        print(f"Result: {link}")
    nj.close()

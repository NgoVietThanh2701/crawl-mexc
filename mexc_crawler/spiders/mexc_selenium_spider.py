import scrapy
from scrapy import Request
from mexc_crawler.items import TokenItem
from datetime import datetime
import re
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time


class MexcSeleniumSpider(scrapy.Spider):
    name = 'mexc_selenium'
    allowed_domains = ['mexc.com']
    start_urls = ['https://www.mexc.com/vi-VN/pre-market']
    
    def __init__(self):
        super().__init__()
        self.driver = None
    
    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse, dont_filter=True)
    
    def parse(self, response):
        # Set up Chrome driver with options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.get(response.url)
            
            # Wait for the page to load
            wait = WebDriverWait(self.driver, 20)
            
            # Wait for the specific tab panel to load
            try:
                # Wait for the "Token khả dụng" tab to be present
                tab_panel = wait.until(
                    EC.presence_of_element_located((By.ID, "rc-tabs-0-panel-1"))
                )
                
                # Wait a bit more for the content to load
                time.sleep(3)
                
                # Try to find the token list
                token_list = self.driver.find_element(By.CSS_SELECTOR, "ul.ant-list-items")
                
                if token_list:
                    # Get all token items
                    token_items = token_list.find_elements(By.TAG_NAME, "li")
                    
                    self.logger.info(f"Found {len(token_items)} token items")
                    
                    for i, item in enumerate(token_items):
                        try:
                            token_item = self.extract_token_data(item)
                            if token_item:
                                yield token_item
                        except Exception as e:
                            self.logger.error(f"Error extracting token {i}: {e}")
                            continue
                
            except TimeoutException:
                self.logger.error("Timeout waiting for token list to load")
                
                # Try alternative approach - look for any token-related elements
                self.try_alternative_extraction()
                
        except Exception as e:
            self.logger.error(f"Error in Selenium spider: {e}")
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def extract_token_data(self, item_element):
        """Extract token data from a list item element"""
        token_item = TokenItem()
        
        try:
            # Get all text content from the item
            item_text = item_element.text
            
            # Try to find specific elements within the item
            # Look for price, change, volume information
            
            # Find name/symbol (usually at the beginning)
            text_lines = [line.strip() for line in item_text.split('\n') if line.strip()]
            
            if len(text_lines) >= 1:
                token_item['symbol'] = text_lines[0]
                token_item['name'] = text_lines[0]
            
            # Look for price information
            price_pattern = r'[\d,]+\.?\d*'
            prices = re.findall(price_pattern, item_text)
            
            if len(prices) >= 1:
                token_item['latest_price'] = prices[0]
            
            # Look for percentage change
            change_pattern = r'[+-]?\d+\.?\d*%'
            changes = re.findall(change_pattern, item_text)
            
            if len(changes) >= 1:
                token_item['price_change_percent'] = changes[0]
            
            # Look for volume information
            volume_pattern = r'[\d,]+[KMB]?'
            volumes = re.findall(volume_pattern, item_text)
            
            if len(volumes) >= 1:
                token_item['volume_24h'] = volumes[0]
            if len(volumes) >= 2:
                token_item['total_volume'] = volumes[1]
            
            # Try to find time information
            time_pattern = r'\d{2}:\d{2}|\d{2}/\d{2}/\d{4}'
            times = re.findall(time_pattern, item_text)
            
            if len(times) >= 1:
                token_item['start_time'] = times[0]
            
            token_item['crawled_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Only return item if we have at least some data
            if token_item.get('symbol') or token_item.get('latest_price'):
                return token_item
            
        except Exception as e:
            self.logger.error(f"Error extracting token data: {e}")
        
        return None
    
    def try_alternative_extraction(self):
        """Try alternative methods to extract token data"""
        try:
            # Look for any divs that might contain token information
            all_divs = self.driver.find_elements(By.TAG_NAME, "div")
            
            for div in all_divs:
                try:
                    div_text = div.text
                    if div_text and any(keyword in div_text.lower() for keyword in ['token', 'symbol', 'price']):
                        self.logger.info(f"Found potential token div: {div_text[:100]}...")
                        
                        # Try to extract data from this div
                        token_item = TokenItem()
                        token_item['name'] = div_text[:50]  # First 50 chars as name
                        token_item['symbol'] = div_text[:20]  # First 20 chars as symbol
                        token_item['crawled_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        yield token_item
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error in alternative extraction: {e}")
    
    def clean_text(self, text):
        """Clean and format text data"""
        if not text:
            return ''
        
        # Remove extra whitespace and special characters
        cleaned = re.sub(r'\s+', ' ', text.strip())
        cleaned = cleaned.replace('\n', '').replace('\t', '')
        
        return cleaned

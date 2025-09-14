import scrapy
from scrapy import Request
from mexc_crawler.items import TokenItem, OrderBookItem
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


class MexcOrderBookSpider(scrapy.Spider):
    name = 'mexc_orderbook'
    allowed_domains = ['mexc.com']
    start_urls = ['https://www.mexc.com/vi-VN/pre-market']
    
    def __init__(self):
        super().__init__()
        self.driver = None
        self.tokens_data = []  # Store tokens from pre-market page
    
    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse, dont_filter=True)
    
    def parse(self, response):
        """First parse the pre-market page to get token list, then crawl order book for each token"""
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
            
            # First, get the token list from pre-market page
            try:
                print("Waiting for token panel to load...")
                tab_panel = wait.until(
                    EC.presence_of_element_located((By.ID, "rc-tabs-0-panel-1"))
                )
                
                # Wait for content to load
                time.sleep(5)
                
                # Try to find the token list
                token_list = self.driver.find_element(By.CSS_SELECTOR, "ul.ant-list-items")
                
                if token_list:
                    print("Found token list, extracting token data...")
                    token_items = token_list.find_elements(By.TAG_NAME, "li")
                    
                    print(f"Found {len(token_items)} token items")
                    
                    for i, item in enumerate(token_items):
                        try:
                            # Extract token data and yield TokenItem
                            token_data = self.extract_token_data_from_element(item)
                            if token_data:
                                token_item = TokenItem()
                                for key, value in token_data.items():
                                    token_item[key] = value
                                yield token_item
                                
                                # Store token data for order book crawling
                                self.tokens_data.append(token_data)
                                
                                print(f"Extracted token {i+1}: {token_data.get('symbol', 'Unknown')}")
                        except Exception as e:
                            print(f"Error extracting token {i+1}: {e}")
                            continue
                
                # Now crawl order book for each token
                for token_data in self.tokens_data:
                    symbol = token_data.get('symbol', '')
                    if symbol:
                        yield Request(
                            url=f'https://www.mexc.com/vi-VN/exchange/{symbol}_USDT',
                            callback=self.parse_order_book,
                            meta={'token_symbol': symbol, 'token_data': token_data},
                            dont_filter=True
                        )
                
            except TimeoutException:
                self.logger.error("Timeout waiting for token list to load")
                
        except Exception as e:
            self.logger.error(f"Error in OrderBook spider: {e}")
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def extract_token_data_from_element(self, element):
        """Extract token data from a web element using smart text parsing"""
        try:
            item_text = element.text
            if not item_text.strip():
                return None
            
            token_data = {
                'name': '',
                'symbol': '',
                'latest_price': '',
                'price_change_percent': '',
                'volume_24h': '',
                'total_volume': '',
                'start_time': '',
                'end_time': '',
                'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Parse the structured text based on the pattern we observed
            # Extract symbol - usually the first token-like word
            symbol_pattern = r'\b([A-Z]{2,10})\b'
            symbols = re.findall(symbol_pattern, item_text)
            if symbols:
                token_data['symbol'] = symbols[0]
            
            # Extract name - try to find the full token name
            lines = [line.strip() for line in item_text.split('\n') if line.strip()]
            
            # Method 1: Look for text after symbol on the same line or next line
            if token_data['symbol']:
                symbol_line_index = -1
                for i, line in enumerate(lines):
                    if token_data['symbol'] in line:
                        symbol_line_index = i
                        break
                
                if symbol_line_index >= 0:
                    # Check the same line for additional text after symbol
                    symbol_line = lines[symbol_line_index]
                    symbol_pos = symbol_line.find(token_data['symbol'])
                    if symbol_pos >= 0:
                        text_after_symbol = symbol_line[symbol_pos + len(token_data['symbol']):].strip()
                        if text_after_symbol and not re.search(r'[\d,]+\.?\d*|[+-]?\d+\.?\d*%', text_after_symbol):
                            # This looks like a name, not a number
                            potential_name = text_after_symbol
                            # Clean up the name (remove extra words)
                            name_parts = potential_name.split()
                            if name_parts:
                                # Take first 1-3 words that look like a name
                                clean_name_parts = []
                                for part in name_parts:
                                    if re.match(r'^[A-Za-z]+$', part) and len(part) > 1:
                                        clean_name_parts.append(part)
                                        if len(clean_name_parts) >= 3:  # Max 3 words
                                            break
                                    else:
                                        break
                                if clean_name_parts:
                                    token_data['name'] = ' '.join(clean_name_parts)
            
            # Fallback to symbol if no name found
            if not token_data['name'] and token_data['symbol']:
                token_data['name'] = token_data['symbol']
            
            # Extract latest price - decimal number after "Giá giao dịch mới nhất"
            price_pattern = r'Giá giao dịch mới nhất\s*([\d,]+\.?\d*)'
            price_match = re.search(price_pattern, item_text)
            if price_match:
                token_data['latest_price'] = price_match.group(1)
            
            # Extract percentage change - pattern like +52.54% or -31.42%
            change_pattern = r'([+-]?\d+\.?\d*%)'
            change_match = re.search(change_pattern, item_text)
            if change_match:
                token_data['price_change_percent'] = change_match.group(1)
            
            # Extract volume 24h - number with K/M/B after "Khối lượng 24 giờ"
            volume_24h_pattern = r'Khối lượng 24 giờ\s*([\d,]+\.?\d*[KMB]?)'
            volume_24h_match = re.search(volume_24h_pattern, item_text)
            if volume_24h_match:
                token_data['volume_24h'] = volume_24h_match.group(1)
            
            # Extract total volume - number with K/M/B after "Tổng khối lượng"
            total_volume_pattern = r'Tổng khối lượng\s*([\d,]+\.?\d*[KMB]?)'
            total_volume_match = re.search(total_volume_pattern, item_text)
            if total_volume_match:
                token_data['total_volume'] = total_volume_match.group(1)
            
            # Extract start time - datetime pattern after "Đang diễn ra"
            time_pattern = r'Đang diễn ra(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
            time_match = re.search(time_pattern, item_text)
            if time_match:
                token_data['start_time'] = time_match.group(1)
            
            # Extract end time - look for status
            end_time_patterns = [
                r'Đợi xác nhận',
                r'Đã kết thúc',
                r'Đang diễn ra',
            ]
            
            for pattern in end_time_patterns:
                end_match = re.search(pattern, item_text)
                if end_match:
                    token_data['end_time'] = pattern
                    break
            
            # Alternative parsing if the above doesn't work
            if not token_data['latest_price']:
                # Look for decimal numbers that could be prices
                price_pattern = r'(\d+\.\d{2,4})'
                prices = re.findall(price_pattern, item_text)
                if prices:
                    token_data['latest_price'] = prices[0]
            
            if not token_data['volume_24h']:
                # Look for numbers with K/M/B suffix
                volume_pattern = r'(\d+\.?\d*[KMB])'
                volumes = re.findall(volume_pattern, item_text)
                if len(volumes) >= 1:
                    token_data['volume_24h'] = volumes[0]
                if len(volumes) >= 2:
                    token_data['total_volume'] = volumes[1]
            
            return token_data
            
        except Exception as e:
            self.logger.error(f"Error extracting token data: {e}")
            return None
    
    def parse_order_book(self, response):
        """Parse the order book page for a specific token"""
        token_symbol = response.meta['token_symbol']
        token_data = response.meta['token_data']
        
        print(f"Crawling order book for token: {token_symbol}")
        
        # Set up Chrome driver for order book page
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(response.url)
            
            # Wait for the page to load
            wait = WebDriverWait(driver, 15)
            time.sleep(3)
            
            # Try to find order book elements
            # Look for common order book selectors
            order_book_selectors = [
                '.order-book',
                '.orderbook',
                '[class*="order"]',
                '[class*="book"]',
                '.depth-chart',
                '.market-depth'
            ]
            
            order_book_found = False
            for selector in order_book_selectors:
                try:
                    order_book_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if order_book_elements:
                        print(f"Found order book elements with selector: {selector}")
                        order_book_found = True
                        
                        # Extract order book data
                        order_book_items = self.extract_order_book_data(driver, token_symbol)
                        
                        # Yield each order book item
                        for item in order_book_items:
                            yield item
                        
                        break
                except Exception as e:
                    continue
            
            if not order_book_found:
                print(f"No order book found for {token_symbol}, trying alternative approach...")
                
                # Try to find any table or list that might contain order data
                tables = driver.find_elements(By.TAG_NAME, 'table')
                divs_with_data = driver.find_elements(By.CSS_SELECTOR, 'div[class*="row"], div[class*="item"]')
                
                if tables or divs_with_data:
                    print(f"Found {len(tables)} tables and {len(divs_with_data)} divs with data for {token_symbol}")
                    
                    # Try to extract order book data from tables
                    for table in tables:
                        order_book_items = self.extract_order_book_from_table(table, token_symbol)
                        for item in order_book_items:
                            yield item
                    
                    # Try to extract order book data from divs
                    for div in divs_with_data[:10]:  # Limit to first 10 divs
                        order_book_items = self.extract_order_book_from_div(div, token_symbol)
                        for item in order_book_items:
                            yield item
                else:
                    print(f"No order book data found for {token_symbol}")
                    
        except Exception as e:
            self.logger.error(f"Error crawling order book for {token_symbol}: {e}")
            
        finally:
            if driver:
                driver.quit()
    
    def extract_order_book_data(self, driver, token_symbol):
        """Extract order book data from the page"""
        order_book_items = []
        
        try:
            # Look for buy and sell orders
            # Common patterns for order book data
            buy_orders = driver.find_elements(By.CSS_SELECTOR, '[class*="buy"], [class*="bid"], .order-book-buy')
            sell_orders = driver.find_elements(By.CSS_SELECTOR, '[class*="sell"], [class*="ask"], .order-book-sell')
            
            # Process buy orders
            for order in buy_orders:
                try:
                    order_data = self.parse_order_element(order, token_symbol, 'BUY')
                    if order_data:
                        order_book_items.append(order_data)
                except Exception as e:
                    continue
            
            # Process sell orders
            for order in sell_orders:
                try:
                    order_data = self.parse_order_element(order, token_symbol, 'SELL')
                    if order_data:
                        order_book_items.append(order_data)
                except Exception as e:
                    continue
            
            # If no specific buy/sell elements found, try to find any order-like data
            if not order_book_items:
                all_divs = driver.find_elements(By.CSS_SELECTOR, 'div')
                for div in all_divs:
                    try:
                        text = div.text
                        if text and any(keyword in text.lower() for keyword in ['price', 'amount', 'total', 'buy', 'sell']):
                            # This might be order data
                            order_data = self.parse_text_for_order_data(text, token_symbol)
                            if order_data:
                                order_book_items.append(order_data)
                    except Exception as e:
                        continue
            
        except Exception as e:
            self.logger.error(f"Error extracting order book data: {e}")
        
        return order_book_items
    
    def extract_order_book_from_table(self, table, token_symbol):
        """Extract order book data from a table element"""
        order_book_items = []
        
        try:
            rows = table.find_elements(By.TAG_NAME, 'tr')
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, 'td')
                if len(cells) >= 3:  # Should have price, quantity, total
                    try:
                        price = cells[0].text.strip()
                        quantity = cells[1].text.strip()
                        total = cells[2].text.strip() if len(cells) > 2 else ''
                        
                        # Determine if this is buy or sell based on position or content
                        order_type = 'BUY'  # Default
                        if any(word in row.text.lower() for word in ['sell', 'ask']):
                            order_type = 'SELL'
                        
                        if price and quantity:
                            order_item = OrderBookItem()
                            order_item['token_symbol'] = token_symbol
                            order_item['order_type'] = order_type
                            order_item['price'] = price
                            order_item['quantity'] = quantity
                            order_item['total'] = total
                            order_item['crawled_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
                            order_book_items.append(order_item)
                    except Exception as e:
                        continue
        except Exception as e:
            self.logger.error(f"Error extracting from table: {e}")
        
        return order_book_items
    
    def extract_order_book_from_div(self, div, token_symbol):
        """Extract order book data from a div element"""
        order_book_items = []
        
        try:
            text = div.text.strip()
            if not text:
                return order_book_items
            
            # Try to parse text for order data
            order_data = self.parse_text_for_order_data(text, token_symbol)
            if order_data:
                order_book_items.append(order_data)
        except Exception as e:
            pass
        
        return order_book_items
    
    def parse_order_element(self, element, token_symbol, order_type):
        """Parse a single order element"""
        try:
            text = element.text.strip()
            if not text:
                return None
            
            # Extract price, quantity, total from text
            # Common patterns: "0.0243 25.568K 28.462K" or "Price: 0.0243 Amount: 25.568K"
            
            # Look for numbers (price, quantity, total)
            numbers = re.findall(r'[\d,]+\.?\d*[KMB]?', text)
            
            if len(numbers) >= 2:
                price = numbers[0]
                quantity = numbers[1]
                total = numbers[2] if len(numbers) >= 3 else ''
                
                order_item = OrderBookItem()
                order_item['token_symbol'] = token_symbol
                order_item['order_type'] = order_type
                order_item['price'] = price
                order_item['quantity'] = quantity
                order_item['total'] = total
                order_item['crawled_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                return order_item
                
        except Exception as e:
            self.logger.error(f"Error parsing order element: {e}")
        
        return None
    
    def parse_text_for_order_data(self, text, token_symbol):
        """Parse text content for order book data"""
        try:
            # Look for patterns like "Price: X Amount: Y" or just numbers
            numbers = re.findall(r'[\d,]+\.?\d*[KMB]?', text)
            
            if len(numbers) >= 2:
                price = numbers[0]
                quantity = numbers[1]
                total = numbers[2] if len(numbers) >= 3 else ''
                
                # Determine order type based on context
                order_type = 'BUY'
                if any(word in text.lower() for word in ['sell', 'ask', 'offer']):
                    order_type = 'SELL'
                
                order_item = OrderBookItem()
                order_item['token_symbol'] = token_symbol
                order_item['order_type'] = order_type
                order_item['price'] = price
                order_item['quantity'] = quantity
                order_item['total'] = total
                order_item['crawled_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                return order_item
                
        except Exception as e:
            pass
        
        return None


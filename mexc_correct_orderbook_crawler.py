#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MEXC Correct Order Book Crawler
Crawls actual order book data using correct CSS selectors from real HTML structure
URL pattern: https://www.mexc.com/vi-VN/pre-market/{SYMBOL}
"""

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re
from datetime import datetime
import json


class MexcCorrectOrderBookCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
        })
        self.tokens_data = []
        self.orderbook_data = []
        
    def crawl_all_data(self):
        """Crawl all data: tokens from pre-market + real order book from correct URLs"""
        print("🚀 MEXC Correct Order Book Crawler")
        print("=" * 70)
        print("📊 Phase 1: Crawling token list from pre-market")
        print("📊 Phase 2: Crawling real order book from correct URLs")
        print("=" * 70)
        
        # Phase 1: Get token list from pre-market
        self.crawl_token_list()
        
        # Phase 2: Crawl real order book for each token
        if self.tokens_data:
            print(f"\n🔄 Phase 2: Crawling real order book for {len(self.tokens_data)} tokens...")
            self.crawl_correct_orderbooks()
        
        print(f"\n🎯 CRAWLING COMPLETED!")
        print(f"   • Tokens extracted: {len(self.tokens_data)}")
        print(f"   • Real order book entries: {len(self.orderbook_data)}")
        
        return self.tokens_data, self.orderbook_data
    
    def crawl_token_list(self):
        """Crawl token list from pre-market page"""
        print("\n📋 Phase 1: Getting token list from pre-market...")
        
        # Set up Chrome driver
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
            url = 'https://www.mexc.com/vi-VN/pre-market'
            print(f"📡 Loading URL: {url}")
            
            driver.get(url)
            
            # Wait for page to load
            wait = WebDriverWait(driver, 20)
            
            # Wait for the specific tab panel
            try:
                print("⏳ Waiting for token panel to load...")
                tab_panel = wait.until(
                    EC.presence_of_element_located((By.ID, "rc-tabs-0-panel-1"))
                )
                
                # Wait for content to load
                time.sleep(5)
                
                # Try to find the token list
                token_list = driver.find_element(By.CSS_SELECTOR, "ul.ant-list-items")
                
                if token_list:
                    print("✅ Found token list, extracting token data...")
                    token_items = token_list.find_elements(By.TAG_NAME, "li")
                    
                    print(f"📊 Found {len(token_items)} token items")
                    
                    for i, item in enumerate(token_items):
                        try:
                            print(f"🔄 Processing token {i+1}/{len(token_items)}...")
                            
                            # Extract token data
                            token_data = self.extract_token_data(item)
                            if token_data:
                                self.tokens_data.append(token_data)
                                symbol = token_data.get('symbol', '')
                                print(f"✅ Token extracted: {symbol}")
                            
                            time.sleep(0.5)
                            
                        except Exception as e:
                            print(f"❌ Error processing token {i+1}: {e}")
                            continue
                
            except TimeoutException:
                print("⚠️ Timeout waiting for token list. Trying alternative approach...")
                self.try_alternative_token_extraction(driver)
                
        except Exception as e:
            print(f"❌ Error in token list crawling: {e}")
            
        finally:
            if driver:
                driver.quit()
    
    def crawl_correct_orderbooks(self):
        """Crawl real order book data from correct URLs"""
        print(f"\n📈 Phase 2: Crawling real order books using correct URLs...")
        
        for i, token in enumerate(self.tokens_data):
            symbol = token.get('symbol', '')
            if symbol:
                print(f"\n🔄 Processing token {i+1}/{len(self.tokens_data)}: {symbol}")
                
                try:
                    # Use correct URL pattern: https://www.mexc.com/vi-VN/pre-market/{SYMBOL}
                    orderbook_entries = self.crawl_orderbook_for_token(symbol)
                    self.orderbook_data.extend(orderbook_entries)
                    
                    if orderbook_entries:
                        print(f"✅ Real order book: {len(orderbook_entries)} entries for {symbol}")
                    else:
                        print(f"⚠️  No real order book data found for {symbol}")
                    
                    # Add delay between tokens to avoid rate limiting
                    time.sleep(3)
                    
                except Exception as e:
                    print(f"❌ Error crawling order book for {symbol}: {e}")
                    continue
    
    def crawl_orderbook_for_token(self, symbol):
        """Crawl real order book data for a specific token using correct URL"""
        orderbook_entries = []
        
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
            
            # Use correct URL pattern from user's information
            url = f'https://www.mexc.com/vi-VN/pre-market/{symbol}'
            print(f"  🔗 Loading URL: {url}")
            
            driver.get(url)
            
            # Wait for the page to load
            wait = WebDriverWait(driver, 15)
            time.sleep(5)
            
            # Check if page loaded successfully
            if "404" not in driver.title and "error" not in driver.title.lower():
                print(f"  ✅ Successfully loaded order book page for {symbol}")
                
                # Extract order book data using correct CSS selectors
                orderbook_entries = self.extract_correct_orderbook(driver, symbol)
                
                if orderbook_entries:
                    print(f"  📊 Found {len(orderbook_entries)} real order book entries")
                else:
                    print(f"  ⚠️  No order book data found on {url}")
            else:
                print(f"  ❌ Page not found: {url}")
                
        except Exception as e:
            print(f"❌ Error crawling order book for {symbol}: {e}")
            
        finally:
            if driver:
                driver.quit()
        
        return orderbook_entries
    
    def extract_correct_orderbook(self, driver, symbol):
        """Extract real order book data using correct CSS selectors"""
        orderbook_entries = []
        crawled_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            # Wait for order book table to load
            wait = WebDriverWait(driver, 10)
            
            # Look for the order book table using correct CSS selector from HTML
            orderbook_table = None
            try:
                # Try to find the table with correct selector
                orderbook_table = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "tbody.ant-table-tbody"))
                )
                print(f"    ✅ Found order book table")
            except TimeoutException:
                print(f"    ⚠️  Order book table not found, trying alternative selectors...")
                
                # Try alternative selectors
                alternative_selectors = [
                    "table tbody",
                    ".ant-table-tbody",
                    "[class*='order-book'] table tbody",
                    "tbody"
                ]
                
                for selector in alternative_selectors:
                    try:
                        orderbook_table = driver.find_element(By.CSS_SELECTOR, selector)
                        print(f"    ✅ Found order book table with selector: {selector}")
                        break
                    except NoSuchElementException:
                        continue
            
            if orderbook_table:
                # Extract order book rows using correct CSS selectors from HTML
                rows = orderbook_table.find_elements(By.CSS_SELECTOR, "tr.ant-table-row")
                
                print(f"    📊 Found {len(rows)} order book rows")
                
                for i, row in enumerate(rows):
                    try:
                        # Extract data from each row using correct CSS selectors
                        order_data = self.parse_correct_orderbook_row(row, symbol, crawled_at)
                        if order_data:
                            orderbook_entries.append(order_data)
                            
                        # Show progress for first few rows
                        if i < 5:
                            print(f"      Row {i+1}: {order_data}")
                            
                    except Exception as e:
                        print(f"      ❌ Error parsing row {i+1}: {e}")
                        continue
                
                # Handle pagination to get more data
                print(f"    🔄 Checking for pagination...")
                pagination_entries = self.handle_pagination(driver, symbol, crawled_at)
                orderbook_entries.extend(pagination_entries)
                
                if pagination_entries:
                    print(f"    📊 Found {len(pagination_entries)} additional entries from pagination")
            
            else:
                print(f"    ❌ Could not find order book table")
                
        except Exception as e:
            print(f"    ❌ Error extracting order book: {e}")
        
        return orderbook_entries
    
    def parse_correct_orderbook_row(self, row_element, symbol, crawled_at):
        """Parse order book data from a table row using correct CSS selectors"""
        try:
            # Extract data using correct CSS selectors from HTML structure
            # Based on the HTML: price is in first td, quantities in second and third td
            
            cells = row_element.find_elements(By.TAG_NAME, 'td')
            if len(cells) < 3:
                return None
            
            # Extract price from first cell using correct selector
            price_cell = cells[0]
            price_element = price_cell.find_element(By.CSS_SELECTOR, ".order-book-table_sellPrice__xAuZe")
            price = price_element.text.strip()
            
            # Extract first quantity from second cell
            quantity1_cell = cells[1]
            quantity1_element = quantity1_cell.find_element(By.CSS_SELECTOR, ".order-book-table_content__ZSAZ_")
            quantity1 = quantity1_element.text.strip()
            
            # Extract second quantity (total) from third cell
            quantity2_cell = cells[2]
            quantity2_element = quantity2_cell.find_element(By.CSS_SELECTOR, ".order-book-table_content__ZSAZ_")
            quantity2 = quantity2_element.text.strip()
            
            # Determine order type based on button text or cell content
            order_type = 'SELL'  # Based on HTML, these are sell orders (with "Mua" button)
            
            # Create order entry
            order_entry = {
                'token_symbol': symbol,
                'crawled_at': crawled_at,
                'order_type': order_type,
                'price': price,
                'quantity': quantity1,
                'total': quantity2
            }
            
            return order_entry
            
        except Exception as e:
            print(f"      ❌ Error parsing orderbook row: {e}")
            return None
    
    def handle_pagination(self, driver, symbol, crawled_at):
        """Handle pagination to get more order book data"""
        pagination_entries = []
        
        try:
            # Look for pagination using correct CSS selector from HTML
            pagination_selectors = [
                ".order-book-table_paginationWrapper__O_FJg",
                ".ant-pagination",
                "[class*='pagination']"
            ]
            
            pagination_found = False
            for selector in pagination_selectors:
                try:
                    pagination = driver.find_element(By.CSS_SELECTOR, selector)
                    pagination_found = True
                    print(f"      ✅ Found pagination with selector: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if pagination_found:
                # Get all pagination links
                page_links = pagination.find_elements(By.CSS_SELECTOR, ".ant-pagination-item a")
                
                print(f"      📄 Found {len(page_links)} pagination pages")
                
                # Process first few pages (limit to avoid too many requests)
                max_pages = min(3, len(page_links))
                
                for page_num in range(2, max_pages + 1):  # Start from page 2
                    try:
                        print(f"      🔄 Processing page {page_num}...")
                        
                        # Click on page number
                        page_link = pagination.find_element(By.CSS_SELECTOR, f".ant-pagination-item-{page_num} a")
                        page_link.click()
                        
                        # Wait for page to load
                        time.sleep(3)
                        
                        # Extract data from current page
                        current_page_entries = self.extract_current_page_orders(driver, symbol, crawled_at)
                        pagination_entries.extend(current_page_entries)
                        
                        print(f"      📊 Page {page_num}: {len(current_page_entries)} entries")
                        
                    except Exception as e:
                        print(f"      ❌ Error processing page {page_num}: {e}")
                        continue
            else:
                print(f"      ⚠️  No pagination found")
                
        except Exception as e:
            print(f"      ❌ Error handling pagination: {e}")
        
        return pagination_entries
    
    def extract_current_page_orders(self, driver, symbol, crawled_at):
        """Extract order book data from current page"""
        page_entries = []
        
        try:
            # Find order book table on current page
            orderbook_table = driver.find_element(By.CSS_SELECTOR, "tbody.ant-table-tbody")
            rows = orderbook_table.find_elements(By.CSS_SELECTOR, "tr.ant-table-row")
            
            for row in rows:
                try:
                    order_data = self.parse_correct_orderbook_row(row, symbol, crawled_at)
                    if order_data:
                        page_entries.append(order_data)
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"      ❌ Error extracting current page orders: {e}")
        
        return page_entries
    
    def extract_token_data(self, element):
        """Extract token data from element with improved name extraction"""
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
            
            # Extract symbol
            symbol_pattern = r'\b([A-Z]{2,10})\b'
            symbols = re.findall(symbol_pattern, item_text)
            if symbols:
                token_data['symbol'] = symbols[0]
            
            # Extract name with CORRECT CSS selector from real HTML
            if token_data['symbol']:
                # Strategy 1: Use the exact CSS selector from real HTML
                try:
                    # The exact CSS selector for token name from HTML
                    name_element = element.find_element(By.CSS_SELECTOR, ".trade-list-item_fullCurrency__UGLmN")
                    if name_element:
                        name_text = name_element.text.strip()
                        # Filter out unwanted text like "Giá giao dịch mới nhất"
                        if (name_text and 
                            name_text != token_data['symbol'] and
                            name_text != "Giá giao dịch mới nhất" and
                            not re.search(r'Giá giao dịch|Khối lượng|Tổng khối lượng|Đang diễn ra|Đợi xác nhận', name_text)):
                            # Clean the name text
                            clean_name = re.sub(r'[^\w\s\-&]', ' ', name_text).strip()
                            if clean_name and len(clean_name) > 1:
                                token_data['name'] = clean_name
                except:
                    pass
                
                # Strategy 2: Fallback to other selectors if the main one fails
                if not token_data['name']:
                    fallback_selectors = [
                        ".trade-list-item_currency__GO5BC",  # Symbol selector (fallback)
                        "[class*='fullCurrency']",
                        "[class*='currency']",
                        "[class*='name']",
                        "[class*='title']"
                    ]
                    
                    for selector in fallback_selectors:
                        try:
                            elements = element.find_elements(By.CSS_SELECTOR, selector)
                            for elem in elements:
                                name_text = elem.text.strip()
                                # Filter out unwanted text
                                if (name_text and 
                                    name_text != token_data['symbol'] and 
                                    name_text != "Giá giao dịch mới nhất" and
                                    not re.search(r'[\d,]+\.?\d*|[+-]?\d+\.?\d*%|Giá giao dịch|Khối lượng|Tổng khối lượng|Đang diễn ra|Đợi xác nhận', name_text)):
                                    # Clean the name text
                                    clean_name = re.sub(r'[^\w\s\-&]', ' ', name_text).strip()
                                    if clean_name and len(clean_name) > 1:
                                        token_data['name'] = clean_name
                                        break
                            if token_data['name']:
                                break
                        except:
                            continue
                
                # Strategy 2: Try to extract from text structure if CSS failed
                if not token_data['name']:
                    lines = [line.strip() for line in item_text.split('\n') if line.strip()]
                    
                    # Look for name in the first line (usually contains the token name)
                    if lines:
                        first_line = lines[0]
                        # Remove symbol from first line and see what's left
                        if token_data['symbol'] in first_line:
                            symbol_pos = first_line.find(token_data['symbol'])
                            # Try text before symbol
                            if symbol_pos > 0:
                                text_before = first_line[:symbol_pos].strip()
                                if text_before and not re.search(r'[\d,]+\.?\d*|[+-]?\d+\.?\d*%', text_before):
                                    clean_name = re.sub(r'[^\w\s\-&]', ' ', text_before).strip()
                                    if clean_name and len(clean_name) > 1:
                                        token_data['name'] = clean_name
                            # Try text after symbol
                            elif symbol_pos >= 0:
                                text_after = first_line[symbol_pos + len(token_data['symbol']):].strip()
                                if text_after and not re.search(r'[\d,]+\.?\d*|[+-]?\d+\.?\d*%', text_after):
                                    clean_name = re.sub(r'[^\w\s\-&]', ' ', text_after).strip()
                                    if clean_name and len(clean_name) > 1:
                                        token_data['name'] = clean_name
                    
                    # If still no name, try previous line
                    if not token_data['name'] and len(lines) > 1:
                        for i, line in enumerate(lines):
                            if token_data['symbol'] in line and i > 0:
                                prev_line = lines[i-1].strip()
                                if prev_line and not re.search(r'[\d,]+\.?\d*|[+-]?\d+\.?\d*%', prev_line):
                                    clean_name = re.sub(r'[^\w\s\-&]', ' ', prev_line).strip()
                                    if clean_name and len(clean_name) > 1:
                                        token_data['name'] = clean_name
                                        break
            
            # Final fallback - use symbol as name only if no name found
            if not token_data['name']:
                token_data['name'] = token_data['symbol']
            
            # Extract latest price
            price_pattern = r'Giá giao dịch mới nhất\s*([\d,]+\.?\d*)'
            price_match = re.search(price_pattern, item_text)
            if price_match:
                token_data['latest_price'] = price_match.group(1)
            
            # Extract percentage change
            change_pattern = r'([+-]?\d+\.?\d*%)'
            change_match = re.search(change_pattern, item_text)
            if change_match:
                token_data['price_change_percent'] = change_match.group(1)
            
            # Extract volume 24h
            volume_24h_pattern = r'Khối lượng 24 giờ\s*([\d,]+\.?\d*[KMB]?)'
            volume_24h_match = re.search(volume_24h_pattern, item_text)
            if volume_24h_match:
                token_data['volume_24h'] = volume_24h_match.group(1)
            
            # Extract total volume
            total_volume_pattern = r'Tổng khối lượng\s*([\d,]+\.?\d*[KMB]?)'
            total_volume_match = re.search(total_volume_pattern, item_text)
            if total_volume_match:
                token_data['total_volume'] = total_volume_match.group(1)
            
            # Extract start time
            time_pattern = r'Đang diễn ra(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
            time_match = re.search(time_pattern, item_text)
            if time_match:
                token_data['start_time'] = time_match.group(1)
            
            # Extract end time/status
            end_time_patterns = [r'Đợi xác nhận', r'Đã kết thúc', r'Đang diễn ra']
            for pattern in end_time_patterns:
                end_match = re.search(pattern, item_text)
                if end_match:
                    token_data['end_time'] = pattern
                    break
            
            # Alternative parsing
            if not token_data['latest_price']:
                price_pattern = r'(\d+\.\d{2,4})'
                prices = re.findall(price_pattern, item_text)
                if prices:
                    token_data['latest_price'] = prices[0]
            
            if not token_data['volume_24h']:
                volume_pattern = r'(\d+\.?\d*[KMB])'
                volumes = re.findall(volume_pattern, item_text)
                if len(volumes) >= 1:
                    token_data['volume_24h'] = volumes[0]
                if len(volumes) >= 2:
                    token_data['total_volume'] = volumes[1]
            
            return token_data
            
        except Exception as e:
            print(f"Error extracting token data: {e}")
            return None
    
    def try_alternative_token_extraction(self, driver):
        """Try alternative methods to extract token data"""
        try:
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            potential_elements = soup.find_all(['div', 'span', 'p'], string=re.compile(r'[A-Z]{2,}'))
            
            for element in potential_elements:
                text = element.get_text().strip()
                if len(text) >= 2 and len(text) <= 10 and text.isalpha():
                    token_data = {
                        'name': text,
                        'symbol': text,
                        'latest_price': '',
                        'price_change_percent': '',
                        'volume_24h': '',
                        'total_volume': '',
                        'start_time': '',
                        'end_time': '',
                        'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    self.tokens_data.append(token_data)
            
        except Exception as e:
            print(f"Error in alternative token extraction: {e}")
    
    def save_to_file(self):
        """Save all data to a single comprehensive file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mexc_correct_orderbook_data_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # Write header
                f.write("=== MEXC CORRECT ORDER BOOK CRAWLER DATA ===\n")
                f.write(f"Crawled at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total tokens: {len(self.tokens_data)}\n")
                f.write(f"Total correct order book entries: {len(self.orderbook_data)}\n")
                f.write("=" * 60 + "\n\n")
                
                # Write token data
                f.write("=== TOKEN DATA ===\n")
                f.write("Name\tSymbol\tLatest Price\tPrice Change %\tVolume 24h\tTotal Volume\tStart Time\tEnd Time\tCrawled At\n")
                
                for token in self.tokens_data:
                    line = f"{token.get('name', '')}\t"
                    line += f"{token.get('symbol', '')}\t"
                    line += f"{token.get('latest_price', '')}\t"
                    line += f"{token.get('price_change_percent', '')}\t"
                    line += f"{token.get('volume_24h', '')}\t"
                    line += f"{token.get('total_volume', '')}\t"
                    line += f"{token.get('start_time', '')}\t"
                    line += f"{token.get('end_time', '')}\t"
                    line += f"{token.get('crawled_at', '')}\n"
                    f.write(line)
                
                f.write("\n" + "=" * 60 + "\n")
                
                # Write order book data
                f.write("=== CORRECT ORDER BOOK DATA ===\n")
                f.write("Token Symbol\tCrawled At\tOrder Type\tPrice\tQuantity\tTotal\n")
                
                for order in self.orderbook_data:
                    line = f"{order.get('token_symbol', '')}\t"
                    line += f"{order.get('crawled_at', '')}\t"
                    line += f"{order.get('order_type', '')}\t"
                    line += f"{order.get('price', '')}\t"
                    line += f"{order.get('quantity', '')}\t"
                    line += f"{order.get('total', '')}\n"
                    f.write(line)
                
                f.write("\n" + "=" * 60 + "\n")
                f.write("END OF CORRECT DATA\n")
            
            print(f"✅ All correct data saved to: {filename}")
            
        except Exception as e:
            print(f"❌ Error saving data: {e}")


def main():
    """Main function"""
    print("🚀 MEXC Correct Order Book Crawler")
    print("Uses correct URL pattern and CSS selectors from real HTML")
    print("=" * 60)
    
    crawler = MexcCorrectOrderBookCrawler()
    
    # Run the correct order book crawler
    tokens_data, orderbook_data = crawler.crawl_all_data()
    
    if tokens_data:
        # Save all data to file
        crawler.save_to_file()
        
        print("\n🎉 CORRECT ORDER BOOK CRAWLING COMPLETED!")
        
        # Display summary
        print("\n📊 SUMMARY:")
        print(f"   • Tokens extracted: {len(tokens_data)}")
        print(f"   • Correct order book entries: {len(orderbook_data)}")
        
        # Display sample token data
        print("\n🔍 SAMPLE TOKEN DATA:")
        for i, token in enumerate(tokens_data[:3]):
            print(f"   {i+1}. {token.get('symbol', 'N/A')}: {token.get('latest_price', 'N/A')} ({token.get('price_change_percent', 'N/A')})")
        
        # Display sample correct order book data
        if orderbook_data:
            print("\n📈 SAMPLE CORRECT ORDER BOOK DATA:")
            for i, order in enumerate(orderbook_data[:10]):  # Show first 10 entries
                print(f"   {i+1}. {order.get('token_symbol', 'N/A')} {order.get('order_type', 'N/A')}: {order.get('price', 'N/A')} x {order.get('quantity', 'N/A')} (Total: {order.get('total', 'N/A')})")
        else:
            print("\n⚠️  No correct order book data was extracted")
        
        print(f"\n📁 Correct data saved to: mexc_correct_orderbook_data_YYYYMMDD_HHMMSS.txt")
        
    else:
        print("❌ No data was extracted. Please check your setup and try again.")


if __name__ == "__main__":
    main()

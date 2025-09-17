#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MEXC MENTO Token Crawler
Crawls order book data for MENTO token specifically
Order type is determined by button content (Mua/Bán) not SELL/BUY
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


class MexcMentoCrawler:
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
        
    def crawl_mento_data(self):
        """Crawl MENTO token data and order book"""
        print("🚀 MEXC MENTO Token Crawler")
        print("=" * 70)
        print("📊 Target: MENTO token only")
        print("📊 Phase 1: Getting MENTO token data from pre-market")
        print("📊 Phase 2: Crawling order book for MENTO")
        print("=" * 70)
        
        # Phase 1: Get MENTO token data from pre-market page
        self.crawl_mento_token_data()
        
        # Phase 2: Crawl order book for MENTO
        if self.tokens_data:
            print(f"\n🔄 Phase 2: Crawling order book for MENTO...")
            self.crawl_mento_orderbook()
        
        print(f"\n🎯 MENTO CRAWLING COMPLETED!")
        print(f"   • Tokens extracted: {len(self.tokens_data)}")
        print(f"   • Order book entries: {len(self.orderbook_data)}")
        
        return self.tokens_data, self.orderbook_data
    
    def crawl_mento_token_data(self):
        """Crawl MENTO token data from pre-market page"""
        print(f"\n📋 Phase 1: Getting MENTO token data from pre-market...")
        
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
                    print("✅ Found token list, searching for MENTO...")
                    token_items = token_list.find_elements(By.TAG_NAME, "li")
                    
                    print(f"📊 Found {len(token_items)} token items, searching for MENTO")
                    
                    mento_found = False
                    for i, item in enumerate(token_items):
                        try:
                            # Check if this item contains MENTO
                            item_text = item.text
                            if 'MENTO' in item_text.upper():
                                print(f"🔄 Found MENTO token at position {i+1}")
                                
                                # Extract token data
                                token_data = self.extract_token_data(item)
                                if token_data:
                                    self.tokens_data.append(token_data)
                                    symbol = token_data.get('symbol', '')
                                    print(f"✅ MENTO token data extracted: {symbol}")
                                    print(f"   • Latest Price: {token_data.get('latest_price', 'N/A')}")
                                    print(f"   • Price Change: {token_data.get('price_change_percent', 'N/A')}")
                                    print(f"   • Volume 24h: {token_data.get('volume_24h', 'N/A')}")
                                    print(f"   • Total Volume: {token_data.get('total_volume', 'N/A')}")
                                    print(f"   • Start Time: {token_data.get('start_time', 'N/A')}")
                                    print(f"   • End Time: {token_data.get('end_time', 'N/A')}")
                                    mento_found = True
                                    break
                            
                        except Exception as e:
                            print(f"❌ Error processing token {i+1}: {e}")
                            continue
                    
                    if not mento_found:
                        print(f"⚠️  MENTO token not found in pre-market list")
                        # Create minimal token data as fallback
                        self.tokens_data = [{
                            'name': 'MENTO',
                            'symbol': 'MENTO',
                            'latest_price': '',
                            'price_change_percent': '',
                            'volume_24h': '',
                            'total_volume': '',
                            'start_time': '',
                            'end_time': '',
                            'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }]
                        print(f"📝 Created minimal token data for MENTO")
                
            except TimeoutException:
                print("⚠️ Timeout waiting for token list. Creating minimal token data...")
                # Create minimal token data as fallback
                self.tokens_data = [{
                    'name': 'MENTO',
                    'symbol': 'MENTO',
                    'latest_price': '',
                    'price_change_percent': '',
                    'volume_24h': '',
                    'total_volume': '',
                    'start_time': '',
                    'end_time': '',
                    'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }]
                print(f"📝 Created minimal token data for MENTO")
                
        except Exception as e:
            print(f"❌ Error in token data crawling: {e}")
            # Create minimal token data as fallback
            self.tokens_data = [{
                'name': 'MENTO',
                'symbol': 'MENTO',
                'latest_price': '',
                'price_change_percent': '',
                'volume_24h': '',
                'total_volume': '',
                'start_time': '',
                'end_time': '',
                'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }]
            print(f"📝 Created minimal token data for MENTO")
            
        finally:
            if driver:
                driver.quit()
    
    def crawl_mento_orderbook(self):
        """Crawl order book data for MENTO token"""
        print(f"\n📈 Phase 2: Crawling order book for MENTO...")
        
        for token in self.tokens_data:
            symbol = token.get('symbol', '')
            if symbol and symbol.upper() == 'MENTO':
                print(f"\n🔄 Processing MENTO order book...")
                
                try:
                    # Use correct URL pattern for MENTO
                    orderbook_entries = self.crawl_orderbook_for_mento(symbol)
                    self.orderbook_data.extend(orderbook_entries)
                    
                    if orderbook_entries:
                        print(f"✅ Order book: {len(orderbook_entries)} entries for MENTO")
                    else:
                        print(f"⚠️  No order book data found for MENTO")
                    
                except Exception as e:
                    print(f"❌ Error crawling order book for MENTO: {e}")
                    continue
    
    def crawl_orderbook_for_mento(self, symbol):
        """Crawl order book data for MENTO token"""
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
            
            # Use correct URL pattern for MENTO
            url = f'https://www.mexc.com/vi-VN/pre-market/{symbol}'
            print(f"  🔗 Loading URL: {url}")
            
            driver.get(url)
            
            # Wait for the page to load
            wait = WebDriverWait(driver, 15)
            time.sleep(5)
            
            # Check if page loaded successfully
            if "404" not in driver.title and "error" not in driver.title.lower():
                print(f"  ✅ Successfully loaded order book page for MENTO")
                
                # Extract order book data - focus on orders with "Mua" button
                orderbook_entries = self.extract_mento_orderbook(driver, symbol)
                
                if orderbook_entries:
                    print(f"  📊 Found {len(orderbook_entries)} order book entries")
                else:
                    print(f"  ⚠️  No order book data found on {url}")
            else:
                print(f"  ❌ Page not found: {url}")
                
        except Exception as e:
            print(f"❌ Error crawling order book for MENTO: {e}")
            
        finally:
            if driver:
                driver.quit()
        
        return orderbook_entries
    
    def extract_mento_orderbook(self, driver, symbol):
        """Extract order book data for MENTO - crawl both Mua and Bán orders"""
        orderbook_entries = []
        crawled_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            print(f"    🔍 Extracting MENTO order book data...")
            
            # Phase 1: Crawl SELL orders (lệnh bán) - table with "Mua" buttons
            print(f"    🔍 Phase 1: Crawling SELL orders (lệnh bán) with 'Mua' buttons...")
            sell_entries = self.crawl_order_type(driver, symbol, crawled_at,
                                               table_selector=".order-book-table_sellTable__Dxd2s",
                                               price_selector=".order-book-table_sellPrice__xAuZe",
                                               expected_button="Mua",
                                               order_type_name="SELL orders")
            orderbook_entries.extend(sell_entries)
            
            # Phase 2: Crawl BUY orders (lệnh mua) - table with "Bán" buttons  
            print(f"    🔍 Phase 2: Crawling BUY orders (lệnh mua) with 'Bán' buttons...")
            buy_entries = self.crawl_order_type(driver, symbol, crawled_at,
                                              table_selector=".order-book-table_buyTable__xqBVW", 
                                              price_selector=".order-book-table_buyPrice__uY0OB",
                                              expected_button="Bán",
                                              order_type_name="BUY orders")
            orderbook_entries.extend(buy_entries)
            
            print(f"    ✅ Total extracted: {len(orderbook_entries)} entries ({len(sell_entries)} SELL + {len(buy_entries)} BUY)")
            
        except Exception as e:
            print(f"    ❌ Error extracting MENTO order book: {str(e)}")
        
        return orderbook_entries
    
    def crawl_order_type(self, driver, symbol, crawled_at, table_selector, price_selector, expected_button, order_type_name):
        """Crawl specific order type (SELL or BUY orders)"""
        orderbook_entries = []
        
        try:
            # Find the specific table
            table = driver.find_element(By.CSS_SELECTOR, table_selector)
            
            if table:
                print(f"      ✅ Found {order_type_name} table")
                
                # Extract rows from this table
                rows = table.find_elements(By.CSS_SELECTOR, "tr")
                print(f"      📊 Found {len(rows)} rows in {order_type_name} table")
                
                # Parse each row
                valid_entries = 0
                for i, row in enumerate(rows):
                    try:
                        # Skip measurement rows
                        if self.is_measurement_row(row):
                            continue
                        
                        # Extract order data from row
                        order_data = self.parse_mento_order_row(row, symbol, crawled_at, price_selector, expected_button)
                        if order_data:
                            orderbook_entries.append(order_data)
                            valid_entries += 1
                            
                            # Show first few entries
                            if i < 5:
                                print(f"        ✅ Row {i+1}: {order_data['order_type']} - {order_data['price']} x {order_data['quantity']}")
                                
                    except Exception as e:
                        print(f"        ❌ Error parsing {order_type_name} row {i+1}: {e}")
                        continue
                
                print(f"      📊 Successfully parsed {valid_entries} entries from {order_type_name}")
                
                # Handle pagination for this table
                pagination_entries = self.handle_mento_pagination(driver, symbol, crawled_at, table_selector, price_selector, expected_button, order_type_name)
                orderbook_entries.extend(pagination_entries)
                
                if pagination_entries:
                    print(f"      📊 Found {len(pagination_entries)} additional entries from {order_type_name} pagination")
                
            else:
                print(f"      ⚠️  {order_type_name} table not found")
                
        except NoSuchElementException:
            print(f"      ⚠️  {order_type_name} table not found with selector: {table_selector}")
        except Exception as e:
            print(f"      ❌ Error with {order_type_name} table: {e}")
        
        return orderbook_entries

    def parse_mento_order_row(self, row_element, symbol, crawled_at, price_selector=None, expected_button=None):
        """Parse order book row for MENTO - order type comes from button content"""
        try:
            # Skip measurement rows
            if self.is_measurement_row(row_element):
                return None
            
            # Extract data from row cells
            cells = row_element.find_elements(By.TAG_NAME, 'td')
            if len(cells) < 3:
                return None
            
            # Extract price from first cell with specific selector
            price = ''
            if price_selector:
                try:
                    price_element = cells[0].find_element(By.CSS_SELECTOR, price_selector)
                    price = price_element.text.strip()
                except:
                    price = cells[0].text.strip()
            else:
                price = cells[0].text.strip()
            
            # Extract quantity from second cell
            quantity = ''
            try:
                quantity_element = cells[1].find_element(By.CSS_SELECTOR, ".order-book-table_content__ZSAZ_")
                quantity = quantity_element.text.strip()
            except:
                quantity = cells[1].text.strip()
            
            # Extract total from third cell
            total = ''
            try:
                total_element = cells[2].find_element(By.CSS_SELECTOR, ".order-book-table_content__ZSAZ_")
                total = total_element.text.strip()
            except:
                total = cells[2].text.strip()
            
            # Extract order type from button content (Mua/Bán)
            order_type = ''
            try:
                # Look for button with expected text
                button = row_element.find_element(By.CSS_SELECTOR, "button")
                button_text = button.text.strip()
                
                # Use the actual button text as order type
                if button_text in ['Mua', 'Bán']:
                    order_type = button_text
                else:
                    # Fallback: look for button content in span
                    try:
                        button_span = button.find_element(By.CSS_SELECTOR, "span")
                        button_span_text = button_span.text.strip()
                        if button_span_text in ['Mua', 'Bán']:
                            order_type = button_span_text
                    except:
                        pass
                
            except NoSuchElementException:
                pass
            
            # Use expected button as fallback
            if not order_type and expected_button:
                order_type = expected_button
            
            # Skip if no valid data
            if not price and not quantity:
                return None
            
            # Create order entry
            order_entry = {
                'token_symbol': symbol,
                'crawled_at': crawled_at,
                'order_type': order_type or 'Unknown',
                'price': price or '',
                'quantity': quantity or '',
                'total': total or ''
            }
            
            return order_entry
            
        except Exception as e:
            print(f"        ❌ Error parsing MENTO order row: {e}")
            return None
    
    def handle_mento_pagination(self, driver, symbol, crawled_at, table_selector, price_selector=None, expected_button=None, order_type_name=""):
        """Handle pagination for MENTO - crawl ALL pages for complete data"""
        pagination_entries = []
        
        try:
            # Look for pagination - use specific selector based on order type
            if "sellTable" in table_selector:
                # SELL orders pagination - first pagination wrapper
                pagination_selectors = [
                    ".order-book-table_paginationWrapper__O_FJg:first-of-type",
                    ".order-book-table_sellTable__Dxd2s + .order-book-table_paginationWrapper__O_FJg",
                    ".ant-pagination",
                    "[class*='pagination']"
                ]
            elif "buyTable" in table_selector:
                # BUY orders pagination - second pagination wrapper
                pagination_selectors = [
                    ".order-book-table_buyTable__xqBVW .order-book-table_paginationWrapper__O_FJg",
                    ".order-book-table_buyTable__xqBVW + .order-book-table_paginationWrapper__O_FJg",
                    ".order-book-table_paginationWrapper__O_FJg:last-of-type",
                    ".ant-pagination",
                    "[class*='pagination']"
                ]
            else:
                # Fallback
                pagination_selectors = [
                    ".order-book-table_paginationWrapper__O_FJg",
                    ".ant-pagination",
                    "[class*='pagination']"
                ]
            
            pagination = None
            for selector in pagination_selectors:
                try:
                    pagination = driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"      ✅ Found pagination with selector: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not pagination:
                print(f"      ℹ️  No pagination found for {order_type_name}")
                return pagination_entries
            
            # Get page numbers
            page_items = pagination.find_elements(By.CSS_SELECTOR, ".ant-pagination-item")
            if not page_items:
                print(f"      ℹ️  No page items found")
                return pagination_entries
            
            # Debug: Show all pagination items
            print(f"      🔍 Debug: Found {len(page_items)} pagination items for {order_type_name}")
            for i, item in enumerate(page_items):
                title = item.get_attribute('title') or 'No title'
                text = item.text.strip()
                classes = item.get_attribute('class') or 'No class'
                print(f"        Item {i+1}: title='{title}', text='{text}', class='{classes}'")
            
            # Get available page numbers (only crawl pages that actually exist)
            available_pages = []
            for item in page_items:
                try:
                    page_num = int(item.get_attribute('title'))
                    available_pages.append(page_num)
                except:
                    continue
            
            # Sort and get max page
            available_pages.sort()
            max_page = max(available_pages) if available_pages else 1
            
            print(f"      📄 Found {len(page_items)} pages, max page: {max_page}, available pages: {available_pages}")
            
            # Process ALL pages from 2 to max_page for both order types
            if max_page > 1:
                print(f"      🔄 Processing ALL pages from 2 to {max_page} for {order_type_name}")
                pages_to_process = list(range(2, max_page + 1))
                
                for page_num in pages_to_process:
                    try:
                        print(f"      🔄 Processing page {page_num}...")
                        
                        # Find and click page link with multiple approaches
                        page_link = None
                        page_selectors = [
                            f".ant-pagination-item-{page_num}",
                            f"[title='{page_num}']",
                            f"li[title='{page_num}']",
                            f"a[title='{page_num}']",
                            f"button[title='{page_num}']"
                        ]
                        
                        for selector in page_selectors:
                            try:
                                page_link = pagination.find_element(By.CSS_SELECTOR, selector)
                                print(f"        ✅ Found page link with selector: {selector}")
                                break
                            except NoSuchElementException:
                                continue
                        
                        # If still not found, try finding by text content
                        if not page_link:
                            try:
                                page_links = pagination.find_elements(By.CSS_SELECTOR, ".ant-pagination-item")
                                for link in page_links:
                                    if link.text.strip() == str(page_num):
                                        page_link = link
                                        print(f"        ✅ Found page link by text content: {page_num}")
                                        break
                            except:
                                pass
                        
                        # If still not found, try finding by index (if we know the order)
                        if not page_link:
                            try:
                                page_links = pagination.find_elements(By.CSS_SELECTOR, ".ant-pagination-item")
                                if page_num - 1 < len(page_links):  # page_num is 1-indexed, array is 0-indexed
                                    page_link = page_links[page_num - 1]
                                    print(f"        ✅ Found page link by index: {page_num}")
                            except:
                                pass
                        
                        # If still not found, try to click next/prev buttons to reveal more pages
                        if not page_link and page_num <= 9:
                            try:
                                # Try clicking next button to reveal more pages
                                next_button = pagination.find_element(By.CSS_SELECTOR, ".ant-pagination-next")
                                if next_button.is_enabled():
                                    driver.execute_script("arguments[0].click();", next_button)
                                    time.sleep(2)
                                    
                                    # Try to find the page link again
                                    for selector in page_selectors:
                                        try:
                                            page_link = pagination.find_element(By.CSS_SELECTOR, selector)
                                            print(f"        ✅ Found page link after clicking next: {selector}")
                                            break
                                        except NoSuchElementException:
                                            continue
                            except:
                                pass
                        
                        if page_link:
                            # Click page link
                            driver.execute_script("arguments[0].click();", page_link)
                            print(f"        ✅ Clicked page {page_num}")
                            
                            # Wait for data to load with longer timeout
                            time.sleep(5)
                            
                            # Wait for pagination to update and show current page
                            max_wait_attempts = 10
                            for attempt in range(max_wait_attempts):
                                try:
                                    # Check if pagination shows we're on the correct page
                                    active_item = pagination.find_element(By.CSS_SELECTOR, ".ant-pagination-item-active")
                                    active_page = int(active_item.get_attribute('title'))
                                    if active_page == page_num:
                                        print(f"        ✅ Confirmed on page {page_num}")
                                        break
                                    else:
                                        print(f"        ⏳ Waiting for page {page_num}, currently on {active_page} (attempt {attempt+1})")
                                        time.sleep(1)
                                except:
                                    print(f"        ⏳ Waiting for pagination to update (attempt {attempt+1})")
                                    time.sleep(1)
                            
                            # Additional wait for table data to refresh
                            time.sleep(3)
                            
                            # Scroll to trigger any lazy loading
                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            time.sleep(1)
                            driver.execute_script("window.scrollTo(0, 0);")
                            time.sleep(1)
                            
                            # Extract data from current page
                            try:
                                table = driver.find_element(By.CSS_SELECTOR, table_selector)
                                rows = table.find_elements(By.CSS_SELECTOR, "tr")
                                
                                page_entries = []
                                # Create new timestamp for this page
                                page_crawled_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                
                                for row in rows:
                                    if not self.is_measurement_row(row):
                                        order_data = self.parse_mento_order_row(row, symbol, page_crawled_at, price_selector, expected_button)
                                        if order_data:
                                            page_entries.append(order_data)
                                
                                # Debug: Show first few entries from this page to verify data is different
                                pagination_entries.extend(page_entries)
                                print(f"        📊 Page {page_num}: {len(page_entries)} entries")
                                
                            except Exception as e:
                                print(f"      ❌ Error extracting page {page_num}: {e}")
                        else:
                            print(f"      ❌ Page {page_num} link not found - trying to scroll and wait...")
                            # Try scrolling to see if more pagination appears
                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            time.sleep(2)
                            driver.execute_script("window.scrollTo(0, 0);")
                            time.sleep(2)
                            
                            # Try to find the page link again after scrolling
                            for selector in page_selectors:
                                try:
                                    page_link = pagination.find_element(By.CSS_SELECTOR, selector)
                                    print(f"        ✅ Found page link after scrolling with selector: {selector}")
                                    break
                                except NoSuchElementException:
                                    continue
                            
                            if page_link:
                                driver.execute_script("arguments[0].click();", page_link)
                                print(f"        ✅ Clicked page {page_num} after scrolling")
                                time.sleep(3)
                            else:
                                print(f"      ❌ Page {page_num} still not found after scrolling")
                            
                    except Exception as e:
                        print(f"      ❌ Error processing page {page_num}: {e}")
                        continue
                
                print(f"      ✅ Completed FULL pagination for {order_type_name}: {len(pagination_entries)} additional entries from {max_page-1} pages")
            else:
                print(f"      ℹ️  Only 1 page available for {order_type_name}, no pagination needed")
                
        except Exception as e:
            print(f"      ❌ Error handling pagination: {e}")
        
        return pagination_entries
    
    def is_measurement_row(self, row_element):
        """Check if this is an Ant Design measurement row that should be skipped"""
        try:
            # Check aria-hidden attribute
            aria_hidden = row_element.get_attribute('aria-hidden')
            if aria_hidden == 'true':
                return True
            
            # Check class name
            class_name = row_element.get_attribute('class') or ''
            if 'ant-table-measure-row' in class_name:
                return True
            
            # Check style
            style = row_element.get_attribute('style') or ''
            if 'height: 0px' in style and 'font-size: 0px' in style:
                return True
            
            return False
            
        except:
            return False
    
    def extract_token_data(self, element):
        """Extract token data from element"""
        try:
            item_text = element.text
            if not item_text.strip():
                return None
            
            token_data = {
                'name': 'MENTO',
                'symbol': 'MENTO',
                'latest_price': '',
                'price_change_percent': '',
                'volume_24h': '',
                'total_volume': '',
                'start_time': '',
                'end_time': '',
                'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
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
            time_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
            time_match = re.search(time_pattern, item_text)
            if time_match:
                token_data['start_time'] = time_match.group(1)
            
            # Extract status
            end_time_patterns = [r'Đợi xác nhận', r'Đã kết thúc', r'Đang diễn ra']
            for pattern in end_time_patterns:
                end_match = re.search(pattern, item_text)
                if end_match:
                    token_data['end_time'] = pattern
                    break
            
            return token_data
            
        except Exception as e:
            print(f"Error extracting token data: {e}")
            return None
    
    def save_to_file(self):
        """Save all data to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mexc_mento_data_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # Write header
                f.write("=== MEXC MENTO TOKEN CRAWLER DATA ===\n")
                f.write(f"Crawled at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total tokens: {len(self.tokens_data)}\n")
                f.write(f"Total order book entries: {len(self.orderbook_data)}\n")
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
                f.write("=== MENTO ORDER BOOK DATA ===\n")
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
                f.write("END OF MENTO DATA\n")
            
            print(f"✅ All MENTO data saved to: {filename}")
            
        except Exception as e:
            print(f"❌ Error saving data: {e}")


def main():
    """Main function to crawl MENTO token"""
    print("🚀 MEXC MENTO Token Crawler")
    print("Focus on orders with Mua button, order type = button content")
    print("=" * 60)
    
    crawler = MexcMentoCrawler()
    
    # Run the MENTO crawler
    tokens_data, orderbook_data = crawler.crawl_mento_data()
    
    if tokens_data:
        # Save all data to file
        crawler.save_to_file()
        
        print("\n🎉 MENTO CRAWLING COMPLETED!")
        
        # Display summary
        print("\n📊 SUMMARY:")
        print(f"   • Tokens extracted: {len(tokens_data)}")
        print(f"   • Order book entries: {len(orderbook_data)}")
        
        # Display token data
        print("\n🔍 MENTO TOKEN DATA:")
        for token in tokens_data:
            print(f"   • {token.get('symbol', 'N/A')}: {token.get('latest_price', 'N/A')} ({token.get('price_change_percent', 'N/A')})")
        
        # Display sample order book data
        if orderbook_data:
            print("\n📈 SAMPLE MENTO ORDER BOOK DATA:")
            for i, order in enumerate(orderbook_data[:10]):  # Show first 10 entries
                print(f"   {i+1}. {order.get('token_symbol', 'N/A')} {order.get('order_type', 'N/A')}: {order.get('price', 'N/A')} x {order.get('quantity', 'N/A')} (Total: {order.get('total', 'N/A')})")
        else:
            print("\n⚠️  No order book data was extracted")
        
        print(f"\n📁 MENTO data saved to: mexc_mento_data_YYYYMMDD_HHMMSS.txt")
        
    else:
        print("❌ No MENTO data was extracted. Please check your setup and try again.")


if __name__ == "__main__":
    main()

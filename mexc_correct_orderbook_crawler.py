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
        
    def crawl_all_data(self, target_symbol=None):
        """Crawl all data: tokens from pre-market + real order book from correct URLs
        
        Args:
            target_symbol (str, optional): If specified, only crawl this specific symbol. 
                                         If None, crawl all tokens from pre-market.
        """
        print("🚀 MEXC Correct Order Book Crawler")
        print("=" * 70)
        
        if target_symbol:
            print(f"📊 Target: {target_symbol} only")
            print("📊 Phase 1: Crawling token data for target symbol")
            print("📊 Phase 2: Crawling real order book for target symbol")
            
            # Crawl token data for target symbol from pre-market page
            self.crawl_token_data_for_symbol(target_symbol)
        else:
            print("📊 Phase 1: Crawling token list from pre-market")
            print("📊 Phase 2: Crawling real order book from correct URLs")
            
            # Phase 1: Get token list from pre-market
            self.crawl_token_list()
        
        print("=" * 70)
        
        # Phase 2: Crawl real order book for each token
        if self.tokens_data:
            print(f"\n🔄 Phase 2: Crawling real order book for {len(self.tokens_data)} tokens...")
            self.crawl_correct_orderbooks()
        
        print(f"\n🎯 CRAWLING COMPLETED!")
        print(f"   • Tokens extracted: {len(self.tokens_data)}")
        print(f"   • Real order book entries: {len(self.orderbook_data)}")
        
        return self.tokens_data, self.orderbook_data
    
    def crawl_token_data_for_symbol(self, target_symbol):
        """Crawl token data for a specific symbol from pre-market page"""
        print(f"\n📋 Phase 1: Getting token data for {target_symbol} from pre-market...")
        
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
                    print("✅ Found token list, searching for target symbol...")
                    token_items = token_list.find_elements(By.TAG_NAME, "li")
                    
                    print(f"📊 Found {len(token_items)} token items, searching for {target_symbol}")
                    
                    target_token_found = False
                    for i, item in enumerate(token_items):
                        try:
                            # Check if this item contains our target symbol
                            item_text = item.text
                            if target_symbol.upper() in item_text.upper():
                                print(f"🔄 Found target token {target_symbol} at position {i+1}")
                                
                                # Extract token data
                                token_data = self.extract_token_data(item)
                                if token_data:
                                    self.tokens_data.append(token_data)
                                    symbol = token_data.get('symbol', '')
                                    print(f"✅ Token data extracted: {symbol}")
                                    print(f"   • Latest Price: {token_data.get('latest_price', 'N/A')}")
                                    print(f"   • Price Change: {token_data.get('price_change_percent', 'N/A')}")
                                    print(f"   • Volume 24h: {token_data.get('volume_24h', 'N/A')}")
                                    print(f"   • Total Volume: {token_data.get('total_volume', 'N/A')}")
                                    print(f"   • Start Time: {token_data.get('start_time', 'N/A')}")
                                    print(f"   • End Time: {token_data.get('end_time', 'N/A')}")
                                    target_token_found = True
                                    break
                            
                        except Exception as e:
                            print(f"❌ Error processing token {i+1}: {e}")
                            continue
                    
                    if not target_token_found:
                        print(f"⚠️  Target token {target_symbol} not found in pre-market list")
                        # Create minimal token data as fallback
                        self.tokens_data = [{
                            'name': target_symbol,
                            'symbol': target_symbol,
                            'latest_price': '',
                            'price_change_percent': '',
                            'volume_24h': '',
                            'total_volume': '',
                            'start_time': '',
                            'end_time': '',
                            'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }]
                        print(f"📝 Created minimal token data for {target_symbol}")
                
            except TimeoutException:
                print("⚠️ Timeout waiting for token list. Creating minimal token data...")
                # Create minimal token data as fallback
                self.tokens_data = [{
                    'name': target_symbol,
                    'symbol': target_symbol,
                    'latest_price': '',
                    'price_change_percent': '',
                    'volume_24h': '',
                    'total_volume': '',
                    'start_time': '',
                    'end_time': '',
                    'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }]
                print(f"📝 Created minimal token data for {target_symbol}")
                
        except Exception as e:
            print(f"❌ Error in token data crawling: {e}")
            # Create minimal token data as fallback
            self.tokens_data = [{
                'name': target_symbol,
                'symbol': target_symbol,
                'latest_price': '',
                'price_change_percent': '',
                'volume_24h': '',
                'total_volume': '',
                'start_time': '',
                'end_time': '',
                'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }]
            print(f"📝 Created minimal token data for {target_symbol}")
            
        finally:
            if driver:
                driver.quit()    
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
        """Extract real order book data using correct CSS selectors for both BUY and SELL orders"""
        orderbook_entries = []
        crawled_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            print(f"    🔍 Phase 1: Crawling SELL orders (lệnh bán) ONLY...")
            # Try to click on SELL tab to ensure we're on the right table
            print(f"    🔄 Trying to click on SELL tab...")
            try:
                # Look for SELL tab or button
                sell_tab_selectors = [
                    "button[data-testid='sell-tab']",
                    ".sell-tab",
                    "button:contains('Sell')",
                    "button:contains('Bán')",
                    "[class*='sell'][class*='tab']",
                    "[class*='tab'][class*='sell']"
                ]
                
                sell_tab_clicked = False
                for selector in sell_tab_selectors:
                    try:
                        sell_tab = driver.find_element(By.CSS_SELECTOR, selector)
                        driver.execute_script("arguments[0].click();", sell_tab)
                        time.sleep(2)
                        print(f"    ✅ Clicked SELL tab with selector: {selector}")
                        sell_tab_clicked = True
                        break
                    except:
                        continue
                
                if not sell_tab_clicked:
                    print(f"    ⚠️  Could not find SELL tab, continuing with current state")
                
            except Exception as e:
                print(f"    ⚠️  Could not click SELL tab: {e}")
            
            # Extract SELL orders first (lệnh bán) - button text "Bán"
            sell_entries = self.extract_orders_from_table(driver, symbol, crawled_at, 'SELL')
            orderbook_entries.extend(sell_entries)
            print(f"    ✅ SELL orders: {len(sell_entries)} entries")
            
            print(f"    🔍 Phase 2: Skipping BUY orders for now...")
            # Skip BUY orders for now to test SELL orders only
            print(f"    ⏭️  BUY orders skipped for testing")
            
        except Exception as e:
            print(f"    ❌ Error extracting order book: {str(e)}")
        
        return orderbook_entries
    
    def extract_orders_from_table(self, driver, symbol, crawled_at, order_type):
        """Extract orders from specific table (SELL or BUY)"""
        entries = []
        
        try:
            # Determine table selector based on order type
            if order_type == 'BUY':
                # BUY orders (lệnh mua) - button "Mua" - are in the SELL table (confusing naming)
                table_selector = ".order-book-table_sellTable__Dxd2s"
                price_selector = ".order-book-table_sellPrice__xAuZe"
                button_text = "Mua"
            else:  # SELL
                # SELL orders (lệnh bán) - button "Bán" - are in the BUY table (confusing naming)
                table_selector = ".order-book-table_buyTable__xqBVW"
                price_selector = ".order-book-table_buyPrice__uY0OB"
                button_text = "Bán"
                
            # Wait for table to load
            wait = WebDriverWait(driver, 10)
            
            try:
                orderbook_table = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, table_selector))
                )
                print(f"    ✅ Found {order_type} orders table")
            except TimeoutException:
                print(f"    ⚠️  {order_type} orders table not found")
                return entries
            
            # Extract rows
            rows = orderbook_table.find_elements(By.CSS_SELECTOR, "tr")
            
            if not rows:
                print(f"    ⚠️  No rows found in {order_type} table")
                return entries
            
            print(f"    📊 Found {len(rows)} rows in {order_type} table")
            
            # Parse each row
            valid_entries = 0
            skipped_measurement_rows = 0
            
            for i, row in enumerate(rows):
                try:
                    # Check if this is a measurement row first
                    if self.is_measurement_row(row):
                        skipped_measurement_rows += 1
                        continue
                    
                    # Extract data from each row
                    order_data = self.parse_correct_orderbook_row(row, symbol, crawled_at, order_type, price_selector, button_text)
                    if order_data:
                        entries.append(order_data)
                        valid_entries += 1
                        
                        # Show progress for first few rows
                        if i < 5:
                            print(f"      {order_type} Row {i+1}: {order_data}")
                            
                except Exception as e:
                    print(f"      ❌ Error parsing {order_type} row {i+1}: {e}")
                    continue
            
            print(f"    📊 Successfully parsed {valid_entries}/{len(rows)} {order_type} rows (skipped {skipped_measurement_rows} measurement rows)")
            
            # Handle pagination for this order type
            print(f"    🔄 Checking for {order_type} orders pagination...")
            pagination_entries = self.handle_pagination_for_order_type(driver, symbol, crawled_at, order_type, table_selector, price_selector, button_text)
            entries.extend(pagination_entries)
            
            if pagination_entries:
                print(f"    📊 Found {len(pagination_entries)} additional {order_type} entries from pagination")
            else:
                print(f"    ℹ️  No pagination found for {order_type} orders or only 1 page available")
            
        except Exception as e:
            print(f"    ❌ Error extracting {order_type} orders: {e}")
        
        return entries
    
    def handle_pagination_for_order_type(self, driver, symbol, crawled_at, order_type, table_selector, price_selector, button_text):
        """Handle pagination for specific order type (BUY or SELL)"""
        pagination_entries = []
        
        try:
            # Check if pagination exists - use specific selector based on order type
            if order_type == 'BUY':
                # BUY orders use the first pagination (after sellTable)
                pagination_selectors = [
                    ".order-book-table_sellTable__Dxd2s + .order-book-table_paginationWrapper__O_FJg",
                    ".order-book-table_paginationWrapper__O_FJg:first-of-type",
                    ".order-book-table_paginationWrapper__O_FJg",
                    ".ant-pagination",
                    "[class*='pagination']"
                ]
            else:  # SELL
                # SELL orders use the second pagination (after buyTable)
                pagination_selectors = [
                    ".order-book-table_buyTable__xqBVW + .order-book-table_paginationWrapper__O_FJg",
                    ".order-book-table_paginationWrapper__O_FJg:last-of-type",
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
                print(f"      ℹ️  No pagination found for {order_type} orders")
                return pagination_entries
            
            # For SELL orders, we need to check if we're on the correct tab/section
            if order_type == 'SELL':
                print(f"      🔍 Checking if we're on SELL orders section...")
                # Try to find SELL table first to ensure we're on the right section
                try:
                    sell_table = driver.find_element(By.CSS_SELECTOR, ".order-book-table_sellTable__Dxd2s")
                    print(f"      ✅ Confirmed SELL table is visible")
                except NoSuchElementException:
                    print(f"      ⚠️  SELL table not visible, trying to switch to SELL section...")
                    # Try to click on SELL tab if it exists
                    try:
                        sell_tab = driver.find_element(By.CSS_SELECTOR, "[class*='sell'], [class*='Sell'], [title*='Sell'], [title*='sell']")
                        driver.execute_script("arguments[0].click();", sell_tab)
                        time.sleep(2)
                        print(f"      ✅ Clicked SELL tab")
                    except NoSuchElementException:
                        print(f"      ℹ️  No SELL tab found, continuing with current section")
            
            # Get pagination info
            try:
                page_items = pagination.find_elements(By.CSS_SELECTOR, ".ant-pagination-item")
                if not page_items:
                    print(f"      ℹ️  No page items found for {order_type} orders")
                    return pagination_entries
                
                # Get max page number
                max_page = 1
                for item in page_items:
                    try:
                        page_num = int(item.get_attribute('title'))
                        max_page = max(max_page, page_num)
                    except:
                        continue
                
                print(f"      📄 Found {len(page_items)} pagination pages, max page: {max_page}")
                
                if max_page <= 1:
                    print(f"      ℹ️  Only 1 page for {order_type} orders, no pagination needed")
                    return pagination_entries
                
                # Process additional pages (skip page 1 as it's already processed)
                print(f"      🔄 FULL CRAWL MODE: Processing ALL pages from 2 to {max_page} for {order_type} orders")
                pages_to_process = list(range(2, max_page + 1))
                print(f"      📄 All pages to process: {pages_to_process}")
                
                # Debug: Check current page before starting pagination
                try:
                    current_page = self.get_current_page_number(driver)
                    print(f"      🔍 Current page before pagination: {current_page}")
                except:
                    print(f"      ⚠️  Could not determine current page")
                
                for page_num in pages_to_process:
                    try:
                        print(f"      🔄 Processing {order_type} page {page_num}...")
                        
                        # Find and click page link
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
                                break
                            except NoSuchElementException:
                                continue
                        
                        # If still not found, try to find by text content
                        if not page_link:
                            try:
                                page_links = pagination.find_elements(By.CSS_SELECTOR, ".ant-pagination-item")
                                for link in page_links:
                                    if link.text.strip() == str(page_num):
                                        page_link = link
                                        break
                            except:
                                pass
                        
                        if not page_link:
                            print(f"        ❌ Page {page_num} link not found for {order_type} orders")
                            # For SELL orders, try to scroll to see more pagination
                            if order_type == 'SELL':
                                print(f"        🔄 Trying to scroll to find more pagination for SELL orders...")
                                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                                time.sleep(1)
                                # Try again after scrolling
                                for selector in page_selectors:
                                    try:
                                        page_link = pagination.find_element(By.CSS_SELECTOR, selector)
                                        break
                                    except NoSuchElementException:
                                        continue
                                if not page_link:
                                    print(f"        ❌ Page {page_num} still not found after scrolling")
                                    continue
                            else:
                                continue
                        
                        # Click page link
                        driver.execute_script("arguments[0].click();", page_link)
                        print(f"        Found page link using CSS selector for page {page_num}")
                        print(f"        Successfully clicked page {page_num}")
                        
                        # Wait for data to load with longer timeout
                        time.sleep(5)
                        print(f"        ⏳ Waiting for JavaScript to populate data...")
                        
                        # Scroll to trigger data loading
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)
                        driver.execute_script("window.scrollTo(0, 0);")
                        time.sleep(2)
                        
                        # Additional wait for pagination to update
                        time.sleep(3)
                        
                        # Debug: Check if we're actually on the correct page
                        try:
                            current_page = self.get_current_page_number(driver)
                            print(f"        🔍 After click: Current page is {current_page}")
                            if current_page != page_num:
                                print(f"        ⚠️  Page mismatch! Expected {page_num}, got {current_page}")
                        except:
                            print(f"        ⚠️  Could not determine current page after click")
                        
                        # Check if data loaded
                        try:
                            table = driver.find_element(By.CSS_SELECTOR, table_selector)
                            rows = table.find_elements(By.CSS_SELECTOR, "tr")
                            valid_rows = [row for row in rows if not self.is_measurement_row(row)]
                            
                            if valid_rows:
                                print(f"        ✅ Data loaded: {len(valid_rows)} valid rows found")
                            else:
                                print(f"        ⚠️  No valid data found on page {page_num}")
                                continue
                                
                        except NoSuchElementException:
                            print(f"        ⚠️  Table not found on page {page_num}")
                            continue
                        
                        # Extract data from current page
                        page_entries = []
                        for i, row in enumerate(valid_rows):
                            try:
                                order_data = self.parse_correct_orderbook_row(row, symbol, crawled_at, order_type, price_selector, button_text)
                                if order_data:
                                    page_entries.append(order_data)
                            except Exception as e:
                                print(f"        ❌ Error parsing {order_type} row {i+1} on page {page_num}: {e}")
                                continue
                        
                        # Debug: Show first few entries from this page to check for duplicates
                        if page_entries:
                            print(f"        🔍 Sample data from page {page_num}:")
                            for i, entry in enumerate(page_entries[:3]):  # Show first 3 entries
                                print(f"          Entry {i+1}: {entry['price']} x {entry['quantity']} = {entry['total']}")
                        
                        # Debug: Check which table we're actually reading from
                        try:
                            current_table = driver.find_element(By.CSS_SELECTOR, table_selector)
                            table_class = current_table.get_attribute("class")
                            print(f"        🔍 Table class: {table_class}")
                            
                            # Check if we're reading from the correct table
                            if order_type == 'BUY' and 'sellTable' not in table_class:
                                print(f"        ⚠️  WARNING: Reading from wrong table for BUY orders! (should be sellTable)")
                            elif order_type == 'SELL' and 'buyTable' not in table_class:
                                print(f"        ⚠️  WARNING: Reading from wrong table for SELL orders! (should be buyTable)")
                        except Exception as e:
                            print(f"        ⚠️  Could not check table class: {e}")
                        
                        pagination_entries.extend(page_entries)
                        print(f"      📊 Page {page_num}: {len(page_entries)} {order_type} entries")
                        
                    except Exception as e:
                        print(f"      ❌ Error processing {order_type} page {page_num}: {e}")
                        continue
                
                print(f"      ✅ Completed {order_type} pagination: {len(pagination_entries)} total additional entries from {len(pages_to_process)} pages")
                
            except Exception as e:
                print(f"      ❌ Error handling {order_type} pagination: {e}")
                
        except Exception as e:
            print(f"      ❌ Error in {order_type} pagination handler: {e}")
        
        return pagination_entries
    
    def get_current_page_number(self, driver, order_type='BUY'):
        """Get the current page number from pagination"""
        try:
            # Use specific pagination selector based on order type
            if order_type == 'BUY':
                pagination_selector = ".order-book-table_sellTable__Dxd2s + .order-book-table_paginationWrapper__O_FJg"
            else:  # SELL
                pagination_selector = ".order-book-table_buyTable__xqBVW + .order-book-table_paginationWrapper__O_FJg"
            
            pagination = driver.find_element(By.CSS_SELECTOR, pagination_selector)
            active_item = pagination.find_element(By.CSS_SELECTOR, ".ant-pagination-item-active")
            page_num = int(active_item.get_attribute('title'))
            return page_num
        except:
            return 1
    
    def parse_correct_orderbook_row(self, row_element, symbol, crawled_at, order_type=None, price_selector=None, button_text=None):
        """Parse order book data from a table row using robust CSS selectors with fallbacks"""
        try:
            # Skip Ant Design measurement rows (hidden rows used for table calculations)
            if self.is_measurement_row(row_element):
                print(f"      ⚠️  Skipping measurement row (aria-hidden or ant-table-measure-row)")
                return None
            
            # Extract data using robust CSS selectors with fallbacks
            # Based on the HTML: price is in first td, quantities in second and third td
            
            cells = row_element.find_elements(By.TAG_NAME, 'td')
            if len(cells) < 3:
                print(f"      ⚠️  Row has only {len(cells)} cells, expected at least 3")
                return None
            
            # Extract price from first cell with specific selector for order type
            price = ''
            if price_selector:
                # Use specific price selector for the order type
                price = self.extract_text_with_fallbacks(cells[0], [price_selector], "price")
            
            # Fallback to generic selectors if specific selector fails
            if not price:
                price = self.extract_text_with_fallbacks(cells[0], [
                    # Page 1 structure
                    ".order-book-table_priceContent__NGers .order-book-table_price__Sevu0",
                    ".order-book-table_price__Sevu0",
                    # Page 2+ structure  
                    ".order-book-table_sellPrice__xAuZe",
                    ".order-book-table_buyPrice__uY0OB",
                    # Generic fallbacks
                    "[class*='sellPrice']",
                    "[class*='buyPrice']",
                    "[class*='price']",
                    "span",
                    "div"
                ], "price")
            
            # If price is still empty, try direct text extraction from the cell
            if not price:
                price = cells[0].text.strip()
            
            # Extract first quantity from second cell with fallbacks
            # Handle both page 1 and page 2+ structures
            quantity1 = self.extract_text_with_fallbacks(cells[1], [
                # Page 1 structure
                ".order-book-table_itemH5Center__7tGxv .order-book-table_content__ZSAZ_",
                # Page 2+ structure
                ".order-book-table_itemCenter__gUPZp .order-book-table_content__ZSAZ_",
                # Generic fallbacks
                ".order-book-table_content__ZSAZ_",
                "[class*='content']",
                "[class*='quantity']",
                "span",
                "div"
            ], "quantity1")
            
            # If quantity1 is still empty, try direct text extraction from the cell
            if not quantity1:
                quantity1 = cells[1].text.strip()
            
            # Extract second quantity (total) from third cell with fallbacks
            # Handle both page 1 and page 2+ structures
            quantity2 = self.extract_text_with_fallbacks(cells[2], [
                # Page 1 structure
                ".order-book-table_itemH5Center__7tGxv .order-book-table_content__ZSAZ_",
                # Page 2+ structure
                ".order-book-table_itemCenter__gUPZp .order-book-table_content__ZSAZ_",
                # Generic fallbacks
                ".order-book-table_content__ZSAZ_",
                "[class*='content']",
                "[class*='total']",
                "span",
                "div"
            ], "quantity2")
            
            # If quantity2 is still empty, try direct text extraction from the cell
            if not quantity2:
                quantity2 = cells[2].text.strip()
            
            # Skip rows with empty essential data
            if not price and not quantity1 and not quantity2:
                print(f"      ⚠️  Skipping row with all empty data")
                return None
            
            # Extract order type from button text in the same row
            if button_text:
                # Use provided button text (Mua/Bán)
                order_type = button_text
            else:
                # Fallback: try to find button and extract text directly
                order_type = 'Mua'  # Default fallback
                try:
                    button = row_element.find_element(By.CSS_SELECTOR, ".order-book-table_doBtn__R6taG span")
                    button_text_found = button.text.strip()
                    
                    # Use the actual button text directly (Mua/Bán)
                    order_type = button_text_found
                        
                except NoSuchElementException:
                    # Fallback: try to determine from button text in the row
                    row_text = row_element.text
                    if 'Mua' in row_text:
                        order_type = 'Mua'
                    elif 'Bán' in row_text:
                        order_type = 'Bán'
            
            # Create order entry
            order_entry = {
                'token_symbol': symbol,
                'crawled_at': crawled_at,
                'order_type': order_type,
                'price': price or '',
                'quantity': quantity1 or '',
                'total': quantity2 or ''
            }
            
            return order_entry
            
        except Exception as e:
            print(f"      ❌ Error parsing orderbook row: {e}")
            return None
    
    def extract_text_with_fallbacks(self, cell_element, selectors, field_name):
        """Extract text from cell using multiple fallback selectors"""
        for selector in selectors:
            try:
                element = cell_element.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip()
                if text:  # Only return non-empty text
                    return text
            except NoSuchElementException:
                continue
            except Exception as e:
                print(f"        ⚠️  Error with selector '{selector}' for {field_name}: {e}")
                continue
        
        # If all selectors fail, try to get any text from the cell
        try:
            cell_text = cell_element.text.strip()
            if cell_text:
                return cell_text
        except:
            pass
        
        return ''
    
    def is_measurement_row(self, row_element):
        """Check if this is an Ant Design measurement row that should be skipped"""
        try:
            # Primary check: aria-hidden="true" attribute (most reliable)
            aria_hidden = row_element.get_attribute('aria-hidden')
            if aria_hidden == 'true':
                return True
            
            # Secondary check: ant-table-measure-row class
            class_name = row_element.get_attribute('class') or ''
            if 'ant-table-measure-row' in class_name:
                return True
            
            # Tertiary check: style with height: 0px AND font-size: 0px (measurement rows are typically hidden)
            style = row_element.get_attribute('style') or ''
            if 'height: 0px' in style and 'font-size: 0px' in style:
                return True
            
            # Additional check: if all cells have height: 0px in style AND contain only &nbsp;
            try:
                cells = row_element.find_elements(By.TAG_NAME, 'td')
                if cells and len(cells) >= 3:
                    # Check if first cell has height: 0px
                    first_cell_style = cells[0].get_attribute('style') or ''
                    if 'height: 0px' in first_cell_style or 'height:0px' in first_cell_style:
                        # Double check: all cells should contain only &nbsp; or be empty
                        all_empty_or_nbsp = True
                        for cell in cells[:3]:  # Check first 3 cells
                            cell_text = cell.text.strip()
                            if cell_text and cell_text != '\u00a0':  # \u00a0 is &nbsp;
                                all_empty_or_nbsp = False
                                break
                        if all_empty_or_nbsp:
                            return True
            except:
                pass
            
            return False
            
        except Exception as e:
            # If we can't determine, assume it's not a measurement row
            return False
    
    def handle_pagination(self, driver, symbol, crawled_at):
        """Handle pagination to get ALL order book data from all pages"""
        pagination_entries = []
        
        try:
            # Look for pagination using correct CSS selector from HTML
            pagination_selectors = [
                ".order-book-table_paginationWrapper__O_FJg",
                ".ant-pagination",
                "[class*='pagination']"
            ]
            
            pagination_found = False
            pagination = None
            for selector in pagination_selectors:
                try:
                    pagination = driver.find_element(By.CSS_SELECTOR, selector)
                    pagination_found = True
                    print(f"      ✅ Found pagination with selector: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if pagination_found:
                # Get all pagination links to determine total pages
                page_links = pagination.find_elements(By.CSS_SELECTOR, ".ant-pagination-item a")
                
                # Extract page numbers from the pagination
                # Based on debug results: page numbers are in title attribute, not text
                page_numbers = []
                for link in page_links:
                    try:
                        # First try text
                        page_text = link.text.strip()
                        if page_text.isdigit():
                            page_numbers.append(int(page_text))
                        else:
                            # If text is empty, try title attribute
                            title_text = link.get_attribute('title')
                            if title_text and title_text.isdigit():
                                page_numbers.append(int(title_text))
                    except:
                        continue
                
                # Also try to get page numbers from li elements with title attribute
                if not page_numbers:
                    try:
                        page_items = pagination.find_elements(By.CSS_SELECTOR, ".ant-pagination-item")
                        for item in page_items:
                            try:
                                title_text = item.get_attribute('title')
                                if title_text and title_text.isdigit():
                                    page_numbers.append(int(title_text))
                            except:
                                continue
                    except:
                        pass
                
                # Find the maximum page number
                max_page = max(page_numbers) if page_numbers else 1
                print(f"      📄 Found {len(page_links)} pagination pages, max page: {max_page}")
                print(f"      📄 Page numbers detected: {sorted(page_numbers)}")
                
                # Debug: Check all pagination elements
                print(f"      🔍 Debug: Checking all pagination elements...")
                try:
                    all_pagination_items = pagination.find_elements(By.CSS_SELECTOR, "li")
                    for i, item in enumerate(all_pagination_items):
                        title = item.get_attribute('title') or 'No title'
                        text = item.text.strip()
                        classes = item.get_attribute('class') or 'No class'
                        print(f"        Item {i+1}: title='{title}', text='{text}', class='{classes}'")
                    
                    # Check if there's a "Next" button or "..." button to see more pages
                    next_buttons = pagination.find_elements(By.CSS_SELECTOR, "li[title='Next Page'], li[title='Next 5 Pages']")
                    if next_buttons:
                        print(f"        🔍 Found {len(next_buttons)} next buttons - there might be more pages!")
                        for btn in next_buttons:
                            print(f"          - {btn.get_attribute('title')}")
                            
                except Exception as e:
                    print(f"        ❌ Error checking pagination items: {e}")
                
                # Try to find the actual last page by clicking "Next Page" repeatedly
                print(f"      🔍 Finding actual last page by clicking 'Next Page' repeatedly...")
                try:
                    # Click "Next Page" until we can't click anymore
                    max_attempts = 10
                    for attempt in range(max_attempts):
                        next_page_btn = pagination.find_element(By.CSS_SELECTOR, "li[title='Next Page']")
                        if next_page_btn and next_page_btn.is_enabled() and "disabled" not in next_page_btn.get_attribute('class'):
                            print(f"        🔄 Attempt {attempt + 1}: Clicking 'Next Page'...")
                            next_page_btn.click()
                            time.sleep(2)
                            
                            # Check pagination again after clicking
                            pagination = driver.find_element(By.CSS_SELECTOR, ".order-book-table_paginationWrapper__O_FJg")
                            page_links = pagination.find_elements(By.CSS_SELECTOR, "li[title]")
                            page_numbers = []
                            for link in page_links:
                                try:
                                    page_num = int(link.get_attribute('title'))
                                    if page_num > 0:
                                        page_numbers.append(page_num)
                                except:
                                    continue
                            
                            current_max_page = max(page_numbers) if page_numbers else max_page
                            print(f"        📄 After click {attempt + 1}: max page is now {current_max_page}")
                            
                            # Update max_page if we found a higher page
                            if current_max_page > max_page:
                                max_page = current_max_page
                        else:
                            print(f"        ✅ 'Next Page' button is now disabled - reached last page")
                            break
                    
                    print(f"        📄 Final max page found: {max_page}")
                    print(f"        📄 All page numbers: {sorted(page_numbers)}")
                        
                except Exception as e:
                    print(f"        ❌ Error finding last page: {e}")
                    print(f"        📄 Using detected max page: {max_page}")
                
                # Process ALL pages from 2 to max_page (page 1 is already processed)
                # Crawl every single page, not just visible ones
                all_pages = list(range(2, max_page + 1))  # Skip page 1 (already processed)
                print(f"      🔄 FULL CRAWL MODE: Processing ALL pages from 2 to {max_page}")
                print(f"      📄 All pages to process: {all_pages}")
                
                for page_num in all_pages:
                    try:
                        print(f"      🔄 Processing page {page_num}...")
                        
                        # Click on page number - try different approaches
                        page_link = None
                        
                        # Approach 1: Try CSS selector with page number class
                        try:
                            page_link = pagination.find_element(By.CSS_SELECTOR, f".ant-pagination-item-{page_num} a")
                            print(f"        Found page link using CSS selector for page {page_num}")
                        except NoSuchElementException:
                            # Approach 2: Try finding by title attribute
                            try:
                                page_items = pagination.find_elements(By.CSS_SELECTOR, ".ant-pagination-item")
                                for item in page_items:
                                    title = item.get_attribute('title')
                                    if title == str(page_num):
                                        page_link = item.find_element(By.TAG_NAME, 'a')
                                        print(f"        Found page link using title attribute for page {page_num}")
                                        break
                            except:
                                pass
                        
                        # Approach 3: Try finding by index (if we know the order)
                        if not page_link and page_num <= 6:  # Based on debug showing 6 links
                            try:
                                page_links = pagination.find_elements(By.CSS_SELECTOR, ".ant-pagination-item a")
                                if page_num - 1 < len(page_links):  # page_num is 1-indexed, array is 0-indexed
                                    page_link = page_links[page_num - 1]
                                    print(f"        Found page link using index for page {page_num}")
                            except:
                                pass
                        
                        if page_link:
                            # Scroll to the link and click
                            driver.execute_script("arguments[0].scrollIntoView(true);", page_link)
                            time.sleep(0.5)
                            
                            # Use JavaScript click to avoid element interception issues
                            driver.execute_script("arguments[0].click();", page_link)
                            print(f"        Successfully clicked page {page_num}")
                        else:
                            # If can't find direct page link, try using "Next Page" navigation
                            print(f"        🔄 Page {page_num} not visible, trying Next Page navigation...")
                            current_page = self.get_current_page_number(driver)
                            
                            if current_page < page_num:
                                # Navigate forward using Next Page
                                while current_page < page_num:
                                    try:
                                        next_button = pagination.find_element(By.CSS_SELECTOR, ".ant-pagination-next:not(.ant-pagination-disabled)")
                                        driver.execute_script("arguments[0].click();", next_button)
                                        time.sleep(2)
                                        current_page = self.get_current_page_number(driver)
                                        print(f"        📄 Now at page {current_page}")
                                        
                                        if current_page == page_num:
                                            print(f"        ✅ Successfully navigated to page {page_num}")
                                            break
                                    except Exception as e:
                                        print(f"        ❌ Error navigating to page {page_num}: {e}")
                                        break
                            else:
                                print(f"        ❌ Could not navigate to page {page_num}, skipping...")
                                continue
                        
                        # Wait for page to load and data to update
                        time.sleep(3)  # Initial wait for page transition
                        
                        # Additional wait for JavaScript to populate data
                        # Sometimes the table structure loads but data is populated later by JS
                        print(f"        ⏳ Waiting for JavaScript to populate data...")
                        time.sleep(2)
                        
                        # Try scrolling to trigger lazy loading
                        print(f"        🔄 Scrolling to trigger data loading...")
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(1)
                        driver.execute_script("window.scrollTo(0, 0);")
                        time.sleep(1)
                        
                        # Wait for table to be visible and populated
                        try:
                            wait = WebDriverWait(driver, 15)
                            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody")))
                            
                            # Wait for actual data to be loaded (not just empty cells)
                            # Check if we have valid data in the first few rows
                            max_retries = 20
                            for retry in range(max_retries):
                                try:
                                    # Find the table and check for valid data
                                    orderbook_table = driver.find_element(By.CSS_SELECTOR, "tbody.ant-table-tbody")
                                    rows = orderbook_table.find_elements(By.CSS_SELECTOR, "tr")
                                    
                                    # Count rows with actual data (not measurement rows)
                                    valid_rows = 0
                                    for row in rows:
                                        if not self.is_measurement_row(row):
                                            cells = row.find_elements(By.TAG_NAME, 'td')
                                            if len(cells) >= 3:
                                                # Check if cells have content using improved logic
                                                has_content = False
                                                for i, cell in enumerate(cells[:3]):
                                                    # Try direct text extraction first (simpler and more reliable)
                                                    cell_text = cell.text.strip()
                                                    if cell_text:
                                                        has_content = True
                                                        break
                                                    
                                                    # If direct text fails, try CSS selectors
                                                    cell_text = self.extract_text_with_fallbacks(cell, [
                                                        ".order-book-table_priceContent__NGers .order-book-table_price__Sevu0",
                                                        ".order-book-table_price__Sevu0",
                                                        ".order-book-table_sellPrice__xAuZe",
                                                        ".order-book-table_itemH5Center__7tGxv .order-book-table_content__ZSAZ_",
                                                        ".order-book-table_itemCenter__gUPZp .order-book-table_content__ZSAZ_",
                                                        ".order-book-table_content__ZSAZ_",
                                                        "span",
                                                        "div"
                                                    ], f"cell_{i}")
                                                    if cell_text and cell_text.strip():
                                                        has_content = True
                                                        break
                                                if has_content:
                                                    valid_rows += 1
                                    
                                    # If we have at least 3 valid rows, data is loaded
                                    if valid_rows >= 3:
                                        print(f"        ✅ Data loaded: {valid_rows} valid rows found")
                                        break
                                    else:
                                        print(f"        ⏳ Waiting for data... ({valid_rows} valid rows, retry {retry+1}/{max_retries})")
                                        time.sleep(1)  # Wait 1 second before retry
                                        
                                except Exception as e:
                                    print(f"        ⚠️  Error checking data: {e}")
                                    time.sleep(1)
                            
                        except TimeoutException:
                            print(f"        ⚠️  Timeout waiting for table to load on page {page_num}")
                        
                        # Debug: Check if there's actually data on this page
                        print(f"        🔍 Debug: Checking page {page_num} content...")
                        try:
                            orderbook_table = driver.find_element(By.CSS_SELECTOR, "tbody.ant-table-tbody")
                            rows = orderbook_table.find_elements(By.CSS_SELECTOR, "tr")
                            print(f"        📊 Found {len(rows)} total rows on page {page_num}")
                            
                            # Check first few rows for content
                            for i, row in enumerate(rows[:5]):
                                if not self.is_measurement_row(row):
                                    cells = row.find_elements(By.TAG_NAME, 'td')
                                    if len(cells) >= 3:
                                        cell_texts = [cell.text.strip() for cell in cells[:3]]
                                        print(f"          Row {i+1}: {cell_texts}")
                        except Exception as e:
                            print(f"        ❌ Debug error: {e}")
                        
                        # Extract data from current page
                        current_page_entries = self.extract_current_page_orders(driver, symbol, crawled_at)
                        pagination_entries.extend(current_page_entries)
                        
                        print(f"      📊 Page {page_num}: {len(current_page_entries)} entries")
                        
                        # Add small delay between pages to avoid overwhelming the server
                        time.sleep(1)
                        
                    except Exception as e:
                        print(f"      ❌ Error processing page {page_num}: {e}")
                        continue
                        
                print(f"      ✅ Completed pagination: {len(pagination_entries)} total additional entries from {max_page-1} pages")
            else:
                print(f"      ⚠️  No pagination found")
                
        except Exception as e:
            print(f"      ❌ Error handling pagination: {e}")
        
        return pagination_entries
    
    def extract_current_page_orders(self, driver, symbol, crawled_at):
        """Extract order book data from current page with robust error handling"""
        page_entries = []
        
        try:
            # Find order book table on current page with fallback selectors
            orderbook_table = None
            table_selectors = [
                "tbody.ant-table-tbody",
                "tbody",
                ".ant-table-tbody",
                "table tbody"
            ]
            
            for selector in table_selectors:
                try:
                    orderbook_table = driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"        ✅ Found table with selector: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not orderbook_table:
                print(f"        ❌ Could not find order book table on current page")
                return page_entries
            
            # Find rows with fallback selectors - include ALL tr elements to catch measurement rows
            rows = []
            row_selectors = [
                "tr",  # Get ALL tr elements first, then filter
                "tr.ant-table-row",
                ".ant-table-row"
            ]
            
            for selector in row_selectors:
                try:
                    rows = orderbook_table.find_elements(By.CSS_SELECTOR, selector)
                    if rows:
                        print(f"        ✅ Found {len(rows)} rows with selector: {selector}")
                        break
                except:
                    continue
            
            if not rows:
                print(f"        ⚠️  No rows found on current page")
                return page_entries
            
            # Parse each row with improved error handling
            valid_entries = 0
            skipped_measurement_rows = 0
            for i, row in enumerate(rows):
                try:
                    # Check if this is a measurement row first
                    if self.is_measurement_row(row):
                        skipped_measurement_rows += 1
                        continue
                    
                    # Debug: Print row structure for first few rows
                    if i < 3:
                        cells = row.find_elements(By.TAG_NAME, 'td')
                        print(f"        🔍 Debug row {i+1}: {len(cells)} cells")
                        for j, cell in enumerate(cells[:3]):
                            cell_text = cell.text.strip()
                            cell_html = cell.get_attribute('outerHTML')[:100] + "..." if len(cell.get_attribute('outerHTML')) > 100 else cell.get_attribute('outerHTML')
                            print(f"          Cell {j+1}: '{cell_text}' | HTML: {cell_html}")
                    
                    order_data = self.parse_correct_orderbook_row(row, symbol, crawled_at)
                    if order_data:
                        page_entries.append(order_data)
                        valid_entries += 1
                        if i < 3:  # Show first few successful extractions
                            print(f"        ✅ Row {i+1} extracted: {order_data}")
                    else:
                        print(f"        ⚠️  Row {i+1} returned empty data")
                        # Debug: Show why it failed
                        if i < 3:
                            cells = row.find_elements(By.TAG_NAME, 'td')
                            for j, cell in enumerate(cells[:3]):
                                cell_text = cell.text.strip()
                                print(f"          Cell {j+1} text: '{cell_text}'")
                except Exception as e:
                    print(f"        ❌ Error parsing row {i+1}: {e}")
                    continue
            
            print(f"        📊 Successfully parsed {valid_entries}/{len(rows)} rows (skipped {skipped_measurement_rows} measurement rows)")
                    
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
            
            # Extract latest price using improved CSS selectors
            try:
                price_element = element.find_element(By.CSS_SELECTOR, ".pre-market-statistic_preMarketStatistic__e2_sE .contentValue")
                if price_element:
                    token_data['latest_price'] = price_element.text.strip()
            except:
                # Fallback to regex
                price_pattern = r'Giá giao dịch mới nhất\s*([\d,]+\.?\d*)'
                price_match = re.search(price_pattern, item_text)
                if price_match:
                    token_data['latest_price'] = price_match.group(1)
            
            # Extract percentage change using improved CSS selectors
            try:
                change_element = element.find_element(By.CSS_SELECTOR, ".trade-list-item_pricePercent__b8g0H")
                if change_element:
                    token_data['price_change_percent'] = change_element.text.strip()
            except:
                # Fallback to regex
                change_pattern = r'([+-]?\d+\.?\d*%)'
                change_match = re.search(change_pattern, item_text)
                if change_match:
                    token_data['price_change_percent'] = change_match.group(1)
            
            # Extract volume 24h using improved CSS selectors
            try:
                volume_elements = element.find_elements(By.CSS_SELECTOR, ".pre-market-statistic_preMarketStatistic__e2_sE .contentValue")
                if len(volume_elements) >= 2:
                    token_data['volume_24h'] = volume_elements[1].text.strip()
            except:
                # Fallback to regex
                volume_24h_pattern = r'Khối lượng 24 giờ\s*([\d,]+\.?\d*[KMB]?)'
                volume_24h_match = re.search(volume_24h_pattern, item_text)
                if volume_24h_match:
                    token_data['volume_24h'] = volume_24h_match.group(1)
            
            # Extract total volume using improved CSS selectors
            try:
                volume_elements = element.find_elements(By.CSS_SELECTOR, ".pre-market-statistic_preMarketStatistic__e2_sE .contentValue")
                if len(volume_elements) >= 3:
                    token_data['total_volume'] = volume_elements[2].text.strip()
            except:
                # Fallback to regex
                total_volume_pattern = r'Tổng khối lượng\s*([\d,]+\.?\d*[KMB]?)'
                total_volume_match = re.search(total_volume_pattern, item_text)
                if total_volume_match:
                    token_data['total_volume'] = total_volume_match.group(1)
            
            # Extract start time using improved CSS selectors
            try:
                time_element = element.find_element(By.CSS_SELECTOR, ".trade-list-item_tradeTimeWrapper__8WVpM span[dir='ltr']")
                if time_element:
                    token_data['start_time'] = time_element.text.strip()
            except:
                # Fallback to regex
                time_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
                time_match = re.search(time_pattern, item_text)
                if time_match:
                    token_data['start_time'] = time_match.group(1)
            
            # Extract end time/status using improved CSS selectors
            try:
                status_element = element.find_element(By.CSS_SELECTOR, ".trade-list-item_tradeLabel__GK3Ih")
                if status_element:
                    token_data['end_time'] = status_element.text.strip()
            except:
                # Fallback to regex
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


def main(target_symbol=None):
    """Main function
    
    Args:
        target_symbol (str, optional): If specified, only crawl this specific symbol.
                                     If None, crawl all tokens from pre-market.
    """
    print("🚀 MEXC Correct Order Book Crawler")
    print("Uses correct URL pattern and CSS selectors from real HTML")
    print("=" * 60)
    
    crawler = MexcCorrectOrderBookCrawler()
    
    # Run the correct order book crawler
    tokens_data, orderbook_data = crawler.crawl_all_data(target_symbol=target_symbol)
    
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


def main_mento_only():
    """Main function to crawl only MENTO token for testing"""
    print("🚀 MEXC MENTO Only Crawler (Full Pagination Test)")
    print("Target: MENTO token with ALL pagination pages")
    print("=" * 60)
    
    main(target_symbol="MENTO")


if __name__ == "__main__":
    import sys
    
    # Check if MENTO-only mode is requested
    if len(sys.argv) > 1 and sys.argv[1].upper() == "MENTO":
        main_mento_only()
    else:
        main()


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
import psycopg2
from psycopg2.extras import RealDictCursor
from config import DATABASE_CONFIG
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue


class MexcPreMarketCrawler:
    def __init__(self, db_config=None):
        self.session = requests.Session()
        self.db_config = db_config or {
            'host': 'localhost',
            'database': 'crawl_mexc',
            'user': 'postgres',
            'password': 'password',
            'port': '5432'
        }
        self.conn = None
        self.driver_pool = Queue()
        self.driver_pool_size = 1  # Chỉ 1 driver để tránh connection issues
        self.driver_lock = threading.Lock()
    
    
    def create_driver(self):
        """Tạo Chrome driver tối ưu - giảm delay và cảnh báo"""
        chrome_options = Options()
        
        # Basic headless settings
        chrome_options.add_argument('--headless=new')  # Sử dụng headless mới
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # GPU và rendering optimization
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-gpu-sandbox')
        chrome_options.add_argument('--disable-gpu-process-crash-limit')
        chrome_options.add_argument('--disable-gpu-memory-buffer-video-frames')
        chrome_options.add_argument('--disable-gpu-rasterization')
        chrome_options.add_argument('--disable-gpu-compositing')
        chrome_options.add_argument('--disable-3d-apis')
        chrome_options.add_argument('--disable-webgl')
        chrome_options.add_argument('--disable-webgl2')
        chrome_options.add_argument('--disable-accelerated-2d-canvas')
        chrome_options.add_argument('--disable-accelerated-jpeg-decoding')
        chrome_options.add_argument('--disable-accelerated-mjpeg-decode')
        chrome_options.add_argument('--disable-accelerated-video-decode')
        chrome_options.add_argument('--disable-accelerated-video-encode')
        
        # Performance optimization
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-features=BlinkGenPropertyTrees')
        chrome_options.add_argument('--disable-features=EnableDrDc')
        
        # Memory và resource optimization
        chrome_options.add_argument('--memory-pressure-off')
        chrome_options.add_argument('--max_old_space_size=4096')
        chrome_options.add_argument('--disable-background-mode')
        chrome_options.add_argument('--disable-component-extensions-with-background-pages')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--disable-translate')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        
        # Network optimization
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--aggressive-cache-discard')
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-background-timer-throttling')
        
        # Logging và debugging
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--silent')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--disable-permissions-api')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-popup-blocking')
        
        # Window settings
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Anti-detection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Disable DevTools
        chrome_options.add_argument('--disable-dev-tools')
        chrome_options.add_argument('--disable-devtools')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--no-default-browser-check')
        chrome_options.add_argument('--disable-default-apps')
        
        # Disable hardware acceleration completely
        chrome_options.add_argument('--disable-accelerated-2d-canvas')
        chrome_options.add_argument('--disable-accelerated-video')
        chrome_options.add_argument('--disable-accelerated-mjpeg-decode')
        chrome_options.add_argument('--disable-accelerated-video-decode')
        chrome_options.add_argument('--disable-accelerated-video-encode')
        
        # Disable WebRTC
        chrome_options.add_argument('--disable-webrtc')
        chrome_options.add_argument('--disable-webrtc-hw-decoding')
        chrome_options.add_argument('--disable-webrtc-hw-encoding')
        
        # Disable media
        chrome_options.add_argument('--disable-audio-output')
        chrome_options.add_argument('--disable-audio-input')
        chrome_options.add_argument('--mute-audio')
        
        # Additional performance flags
        chrome_options.add_argument('--disable-hang-monitor')
        chrome_options.add_argument('--disable-prompt-on-repost')
        chrome_options.add_argument('--disable-domain-reliability')
        chrome_options.add_argument('--disable-client-side-phishing-detection')
        chrome_options.add_argument('--disable-component-update')
        chrome_options.add_argument('--disable-background-downloads')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    
    def get_driver(self):
        """Lấy driver từ pool hoặc tạo mới"""
        with self.driver_lock:
            if not self.driver_pool.empty():
                return self.driver_pool.get()
            else:
                return self.create_driver()
    
    def return_driver(self, driver):
        """Trả driver về pool"""
        if driver:
            try:
                # Clear cookies và cache để tránh conflict
                driver.delete_all_cookies()
                driver.execute_script("window.localStorage.clear();")
                driver.execute_script("window.sessionStorage.clear();")
                
                with self.driver_lock:
                    if self.driver_pool.qsize() < self.driver_pool_size:
                        self.driver_pool.put(driver)
                    else:
                        driver.quit()
            except:
                try:
                    driver.quit()
                except:
                    pass
    
    def cleanup_driver_pool(self):
        """Dọn dẹp tất cả driver trong pool"""
        with self.driver_lock:
            while not self.driver_pool.empty():
                try:
                    driver = self.driver_pool.get()
                    driver.quit()
                except:
                    pass
    
    def connect_database(self):
        """Kết nối đến PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            print(f"✅ Connected to PostgreSQL database: {self.db_config['database']}")
            return True
        except psycopg2.Error as e:
            print(f"❌ Error connecting to database: {e}")
            return False
    
    def close_database(self):
        """Đóng kết nối database và cleanup driver pool"""
        if self.conn:
            self.conn.close()
            print("✅ Database connection closed")
        
        # Cleanup driver pool
        self.cleanup_driver_pool()
        print("✅ Driver pool cleaned up")
    
    def create_tables(self):
        """Tạo tables nếu chưa tồn tại"""
        if not self.conn:
            print("❌ No database connection")
            return False
        
        try:
            cursor = self.conn.cursor()
            
            # Tạo table tokens
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tokens (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20),
                    name VARCHAR(100),
                    latest_price DECIMAL(18,8),
                    price_change_percent DECIMAL(8,2),
                    volume_24h DECIMAL(18,2),
                    total_volume DECIMAL(18,2),
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Tạo table order_books
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_books (
                    id SERIAL PRIMARY KEY,
                    token_id INT REFERENCES tokens(id) ON DELETE CASCADE,
                    order_type VARCHAR(10),
                    price DECIMAL(18,8),
                    quantity DECIMAL(18,8),
                    total DECIMAL(18,8),
                    crawled_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            self.conn.commit()
            cursor.close()
            print("✅ Database tables created/verified successfully")
            return True
            
        except psycopg2.Error as e:
            print(f"❌ Error creating tables: {e}")
            self.conn.rollback()
            return False
    
    def insert_token(self, token_data):
        """Upsert token vào database (insert or update)"""
        if not self.conn:
            return None
        
        try:
            cursor = self.conn.cursor()
            
            # Check if token already exists by symbol
            cursor.execute("SELECT id FROM tokens WHERE symbol = %s", (token_data['symbol'],))
            existing_token = cursor.fetchone()
            
            if existing_token:
                # Update existing token
                token_id = existing_token[0]
                cursor.execute("""
                    UPDATE tokens SET 
                        name = %s,
                        latest_price = %s,
                        price_change_percent = %s,
                        volume_24h = %s,
                        total_volume = %s,
                        start_time = %s,
                        end_time = %s,
                        created_at = %s
                    WHERE id = %s
                """, (
                    token_data['name'],
                    token_data['latest_price'],
                    token_data['price_change_percent'],
                    token_data['volume_24h'],
                    token_data['total_volume'],
                    token_data['start_time'],
                    token_data['end_time'],
                    token_data['created_at'],
                    token_id
                ))
                print(f"✅ Token {token_data['symbol']} updated with ID: {token_id}")
            else:
                # Insert new token
                cursor.execute("""
                    INSERT INTO tokens (symbol, name, latest_price, price_change_percent, 
                                      volume_24h, total_volume, start_time, end_time, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    token_data['symbol'],
                    token_data['name'],
                    token_data['latest_price'],
                    token_data['price_change_percent'],
                    token_data['volume_24h'],
                    token_data['total_volume'],
                    token_data['start_time'],
                    token_data['end_time'],
                    token_data['created_at']
                ))
                token_id = cursor.fetchone()[0]
                print(f"✅ Token {token_data['symbol']} inserted with ID: {token_id}")
            
            self.conn.commit()
            cursor.close()
            return token_id
            
        except psycopg2.Error as e:
            print(f"❌ Error upserting token: {e}")
            self.conn.rollback()
            return None
    
    def cleanup_old_tokens(self, current_symbols):
        """Xóa các tokens không còn trong danh sách hiện tại"""
        if not self.conn or not current_symbols:
            return False
        
        try:
            cursor = self.conn.cursor()
            
            
            # Convert list to tuple for SQL IN clause
            symbols_tuple = tuple(current_symbols)
            
            # Delete tokens that are not in current crawl (including NULL symbols)
            cursor.execute("""
                DELETE FROM tokens 
                WHERE symbol IS NULL OR symbol NOT IN %s
            """, (symbols_tuple,))
            
            deleted_count = cursor.rowcount
            if deleted_count > 0:
                print(f"🗑️ Deleted {deleted_count} old tokens not in current crawl")
            else:
                print("ℹ️ No old tokens to delete")
            
            self.conn.commit()
            cursor.close()
            return True
            
        except psycopg2.Error as e:
            print(f"❌ Error cleaning up old tokens: {e}")
            self.conn.rollback()
            return False
    
    def insert_order_books(self, token_id, order_books):
        """Thêm order books vào database"""
        if not self.conn or not order_books:
            return False
        
        try:
            cursor = self.conn.cursor()
            
            # Prepare data for batch insert
            order_data = []
            for order in order_books:
                order_data.append((
                    token_id,
                    order['order_type'],
                    order['price'],
                    order['quantity'],
                    order['total']
                ))
            
            # Batch insert
            cursor.executemany("""
                INSERT INTO order_books (token_id, order_type, price, quantity, total)
                VALUES (%s, %s, %s, %s, %s)
            """, order_data)
            
            self.conn.commit()
            cursor.close()
            print(f"✅ Inserted {len(order_books)} order book entries")
            return True
            
        except psycopg2.Error as e:
            print(f"❌ Error inserting order books: {e}")
            self.conn.rollback()
            return False
    
    def setup_session(self):
        """Setup session headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
        })
        self.tokens_data = []
        self.orderbook_data = []
        
    def crawl_premarket_data(self):
        """Crawl all pre-market token data and order books"""
        print("🚀 MEXC Pre-Market Token Crawler")
        print("=" * 70)
        print("📊 Target: All pre-market tokens")
        print("📊 Phase 1: Getting all token data from pre-market")
        print("📊 Phase 2: Crawling order books")
        print("📊 Phase 3: Saving to PostgreSQL database")
        print("=" * 70)
        
        # Connect to database
        if not self.connect_database():
            print("❌ Failed to connect to database. Exiting...")
            return None, None
        
        # Create tables if not exist
        if not self.create_tables():
            print("❌ Failed to create tables. Exiting...")
            self.close_database()
            return None, None
        
        try:
            # Phase 1: Get all token data from pre-market page
            phase1_start = time.time()
            phase1_start_time = datetime.now().strftime("%H:%M:%S")
            print(f"🕐 Phase 1 start: {phase1_start_time}")
            self.crawl_all_tokens_data()
            phase1_time = time.time() - phase1_start
            phase1_end_time = datetime.now().strftime("%H:%M:%S")
            print(f"✅ Phase 1 completed! ({phase1_time:.1f}s) - {phase1_start_time} to {phase1_end_time}")
            
            # Phase 2: Crawl order books for each token
            if self.tokens_data:
                phase2_start = time.time()
                phase2_start_time = datetime.now().strftime("%H:%M:%S")
                print(f"\n🔄 Phase 2: Crawling order books for {len(self.tokens_data)} tokens...")
                print(f"🕐 Phase 2 start: {phase2_start_time}")
                self.crawl_all_orderbooks()
                phase2_time = time.time() - phase2_start
                phase2_end_time = datetime.now().strftime("%H:%M:%S")
                print(f"✅ Phase 2 completed! ({phase2_time:.1f}s) - {phase2_start_time} to {phase2_end_time}")
            
            # Phase 3: Save to database
            if self.tokens_data:
                phase3_start = time.time()
                phase3_start_time = datetime.now().strftime("%H:%M:%S")
                print(f"\n💾 Phase 3: Saving to PostgreSQL database...")
                print(f"🕐 Phase 3 start: {phase3_start_time}")
                
                total_order_entries = 0
                # Insert/Update token data and their order books
                for token in self.tokens_data:
                    token_id = self.insert_token(token)
                    if token_id and token['symbol'] in self.orderbook_data:
                        # Insert order book data for this specific token
                        token_orders = self.orderbook_data[token['symbol']]
                        self.insert_order_books(token_id, token_orders)
                        total_order_entries += len(token_orders)
                
                # Clean up old tokens not in current crawl
                current_symbols = [token['symbol'] for token in self.tokens_data if token.get('symbol')]
                self.cleanup_old_tokens(current_symbols)
                
                phase3_time = time.time() - phase3_start
                phase3_end_time = datetime.now().strftime("%H:%M:%S")
                print(f"✅ Phase 3 completed! ({phase3_time:.1f}s) - {phase3_start_time} to {phase3_end_time}")
            
            print(f"\n🎯 PRE-MARKET CRAWLING COMPLETED!")
            print(f"   • Tokens extracted: {len(self.tokens_data)}")
            print(f"   • Total order book entries: {total_order_entries}")
            
            return self.tokens_data, self.orderbook_data
            
        finally:
            # Always close database connection
            self.close_database()
    
    def crawl_all_tokens_data(self):
        """Crawl all token data from pre-market page"""
        print(f"\n📋 Phase 1: Getting all token data from pre-market...")
        
        # Set up Chrome driver - sử dụng cùng cấu hình tối ưu
        chrome_options = Options()
        
        # Basic headless settings
        chrome_options.add_argument('--headless=new')  # Sử dụng headless mới
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # GPU và rendering optimization
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-gpu-sandbox')
        chrome_options.add_argument('--disable-gpu-process-crash-limit')
        chrome_options.add_argument('--disable-gpu-memory-buffer-video-frames')
        chrome_options.add_argument('--disable-gpu-rasterization')
        chrome_options.add_argument('--disable-gpu-compositing')
        chrome_options.add_argument('--disable-3d-apis')
        chrome_options.add_argument('--disable-webgl')
        chrome_options.add_argument('--disable-webgl2')
        chrome_options.add_argument('--disable-accelerated-2d-canvas')
        chrome_options.add_argument('--disable-accelerated-jpeg-decoding')
        chrome_options.add_argument('--disable-accelerated-mjpeg-decode')
        chrome_options.add_argument('--disable-accelerated-video-decode')
        chrome_options.add_argument('--disable-accelerated-video-encode')
        
        # Performance optimization
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-features=BlinkGenPropertyTrees')
        chrome_options.add_argument('--disable-features=EnableDrDc')
        
        # Memory và resource optimization
        chrome_options.add_argument('--memory-pressure-off')
        chrome_options.add_argument('--max_old_space_size=4096')
        chrome_options.add_argument('--disable-background-mode')
        chrome_options.add_argument('--disable-component-extensions-with-background-pages')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--disable-translate')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        
        # Network optimization
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--aggressive-cache-discard')
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-background-timer-throttling')
        
        # Logging và debugging
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--silent')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--disable-permissions-api')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-popup-blocking')
        
        # Window settings
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Anti-detection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Disable DevTools
        chrome_options.add_argument('--disable-dev-tools')
        chrome_options.add_argument('--disable-devtools')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--no-default-browser-check')
        chrome_options.add_argument('--disable-default-apps')
        
        # Disable hardware acceleration completely
        chrome_options.add_argument('--disable-accelerated-2d-canvas')
        chrome_options.add_argument('--disable-accelerated-video')
        chrome_options.add_argument('--disable-accelerated-mjpeg-decode')
        chrome_options.add_argument('--disable-accelerated-video-decode')
        chrome_options.add_argument('--disable-accelerated-video-encode')
        
        # Disable WebRTC
        chrome_options.add_argument('--disable-webrtc')
        chrome_options.add_argument('--disable-webrtc-hw-decoding')
        chrome_options.add_argument('--disable-webrtc-hw-encoding')
        
        # Disable media
        chrome_options.add_argument('--disable-audio-output')
        chrome_options.add_argument('--disable-audio-input')
        chrome_options.add_argument('--mute-audio')
        
        # Additional performance flags
        chrome_options.add_argument('--disable-hang-monitor')
        chrome_options.add_argument('--disable-prompt-on-repost')
        chrome_options.add_argument('--disable-domain-reliability')
        chrome_options.add_argument('--disable-client-side-phishing-detection')
        chrome_options.add_argument('--disable-component-update')
        chrome_options.add_argument('--disable-background-downloads')
        
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
                
                # Smart wait for token list to be populated instead of fixed sleep
                print("⏳ Waiting for token list to load...")
                token_list = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ul.ant-list-items"))
                )
                
                # Wait for actual token items to be present
                wait.until(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "ul.ant-list-items li")) > 0)
                
                if token_list:
                    print("✅ Found token list, processing all tokens...")
                    token_items = token_list.find_elements(By.TAG_NAME, "li")
                    
                    print(f"📊 Found {len(token_items)} token items")
                    
                    for i, item in enumerate(token_items):
                        try:
                            # Extract token data for all tokens
                            token_data = self.extract_token_data(item)
                            if token_data:
                                self.tokens_data.append(token_data)
                                symbol = token_data.get('symbol', '')
                                print(f"✅ Token {i+1}: {symbol} extracted")
                            
                        except Exception as e:
                            print(f"❌ Error processing token {i+1}: {e}")
                            continue
                    
                    print(f"✅ Successfully extracted {len(self.tokens_data)} tokens")
                
            except TimeoutException:
                print("⚠️ Timeout waiting for token list. No tokens extracted.")
                
        except Exception as e:
            print(f"❌ Error in token data crawling: {e}")
            
        finally:
            if driver:
                driver.quit()
    
    def crawl_all_orderbooks(self):
        """Crawl order books for all tokens using parallel processing"""
        # Initialize orderbook_data as dictionary to store orders by token symbol
        self.orderbook_data = {}
        
        # Filter tokens with valid symbols
        valid_tokens = [token for token in self.tokens_data if token.get('symbol', '')]
        
        if not valid_tokens:
            print("⚠️ No valid tokens to process")
            return
        
        print(f"🚀 Starting parallel order book crawling for {len(valid_tokens)} tokens...")
        
        # Use ThreadPoolExecutor for parallel processing
        max_workers = 1  # Chỉ 1 worker để tránh connection issues  # Tối đa 3 threads để tránh quá tải
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_symbol = {
                executor.submit(self.crawl_token_orderbook_optimized, token): token.get('symbol', '')
                for token in valid_tokens
            }
            
            # Process completed tasks
            completed = 0
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                completed += 1
                token_start_time = time.time()
                
                try:
                    token_orders = future.result()
                    token_time = time.time() - token_start_time
                    if token_orders:
                        self.orderbook_data[symbol] = token_orders
                        print(f"✅ [{completed}/{len(valid_tokens)}] {symbol}: {len(token_orders)} order entries ({token_time:.1f}s)")
                    else:
                        print(f"⚠️ [{completed}/{len(valid_tokens)}] {symbol}: No order book data found ({token_time:.1f}s)")
                except Exception as e:
                    token_time = time.time() - token_start_time
                    print(f"❌ [{completed}/{len(valid_tokens)}] {symbol}: Error - {e} ({token_time:.1f}s)")
                
                # Add delay between requests to avoid overwhelming the server
                time.sleep(1)
        
        print(f"🎯 Parallel crawling completed! Processed {len(self.orderbook_data)} tokens successfully")
    
    def crawl_token_orderbook_optimized(self, token):
        """Crawl order book for a specific token using driver pool"""
        symbol = token.get('symbol', '')
        if not symbol:
            return []
        
        driver = None
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                # Get driver from pool
                driver = self.get_driver()
                
                # Use correct URL pattern for the token
                url = f'https://www.mexc.com/vi-VN/pre-market/{symbol}'
                print(f"  🔗 [{symbol}] Loading URL: {url} (attempt {attempt + 1})")
                
                driver.get(url)
                
                # Wait for page to load
                wait = WebDriverWait(driver, 15)
                time.sleep(3)  # Simple wait
                
                # Check if page loaded successfully
                if "404" not in driver.title and "error" not in driver.title.lower():
                    print(f"  ✅ [{symbol}] Successfully loaded order book page")
                    
                    # Extract order book data for this token
                    orderbook_entries = self.extract_orderbook_optimized(driver, symbol)
                    
                    if orderbook_entries:
                        print(f"  📊 [{symbol}] Found {len(orderbook_entries)} order book entries")
                    else:
                        print(f"  ⚠️ [{symbol}] No order book data found")
                    
                    return orderbook_entries
                else:
                    print(f"  ❌ [{symbol}] Page not found: {url}")
                    return []
                    
            except Exception as e:
                error_msg = str(e)
                if "Connection aborted" in error_msg or "ConnectionResetError" in error_msg:
                    print(f"  ⚠️ [{symbol}] Connection error (attempt {attempt + 1}): {error_msg}")
                    if attempt < max_retries - 1:
                        time.sleep(2)  # Wait before retry
                        continue
                    else:
                        print(f"❌ [{symbol}] Max retries reached, giving up")
                        return []
                else:
                    print(f"❌ [{symbol}] Error crawling order book: {e}")
                    return []
            finally:
                # Return driver to pool
                if driver:
                    self.return_driver(driver)
                    driver = None
    
    def extract_orderbook_optimized(self, driver, symbol):
        """Extract order book data for any token - optimized version"""
        orderbook_entries = []
        crawled_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            print(f"    🔍 [{symbol}] Extracting order book data...")
            
            # Phase 1: Crawl SELL orders (lệnh bán) - table with "Mua" buttons
            print(f"    🔍 [{symbol}] Phase 1: Crawling SELL orders...")
            sell_entries = self.crawl_order_type_optimized(driver, symbol, crawled_at,
                                                         table_selector=".order-book-table_sellTable__Dxd2s",
                                                         price_selector=".order-book-table_sellPrice__xAuZe",
                                                         expected_button="Mua",
                                                         order_type_name="SELL orders")
            orderbook_entries.extend(sell_entries)
            
            # Phase 2: Crawl BUY orders (lệnh mua) - table with "Bán" buttons  
            print(f"    🔍 [{symbol}] Phase 2: Crawling BUY orders...")
            buy_entries = self.crawl_order_type_optimized(driver, symbol, crawled_at,
                                                        table_selector=".order-book-table_buyTable__xqBVW", 
                                                        price_selector=".order-book-table_buyPrice__uY0OB",
                                                        expected_button="Bán",
                                                        order_type_name="BUY orders")
            orderbook_entries.extend(buy_entries)
            
            print(f"    ✅ [{symbol}] Total extracted: {len(orderbook_entries)} entries ({len(sell_entries)} SELL + {len(buy_entries)} BUY)")
            
        except Exception as e:
            print(f"    ❌ [{symbol}] Error extracting order book: {str(e)}")
        
        return orderbook_entries
    
    def crawl_order_type_optimized(self, driver, symbol, crawled_at, table_selector, price_selector, expected_button, order_type_name):
        """Crawl specific order type (SELL or BUY orders) - optimized version"""
        orderbook_entries = []
        
        try:
            # Quick check for table data
            try:
                table = driver.find_element(By.CSS_SELECTOR, table_selector)
                table_ready = True
            except:
                table_ready = False
            
            if table_ready:
                if not table:
                    print(f"      ⚠️ [{symbol}] Table not found with selector: {table_selector}")
                    return orderbook_entries
                
                print(f"      ✅ [{symbol}] Found {order_type_name} table")
                
                # Extract rows from this table with stale element handling
                rows = table.find_elements(By.CSS_SELECTOR, "tr")
                if not rows:
                    print(f"      ⚠️ [{symbol}] No rows found in table")
                    return orderbook_entries
                
                # Parse each row quickly
                valid_entries = 0
                for i, row in enumerate(rows):
                    try:
                        # Skip measurement rows
                        if self.is_measurement_row(row):
                            continue
                        
                        # Extract order data from row
                        order_data = self.parse_order_row(row, symbol, price_selector, expected_button)
                        if order_data:
                            orderbook_entries.append(order_data)
                            valid_entries += 1
                                
                    except Exception as e:
                        # Skip error rows silently to avoid spam
                        continue
                
                print(f"      📊 [{symbol}] Successfully parsed {valid_entries} entries from {order_type_name}")
                
                # Handle pagination for this table - optimized (only if needed)
                if valid_entries > 0:  # Only check pagination if we have data
                    pagination_entries = self.handle_pagination_optimized(driver, symbol, crawled_at, table_selector, price_selector, expected_button, order_type_name)
                    orderbook_entries.extend(pagination_entries)
                    
                    if pagination_entries:
                        print(f"      📊 [{symbol}] Found {len(pagination_entries)} additional entries from {order_type_name} pagination")
                
            else:
                print(f"      ⚠️ [{symbol}] {order_type_name} table not found")
                
        except NoSuchElementException:
            print(f"      ⚠️ [{symbol}] {order_type_name} table not found with selector: {table_selector}")
        except Exception as e:
            print(f"      ❌ [{symbol}] Error with {order_type_name} table: {e}")
        
        return orderbook_entries
    
    def handle_pagination_optimized(self, driver, symbol, crawled_at, table_selector, price_selector=None, expected_button=None, order_type_name=""):
        """Handle pagination - optimized version with reduced wait times"""
        pagination_entries = []
        
        try:
            # Look for pagination - use specific selector based on order type
            if "sellTable" in table_selector:
                pagination_selectors = [
                    ".order-book-table_paginationWrapper__O_FJg:first-of-type",
                    ".order-book-table_sellTable__Dxd2s + .order-book-table_paginationWrapper__O_FJg",
                    ".ant-pagination",
                    "[class*='pagination']"
                ]
            elif "buyTable" in table_selector:
                pagination_selectors = [
                    ".order-book-table_buyTable__xqBVW .order-book-table_paginationWrapper__O_FJg",
                    ".order-book-table_buyTable__xqBVW + .order-book-table_paginationWrapper__O_FJg",
                    ".order-book-table_paginationWrapper__O_FJg:last-of-type",
                    ".ant-pagination",
                    "[class*='pagination']"
                ]
            else:
                pagination_selectors = [
                    ".order-book-table_paginationWrapper__O_FJg",
                    ".ant-pagination",
                    "[class*='pagination']"
                ]
            
            # Quick check for pagination
            pagination = None
            for selector in pagination_selectors:
                try:
                    pagination = driver.find_element(By.CSS_SELECTOR, selector)
                    if pagination:
                        break
                except:
                    continue
            
            if not pagination:
                return pagination_entries
            
            # Get page numbers
            page_items = pagination.find_elements(By.CSS_SELECTOR, ".ant-pagination-item")
            if not page_items:
                print(f"      ℹ️ [{symbol}] No page items found")
                return pagination_entries
            
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
            
            print(f"      📄 [{symbol}] Processing pages 1 to {max_page} for {order_type_name}")
            
            # Process pages from 2 to max_page - optimized with shorter waits
            if max_page > 1:
                pages_to_process = list(range(2, max_page + 1))
                
                for page_num in pages_to_process:
                    try:
                        print(f"      🔄 [{symbol}] Processing page {page_num}...")
                        
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
                        
                        if page_link:
                            # Click page link
                            driver.execute_script("arguments[0].click();", page_link)
                            print(f"        ✅ [{symbol}] Clicked page {page_num}")
                            
                            # Smart wait for page change instead of fixed sleep
                            # Wait for page change
                            time.sleep(2)  # Simple wait
                            page_changed = True
                            if not page_changed:
                                print(f"        ⚠️ [{symbol}] Page change verification failed, continuing...")
                            
                            # Extract data from current page with stale element handling
                            try:
                                # Re-find table after page change to avoid stale elements
                                table = driver.find_element(By.CSS_SELECTOR, table_selector)
                                if not table:
                                    print(f"        ⚠️ [{symbol}] Table not found on page {page_num}")
                                    continue
                                
                                rows = table.find_elements(By.CSS_SELECTOR, "tr")
                                if not rows:
                                    print(f"        ⚠️ [{symbol}] No rows found on page {page_num}")
                                    continue
                                
                                page_entries = []
                                page_crawled_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                
                                for row in rows:
                                    try:
                                        if not self.is_measurement_row(row):
                                            order_data = self.parse_order_row(row, symbol, price_selector, expected_button)
                                            if order_data:
                                                page_entries.append(order_data)
                                    except Exception as e:
                                        print(f"          ⚠️ [{symbol}] Error parsing row on page {page_num}: {str(e)}")
                                        continue
                                
                                pagination_entries.extend(page_entries)
                                print(f"        📄 [{symbol}] Page {page_num}: {len(page_entries)} entries")
                                
                            except Exception as e:
                                print(f"        ❌ [{symbol}] Error extracting page {page_num}: {str(e)}")
                        else:
                            print(f"      ❌ [{symbol}] Page {page_num} link not found")
                            
                    except Exception as e:
                        print(f"      ❌ [{symbol}] Error processing page {page_num}: {e}")
                        continue
                
                print(f"      ✅ [{symbol}] Completed pagination for {order_type_name}: {len(pagination_entries)} additional entries from {max_page-1} pages")
            else:
                print(f"      ℹ️ [{symbol}] Only 1 page available for {order_type_name}, no pagination needed")
                
        except Exception as e:
            print(f"      ❌ [{symbol}] Error handling pagination: {e}")
        
        return pagination_entries
    
    
    
    
    
    
    
    
    
    def crawl_token_orderbook(self, symbol):
        """Crawl order book for a specific token"""
        
        try:
            # Use correct URL pattern for the token
            orderbook_entries = self.crawl_orderbook_for_token(symbol)
            
            if not orderbook_entries:
                print(f"⚠️  No order book data found for {symbol}")
            
            return orderbook_entries
            
        except Exception as e:
            print(f"❌ Error crawling order book for {symbol}: {e}")
            return []
    
    def crawl_orderbook_for_token(self, symbol):
        """Crawl order book data for a specific token - using driver pool"""
        orderbook_entries = []
        driver = None
        
        try:
            # Get driver from pool
            driver = self.get_driver()
            
            # Use correct URL pattern for the token
            url = f'https://www.mexc.com/vi-VN/pre-market/{symbol}'
            print(f"  🔗 Loading URL: {url}")
            
            driver.get(url)
            
            # Smart wait for page elements instead of fixed sleep
            # Wait for page to load
            wait = WebDriverWait(driver, 15)
            try:
                wait.until(EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".order-book-table_sellTable__Dxd2s")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".order-book-table_buyTable__xqBVW"))
                ))
                page_loaded = True
            except:
                page_loaded = False
            
            # Check if page loaded successfully
            if "404" not in driver.title and "error" not in driver.title.lower() and page_loaded:
                print(f"  ✅ Successfully loaded order book page for {symbol}")
                
                # Extract order book data for this token
                orderbook_entries = self.extract_orderbook(driver, symbol)
                
                if orderbook_entries:
                    print(f"  📊 Found {len(orderbook_entries)} order book entries")
                else:
                    print(f"  ⚠️  No order book data found on {url}")
            else:
                print(f"  ❌ Page not found: {url}")
                
        except Exception as e:
            print(f"❌ Error crawling order book for {symbol}: {e}")
            
        finally:
            # Return driver to pool
            if driver:
                self.return_driver(driver)
        
        return orderbook_entries
    
    def extract_orderbook(self, driver, symbol):
        """Extract order book data for any token - crawl both Mua and Bán orders"""
        orderbook_entries = []
        crawled_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            print(f"    🔍 Extracting {symbol} order book data...")
            
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
            print(f"    ❌ Error extracting {symbol} order book: {str(e)}")
        
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
                
                # Parse each row
                valid_entries = 0
                for i, row in enumerate(rows):
                    try:
                        # Skip measurement rows
                        if self.is_measurement_row(row):
                            continue
                        
                        # Extract order data from row
                        order_data = self.parse_order_row(row, symbol, price_selector, expected_button)
                        if order_data:
                            orderbook_entries.append(order_data)
                            valid_entries += 1
                            
                                
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

    def parse_order_row(self, row_element, symbol, price_selector=None, expected_button=None):
        """Parse order book row for any token - order type comes from button content"""
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
            
            # Convert numeric values and remove commas
            def clean_numeric(value):
                if not value:
                    return None
                # Remove commas and convert to float
                clean_value = str(value).replace(',', '').strip()
                try:
                    return float(clean_value)
                except (ValueError, TypeError):
                    return None
            
            # Create order entry
            order_entry = {
                'token_symbol': symbol,
                'order_type': order_type or 'Unknown',
                'price': clean_numeric(price),
                'quantity': clean_numeric(quantity),
                'total': clean_numeric(total)
            }
            
            return order_entry
            
        except Exception as e:
            print(f"        ❌ Error parsing order row: {e}")
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
            
            print(f"      📄 Processing ALL pages from 1 to {max_page} for {order_type_name}")
            
            # Process ALL pages from 2 to max_page for both order types
            if max_page > 1:
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
                                    time.sleep(1)  # Simple wait
                                    
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
                            
                            # Smart wait for data to load instead of fixed sleep
                            time.sleep(1)  # Simple wait
                            
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
                                        time.sleep(0.5)  # Simple wait
                                except:
                                    print(f"        ⏳ Waiting for pagination to update (attempt {attempt+1})")
                                    time.sleep(0.5)  # Simple wait
                            
                            # Smart wait for table data to refresh
                            time.sleep(1)  # Simple wait
                            
                            # Scroll to trigger any lazy loading
                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            time.sleep(1)  # Simple wait
                            driver.execute_script("window.scrollTo(0, 0);")
                            time.sleep(1)  # Simple wait
                            
                            # Extract data from current page
                            try:
                                table = driver.find_element(By.CSS_SELECTOR, table_selector)
                                rows = table.find_elements(By.CSS_SELECTOR, "tr")
                                
                                page_entries = []
                                # Create new timestamp for this page
                                page_crawled_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                
                                for row in rows:
                                    if not self.is_measurement_row(row):
                                        order_data = self.parse_order_row(row, symbol, price_selector, expected_button)
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
                            time.sleep(1)  # Simple wait
                            driver.execute_script("window.scrollTo(0, 0);")
                            time.sleep(1)  # Simple wait
                            
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
                                time.sleep(1)  # Simple wait
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
            
            # Extract token name and symbol from element
            name = ''
            symbol = ''
            
            # Parse the text to extract symbol and name
            lines = item_text.strip().split('\n')
            if len(lines) >= 2:
                # First line is usually the symbol
                symbol = lines[0].strip()
                # Second line is usually the name
                name = lines[1].strip()
                
                # Clean up symbol (remove any extra characters)
                symbol = re.sub(r'[^A-Za-z0-9]', '', symbol)
                
                # Clean up name (remove any extra characters)
                name = re.sub(r'\s+', ' ', name).strip()
            
            token_data = {
                'name': name,
                'symbol': symbol,
                'latest_price': '',
                'price_change_percent': '',
                'volume_24h': '',
                'total_volume': '',
                'start_time': None,
                'end_time': None,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Extract latest price
            price_pattern = r'Giá giao dịch mới nhất\s*([\d,]+\.?\d*)'
            price_match = re.search(price_pattern, item_text)
            if price_match:
                # Remove commas and convert to float
                price_str = price_match.group(1).replace(',', '')
                token_data['latest_price'] = float(price_str)
            
            # Extract percentage change (remove % sign for numeric field)
            change_pattern = r'([+-]?\d+\.?\d*)%'
            change_match = re.search(change_pattern, item_text)
            if change_match:
                token_data['price_change_percent'] = float(change_match.group(1))
            
            # Extract volume 24h
            volume_24h_pattern = r'Khối lượng 24 giờ\s*([\d,]+\.?\d*[KMB]?)'
            volume_24h_match = re.search(volume_24h_pattern, item_text)
            if volume_24h_match:
                volume_str = volume_24h_match.group(1).replace(',', '')
                # Convert K/M/B suffixes to numeric values
                if volume_str.endswith('K'):
                    token_data['volume_24h'] = float(volume_str[:-1]) * 1000
                elif volume_str.endswith('M'):
                    token_data['volume_24h'] = float(volume_str[:-1]) * 1000000
                elif volume_str.endswith('B'):
                    token_data['volume_24h'] = float(volume_str[:-1]) * 1000000000
                else:
                    token_data['volume_24h'] = float(volume_str)
            
            # Extract total volume
            total_volume_pattern = r'Tổng khối lượng\s*([\d,]+\.?\d*[KMB]?)'
            total_volume_match = re.search(total_volume_pattern, item_text)
            if total_volume_match:
                volume_str = total_volume_match.group(1).replace(',', '')
                # Convert K/M/B suffixes to numeric values
                if volume_str.endswith('K'):
                    token_data['total_volume'] = float(volume_str[:-1]) * 1000
                elif volume_str.endswith('M'):
                    token_data['total_volume'] = float(volume_str[:-1]) * 1000000
                elif volume_str.endswith('B'):
                    token_data['total_volume'] = float(volume_str[:-1]) * 1000000000
                else:
                    token_data['total_volume'] = float(volume_str)
            
            # Extract timestamps
            time_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
            time_matches = re.findall(time_pattern, item_text)
            
            # Check for status patterns first
            status_patterns = [r'Đợi xác nhận', r'Đã kết thúc', r'Đang diễn ra', r'Đang xác nhận']
            has_status = False
            for pattern in status_patterns:
                if re.search(pattern, item_text):
                    has_status = True
                    break
            
            if time_matches:
                # Has timestamps
                if len(time_matches) >= 2:
                    # 2 timestamps: start_time = first, end_time = second
                    token_data['start_time'] = time_matches[0]
                    token_data['end_time'] = time_matches[1]
                else:
                    # 1 timestamp: start_time = timestamp, end_time = NULL (waiting for confirmation)
                    token_data['start_time'] = time_matches[0]
                    token_data['end_time'] = None
            elif has_status:
                # Only status, no timestamps: both start_time and end_time = NULL
                token_data['start_time'] = None
                token_data['end_time'] = None
            else:
                # No timestamps and no status found
                token_data['start_time'] = None
                token_data['end_time'] = None
            
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
    """Main function to crawl all pre-market tokens"""
    start_time = time.time()
    start_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("🚀 MEXC Pre-Market Token Crawler")
    print("Crawling all pre-market tokens and their order books")
    print("=" * 60)
    print(f"🕐 Start time: {start_datetime}")
    
    # Initialize crawler with database config from config.py
    crawler = MexcPreMarketCrawler(DATABASE_CONFIG)
    crawler.setup_session()
    
    # Run the pre-market crawler
    tokens_data, orderbook_data = crawler.crawl_premarket_data()
    
    # Calculate execution time
    end_time = time.time()
    end_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    execution_time = end_time - start_time
    hours = int(execution_time // 3600)
    minutes = int((execution_time % 3600) // 60)
    seconds = int(execution_time % 60)
    
    if tokens_data:
        print("\n🎉 PRE-MARKET CRAWLING COMPLETED!")
        print(f"🕐 End time: {end_datetime}")
        
        # Display summary
        print(f"\n📊 SUMMARY:")
        print(f"   • Tokens: {len(tokens_data)}")
        if orderbook_data:
            total_orders = sum(len(orders) for orders in orderbook_data.values())
            print(f"   • Order books: {total_orders} entries across {len(orderbook_data)} tokens")
        else:
            print(f"   • Order books: No data available")
        
        print(f"\n⏱️ EXECUTION TIME:")
        print(f"   • Start: {start_datetime}")
        print(f"   • End: {end_datetime}")
        if hours > 0:
            print(f"   • Total time: {hours}h {minutes}m {seconds}s")
        elif minutes > 0:
            print(f"   • Total time: {minutes}m {seconds}s")
        else:
            print(f"   • Total time: {seconds}s")
        
        print(f"\n💾 Data saved to PostgreSQL database: crawl_mexc")
        
    else:
        print("❌ No token data was extracted. Please check your setup and try again.")
        print(f"🕐 End time: {end_datetime}")
        print(f"\n⏱️ EXECUTION TIME:")
        print(f"   • Start: {start_datetime}")
        print(f"   • End: {end_datetime}")
        if hours > 0:
            print(f"   • Total time: {hours}h {minutes}m {seconds}s")
        elif minutes > 0:
            print(f"   • Total time: {minutes}m {seconds}s")
        else:
            print(f"   • Total time: {seconds}s")


if __name__ == "__main__":
    main()

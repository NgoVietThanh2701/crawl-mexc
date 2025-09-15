#!/usr/bin/env python3
"""
MEXC Page Counter - Test pagination and count entries per page
Only counts entries without extracting detailed order book data
"""

import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class MEXCPageCounter:
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver with optimized settings"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Disable images and CSS for faster loading
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.stylesheets": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        
    def count_page_entries(self, symbol):
        """Count entries on each page without extracting detailed data"""
        try:
            print(f"🔍 Counting entries for {symbol}...")
            
            # Load the order book page
            url = f"https://www.mexc.com/vi-VN/pre-market/{symbol}"
            print(f"📡 Loading URL: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Find the order book table
            try:
                orderbook_table = self.driver.find_element(By.CSS_SELECTOR, "tbody.ant-table-tbody")
                print("✅ Found order book table")
            except NoSuchElementException:
                print("❌ Order book table not found")
                return {}
            
            # Count entries on page 1
            page_data = {}
            page_1_entries = self.count_current_page_entries()
            page_data[1] = page_1_entries
            print(f"📊 Page 1: {page_1_entries} entries")
            
            # Check for pagination
            try:
                pagination = self.driver.find_element(By.CSS_SELECTOR, ".order-book-table_paginationWrapper__O_FJg")
                print("✅ Found pagination")
                
                # Get all page numbers
                page_links = pagination.find_elements(By.CSS_SELECTOR, "li[title]")
                page_numbers = []
                for link in page_links:
                    try:
                        page_num = int(link.get_attribute('title'))
                        if page_num > 0:
                            page_numbers.append(page_num)
                    except:
                        continue
                
                max_page = max(page_numbers) if page_numbers else 1
                print(f"📄 Found {len(page_links)} pagination pages, max page: {max_page}")
                print(f"📄 Page numbers detected: {sorted(page_numbers)}")
                
                # Test all accessible pages
                for page_num in sorted(page_numbers):
                    if page_num == 1:
                        continue  # Already processed
                        
                    try:
                        print(f"🔄 Testing page {page_num}...")
                        
                        # Find and click page link
                        page_link = pagination.find_element(By.CSS_SELECTOR, f"li[title='{page_num}']")
                        if page_link and page_link.is_enabled():
                            page_link.click()
                            time.sleep(2)  # Wait for page to load
                            
                            # Count entries on current page
                            entries_count = self.count_current_page_entries()
                            page_data[page_num] = entries_count
                            print(f"📊 Page {page_num}: {entries_count} entries")
                            
                            # Update pagination reference
                            try:
                                pagination = self.driver.find_element(By.CSS_SELECTOR, ".order-book-table_paginationWrapper__O_FJg")
                            except:
                                print(f"⚠️ Could not find pagination after page {page_num}")
                                break
                        else:
                            print(f"❌ Page {page_num} link not found or disabled")
                            break
                            
                    except Exception as e:
                        print(f"❌ Error accessing page {page_num}: {e}")
                        break
                        
            except NoSuchElementException:
                print("ℹ️ No pagination found - only 1 page available")
            
            return page_data
            
        except Exception as e:
            print(f"❌ Error counting pages: {e}")
            return {}
    
    def count_current_page_entries(self):
        """Count entries on current page without extracting data"""
        try:
            # Find the order book table
            orderbook_table = self.driver.find_element(By.CSS_SELECTOR, "tbody.ant-table-tbody")
            rows = orderbook_table.find_elements(By.CSS_SELECTOR, "tr")
            
            print(f"        🔍 Found {len(rows)} total rows")
            
            # Count valid rows (skip measurement rows)
            valid_entries = 0
            for i, row in enumerate(rows):
                try:
                    # Check if this is a measurement row
                    classes = row.get_attribute('class') or ''
                    aria_hidden = row.get_attribute('aria-hidden') or ''
                    
                    if 'ant-table-measure-row' in classes or 'true' in aria_hidden:
                        print(f"        ⚠️ Skipping measurement row {i+1}")
                        continue
                    
                    # Check if row has data by looking for cells with content
                    cells = row.find_elements(By.TAG_NAME, 'td')
                    if len(cells) >= 3:
                        # Check if first cell has price data
                        first_cell = cells[0]
                        price_text = first_cell.text.strip()
                        
                        # More flexible price detection
                        if price_text and (price_text.replace('.', '').replace(',', '').isdigit() or 
                                         any(char.isdigit() for char in price_text)):
                            valid_entries += 1
                            print(f"        ✅ Row {i+1}: Valid entry (price: {price_text})")
                        else:
                            print(f"        ⚠️ Row {i+1}: No valid price data ('{price_text}')")
                    else:
                        print(f"        ⚠️ Row {i+1}: Not enough cells ({len(cells)})")
                        
                except Exception as e:
                    print(f"        ❌ Row {i+1}: Error - {e}")
                    continue
            
            print(f"        📊 Counted {valid_entries} valid entries")
            return valid_entries
            
        except Exception as e:
            print(f"❌ Error counting current page entries: {e}")
            return 0
    
    def test_pagination(self, symbol):
        """Test pagination and return page counts"""
        try:
            self.setup_driver()
            page_data = self.count_page_entries(symbol)
            
            # Summary
            print(f"\n📊 PAGINATION TEST SUMMARY for {symbol}:")
            print(f"   Total pages tested: {len(page_data)}")
            total_entries = sum(page_data.values())
            print(f"   Total entries found: {total_entries}")
            print(f"   Page breakdown:")
            
            for page_num in sorted(page_data.keys()):
                entries = page_data[page_num]
                print(f"     - Page {page_num}: {entries} entries")
            
            # Check if we found the last page
            if page_data:
                last_page = max(page_data.keys())
                last_entries = page_data[last_page]
                if last_entries < 10:
                    print(f"   ✅ Page {last_page} appears to be the last page ({last_entries} entries)")
                else:
                    print(f"   ⚠️ Last tested page has {last_entries} entries - may not be the actual last page")
            
            return page_data
            
        except Exception as e:
            print(f"❌ Error in pagination test: {e}")
            return {}
        finally:
            if self.driver:
                self.driver.quit()

def main():
    if len(sys.argv) != 2:
        print("Usage: python mexc_page_counter.py <SYMBOL>")
        print("Example: python mexc_page_counter.py STBL")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    
    print(f"🚀 MEXC Page Counter - Testing pagination for {symbol}")
    print("=" * 60)
    
    counter = MEXCPageCounter()
    page_data = counter.test_pagination(symbol)
    
    if page_data:
        print(f"\n🎉 Test completed successfully!")
    else:
        print(f"\n❌ Test failed!")

if __name__ == "__main__":
    main()

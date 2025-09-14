import scrapy
from scrapy import Request
from mexc_crawler.items import TokenItem
from datetime import datetime
import re
import json


class MexcSpider(scrapy.Spider):
    name = 'mexc'
    allowed_domains = ['mexc.com']
    start_urls = ['https://www.mexc.com/vi-VN/pre-market']
    
    def start_requests(self):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        }
        
        for url in self.start_urls:
            yield Request(url=url, headers=headers, callback=self.parse)
    
    def parse(self, response):
        # Wait for JavaScript to load and try to find the data
        # The data might be loaded via AJAX or be embedded in the page
        
        # First, let's try to find the specific div with id "rc-tabs-0-panel-1"
        token_panel = response.css('#rc-tabs-0-panel-1')
        
        if token_panel:
            # Look for the ul with class "ant-list-items"
            token_list = token_panel.css('ul.ant-list-items')
            
            if token_list:
                # Extract individual token items
                token_items = token_list.css('li')
                
                for item in token_items:
                    token_item = TokenItem()
                    
                    # Extract token information
                    # The structure might vary, so we'll try multiple selectors
                    
                    # Try to find name/symbol - could be in various places
                    name_elem = item.css('.token-name, .symbol, [class*="name"], [class*="symbol"]::text').get()
                    if not name_elem:
                        name_elem = item.css('div::text').re_first(r'([A-Z]+)')
                    
                    # Try to find price information
                    price_elem = item.css('[class*="price"], .price::text').get()
                    if not price_elem:
                        price_elem = item.css('div::text').re_first(r'[\d,]+\.?\d*')
                    
                    # Try to find percentage change
                    change_elem = item.css('[class*="change"], [class*="percent"]::text').get()
                    if not change_elem:
                        change_elem = item.css('div::text').re_first(r'[+-]?\d+\.?\d*%')
                    
                    # Try to find volume information
                    volume_elem = item.css('[class*="volume"]::text').get()
                    
                    # Clean and assign data
                    token_item['name'] = self.clean_text(name_elem) if name_elem else ''
                    token_item['symbol'] = self.clean_text(name_elem) if name_elem else ''
                    token_item['latest_price'] = self.clean_text(price_elem) if price_elem else ''
                    token_item['price_change_percent'] = self.clean_text(change_elem) if change_elem else ''
                    token_item['volume_24h'] = self.clean_text(volume_elem) if volume_elem else ''
                    token_item['total_volume'] = ''  # Might need additional parsing
                    token_item['start_time'] = ''  # Might need additional parsing
                    token_item['crawled_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    yield token_item
        
        # If we couldn't find the expected structure, let's try alternative approaches
        # Sometimes the data might be loaded via JavaScript or be in a different format
        
        # Try to find any token-related data in the page
        all_divs = response.css('div')
        token_related = []
        
        for div in all_divs:
            text = div.get()
            if text and any(keyword in text.lower() for keyword in ['token', 'symbol', 'price', 'volume']):
                token_related.append(text)
        
        # If we still don't have data, try to look for JSON data in script tags
        script_tags = response.css('script::text').getall()
        
        for script in script_tags:
            if 'token' in script.lower() or 'premarket' in script.lower():
                # Try to extract JSON data
                try:
                    # Look for JSON objects in the script
                    json_match = re.search(r'\{.*\}', script)
                    if json_match:
                        json_data = json.loads(json_match.group())
                        # Process the JSON data if it contains token information
                        if isinstance(json_data, dict) and 'tokens' in json_data:
                            for token_data in json_data['tokens']:
                                token_item = self.create_token_item_from_json(token_data)
                                yield token_item
                except (json.JSONDecodeError, AttributeError):
                    continue
        
        # If still no data found, log the response for debugging
        if not token_related:
            self.logger.warning(f"No token data found. Response length: {len(response.text)}")
            # Save response for debugging
            with open('debug_response.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
    
    def clean_text(self, text):
        """Clean and format text data"""
        if not text:
            return ''
        
        # Remove extra whitespace and special characters
        cleaned = re.sub(r'\s+', ' ', text.strip())
        cleaned = cleaned.replace('\n', '').replace('\t', '')
        
        return cleaned
    
    def create_token_item_from_json(self, data):
        """Create a token item from JSON data"""
        token_item = TokenItem()
        
        token_item['name'] = data.get('name', '')
        token_item['symbol'] = data.get('symbol', '')
        token_item['latest_price'] = data.get('price', data.get('latest_price', ''))
        token_item['price_change_percent'] = data.get('change_percent', data.get('price_change_percent', ''))
        token_item['volume_24h'] = data.get('volume_24h', '')
        token_item['total_volume'] = data.get('total_volume', '')
        token_item['start_time'] = data.get('start_time', '')
        token_item['crawled_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return token_item

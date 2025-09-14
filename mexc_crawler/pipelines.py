# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import json
from datetime import datetime
import os


class TxtFilePipeline:
    def __init__(self):
        self.token_file = None
        self.orderbook_file = None
        
    def open_spider(self, spider):
        # Create output files with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Token data file
        token_filename = f"mexc_premarket_tokens_{timestamp}.txt"
        self.token_file = open(token_filename, 'w', encoding='utf-8')
        token_header = "Name\tSymbol\tLatest Price\tPrice Change %\tVolume 24h\tTotal Volume\tStart Time\tEnd Time\tCrawled At\n"
        self.token_file.write(token_header)
        
        # Order book data file
        orderbook_filename = f"mexc_orderbook_{timestamp}.txt"
        self.orderbook_file = open(orderbook_filename, 'w', encoding='utf-8')
        orderbook_header = "Token Symbol\tOrder Type\tPrice\tQuantity\tTotal\tCrawled At\n"
        self.orderbook_file.write(orderbook_header)
        
    def close_spider(self, spider):
        if self.token_file:
            self.token_file.close()
        if self.orderbook_file:
            self.orderbook_file.close()
            
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Check if this is a TokenItem or OrderBookItem
        if 'token_symbol' in adapter.asdict():
            # This is an OrderBookItem
            line = f"{adapter.get('token_symbol', '')}\t"
            line += f"{adapter.get('order_type', '')}\t"
            line += f"{adapter.get('price', '')}\t"
            line += f"{adapter.get('quantity', '')}\t"
            line += f"{adapter.get('total', '')}\t"
            line += f"{adapter.get('crawled_at', '')}\n"
            
            self.orderbook_file.write(line)
            self.orderbook_file.flush()
        else:
            # This is a TokenItem
            line = f"{adapter.get('name', '')}\t"
            line += f"{adapter.get('symbol', '')}\t"
            line += f"{adapter.get('latest_price', '')}\t"
            line += f"{adapter.get('price_change_percent', '')}\t"
            line += f"{adapter.get('volume_24h', '')}\t"
            line += f"{adapter.get('total_volume', '')}\t"
            line += f"{adapter.get('start_time', '')}\t"
            line += f"{adapter.get('end_time', '')}\t"
            line += f"{adapter.get('crawled_at', '')}\n"
            
            self.token_file.write(line)
            self.token_file.flush()
        
        return item

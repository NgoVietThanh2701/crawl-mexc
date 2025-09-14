# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class TokenItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()
    symbol = scrapy.Field()
    latest_price = scrapy.Field()
    price_change_percent = scrapy.Field()
    volume_24h = scrapy.Field()
    total_volume = scrapy.Field()
    start_time = scrapy.Field()
    crawled_at = scrapy.Field()


class OrderBookItem(scrapy.Item):
    # Order book data fields
    token_symbol = scrapy.Field()  # Symbol của token (ví dụ: STBL, ASTER)
    order_type = scrapy.Field()    # BUY hoặc SELL
    price = scrapy.Field()         # Giá
    quantity = scrapy.Field()      # Số lượng
    total = scrapy.Field()         # Tổng số lượng theo từng mức giá
    crawled_at = scrapy.Field()    # Thời gian crawl
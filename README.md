# MEXC Pre-Market Token & Order Book Crawler

Crawler để lấy thông tin token pre-market và order book từ sàn MEXC, lưu trữ dữ liệu vào PostgreSQL database.

## 📁 Cấu trúc dự án

```
D:\Crawl_MEXC\
├── mexc_premarket_crawler.py           # Crawler chính cho tất cả pre-market tokens
├── config.py                           # Database configuration
├── mexc_crawler/                       # Scrapy project (legacy)
│   ├── items.py                        # Data models
│   ├── pipelines.py                    # Data processing
│   ├── settings.py                     # Scrapy settings
│   └── spiders/                        # Scrapy spiders
│       ├── mexc_spider.py             # Basic spider
│       ├── mexc_selenium_spider.py    # Selenium spider
│       └── mexc_orderbook_spider.py   # Order book spider
├── scrapy.cfg                          # Scrapy config
├── html_extract.txt                    # HTML mẫu (reference)
├── README.md                           # File này
└── mexc_premarket_data_*.txt           # File kết quả (backup)
```

## 🚀 Hướng dẫn chạy

### 1. Cài đặt Python dependencies:

```bash
pip install requests beautifulsoup4 selenium psycopg2-binary
```

### 2. Cài đặt PostgreSQL:

- Tải và cài đặt PostgreSQL từ [postgresql.org](https://www.postgresql.org/download/)
- Tạo database `crawl_mexc`
- Cấu hình thông tin database trong `config.py`:

```python
DATABASE_CONFIG = {
    'host': 'localhost',
    'database': 'crawl_mexc',
    'user': 'postgres',
    'password': 'your_password',
    'port': '5432'
}
```

### 4. Chạy crawler:

```bash
python mexc_premarket_crawler.py
```

## 📊 Kết quả

Dữ liệu được lưu trữ trong PostgreSQL database `crawl_mexc` với 2 bảng:

### Bảng `tokens`:

- **symbol**: Mã token (ví dụ: MENTO)
- **name**: Tên token
- **latest_price**: Giá giao dịch mới nhất
- **price_change_percent**: Phần trăm thay đổi giá
- **volume_24h**: Khối lượng giao dịch 24h
- **total_volume**: Tổng khối lượng
- **start_time**: Thời gian bắt đầu
- **end_time**: Thời gian kết thúc (NULL nếu "Đợi xác nhận")
- **created_at**: Thời gian tạo record

### Bảng `order_books`:

- **token_id**: ID tham chiếu đến bảng tokens
- **order_type**: Loại lệnh (Mua/Bán)
- **price**: Giá
- **quantity**: Số lượng
- **total**: Tổng tiền
- **crawled_at**: Thời gian crawl record

### File backup:

File `mexc_premarket_data_YYYYMMDD_HHMMSS.txt` sẽ được tạo làm backup chứa toàn bộ dữ liệu đã crawl.

## 🎯 Tính năng chính

- ✅ Crawl tất cả tokens từ pre-market page
- ✅ Crawl toàn bộ order book với phân trang (SELL & BUY orders) cho từng token
- ✅ Lưu trữ dữ liệu vào PostgreSQL database
- ✅ Xử lý đúng order type từ button content (Mua/Bán)
- ✅ Tự động tạo timestamp cho mỗi record
- ✅ Xử lý numeric data (price, quantity, volume) đúng định dạng
- ✅ Xử lý end_time đúng: NULL cho "Đợi xác nhận", timestamp cho thời gian thực

## 🚨 Troubleshooting

**Lỗi database connection**: Kiểm tra config.py và đảm bảo PostgreSQL đang chạy

**Lỗi ChromeDriver**: Tải ChromeDriver và đặt vào PATH

**Lỗi timeout**: Kiểm tra kết nối internet

**Lỗi data type**: Đảm bảo database schema đã được tạo đúng

## 📝 Lưu ý

- Crawler sẽ tự động tạo database tables nếu chưa tồn tại
- Dữ liệu được lưu với timestamp tự động
- File backup được tạo để phòng trường hợp cần thiết

---

**Version**: 2.0 | **Status**: ✅ Hoạt động tốt với PostgreSQL

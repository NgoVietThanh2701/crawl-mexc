# MEXC Pre-Market Token & Order Book Crawler

Crawler để lấy thông tin token pre-market và order book từ sàn MEXC.

## 📁 Cấu trúc dự án

```
D:\Crawl_MEXC\
├── mexc_correct_orderbook_crawler.py    # Crawler chính (recommended)
├── mexc_crawler/                        # Scrapy project
│   ├── items.py                         # Data models
│   ├── pipelines.py                     # Data processing
│   ├── settings.py                      # Scrapy settings
│   └── spiders/                         # Scrapy spiders
│       ├── mexc_spider.py              # Basic spider
│       ├── mexc_selenium_spider.py     # Selenium spider
│       └── mexc_orderbook_spider.py    # Order book spider
├── scrapy.cfg                           # Scrapy config
├── html_extract.txt                     # HTML mẫu (reference)
├── README.md                            # File này
└── mexc_correct_orderbook_data_*.txt    # File kết quả
```

## 🚀 Hướng dẫn chạy

### 1. Cài đặt dependencies:

```bash
pip install scrapy selenium requests beautifulsoup4
```

### 2. Cài đặt ChromeDriver:

- Tải ChromeDriver phù hợp với phiên bản Chrome
- Đặt vào PATH hoặc cùng thư mục với script

### 3. Chạy crawler:

```bash
python mexc_correct_orderbook_crawler.py
```

## 📊 Kết quả

File `mexc_correct_orderbook_data_YYYYMMDD_HHMMSS.txt` sẽ chứa:

- **Token data**: Name, Symbol, Price, Volume, etc.
- **Order book data**: Price, Quantity, Total cho từng token

## 🎯 Dữ liệu chính xác

- ✅ Token names: "BluWhale AI", "Plasma", "Aster", etc.
- ✅ Order book thực tế từ website
- ✅ CSS selectors chính xác từ HTML thực tế
- ✅ Xử lý phân trang để lấy đầy đủ dữ liệu

## 🚨 Troubleshooting

**Lỗi ChromeDriver**: Tải ChromeDriver và đặt vào PATH

**Lỗi timeout**: Kiểm tra kết nối internet

**Không crawl được**: Website có thể đã thay đổi cấu trúc

---

**Version**: 1.0 | **Status**: ✅ Hoạt động tốt

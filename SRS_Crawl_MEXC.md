# 📑 Software Requirement Specification (SRS)

## Hệ thống Crawl Data Pre-Market & Order Book (MEXC)

---

### 1. Giới thiệu

#### 1.1. Mục tiêu

Xây dựng hệ thống tự động crawl dữ liệu từ sàn giao dịch **MEXC**:

- Lấy danh sách các token đang diễn ra trong **Pre-Market**.
- Vào chi tiết từng token, crawl dữ liệu **Order Book** (bảng lệnh mua/bán).
- Lưu dữ liệu có cấu trúc vào **cơ sở dữ liệu** (Postgres/MySQL/SQLite tuỳ chọn).

#### 1.2. Phạm vi

- Nguồn dữ liệu: [https://www.mexc.com/vi-VN/pre-market](https://www.mexc.com/vi-VN/pre-market).
- Token chi tiết: trang order book riêng cho từng token.
- Người dùng cuối: đội ngũ phân tích dữ liệu & trading bot.

---

### 2. Yêu cầu hệ thống

#### 2.1. Chức năng chính

1. **Crawl danh sách token**

   - Truy cập trang pre-market.
   - Lấy thông tin cơ bản của token:
     - Ticker / Name
     - Thời gian giao dịch
     - Giá giao dịch mới nhất
     - % thay đổi giá
     - Khối lượng 24h
     - Tổng khối lượng

2. **Crawl dữ liệu Order Book**

   - Vào chi tiết từng token.
   - Thu thập dữ liệu:
     - Thời gian crawl
     - Lệnh Mua/Bán
     - Giá
     - Số lượng
     - Tổng số lượng theo từng mức giá

3. **Lưu trữ dữ liệu**

   - Lưu thông tin token và order book vào cơ sở dữ liệu.
   - Có bảng liên kết giữa token và order book.
   - Hỗ trợ truy vấn phục vụ phân tích.

4. **Lên lịch tự động**
   - Cron job chạy định kỳ (ví dụ: mỗi 5 phút crawl order book).
   - Lưu log crawl để debug khi lỗi.

---

### 3. Thiết kế hệ thống

#### 3.1. Kiến trúc tổng quan

- **Crawler Service**: viết bằng Python (Scrapy/Requests/Playwright).
- **Database**: PostgreSQL (khuyến nghị) hoặc MySQL.
- **Scheduler**: Cron job hoặc Celery beat.
- **Storage**: Dữ liệu lưu dạng bảng quan hệ.

#### 3.2. Thiết kế Database

```sql
-- Bảng token
CREATE TABLE tokens (
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
);

-- Bảng order book
CREATE TABLE order_books (
    id SERIAL PRIMARY KEY,
    token_id INT REFERENCES tokens(id) ON DELETE CASCADE,
    order_type VARCHAR(10), -- 'BUY' hoặc 'SELL'
    price DECIMAL(18,8),
    quantity DECIMAL(18,8),
    total DECIMAL(18,8),
    crawled_at TIMESTAMP DEFAULT NOW()
);
```

---

### 4. Yêu cầu phi chức năng

- **Hiệu năng**: crawl dữ liệu pre-market trong < 5 giây, order book mỗi token < 3 giây.
- **Độ tin cậy**: retry 3 lần nếu request thất bại.
- **Mở rộng**: dễ thêm sàn khác ngoài MEXC.
- **Bảo mật**: tránh bị chặn IP → hỗ trợ proxy/rotate User-Agent.

---

### 5. Luồng hoạt động

1. Hệ thống gọi API hoặc render HTML → lấy danh sách token.
2. Lưu token mới vào DB (nếu chưa có).
3. Với mỗi token, đi vào trang order book → crawl dữ liệu.
4. Lưu dữ liệu order book vào DB.
5. Scheduler chạy lặp lại theo thời gian cấu hình.

---

### 6. Công nghệ đề xuất

- **Ngôn ngữ**: Python
- **Crawler**: Requests + BeautifulSoup / Playwright (nếu cần render JS).
- **DB**: PostgreSQL
- **Scheduler**: Cronjob hoặc Airflow (nếu muốn phức tạp hơn).

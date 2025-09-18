# MEXC Pre-Market Crawler

## 🚀 Cách sử dụng

### Chạy 1 lần

```cmd
python mexc_premarket_crawler.py
```

## 📁 Files

- `mexc_premarket_crawler.py` - **Crawler chính**
- `cron_wrapper.bat` - **Wrapper cho cron job với logging**
- `config.py` - Database configuration
- `logs/` - **Thư mục logs** (tự động tạo)
  - `cron_YYYY-MM-DD.log` - Log file cron job theo ngày với thời gian bắt đầu/kết thúc

## ⚙️ Hướng dẫn cài đặt

### 1. Cài đặt Python dependencies

```cmd
pip install selenium
pip install psycopg2-binary
pip install requests
pip install beautifulsoup4
pip install webdriver-manager
```

### 2. Cài đặt ChromeDriver

ChromeDriver sẽ được tự động tải xuống khi chạy lần đầu.

### 3. Cấu hình Database

Chỉnh sửa file `config.py`:

```python
# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'mexc_data',
    'user': 'your_username',
    'password': 'your_password',
    'port': 5432
}
```

### 4. Tạo database

```sql
-- Tạo database
CREATE DATABASE mexc_data;
```

**Lưu ý**: Table sẽ được tự động tạo khi chạy crawler lần đầu.

## ⏰ Cron Job Windows

### 1. Tạo cron job (chạy mỗi 1 phút sau khi task crawl hoàn thành)

```cmd
schtasks /create /tn "MEXC_PreMarket_Crawler" /tr "D:\Crawl_MEXC\cron_wrapper.bat" /sc minute /mo 1 /f
```

### 2. Kiểm tra cron job

```cmd
schtasks /query /tn "MEXC_PreMarket_Crawler"
```

### 3. Hủy bỏ cron job

```cmd
schtasks /delete /tn "MEXC_PreMarket_Crawler" /f
```

## ✅ Kết quả

Sau khi thiết lập:

- ✅ Crawler chạy tự động theo lịch đã đặt
- ✅ Data được lưu vào PostgreSQL database
- ✅ Logs được ghi vào `logs/` folder (mỗi ngày 1 file)
- ✅ Chạy 24/7 ngay cả khi không đăng nhập

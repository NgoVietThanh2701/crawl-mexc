@echo off
cd /d "D:\Crawl_MEXC"

REM Tạo thư mục logs nếu chưa có
if not exist "logs" mkdir logs

REM Tạo tên file log theo ngày
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%-%MM%-%DD% %HH%:%Min%:%Sec%"

REM Ghi log bắt đầu
echo [%timestamp%] CRON JOB STARTED >> logs\cron_%YYYY%-%MM%-%DD%.log

REM Chạy crawler
python mexc_premarket_crawler.py

REM Ghi log kết thúc
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%-%MM%-%DD% %HH%:%Min%:%Sec%"
echo [%timestamp%] CRON JOB FINISHED - Exit code: %errorlevel% >> logs\cron_%YYYY%-%MM%-%DD%.log
echo. >> logs\cron_%YYYY%-%MM%-%DD%.log

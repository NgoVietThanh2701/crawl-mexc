# Database Configuration
DATABASE_CONFIG = {
    'host': 'localhost',
    'database': 'crawl_mexc',
    'user': 'postgres',
    'password': '123456',  # Change this to your PostgreSQL password
    'port': '5432'
}

# Crawler Configuration
CRAWLER_CONFIG = {
    'headless': True,
    'wait_timeout': 10,
    'page_load_timeout': 30
}

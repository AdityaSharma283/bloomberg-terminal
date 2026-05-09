import os
from dotenv import load_dotenv

load_dotenv()

# API Keys (we'll add these to .env)
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY", "demo")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
FRED_API_KEY = os.getenv("FRED_API_KEY", "")

# App settings
APP_HOST = "127.0.0.1"
APP_PORT = 8000
DEBUG = True

# Default watchlist — mix of US + India
DEFAULT_WATCHLIST = [
    "AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "META",
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "WIPRO.NS"
]

# Cache settings
CACHE_DB = "cache.db"
CACHE_EXPIRY_SECONDS = 300  # 5 minutes
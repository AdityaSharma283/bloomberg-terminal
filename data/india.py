import yfinance as yf
from data.cache import cache_get, cache_set

INDIA_INDICES = {
    "NIFTY 50":    "^NSEI",
    "SENSEX":      "^BSESN",
    "NIFTY BANK":  "^NSEBANK",
    "NIFTY IT":    "^CNXIT",
}

INDIA_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS",
    "ICICIBANK.NS", "HINDUNILVR.NS", "ITC.NS", "WIPRO.NS",
    "AXISBANK.NS", "BAJFINANCE.NS",
]

def get_india_indices() -> list:
    cached = cache_get("india_indices")
    if cached:
        return cached

    results = []
    for name, symbol in INDIA_INDICES.items():
        try:
            t = yf.Ticker(symbol)
            info = t.info
            results.append({
                "name": name,
                "symbol": symbol,
                "price": info.get("regularMarketPrice", 0),
                "change": round(info.get("regularMarketChangePercent", 0), 2),
            })
        except:
            pass

    cache_set("india_indices", results)
    return results


def get_india_top_stocks() -> list:
    cached = cache_get("india_top_stocks")
    if cached:
        return cached

    results = []
    for symbol in INDIA_STOCKS:
        try:
            t = yf.Ticker(symbol)
            info = t.info
            results.append({
                "symbol": symbol.replace(".NS", ""),
                "name": info.get("longName", symbol),
                "price": info.get("currentPrice") or info.get("regularMarketPrice", 0),
                "change": round(info.get("regularMarketChangePercent", 0), 2),
            })
        except:
            pass

    cache_set("india_top_stocks", results)
    return results
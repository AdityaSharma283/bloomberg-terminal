import yfinance as yf
from data.cache import cache_get, cache_set

SCREEN_UNIVERSE = [
    "AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA","JPM","GS","MS",
    "RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS",
    "WIPRO.NS","AXISBANK.NS","ITC.NS","BAJFINANCE.NS","HINDUNILVR.NS",
]

def run_screener(
    min_pe: float = None, max_pe: float = None,
    min_mktcap: float = None,
    min_change: float = None, max_change: float = None,
) -> list:
    cache_key = f"screener:{min_pe}:{max_pe}:{min_mktcap}:{min_change}:{max_change}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    results = []
    for ticker in SCREEN_UNIVERSE:
        try:
            stock = yf.Ticker(ticker)
            info  = stock.info
            pe    = info.get("trailingPE")
            mcap  = info.get("marketCap", 0)
            chg   = info.get("regularMarketChangePercent", 0)
            price = info.get("currentPrice") or info.get("regularMarketPrice", 0)

            if min_pe    is not None and (pe is None or pe < min_pe):       continue
            if max_pe    is not None and (pe is None or pe > max_pe):       continue
            if min_mktcap is not None and mcap < min_mktcap:                continue
            if min_change is not None and chg < min_change:                 continue
            if max_change is not None and chg > max_change:                 continue

            results.append({
                "symbol":     ticker,
                "name":       info.get("longName", ticker)[:28],
                "price":      round(price, 2),
                "change":     round(chg, 2),
                "pe_ratio":   round(pe, 2) if pe else None,
                "market_cap": mcap,
                "sector":     info.get("sector", "N/A"),
            })
        except:
            continue

    cache_set(cache_key, results)
    return results
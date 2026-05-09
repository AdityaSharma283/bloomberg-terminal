import yfinance as yf
import pandas as pd
from data.cache import cache_get, cache_set
from config import DEFAULT_WATCHLIST

def get_quote(ticker: str) -> dict:
    cached = cache_get(f"quote:{ticker}")
    if cached:
        return cached

    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        result = {
            "symbol": ticker,
            "name": info.get("longName", ticker),
            "price": info.get("currentPrice") or info.get("regularMarketPrice") or 0,
            "prev_close": info.get("previousClose", 0),
            "change": round(info.get("regularMarketChangePercent", 0), 2),
            "volume": info.get("regularMarketVolume", 0),
            "avg_volume": info.get("averageVolume", 0),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", None),
            "eps": info.get("trailingEps", None),
            "week_52_high": info.get("fiftyTwoWeekHigh", 0),
            "week_52_low": info.get("fiftyTwoWeekLow", 0),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "currency": info.get("currency", "USD"),
        }
        cache_set(f"quote:{ticker}", result)
        return result
    except Exception as e:
        return {"symbol": ticker, "error": str(e)}


def get_history(ticker: str, period: str = "3mo", interval: str = "1d") -> dict:
    cache_key = f"history:{ticker}:{period}:{interval}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        hist.index = hist.index.strftime("%Y-%m-%d %H:%M")
        result = {
            "dates":   hist.index.tolist(),
            "open":    [round(x, 2) for x in hist["Open"].tolist()],
            "high":    [round(x, 2) for x in hist["High"].tolist()],
            "low":     [round(x, 2) for x in hist["Low"].tolist()],
            "close":   [round(x, 2) for x in hist["Close"].tolist()],
            "volume":  hist["Volume"].tolist(),
        }
        cache_set(cache_key, result)
        return result
    except Exception as e:
        return {"error": str(e)}


def get_watchlist() -> list:
    results = []
    for ticker in DEFAULT_WATCHLIST:
        quote = get_quote(ticker)
        if "error" not in quote:
            results.append({
                "symbol": quote["symbol"],
                "name": quote["name"],
                "price": quote["price"],
                "change": quote["change"],
                "currency": quote["currency"],
            })
    return results


def get_financials(ticker: str) -> dict:
    cached = cache_get(f"financials:{ticker}")
    if cached:
        return cached

    try:
        stock = yf.Ticker(ticker)
        income = stock.income_stmt
        balance = stock.balance_sheet

        result = {
            "revenue": income.loc["Total Revenue"].iloc[0] if "Total Revenue" in income.index else None,
            "net_income": income.loc["Net Income"].iloc[0] if "Net Income" in income.index else None,
            "gross_profit": income.loc["Gross Profit"].iloc[0] if "Gross Profit" in income.index else None,
            "total_assets": balance.loc["Total Assets"].iloc[0] if "Total Assets" in balance.index else None,
            "total_debt": balance.loc["Total Debt"].iloc[0] if "Total Debt" in balance.index else None,
        }
        cache_set(f"financials:{ticker}", result)
        return result
    except Exception as e:
        return {"error": str(e)}
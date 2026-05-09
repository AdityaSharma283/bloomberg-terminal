from fastapi import APIRouter
from data.fetcher import get_quote, get_history, get_watchlist, get_financials
from data.news import get_market_news
from data.india import get_india_indices, get_india_top_stocks
from data.indicators import get_indicators

router = APIRouter()

@router.get("/quote/{ticker}")
def quote(ticker: str):
    return get_quote(ticker.upper())

@router.get("/history/{ticker}")
def history(ticker: str, period: str = "3mo", interval: str = "1d"):
    return get_history(ticker.upper(), period, interval)

@router.get("/watchlist")
def watchlist():
    return get_watchlist()

@router.get("/financials/{ticker}")
def financials(ticker: str):
    return get_financials(ticker.upper())

@router.get("/news")
def news(query: str = "stock market"):
    return get_market_news(query)

@router.get("/india/indices")
def india_indices():
    return get_india_indices()

@router.get("/india/stocks")
def india_stocks():
    return get_india_top_stocks()

@router.get("/indicators/{ticker}")
def indicators(ticker: str, period: str = "6mo"):
    return get_indicators(ticker.upper(), period)
import sqlite3
import json
from datetime import datetime
from data.cache import get_connection as get_cache_conn

DB = "portfolio.db"

def get_conn():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker    TEXT NOT NULL,
            shares    REAL NOT NULL,
            buy_price REAL NOT NULL,
            buy_date  TEXT NOT NULL,
            notes     TEXT
        )
    """)
    conn.commit()
    return conn


def add_position(ticker: str, shares: float, buy_price: float, notes: str = "") -> dict:
    conn = get_conn()
    conn.execute(
        "INSERT INTO portfolio (ticker, shares, buy_price, buy_date, notes) VALUES (?, ?, ?, ?, ?)",
        (ticker.upper(), shares, buy_price, datetime.now().strftime("%Y-%m-%d"), notes)
    )
    conn.commit()
    conn.close()
    return {"status": "added", "ticker": ticker.upper(), "shares": shares, "buy_price": buy_price}


def remove_position(position_id: int) -> dict:
    conn = get_conn()
    conn.execute("DELETE FROM portfolio WHERE id = ?", (position_id,))
    conn.commit()
    conn.close()
    return {"status": "removed", "id": position_id}


def get_portfolio() -> list:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, ticker, shares, buy_price, buy_date, notes FROM portfolio"
    ).fetchall()
    conn.close()
    return [
        {
            "id": r[0], "ticker": r[1], "shares": r[2],
            "buy_price": r[3], "buy_date": r[4], "notes": r[5]
        }
        for r in rows
    ]


def get_portfolio_with_pnl() -> dict:
    import yfinance as yf
    positions = get_portfolio()
    if not positions:
        return {"positions": [], "summary": {"total_invested": 0, "current_value": 0, "total_pnl": 0, "total_pnl_pct": 0}}

    total_invested = 0
    current_value  = 0
    enriched = []

    for p in positions:
        try:
            stock = yf.Ticker(p["ticker"])
            info  = stock.info
            current_price = info.get("currentPrice") or info.get("regularMarketPrice") or p["buy_price"]
            invested      = p["shares"] * p["buy_price"]
            value         = p["shares"] * current_price
            pnl           = value - invested
            pnl_pct       = round((pnl / invested) * 100, 2) if invested else 0

            total_invested += invested
            current_value  += value

            enriched.append({
                **p,
                "current_price": round(current_price, 2),
                "invested":      round(invested, 2),
                "current_value": round(value, 2),
                "pnl":           round(pnl, 2),
                "pnl_pct":       pnl_pct,
            })
        except:
            enriched.append({**p, "current_price": p["buy_price"], "pnl": 0, "pnl_pct": 0})

    total_pnl     = current_value - total_invested
    total_pnl_pct = round((total_pnl / total_invested) * 100, 2) if total_invested else 0

    return {
        "positions": enriched,
        "summary": {
            "total_invested":  round(total_invested, 2),
            "current_value":   round(current_value, 2),
            "total_pnl":       round(total_pnl, 2),
            "total_pnl_pct":   total_pnl_pct,
        }
    }
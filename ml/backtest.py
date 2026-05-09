import yfinance as yf
import pandas as pd
import pandas_ta as ta
from data.cache import cache_get, cache_set


def run_backtest(
    ticker: str,
    strategy: str = "rsi",
    period: str = "2y",
    initial_capital: float = 100000,
) -> dict:
    cache_key = f"backtest:{ticker}:{strategy}:{period}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    try:
        stock = yf.Ticker(ticker)
        df    = stock.history(period=period, interval="1d")

        if df.empty or len(df) < 50:
            return {"error": "Not enough data"}

        df["rsi"]    = ta.rsi(df["Close"], length=14)
        df["sma_20"] = ta.sma(df["Close"], length=20)
        df["sma_50"] = ta.sma(df["Close"], length=50)

        macd = ta.macd(df["Close"], fast=12, slow=26, signal=9)
        if macd is not None:
            mc = [c for c in macd.columns if c.startswith("MACD_")][0]
            ms = [c for c in macd.columns if c.startswith("MACDs_")][0]
            df["macd"]        = macd[mc]
            df["macd_signal"] = macd[ms]

        df = df.dropna()

        # Generate signals based on strategy
        df["signal"] = 0
        if strategy == "rsi":
            df.loc[df["rsi"] < 30, "signal"] = 1   # BUY
            df.loc[df["rsi"] > 70, "signal"] = -1  # SELL
        elif strategy == "macd":
            df.loc[df["macd"] > df["macd_signal"], "signal"] = 1
            df.loc[df["macd"] < df["macd_signal"], "signal"] = -1
        elif strategy == "sma_cross":
            df.loc[df["sma_20"] > df["sma_50"], "signal"] = 1
            df.loc[df["sma_20"] < df["sma_50"], "signal"] = -1

        # Simulate trades
        capital    = initial_capital
        shares     = 0
        trades     = []
        equity     = []
        in_trade   = False
        entry_price = 0

        for i, row in df.iterrows():
            price = row["Close"]

            if row["signal"] == 1 and not in_trade:
                shares      = capital / price
                entry_price = price
                capital     = 0
                in_trade    = True
                trades.append({"date": str(i)[:10], "type": "BUY", "price": round(price, 2), "shares": round(shares, 4)})

            elif row["signal"] == -1 and in_trade:
                capital  = shares * price
                pnl      = round(capital - shares * entry_price, 2)
                pnl_pct  = round((price - entry_price) / entry_price * 100, 2)
                in_trade = False
                trades.append({"date": str(i)[:10], "type": "SELL", "price": round(price, 2), "pnl": pnl, "pnl_pct": pnl_pct})
                shares = 0

            current_value = capital + shares * price
            equity.append({"date": str(i)[:10], "value": round(current_value, 2)})

        # Close open position at end
        if in_trade:
            final_price = df["Close"].iloc[-1]
            capital     = shares * final_price

        final_value  = capital
        total_return = round((final_value - initial_capital) / initial_capital * 100, 2)

        # Buy and hold comparison
        bh_return = round(
            (df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0] * 100, 2
        )

        # Win rate
        sell_trades = [t for t in trades if t["type"] == "SELL"]
        wins        = [t for t in sell_trades if t.get("pnl", 0) > 0]
        win_rate    = round(len(wins) / len(sell_trades) * 100, 1) if sell_trades else 0

        result = {
            "ticker":          ticker,
            "strategy":        strategy,
            "period":          period,
            "initial_capital": initial_capital,
            "final_value":     round(final_value, 2),
            "total_return":    total_return,
            "bh_return":       bh_return,
            "total_trades":    len(sell_trades),
            "win_rate":        win_rate,
            "trades":          trades[-20:],
            "equity_curve":    equity,
        }

        cache_set(cache_key, result)
        return result

    except Exception as e:
        return {"error": str(e)}
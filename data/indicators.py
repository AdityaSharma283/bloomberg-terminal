import pandas as pd
import pandas_ta as ta
import yfinance as yf
from data.cache import cache_get, cache_set


def get_indicators(ticker: str, period: str = "6mo") -> dict:
    cache_key = f"indicators:{ticker}:{period}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    try:
        stock = yf.Ticker(ticker)
        interval = "1h" if period == "1mo" else "1d"
        df = stock.history(period=period, interval=interval)

        if df.empty:
            return {"error": f"No data found for {ticker}"}

        def clean(series):
            return [round(float(x), 4) if pd.notna(x) else None for x in series]

        result = {
            "dates":  df.index.strftime("%Y-%m-%d %H:%M" if interval == "1h" else "%Y-%m-%d").tolist(),
            "close":  clean(df["Close"]),
            "open":   clean(df["Open"]),
            "high":   clean(df["High"]),
            "low":    clean(df["Low"]),
            "volume": [int(x) for x in df["Volume"]],
            "rsi":         None,
            "macd":        None,
            "macd_signal": None,
            "macd_hist":   None,
            "bb_upper":    None,
            "bb_mid":      None,
            "bb_lower":    None,
            "ema_20":      None,
            "ema_50":      None,
            "ema_200":     None,
            "signals":     None,
        }

        # RSI — needs 14+ candles
        if len(df) >= 14:
            rsi = ta.rsi(df["Close"], length=14)
            if rsi is not None:
                result["rsi"] = clean(rsi)

        # MACD — needs 26+ candles
        if len(df) >= 26:
            macd = ta.macd(df["Close"], fast=12, slow=26, signal=9)
            if macd is not None:
                macd_col   = [c for c in macd.columns if c.startswith("MACD_")][0]
                signal_col = [c for c in macd.columns if c.startswith("MACDs_")][0]
                hist_col   = [c for c in macd.columns if c.startswith("MACDh_")][0]
                result["macd"]        = clean(macd[macd_col])
                result["macd_signal"] = clean(macd[signal_col])
                result["macd_hist"]   = clean(macd[hist_col])

        # Bollinger Bands — needs 20+ candles
        if len(df) >= 20:
            bbands = ta.bbands(df["Close"], length=20, std=2)
            if bbands is not None:
                bb_upper_col = [c for c in bbands.columns if "BBU" in c][0]
                bb_mid_col   = [c for c in bbands.columns if "BBM" in c][0]
                bb_lower_col = [c for c in bbands.columns if "BBL" in c][0]
                result["bb_upper"] = clean(bbands[bb_upper_col])
                result["bb_mid"]   = clean(bbands[bb_mid_col])
                result["bb_lower"] = clean(bbands[bb_lower_col])

        # EMAs
        if len(df) >= 20:
            ema20 = ta.ema(df["Close"], length=20)
            if ema20 is not None:
                result["ema_20"] = clean(ema20)

        if len(df) >= 50:
            ema50 = ta.ema(df["Close"], length=50)
            if ema50 is not None:
                result["ema_50"] = clean(ema50)

        if len(df) >= 200:
            ema200 = ta.ema(df["Close"], length=200)
            if ema200 is not None:
                result["ema_200"] = clean(ema200)

        # Signals — only compute if we have the data
        signals = {}

        if result["rsi"]:
            valid_rsi = [x for x in result["rsi"] if x is not None]
            if valid_rsi:
                latest_rsi = valid_rsi[-1]
                signals["rsi_value"]  = round(latest_rsi, 2)
                signals["rsi_signal"] = (
                    "OVERSOLD — potential buy zone"    if latest_rsi < 30 else
                    "OVERBOUGHT — potential sell zone" if latest_rsi > 70 else
                    "NEUTRAL — no extreme reading"
                )

        if result["macd"] and result["macd_signal"]:
            valid_macd = [x for x in result["macd"] if x is not None]
            valid_sig  = [x for x in result["macd_signal"] if x is not None]
            if valid_macd and valid_sig:
                latest_macd = valid_macd[-1]
                latest_sig  = valid_sig[-1]
                signals["macd_signal"] = (
                    "BULLISH — MACD above signal line" if latest_macd > latest_sig else
                    "BEARISH — MACD below signal line"
                )

        if result["bb_upper"] and result["bb_lower"]:
            valid_close = [x for x in result["close"] if x is not None]
            valid_bbu   = [x for x in result["bb_upper"] if x is not None]
            valid_bbl   = [x for x in result["bb_lower"] if x is not None]
            if valid_close and valid_bbu and valid_bbl:
                latest_close = valid_close[-1]
                latest_bbu   = valid_bbu[-1]
                latest_bbl   = valid_bbl[-1]
                signals["bb_signal"] = (
                    "Near upper band — overbought pressure" if latest_close >= latest_bbu * 0.98 else
                    "Near lower band — oversold pressure"   if latest_close <= latest_bbl * 1.02 else
                    "Inside bands — normal range"
                )

        result["signals"] = signals if signals else None
        cache_set(cache_key, result)
        return result

    except Exception as e:
        return {"error": str(e)}
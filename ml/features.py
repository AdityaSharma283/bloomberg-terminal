import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta


def build_features(ticker: str, period: str = "2y") -> pd.DataFrame:
    """
    Downloads historical data and engineers features for ML training.
    Returns a DataFrame with features + target column.
    """
    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval="1d")

    if df.empty or len(df) < 60:
        raise ValueError(f"Not enough data for {ticker}")

    # ── Price-based features ──────────────────────────────────────────
    df["return_1d"]  = df["Close"].pct_change(1)
    df["return_3d"]  = df["Close"].pct_change(3)
    df["return_5d"]  = df["Close"].pct_change(5)
    df["return_10d"] = df["Close"].pct_change(10)

    df["hl_ratio"]   = (df["High"] - df["Low"]) / df["Close"]
    df["oc_ratio"]   = (df["Close"] - df["Open"]) / df["Open"]

    # ── Volume features ───────────────────────────────────────────────
    df["vol_change"]  = df["Volume"].pct_change(1)
    df["vol_ma5"]     = df["Volume"].rolling(5).mean()
    df["vol_ratio"]   = df["Volume"] / df["vol_ma5"]

    # ── Moving averages ───────────────────────────────────────────────
    df["sma_10"]  = ta.sma(df["Close"], length=10)
    df["sma_20"]  = ta.sma(df["Close"], length=20)
    df["sma_50"]  = ta.sma(df["Close"], length=50)
    df["ema_20"]  = ta.ema(df["Close"], length=20)

    df["price_vs_sma20"] = (df["Close"] - df["sma_20"]) / df["sma_20"]
    df["price_vs_sma50"] = (df["Close"] - df["sma_50"]) / df["sma_50"]
    df["sma10_vs_sma20"] = (df["sma_10"] - df["sma_20"]) / df["sma_20"]

    # ── Momentum indicators ───────────────────────────────────────────
    df["rsi"]  = ta.rsi(df["Close"], length=14)
    df["rsi_prev"] = df["rsi"].shift(1)
    df["rsi_slope"] = df["rsi"] - df["rsi_prev"]

    macd = ta.macd(df["Close"], fast=12, slow=26, signal=9)
    if macd is not None:
        macd_col   = [c for c in macd.columns if c.startswith("MACD_")][0]
        signal_col = [c for c in macd.columns if c.startswith("MACDs_")][0]
        hist_col   = [c for c in macd.columns if c.startswith("MACDh_")][0]
        df["macd"]        = macd[macd_col]
        df["macd_signal"] = macd[signal_col]
        df["macd_hist"]   = macd[hist_col]
        df["macd_cross"]  = (df["macd"] > df["macd_signal"]).astype(int)

    # ── Volatility ────────────────────────────────────────────────────
    bbands = ta.bbands(df["Close"], length=20, std=2)
    if bbands is not None:
        bbu = [c for c in bbands.columns if "BBU" in c][0]
        bbm = [c for c in bbands.columns if "BBM" in c][0]
        bbl = [c for c in bbands.columns if "BBL" in c][0]
        df["bb_upper"] = bbands[bbu]
        df["bb_lower"] = bbands[bbl]
        df["bb_width"]  = (bbands[bbu] - bbands[bbl]) / bbands[bbm]
        df["bb_pos"]    = (df["Close"] - bbands[bbl]) / (bbands[bbu] - bbands[bbl])

    df["atr"] = ta.atr(df["High"], df["Low"], df["Close"], length=14)
    df["atr_ratio"] = df["atr"] / df["Close"]

    # ── Target variable ───────────────────────────────────────────────
    # 1 = BUY (price up >1% in next 5 days)
    # 2 = SELL (price down >1% in next 5 days)
    # 0 = HOLD (everything else)
    future_return = df["Close"].shift(-3) / df["Close"] - 1
    df["target"] = 0
    df.loc[future_return >  0.005, "target"] = 1
    df.loc[future_return < -0.005, "target"] = 2
    # Replace inf values with NaN then drop
    df = df.replace([float('inf'), float('-inf')], float('nan'))
    df = df.dropna()
    # ── Clean up ──────────────────────────────────────────────────────
    feature_cols = [
        "return_1d", "return_3d", "return_5d", "return_10d",
        "hl_ratio", "oc_ratio",
        "vol_change", "vol_ratio",
        "price_vs_sma20", "price_vs_sma50", "sma10_vs_sma20",
        "rsi", "rsi_slope",
        "macd_hist", "macd_cross",
        "bb_width", "bb_pos",
        "atr_ratio",
    ]

    df = df[feature_cols + ["target"]].dropna()
    return df
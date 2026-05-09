import numpy as np
import pandas as pd
from ml.features import build_features
from ml.model import load_model, train_model
from data.cache import cache_get, cache_set

LABEL_MAP = {0: "HOLD", 1: "BUY", 2: "SELL"}
COLOR_MAP  = {0: "#e0a020", 1: "#00cc66", 2: "#ff4444"}


def get_signal(ticker: str, force_retrain: bool = False) -> dict:
    """
    Returns ML signal for a ticker.
    Auto-trains if no model exists.
    """
    cache_key = f"ml_signal:{ticker}"
    if not force_retrain:
        cached = cache_get(cache_key)
        if cached:
            return cached

    # Load or train model
    model_data = load_model(ticker)
    if model_data is None or force_retrain:
        try:
            train_model(ticker)
            model_data = load_model(ticker)
        except Exception as e:
            return {
                "ticker": ticker,
                "signal": "UNAVAILABLE",
                "confidence": 0,
                "error": str(e),
            }

    if model_data is None:
        return {"ticker": ticker, "signal": "UNAVAILABLE", "confidence": 0}

    try:
        model       = model_data["model"]
        feature_cols = model_data["feature_cols"]
        accuracy    = model_data["accuracy"]

        # Build latest features
        df = build_features(ticker, period="1y")
        if df.empty:
            return {"ticker": ticker, "signal": "UNAVAILABLE", "confidence": 0}

        # Use last row as live input
        latest = df[feature_cols].iloc[-1].values.reshape(1, -1)

        # Predict
        pred_class = int(model.predict(latest)[0])
        pred_proba = model.predict_proba(latest)[0]
        confidence = round(float(pred_proba[pred_class]) * 100, 1)

        signal = LABEL_MAP[pred_class]
        color  = COLOR_MAP[pred_class]

        # Feature importance — top 5
        importance = model.feature_importances_
        top_features = sorted(
            zip(feature_cols, importance),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        result = {
            "ticker":       ticker,
            "signal":       signal,
            "confidence":   confidence,
            "color":        color,
            "model_accuracy": accuracy,
            "probabilities": {
                "BUY":  round(float(pred_proba[1]) * 100, 1),
                "HOLD": round(float(pred_proba[0]) * 100, 1),
                "SELL": round(float(pred_proba[2]) * 100, 1),
            },
            "top_features": [
                {"feature": f, "importance": round(float(i) * 100, 2)}
                for f, i in top_features
            ],
        }

        cache_set(cache_key, result)
        return result

    except Exception as e:
        return {"ticker": ticker, "signal": "UNAVAILABLE", "confidence": 0, "error": str(e)}
import os
import pickle
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder
from ml.features import build_features
from collections import Counter

MODEL_DIR = "ml/saved_models"
os.makedirs(MODEL_DIR, exist_ok=True)


def train_model(ticker: str) -> dict:
    """
    Trains an XGBoost model for a given ticker.
    Saves model to disk and returns performance metrics.
    """
    print(f"[ML] Training model for {ticker}...")

    df = build_features(ticker, period="5y")

    feature_cols = [c for c in df.columns if c != "target"]
    X = df[feature_cols].values
    y = df["target"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    class_counts = Counter(y_train)
    total = sum(class_counts.values())
    sample_weights = [total / (len(class_counts) * class_counts[label]) for label in y_train]

    model = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.1,
        eval_metric="mlogloss",
        random_state=42,
        verbosity=0,
    )

    model.fit(
        X_train, y_train,
        sample_weight=sample_weights,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)

    accuracy = round(report["accuracy"] * 100, 2)
    print(f"[ML] {ticker} model accuracy: {accuracy}%")

    # Save model + feature columns
    model_path = os.path.join(MODEL_DIR, f"{ticker.replace('.', '_')}.pkl")
    with open(model_path, "wb") as f:
        pickle.dump({
            "model": model,
            "feature_cols": feature_cols,
            "accuracy": accuracy,
            "report": report,
        }, f)

    print(f"[ML] Model saved → {model_path}")
    return {"ticker": ticker, "accuracy": accuracy, "report": report}


def load_model(ticker: str):
    """Loads a saved model from disk. Returns None if not found."""
    model_path = os.path.join(MODEL_DIR, f"{ticker.replace('.', '_')}.pkl")
    if not os.path.exists(model_path):
        return None
    with open(model_path, "rb") as f:
        return pickle.load(f)


def get_model_accuracy(ticker: str) -> float:
    """Returns saved model accuracy or 0 if not trained."""
    data = load_model(ticker)
    if data is None:
        return 0.0
    return data.get("accuracy", 0.0)
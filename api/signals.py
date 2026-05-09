from fastapi import APIRouter, BackgroundTasks
from ml.signals import get_signal
from ml.sentiment import get_ticker_sentiment
from ml.model import train_model

router = APIRouter()

@router.get("/signal/{ticker}")
def signal(ticker: str):
    return get_signal(ticker.upper())

@router.get("/signal/{ticker}/retrain")
def retrain(ticker: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(train_model, ticker.upper())
    return {"message": f"Retraining started for {ticker.upper()} in background"}

@router.get("/sentiment/{ticker}")
def sentiment(ticker: str):
    return get_ticker_sentiment(ticker.upper())
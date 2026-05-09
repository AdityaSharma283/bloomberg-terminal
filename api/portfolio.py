from fastapi import APIRouter
from pydantic import BaseModel
from data.portfolio import add_position, remove_position, get_portfolio_with_pnl
from data.screener import run_screener
from data.macro import get_macro_dashboard
from ml.backtest import run_backtest

router = APIRouter()

class PositionIn(BaseModel):
    ticker:    str
    shares:    float
    buy_price: float
    notes:     str = ""

@router.get("/portfolio")
def portfolio():
    return get_portfolio_with_pnl()

@router.post("/portfolio/add")
def add(pos: PositionIn):
    return add_position(pos.ticker, pos.shares, pos.buy_price, pos.notes)

@router.delete("/portfolio/{position_id}")
def remove(position_id: int):
    return remove_position(position_id)

@router.get("/screener")
def screener(
    min_pe: float = None, max_pe: float = None,
    min_mktcap: float = None,
    min_change: float = None, max_change: float = None,
):
    return run_screener(min_pe, max_pe, min_mktcap, min_change, max_change)

@router.get("/macro")
def macro():
    return get_macro_dashboard()

@router.get("/backtest/{ticker}")
def backtest(ticker: str, strategy: str = "rsi", period: str = "2y"):
    return run_backtest(ticker.upper(), strategy, period)
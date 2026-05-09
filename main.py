from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from api.quotes import router as quotes_router
from api.signals import router as signals_router
from api.portfolio import router as portfolio_router

app = FastAPI(title="Bloomberg Terminal", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(quotes_router, prefix="/api")
app.include_router(signals_router, prefix="/api")
app.include_router(portfolio_router, prefix="/api")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html")
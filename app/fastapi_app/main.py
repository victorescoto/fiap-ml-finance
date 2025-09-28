from fastapi import FastAPI, HTTPException, Query
from .schemas import SymbolsResponse, LatestResponse, Candle, PredictResponse
import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import List
import os

app = FastAPI(title="FIAP Fase 3 - Finance API", version="0.1.0")

SYMBOLS = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA"]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/symbols", response_model=SymbolsResponse)
def symbols():
    return SymbolsResponse(symbols=SYMBOLS)


@app.get("/latest", response_model=LatestResponse)
def latest(symbol: str, interval: str = "5m", limit: int = 120):
    if symbol not in SYMBOLS:
        raise HTTPException(status_code=400, detail="symbol not allowed")
    # Obter intraday do dia atual (yfinance limita histórico intraday)
    try:
        df = yf.download(
            tickers=symbol,
            period="1d",
            interval=interval,
            progress=False,
            prepost=False,
            threads=False,
        )
        if df.empty:
            raise ValueError("Empty dataframe")
        if "Datetime" in df.columns:
            df = df.rename_axis("Datetime").reset_index()
        else:
            df = df.reset_index()
        df = df.tail(limit)
        candles = [
            Candle(
                timestamp=row["Datetime"].isoformat(),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"]),
            )
            for _, row in df.iterrows()
        ]
        return LatestResponse(symbol=symbol, interval=interval, candles=candles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to fetch latest: {e}")


@app.post("/predict", response_model=PredictResponse)
def predict(symbol: str):
    if symbol not in SYMBOLS:
        raise HTTPException(status_code=400, detail="symbol not allowed")
    # MVP: placeholder até o treino diário publicar model.pkl no S3
    # Retornar 'hold' com prob 0.5 e timestamp; depois conectaremos ao modelo real.
    ts = datetime.utcnow().isoformat() + "Z"
    return PredictResponse(symbol=symbol, prob_up=0.5, signal="hold", asof=ts)

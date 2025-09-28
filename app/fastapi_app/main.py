from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .schemas import SymbolsResponse, LatestResponse, Candle, PredictResponse
import yfinance as yf
from datetime import datetime
from typing import List

app = FastAPI(title="FIAP Fase 3 - Finance API", version="0.1.0")

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

    # Carregar modelo do S3 se existir; cache /tmp em Lambda
    import os, joblib, boto3
    import pandas as pd
    import yfinance as yf
    from app.ml.features import add_basic_features
    from app.ml.model import FEATURES

    bucket = os.getenv("MODELS_BUCKET", "fiap-fase3-finance-models")
    key = f"models/{symbol}_daily_logreg.pkl"

    local_cache_dir = "/tmp/models"
    os.makedirs(local_cache_dir, exist_ok=True)
    local_path = os.path.join(local_cache_dir, f"{symbol}_daily_logreg.pkl")

    clf = None
    if os.path.exists(local_path):
        try:
            clf = joblib.load(local_path)
        except Exception:
            clf = None

    if clf is None:
        s3 = boto3.client("s3")
        try:
            s3.download_file(bucket, key, local_path)
            clf = joblib.load(local_path)
        except Exception:
            # Modelo não disponível ainda: fallback
            ts = datetime.utcnow().isoformat() + "Z"
            return PredictResponse(symbol=symbol, prob_up=0.5, signal="hold", asof=ts)

    # Inferência com último dia (diário)
    df = yf.download(
        tickers=symbol, period="2mo", interval="1d", progress=False, threads=False
    )
    if df.empty:
        raise HTTPException(
            status_code=500, detail="failed to fetch daily data for inference"
        )
    df = df.reset_index().rename(
        columns={
            "Date": "timestamp",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.rename(columns=str.lower)

    feats = add_basic_features(df)
    x = feats.iloc[[-1]][FEATURES]
    prob_up = float(getattr(clf, "predict_proba")(x)[0][1])
    signal = "buy" if prob_up >= 0.6 else ("sell" if prob_up <= 0.4 else "hold")
    ts = datetime.utcnow().isoformat() + "Z"
    return PredictResponse(symbol=symbol, prob_up=prob_up, signal=signal, asof=ts)

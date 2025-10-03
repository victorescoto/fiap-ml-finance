from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .schemas import SymbolsResponse, LatestResponse, Candle, PredictResponse
import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import List
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
load_dotenv()

# Configurações a partir do .env
API_TITLE = os.getenv("API_TITLE", "FIAP Fase 3 - Finance API")
API_VERSION = os.getenv("API_VERSION", "0.1.0")
SYMBOLS_ENV = os.getenv("SYMBOLS", "AAPL,MSFT,AMZN,GOOGL,META,NVDA,TSLA")
SYMBOLS = [s.strip() for s in SYMBOLS_ENV.split(",")]
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

app = FastAPI(title=API_TITLE, version=API_VERSION, debug=DEBUG)

# Configuração CORS
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        # Handle multi-index columns (yfinance sometimes returns multi-level columns)
        if isinstance(df.columns, pd.MultiIndex):
            # Flatten multi-index columns, keeping only the first level (OHLCV names)
            df.columns = [col[0] if col[1] == symbol else col[0] for col in df.columns]
        
        df = df.reset_index()
        df = df.tail(limit)
        
        # Determine the timestamp column name
        timestamp_col = None
        for col in df.columns:
            col_str = str(col).lower()
            if 'datetime' in col_str or 'date' in col_str or col_str == 'timestamp':
                timestamp_col = col
                break
        
        if timestamp_col is None:
            # Use the first column as timestamp
            timestamp_col = df.columns[0]
        
        candles = [
            Candle(
                timestamp=pd.to_datetime(row[timestamp_col]).isoformat(),
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
    
    # CORREÇÃO: Lidar com MultiIndex do yfinance
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
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


# Lambda handler para AWS Lambda
try:
    from mangum import Mangum
    lambda_handler = Mangum(app)
except ImportError:
    # Para desenvolvimento local
    lambda_handler = None

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


def fetch_from_s3(symbol: str, interval: str, limit: int = 120):
    """Try to fetch data from S3 first, fallback to yfinance"""
    print(f"=== STARTING S3 FETCH for {symbol} {interval} ===")
    
    try:
        print("Step 1: Importing boto3...")
        import boto3
        from pathlib import Path
        print("✓ boto3 imported successfully")
        
        print("Step 2: Creating S3 client...")
        s3 = boto3.client('s3')
        bucket = os.getenv('S3_RAW_BUCKET', 'fiap-fase3-finance-raw')
        print(f"✓ S3 client created, bucket: {bucket}")
        
        # S3 structure: /prices_1d/interval=1d/symbol=AAPL/ or /prices_1h/interval=1h/symbol=AAPL/
        prefix = f"/prices_{interval}/interval={interval}/symbol={symbol}/"
        print(f"Step 3: Using prefix: {prefix}")
        
        print("Step 4: Listing S3 objects...")
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=1000)
        print(f"✓ S3 list_objects_v2 completed")
        print(f"Response keys: {list(response.keys())}")
        
        if 'Contents' not in response:
            print(f"❌ No Contents in response - no objects found")
            return None
        
        contents = response['Contents']
        print(f"✓ Found {len(contents)} objects in S3")
        print(f"First 3 objects: {[obj['Key'] for obj in contents[:3]]}")
        
        # Download and process recent files
        temp_dir = Path("/tmp") / f"data_{symbol}_{interval}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        print(f"Step 5: Created temp dir: {temp_dir}")
        
        # Sort by last modified and get recent files
        max_files = 20 if interval == "1h" else 10
        files = sorted(contents, key=lambda x: x['LastModified'], reverse=True)[:max_files]
        print(f"Step 6: Processing {len(files)} recent files...")
        
        dfs = []
        for i, file_obj in enumerate(files):
            key = file_obj['Key']
            if key.endswith('.parquet'):
                try:
                    local_path = temp_dir / f"file_{i}.parquet"
                    print(f"  Downloading {key}...")
                    s3.download_file(bucket, key, str(local_path))
                    
                    df_temp = pd.read_parquet(local_path)
                    dfs.append(df_temp)
                    print(f"  ✓ Processed file with {len(df_temp)} rows")
                except Exception as e:
                    print(f"  ❌ Error processing file {key}: {e}")
                    continue
        
        if not dfs:
            print("❌ No data files processed successfully")
            return None
            
        # Combine and sort by timestamp
        print(f"Step 7: Combining {len(dfs)} dataframes...")
        df = pd.concat(dfs, ignore_index=True)
        
        # Ensure timestamp is datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Sort by timestamp and get the most recent data
        df = df.sort_values('timestamp').tail(limit)
        
        print(f"✓ S3 fetch completed: {len(df)} rows from {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        # Clean up temp files
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return df
        
    except Exception as e:
        print(f"❌ ERROR in fetch_from_s3: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None
            
        # Download a few recent files
        temp_dir = Path("/tmp") / f"data_{symbol}_{interval}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Sort by last modified and get recent files
        # For hourly data, get more files since they contain less data per file
        max_files = 20 if interval == "1h" else 10
        files = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)[:max_files]
        
        print(f"Found {len(files)} recent files in S3 for {symbol} {interval}")
        
        dfs = []
        for file_obj in files:
            key = file_obj['Key']
            if key.endswith('.parquet'):
                try:
                    local_path = temp_dir / Path(key).name
                    s3.download_file(bucket, key, str(local_path))
                    
                    df_temp = pd.read_parquet(local_path)
                    dfs.append(df_temp)
                except Exception as e:
                    print(f"Error processing file {key}: {e}")
                    continue
                
        if not dfs:
            return None
            
        # Combine and sort by timestamp
        df = pd.concat(dfs, ignore_index=True)
        
        # Ensure timestamp is datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Sort by timestamp and get the most recent data
        df = df.sort_values('timestamp').tail(limit)
        
        print(f"Loaded {len(df)} rows from S3 for {symbol} {interval}")
        print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        # Clean up temp files
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return df
        
    except Exception as e:
        print(f"Error fetching from S3: {e}")
        return None


@app.get("/latest", response_model=LatestResponse)
def latest(symbol: str, interval: str = "1h", limit: int = 120):
    if symbol not in SYMBOLS:
        raise HTTPException(status_code=400, detail="symbol not allowed")
    
    try:
        # Try S3 first, fallback to yfinance
        df = fetch_from_s3(symbol, interval, limit)
        
        if df is None or df.empty:
            print(f"Using yfinance fallback for {symbol} {interval}")
            # Fallback to yfinance with appropriate period
            period_map = {"1h": "1d", "1d": "30d"}
            period = period_map.get(interval, "30d")
            
            df = yf.download(
                tickers=symbol,
                period=period,
                interval=interval,
                progress=False,
                prepost=False,
                threads=False,
            )
            
            if df.empty:
                raise ValueError("Empty dataframe")
                
            # Handle multi-index columns (yfinance sometimes returns multi-level columns)
            if isinstance(df.columns, pd.MultiIndex):
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
                timestamp_col = df.columns[0]
            
            # Rename columns to match our S3 format
            column_mapping = {
                timestamp_col: 'timestamp',
                'Open': 'open',
                'High': 'high', 
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            }
            df = df.rename(columns=column_mapping)
        
        # Ensure we have the required columns
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        candles = [
            Candle(
                timestamp=pd.to_datetime(row['timestamp']).isoformat(),
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=float(row['volume']),
            )
            for _, row in df.iterrows()
        ]
        
        print(f"Returning {len(candles)} candles for {symbol} {interval}")
        return LatestResponse(symbol=symbol, interval=interval, candles=candles)
        
    except Exception as e:
        print(f"Error in latest endpoint: {e}")
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

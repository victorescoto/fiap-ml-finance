import argparse
import os
import pathlib
import pandas as pd
import yfinance as yf
import pyarrow as pa
import pyarrow.parquet as pq
import boto3
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()


def write_parquet_partitioned(
    df: pd.DataFrame, base_path: pathlib.Path, interval: str, symbol: str
):
    df = df.copy()
    
    # Achatar colunas MultiIndex se necessário - manter apenas o primeiro nível
    if isinstance(df.columns, pd.MultiIndex):
        # Para yfinance, queremos manter os nomes padrão (Open, High, Low, Close, Volume)
        new_columns = []
        for col in df.columns:
            if col[0] in ['Open', 'High', 'Low', 'Close', 'Volume']:
                new_columns.append(col[0].lower())
            else:
                new_columns.append(col[0] if col[0] else col[1])
        df.columns = new_columns
    
    # Garantir que timestamp é datetime
    timestamp_col = 'timestamp' if 'timestamp' in df.columns else [col for col in df.columns if 'timestamp' in col.lower()][0]
    if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
        df[timestamp_col] = pd.to_datetime(df[timestamp_col], utc=True)
    
    # Renomear para padrão se necessário
    if timestamp_col != 'timestamp':
        df = df.rename(columns={timestamp_col: 'timestamp'})
    
    # Renomear Date para timestamp se necessário
    if 'Date' in df.columns:
        df = df.rename(columns={'Date': 'timestamp'})
    
    df["year"] = df["timestamp"].dt.year
    df["month"] = df["timestamp"].dt.month
    
    # Converter para int para evitar problemas com PyArrow
    df["year"] = df["year"].astype(int)
    df["month"] = df["month"].astype(int)
    
    # Escrever particionado por ano/mês apenas
    pq.write_to_dataset(
        pa.Table.from_pandas(df),
        root_path=base_path / f"symbol={symbol}" / f"interval={interval}",
        partition_cols=["year", "month"],
        compression="snappy",
        use_dictionary=True,
    )
    
    print(f"✅ Written {len(df)} rows for {symbol} to {base_path}")
    return base_path / f"symbol={symbol}" / f"interval={interval}"


def copy_to_s3(local_path, s3_uri, progress_callback=None):
    """Copia dados locais para S3 com progresso"""
    if not s3_uri:
        return
    
    import subprocess
    import sys
    
    s3_bucket = s3_uri.replace("s3://", "").split("/")[0]
    s3_prefix = "/".join(s3_uri.replace("s3://", "").split("/")[1:])
    
    print(f"📤 Uploading to S3: {s3_uri}")
    
    # Usar AWS CLI com progresso
    cmd = [
        "aws", "s3", "sync", 
        str(local_path), 
        f"s3://{s3_bucket}/{s3_prefix}",
        "--only-show-errors"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ Successfully uploaded to {s3_uri}")
    else:
        print(f"❌ Upload failed: {result.stderr}")
        sys.exit(1)


def fetch_historical(symbol: str, period: str = "2y"):
    """Download dados históricos de 2 anos - usado apenas na inicialização"""
    print(f"📊 Downloading {period} historical data for {symbol}...")
    df = yf.download(
        tickers=symbol, period=period, interval="1d", progress=False, threads=False, auto_adjust=False
    )
    if df.empty:
        return pd.DataFrame()
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
    df["symbol"] = symbol
    df["interval"] = "1d"
    print(f"✅ Downloaded {len(df)} rows for {symbol}")
    return df[
        ["timestamp", "open", "high", "low", "close", "volume", "symbol", "interval"]
    ]


def main():
    ap = argparse.ArgumentParser(description="Initialize historical data (2 years) - run once or on-demand")
    
    # Usar variáveis de ambiente como padrão
    default_symbols = os.getenv("SYMBOLS", "AAPL,MSFT,AMZN,GOOGL,META,NVDA,TSLA")
    default_data_dir = os.getenv("DATA_DIR", "./data")
    
    ap.add_argument(
        "--symbols", default=default_symbols, help="comma separated list, e.g. AAPL,MSFT"
    )
    ap.add_argument("--out", default=default_data_dir, help="local output base path")
    ap.add_argument(
        "--to", default="", help="optional s3://bucket/prefix to copy after write"
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--period", default="2y", help="historical period (2y, 1y, 6mo, etc)")
    args = ap.parse_args()

    if args.dry_run:
        print("🚨 DRY RUN MODE - no files will be written")

    base_path = pathlib.Path(args.out) / "prices_1d"
    base_path.mkdir(parents=True, exist_ok=True)

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    written_paths = []
    
    print(f"🏗️ HISTORICAL INITIALIZATION - Downloading {args.period} data for {len(symbols)} symbols")
    
    # Download individual para cada símbolo (mais confiável)
    for i, sym in enumerate(symbols, 1):
        print(f"\n[{i}/{len(symbols)}] Processing {sym}...")
        df = fetch_historical(sym, args.period)
        if df.empty:
            print(f"⚠️ No data found for {sym}")
            continue
        
        if not args.dry_run:
            out = write_parquet_partitioned(df, base_path, "1d", sym)
            written_paths.append(out)
        else:
            print(f"📊 Would write {len(df)} rows for {sym}")

    total_files = sum(len(list(p.rglob("*.parquet"))) for p in written_paths if p.exists())
    print(f"\n✅ Historical initialization complete!")
    print(f"📊 Total symbols processed: {len(written_paths)}")
    print(f"📁 Total parquet files: {total_files}")

    # Upload para S3 se especificado
    if args.to and not args.dry_run:
        copy_to_s3(base_path, args.to)


def lambda_handler(event, context):
    """Handler para AWS Lambda"""
    import sys
    
    # Configurar argumentos baseado no evento Lambda
    symbols = event.get("symbols", os.getenv("SYMBOLS", "AAPL,MSFT,AMZN,GOOGL,META,NVDA,TSLA"))
    data_dir = "/tmp/data"  # Lambda temp directory
    s3_bucket = os.getenv("S3_BUCKET")
    s3_prefix = "data"
    period = event.get("period", "2y")
    
    if not s3_bucket:
        print("❌ S3_BUCKET environment variable not set")
        return {"statusCode": 500, "body": "S3_BUCKET not configured"}
    
    # Simular argumentos para main()
    sys.argv = [
        "ingest_historical.py",
        "--symbols", symbols,
        "--out", data_dir,
        "--to", f"s3://{s3_bucket}/{s3_prefix}",
        "--period", period
    ]
    
    try:
        main()
        return {
            "statusCode": 200, 
            "body": f"Historical data initialization complete for period {period}"
        }
    except Exception as e:
        print(f"❌ Error in historical initialization: {str(e)}")
        return {"statusCode": 500, "body": f"Error: {str(e)}"}


if __name__ == "__main__":
    main()
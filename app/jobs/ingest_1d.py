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
    df["day"] = df["timestamp"].dt.day
    
    # Converter para int para evitar problemas com PyArrow
    df["year"] = df["year"].astype(int)
    df["month"] = df["month"].astype(int)
    df["day"] = df["day"].astype(int)
    
    table = pa.Table.from_pandas(df)
    out = base_path / f"interval={interval}" / f"symbol={symbol}"
    out.mkdir(parents=True, exist_ok=True)
    pq.write_to_dataset(
        table,
        root_path=str(out),
        partition_cols=["year", "month", "day"],
        use_dictionary=True,
    )
    return out


def fetch_daily(symbol: str, period: str = "2y"):
    df = yf.download(
        tickers=symbol, period=period, interval="1d", progress=False, threads=False
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
    return df[
        ["timestamp", "open", "high", "low", "close", "volume", "symbol", "interval"]
    ]


def main():
    ap = argparse.ArgumentParser()
    
    # Usar variáveis de ambiente como padrão
    default_symbols = os.getenv("SYMBOLS", "AAPL,MSFT,AMZN,GOOGL,META,NVDA,TSLA")
    default_data_dir = os.getenv("DATA_DIR", "./data")
    default_s3_bucket = f"s3://{os.getenv('S3_RAW_BUCKET', '')}" if os.getenv("S3_RAW_BUCKET") else ""
    
    ap.add_argument(
        "--symbols", default=default_symbols, help="comma separated list, e.g. AAPL,MSFT"
    )
    ap.add_argument("--out", default=default_data_dir, help="local output base path")
    ap.add_argument(
        "--to", default=default_s3_bucket, help="optional s3://bucket/prefix to copy after write"
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    base_path = pathlib.Path(args.out) / "prices_1d"
    base_path.mkdir(parents=True, exist_ok=True)

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    written_paths = []
    for sym in symbols:
        df = fetch_daily(sym)
        if df.empty:
            continue
        out = write_parquet_partitioned(df, base_path, "1d", sym)
        written_paths.append(out)

    if args.to.startswith("s3://") and not args.dry_run:
        s3 = boto3.client("s3")
        bucket = args.to.replace("s3://", "").split("/")[0]
        prefix = "/".join(args.to.replace("s3://", "").split("/")[1:])
        for p in written_paths:
            for file in p.rglob("*.parquet"):
                key = "/".join(
                    [prefix, "prices_1d", str(file.relative_to((base_path)))]
                )
                s3.upload_file(str(file), bucket, key)


if __name__ == "__main__":
    main()

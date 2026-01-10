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
    timestamp_col = 'timestamp' if 'timestamp' in df.columns else [
        col for col in df.columns if 'timestamp' in col.lower()][0]
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

    table = pa.Table.from_pandas(df)
    out = base_path / f"interval={interval}" / f"symbol={symbol}"
    out.mkdir(parents=True, exist_ok=True)

    # Particionar apenas por ano/mês para reduzir número de arquivos
    pq.write_to_dataset(
        table,
        root_path=str(out),
        partition_cols=["year", "month"],  # Removido "day" para menos arquivos
        use_dictionary=True,
    )
    return out


def merge_incremental_data(new_df: pd.DataFrame, base_path: pathlib.Path, symbol: str):
    """Merge novos dados com dados existentes, removendo duplicatas"""
    if new_df.empty:
        return new_df

    # Tentar ler dados existentes
    existing_path = base_path / f"symbol={symbol}" / "interval=1d"

    if existing_path.exists():
        try:
            # Ler dados existentes dos últimos 30 dias para merge
            import glob
            parquet_files = glob.glob(
                str(existing_path / "**" / "*.parquet"), recursive=True)

            if parquet_files:
                # Ler apenas arquivos recentes para performance
                # últimos 10 arquivos
                recent_files = sorted(parquet_files)[-10:]
                existing_dfs = []

                for file in recent_files:
                    try:
                        df_existing = pd.read_parquet(file)
                        existing_dfs.append(df_existing)
                    except Exception as e:
                        print(f"⚠️ Warning reading {file}: {e}")
                        continue

                if existing_dfs:
                    existing_df = pd.concat(existing_dfs, ignore_index=True)

                    # Combine novos e existentes, removendo duplicatas
                    combined_df = pd.concat(
                        [existing_df, new_df], ignore_index=True)
                    combined_df = combined_df.drop_duplicates(
                        subset=['timestamp', 'symbol'], keep='last')
                    combined_df = combined_df.sort_values('timestamp')

                    print(
                        f"🔄 Merged {len(new_df)} new rows with {len(existing_df)} existing rows for {symbol}")
                    return combined_df
        except Exception as e:
            print(
                f"⚠️ Warning merging data for {symbol}: {e}, using new data only")

    print(f"📊 No existing data found for {symbol}, using new data only")
    return new_df


def fetch_daily_incremental(symbol: str, days: str = "2d"):
    """Download apenas últimos dias - usado para atualizações incrementais diárias"""
    print(f"📊 Downloading {days} incremental data for {symbol}...")
    df = yf.download(
        tickers=symbol, period=days, interval="1d", progress=False, threads=False, auto_adjust=False
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
    print(f"✅ Downloaded {len(df)} rows for {symbol} (incremental)")
    return df[
        ["timestamp", "open", "high", "low", "close", "volume", "symbol", "interval"]
    ]


def main():
    ap = argparse.ArgumentParser(
        description="Daily incremental data ingestion (2 days) - runs automatically")

    # Usar variáveis de ambiente como padrão
    default_symbols = os.getenv(
        "SYMBOLS", "AAPL,MSFT,AMZN,GOOGL,META,NVDA,TSLA")
    default_data_dir = os.getenv("DATA_DIR", "./data")

    ap.add_argument(
        "--symbols", default=default_symbols, help="comma separated list, e.g. AAPL,MSFT"
    )
    ap.add_argument("--out", default=default_data_dir,
                    help="local output base path")
    ap.add_argument(
        "--to", default="", help="optional s3://bucket/prefix to copy after write"
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    base_path = pathlib.Path(args.out) / "prices_1d"
    base_path.mkdir(parents=True, exist_ok=True)

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    written_paths = []

    print(f"🔄 INCREMENTAL DAILY UPDATE - Processing {len(symbols)} symbols")

    # Download incremental para cada símbolo (apenas últimos 2 dias)
    for i, sym in enumerate(symbols, 1):
        print(f"\n[{i}/{len(symbols)}] Processing {sym}...")
        df_new = fetch_daily_incremental(sym, "2d")
        if df_new.empty:
            print(f"⚠️ No new data found for {sym}")
            continue

        # Merge com dados existentes
        df_merged = merge_incremental_data(df_new, base_path, sym)

        if not args.dry_run:
            out = write_parquet_partitioned(df_merged, base_path, "1d", sym)
            written_paths.append(out)
        else:
            print(
                f"📊 Would write {len(df_merged)} rows for {sym} (incremental)")

    if args.to.startswith("s3://") and not args.dry_run:
        print(f"📤 Uploading files to S3: {args.to}")
        s3 = boto3.client("s3")
        bucket = args.to.replace("s3://", "").split("/")[0]
        prefix = "/".join(args.to.replace("s3://", "").split("/")[1:])

        # Coletar todos os arquivos primeiro
        all_files = []
        for p in written_paths:
            for file in p.rglob("*.parquet"):
                key = "/".join([prefix, "prices_1d",
                               str(file.relative_to((base_path)))])
                all_files.append((str(file), key))

        print(f"📊 Found {len(all_files)} files to upload")

        # Upload com progresso
        for i, (local_file, s3_key) in enumerate(all_files, 1):
            try:
                s3.upload_file(local_file, bucket, s3_key)
                # Progresso a cada 10 arquivos
                if i % 10 == 0 or i == len(all_files):
                    print(
                        f"📤 Uploaded {i}/{len(all_files)} files ({i/len(all_files)*100:.1f}%)")
            except Exception as e:
                print(f"❌ Error uploading {s3_key}: {e}")

        print(
            f"✅ Upload completed: {len(all_files)} files sent to s3://{bucket}/{prefix}")


def lambda_handler(event, context):
    """Handler para AWS Lambda"""
    import time
    from datetime import datetime

    start_time = time.time()

    print(f"🚀 Starting daily ingest job at {datetime.now()}")
    print(f"Event: {event}")
    print(f"Available memory: {context.memory_limit_in_mb} MB")
    print(f"Time remaining: {context.get_remaining_time_in_millis()} ms")

    # Verificar se é o job correto
    job_name = event.get("JOB_NAME", "ingest_1d")
    if job_name != "ingest_1d":
        print(f"⚠️ Skipping: This is for {job_name}, not ingest_1d")
        return {"statusCode": 200, "body": {"message": f"Skipped: {job_name}"}}

    # Configurar argumentos para o Lambda
    class Args:
        symbols = os.getenv(
            "SYMBOLS", "AAPL,MSFT,AMZN,GOOGL,META,NVDA,TSLA,DIS")
        out = "/tmp/data"  # Diretório temporário no Lambda
        to = f"s3://{os.getenv('S3_RAW_BUCKET', 'fiap-fase4-finance-raw')}"
        dry_run = False

    print(f"📦 S3 Bucket: {Args.to}")
    print(f"🎯 Symbols: {Args.symbols}")

    try:
        # Executar lógica principal
        base_path = pathlib.Path(Args.out) / "prices_1d"
        base_path.mkdir(parents=True, exist_ok=True)

        symbols = [s.strip() for s in Args.symbols.split(",") if s.strip()]
        written_paths = []

        # Download incremental para cada símbolo (apenas últimos 2 dias)
        for i, sym in enumerate(symbols, 1):
            print(f"\n[{i}/{len(symbols)}] Processing {sym}...")
            df_new = fetch_daily_incremental(sym, "2d")
            if df_new.empty:
                print(f"⚠️ No new data found for {sym}")
                continue

            # Merge com dados existentes
            df_merged = merge_incremental_data(df_new, base_path, sym)

            out = write_parquet_partitioned(df_merged, base_path, "1d", sym)
            written_paths.append(out)
            print(f"✅ Processed {sym}: {len(df_merged)} rows (incremental)")

        # Upload para S3
        if Args.to.startswith("s3://"):
            s3 = boto3.client("s3")
            bucket = Args.to.replace("s3://", "").split("/")[0]
            prefix = "/".join(Args.to.replace("s3://", "").split("/")[1:])
            for p in written_paths:
                for file in p.rglob("*.parquet"):
                    key = "/".join([prefix, "prices_1d",
                                   str(file.relative_to(base_path))])
                    s3.upload_file(str(file), bucket, key)

        execution_time = time.time() - start_time
        files_count = len(
            [f for p in written_paths for f in p.rglob("*.parquet")])

        print(f"✅ Job completed in {execution_time:.2f}s")
        print(
            f"📊 Processed {len(symbols)} symbols, uploaded {files_count} files")

        return {
            "statusCode": 200,
            "body": {
                "message": "Daily data ingestion completed successfully",
                "symbols": symbols,
                "files_uploaded": files_count,
                "execution_time": execution_time
            }
        }

    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = f"❌ Job failed after {execution_time:.2f}s: {str(e)}"
        print(error_msg)
        return {
            "statusCode": 500,
            "body": {
                "message": "Daily data ingestion failed",
                "error": str(e),
                "execution_time": execution_time
            }
        }


if __name__ == "__main__":
    main()

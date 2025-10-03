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
    
    # Renomear Datetime para timestamp se necessário
    if 'Datetime' in df.columns:
        df = df.rename(columns={'Datetime': 'timestamp'})
    
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
    
    # Particionar por ano/mês/dia para dados horários (mais granular que diários)
    pq.write_to_dataset(
        table,
        root_path=str(out),
        partition_cols=["year", "month", "day"],
        use_dictionary=True,
    )
    return out


def merge_incremental_hourly_data(new_df: pd.DataFrame, base_path: pathlib.Path, symbol: str):
    """Merge novos dados horários com dados existentes, removendo duplicatas"""
    if new_df.empty:
        return new_df
    
    # Tentar ler dados existentes
    existing_path = base_path / f"symbol={symbol}" / "interval=1h"
    
    if existing_path.exists():
        try:
            # Ler dados existentes dos últimos dias para merge
            import glob
            parquet_files = glob.glob(str(existing_path / "**" / "*.parquet"), recursive=True)
            
            if parquet_files:
                # Ler apenas arquivos recentes para performance (últimos 5)
                recent_files = sorted(parquet_files)[-5:]  
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
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                    combined_df = combined_df.drop_duplicates(subset=['timestamp', 'symbol'], keep='last')
                    combined_df = combined_df.sort_values('timestamp')
                    
                    print(f"🔄 Merged {len(new_df)} new rows with {len(existing_df)} existing rows for {symbol}")
                    return combined_df
        except Exception as e:
            print(f"⚠️ Warning merging hourly data for {symbol}: {e}, using new data only")
    
    print(f"📊 No existing hourly data found for {symbol}, using new data only")
    return new_df


def fetch_1h_incremental(symbol: str, hours: int = 12):
    """Download apenas últimas horas - usado para atualizações incrementais horárias"""
    print(f"📊 Downloading last {hours}h incremental hourly data for {symbol}...")
    
    # yfinance só aceita períodos fixos, usar 1d e filtrar
    df = yf.download(
        tickers=symbol, period="1d", interval="1h", progress=False, threads=False, auto_adjust=False
    )
    if df.empty:
        return pd.DataFrame()
    
    df = df.reset_index().rename(
        columns={
            "Datetime": "timestamp",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    
    # Filtrar apenas as últimas N horas
    if hours < 24:
        cutoff_time = df["timestamp"].max() - pd.Timedelta(hours=hours)
        df = df[df["timestamp"] > cutoff_time]
    
    df["symbol"] = symbol
    df["interval"] = "1h"
    print(f"✅ Downloaded {len(df)} rows for {symbol} (last {hours}h incremental)")
    return df[
        ["timestamp", "open", "high", "low", "close", "volume", "symbol", "interval"]
    ]


def fetch_1h_recent(symbol: str, period: str = "5d"):
    """Busca dados horários dos últimos dias"""
    df = yf.download(
        tickers=symbol, period=period, interval="1h", progress=False, threads=False, auto_adjust=False
    )
    if df.empty:
        return pd.DataFrame()
    df = df.reset_index().rename(
        columns={
            "Datetime": "timestamp",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )
    return df


def main():
    ap = argparse.ArgumentParser(description="Hourly incremental data ingestion (12 hours) - runs automatically")
    
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
    ap.add_argument("--period", default="5d", help="period for hourly data (1d, 5d, 1mo) - legacy mode")
    ap.add_argument("--hours", default=12, type=int, help="hours for incremental mode (6, 12, 24)")
    args = ap.parse_args()

    base_path = pathlib.Path(args.out) / "prices_1h"
    base_path.mkdir(parents=True, exist_ok=True)

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    written_paths = []
    
    print(f"🔄 INCREMENTAL HOURLY UPDATE - Processing {len(symbols)} symbols")
    
    # Download incremental para cada símbolo (apenas últimas 12 horas)
    for i, sym in enumerate(symbols, 1):
        print(f"\n[{i}/{len(symbols)}] Processing {sym}...")
        df_new = fetch_1h_incremental(sym, args.hours)
        if df_new.empty:
            print(f"⚠️ No new hourly data found for {sym}")
            continue
        
        # Merge com dados existentes
        df_merged = merge_incremental_hourly_data(df_new, base_path, sym)
        
        if not args.dry_run:
            out = write_parquet_partitioned(df_merged, base_path, "1h", sym)
            written_paths.append(out)
        else:
            print(f"📊 Would write {len(df_merged)} rows for {sym} (hourly incremental)")

    if args.to.startswith("s3://") and not args.dry_run:
        print(f"📤 Uploading hourly files to S3: {args.to}")
        s3 = boto3.client("s3")
        bucket = args.to.replace("s3://", "").split("/")[0]
        prefix = "/".join(args.to.replace("s3://", "").split("/")[1:])
        
        # Coletar todos os arquivos primeiro
        all_files = []
        for p in written_paths:
            for file in p.rglob("*.parquet"):
                key = "/".join([prefix, "prices_1h", str(file.relative_to((base_path)))])
                all_files.append((str(file), key))
        
        print(f"📊 Found {len(all_files)} hourly files to upload")
        
        # Upload com progresso
        for i, (local_file, s3_key) in enumerate(all_files, 1):
            try:
                s3.upload_file(local_file, bucket, s3_key)
                if i % 10 == 0 or i == len(all_files):  # Progresso a cada 10 arquivos
                    print(f"📤 Uploaded {i}/{len(all_files)} files ({i/len(all_files)*100:.1f}%)")
            except Exception as e:
                print(f"❌ Error uploading {s3_key}: {e}")
        
        print(f"✅ Incremental hourly upload completed: {len(all_files)} files sent to s3://{bucket}/{prefix}")


def lambda_handler(event, context):
    """Handler para AWS Lambda"""
    import time
    from datetime import datetime
    
    start_time = time.time()
    
    print(f"🚀 Starting hourly ingest job at {datetime.now()}")
    print(f"Event: {event}")
    print(f"Available memory: {context.memory_limit_in_mb} MB")
    print(f"Time remaining: {context.get_remaining_time_in_millis()} ms")
    
    # Verificar se é o job correto
    job_name = event.get("JOB_NAME", "ingest_1h")
    if job_name != "ingest_1h":
        print(f"⚠️ Skipping: This is for {job_name}, not ingest_1h")
        return {"statusCode": 200, "body": {"message": f"Skipped: {job_name}"}}
    
    # Configurar argumentos para o Lambda
    class Args:
        symbols = os.getenv("SYMBOLS", "AAPL,MSFT,AMZN,GOOGL,META,NVDA,TSLA")
        out = "/tmp/data"  # Diretório temporário no Lambda
        to = f"s3://{os.getenv('S3_RAW_BUCKET', 'fiap-fase3-finance-raw')}"
        dry_run = False
        hours = 12  # Incremental: últimas 12 horas
    
    print(f"📦 S3 Bucket: {Args.to}")
    print(f"🎯 Symbols: {Args.symbols}")
    print(f"⏰ Hours: {Args.hours} (incremental mode)")
    
    try:
        # Executar lógica principal
        base_path = pathlib.Path(Args.out) / "prices_1h"
        base_path.mkdir(parents=True, exist_ok=True)

        symbols = [s.strip() for s in Args.symbols.split(",") if s.strip()]
        written_paths = []
        
        # Download incremental para cada símbolo (apenas últimas 12 horas)
        for i, sym in enumerate(symbols, 1):
            print(f"\n[{i}/{len(symbols)}] Processing {sym}...")
            df_new = fetch_1h_incremental(sym, Args.hours)
            if df_new.empty:
                print(f"⚠️ No new hourly data found for {sym}")
                continue
            
            # Merge com dados existentes
            df_merged = merge_incremental_hourly_data(df_new, base_path, sym)
            
            out = write_parquet_partitioned(df_merged, base_path, "1h", sym)
            written_paths.append(out)
            print(f"✅ Processed {sym}: {len(df_merged)} rows (hourly incremental)")

        # Upload para S3
        if Args.to.startswith("s3://"):
            s3 = boto3.client("s3")
            bucket = Args.to.replace("s3://", "").split("/")[0]
            prefix = "/".join(Args.to.replace("s3://", "").split("/")[1:])
            
            all_files = []
            for p in written_paths:
                for file in p.rglob("*.parquet"):
                    key = "/".join([prefix, "prices_1h", str(file.relative_to(base_path))])
                    all_files.append((str(file), key))
            
            for local_file, s3_key in all_files:
                s3.upload_file(local_file, bucket, s3_key)
        
        execution_time = time.time() - start_time
        files_count = len([f for p in written_paths for f in p.rglob("*.parquet")])
        
        print(f"✅ Hourly job completed in {execution_time:.2f}s")
        print(f"📊 Processed {len(symbols)} symbols, uploaded {files_count} files")
        
        return {
            "statusCode": 200,
            "body": {
                "message": "Hourly data ingestion completed successfully",
                "symbols": symbols,
                "files_uploaded": files_count,
                "execution_time": execution_time,
                "hours": Args.hours
            }
        }
    
    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = f"❌ Hourly job failed after {execution_time:.2f}s: {str(e)}"
        print(error_msg)
        return {
            "statusCode": 500,
            "body": {
                "message": "Hourly data ingestion failed",
                "error": str(e),
                "execution_time": execution_time
            }
        }


if __name__ == "__main__":
    main()
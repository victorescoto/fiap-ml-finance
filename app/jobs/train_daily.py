import argparse
import pathlib
import json
import os
import pandas as pd
from dateutil.relativedelta import relativedelta
from datetime import datetime, timezone
from dotenv import load_dotenv
from app.ml.features import add_basic_features, make_label
from app.ml.model import train_classifier, evaluate, save_model

# Carregar variáveis de ambiente
load_dotenv()


def load_local_prices_1d(data_dir: str, months: int = 12) -> pd.DataFrame:
    base = pathlib.Path(data_dir) / "prices_1d"
    if not base.exists():
        return pd.DataFrame()
    files = list(base.rglob("*.parquet"))
    if not files:
        return pd.DataFrame()
    dfs = [pd.read_parquet(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    cutoff = datetime.now(timezone.utc) - relativedelta(months=months)
    df = df[df["timestamp"] >= cutoff]
    return df


def main():
    ap = argparse.ArgumentParser()
    
    # Usar variáveis de ambiente como padrão
    default_symbols = os.getenv("SYMBOLS", "AAPL,MSFT,AMZN,GOOGL,META,NVDA,TSLA")
    default_data_dir = os.getenv("DATA_DIR", "./data")
    default_models_dir = os.getenv("MODELS_DIR", "./models")
    default_train_period = int(os.getenv("ML_TRAIN_PERIOD", "12"))
    
    ap.add_argument("--symbols", default=default_symbols, help="comma separated list")
    ap.add_argument("--data", default=default_data_dir)
    ap.add_argument("--models", default=default_models_dir)
    ap.add_argument("--months", type=int, default=default_train_period)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    df = load_local_prices_1d(args.data, months=args.months)
    if df.empty:
        print("No data found. Run ingest_1d first.")
        return

    os.makedirs(args.models, exist_ok=True)
    report = {}
    for sym in symbols:
        d = df[df["symbol"] == sym].sort_values("timestamp").rename(columns=str.lower)
        if d.shape[0] < 200:
            continue
        d = add_basic_features(d)
        d = make_label(d)
        # simple split: last 90 days as test
        cutoff = d["timestamp"].max() - pd.Timedelta(days=90)
        train = d[d["timestamp"] <= cutoff]
        test = d[d["timestamp"] > cutoff]
        if train.empty or test.empty:
            continue
        clf = train_classifier(train)
        metrics = evaluate(clf, test)
        model_path = pathlib.Path(args.models) / f"{sym}_daily_logreg.pkl"
        if not args.dry_run:
            save_model(clf, str(model_path))
        report[sym] = {"metrics": metrics, "model_path": str(model_path)}

    rep_path = pathlib.Path(args.models) / "training_report.json"
    rep_path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


def lambda_handler(event, context):
    """Handler para AWS Lambda"""
    import boto3
    
    # Configurar argumentos para o Lambda
    class Args:
        symbols = os.getenv("SYMBOLS", "AAPL,MSFT,AMZN,GOOGL,META,NVDA,TSLA")
        data = "/tmp/data"  # Diretório temporário no Lambda
        models = "/tmp/models"
        months = int(os.getenv("ML_TRAIN_PERIOD", "12"))
        dry_run = False
    
    # Baixar dados do S3 para /tmp
    s3 = boto3.client("s3")
    bucket = os.getenv("S3_RAW_BUCKET", "fiap-fase3-raw")
    
    # Criar diretórios
    os.makedirs(Args.data, exist_ok=True)
    os.makedirs(Args.models, exist_ok=True)
    
    # Baixar arquivos parquet do S3
    try:
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket, Prefix="prices_1d/"):
            for obj in page.get('Contents', []):
                if obj['Key'].endswith('.parquet'):
                    local_path = pathlib.Path(Args.data) / obj['Key']
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    s3.download_file(bucket, obj['Key'], str(local_path))
    except Exception as e:
        return {
            "statusCode": 500,
            "body": {"error": f"Failed to download data from S3: {str(e)}"}
        }
    
    # Executar treinamento
    symbols = [s.strip() for s in Args.symbols.split(",") if s.strip()]
    df = load_local_prices_1d(Args.data, months=Args.months)
    if df.empty:
        return {
            "statusCode": 400,
            "body": {"error": "No data found for training"}
        }

    report = {}
    for sym in symbols:
        d = df[df["symbol"] == sym].sort_values("timestamp").rename(columns=str.lower)
        if d.shape[0] < 200:
            continue
        d = add_basic_features(d)
        d = make_label(d)
        cutoff = d["timestamp"].max() - pd.Timedelta(days=90)
        train = d[d["timestamp"] <= cutoff]
        test = d[d["timestamp"] > cutoff]
        if train.empty or test.empty:
            continue
        clf = train_classifier(train)
        metrics = evaluate(clf, test)
        model_path = pathlib.Path(Args.models) / f"{sym}_daily_logreg.pkl"
        save_model(clf, str(model_path))
        report[sym] = {"metrics": metrics, "model_path": str(model_path)}

    # Upload modelos para S3
    models_bucket = os.getenv("S3_MODELS_BUCKET", "fiap-fase3-models")
    for sym in report:
        model_path = pathlib.Path(Args.models) / f"{sym}_daily_logreg.pkl"
        if model_path.exists():
            s3.upload_file(str(model_path), models_bucket, f"daily/{sym}_daily_logreg.pkl")
    
    # Salvar relatório
    rep_path = pathlib.Path(Args.models) / "training_report.json"
    rep_path.write_text(json.dumps(report, indent=2))
    s3.upload_file(str(rep_path), models_bucket, "daily/training_report.json")
    
    return {
        "statusCode": 200,
        "body": {
            "message": "Model training completed successfully",
            "trained_models": list(report.keys()),
            "report": report
        }
    }


if __name__ == "__main__":
    main()

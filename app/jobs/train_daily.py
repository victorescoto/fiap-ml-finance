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


if __name__ == "__main__":
    main()

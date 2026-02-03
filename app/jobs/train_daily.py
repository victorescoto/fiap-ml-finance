import argparse
import pathlib
import json
import os
import pandas as pd
from dateutil.relativedelta import relativedelta
from datetime import datetime, timezone
from dotenv import load_dotenv
from app.ml.lstm_model import LSTMStockPredictor

# Carregar variáveis de ambiente
load_dotenv()


def main():
    ap = argparse.ArgumentParser()

    # Usar variáveis de ambiente como padrão
    default_symbols = os.getenv(
        "SYMBOLS", "AAPL,MSFT,AMZN,GOOGL,META,NVDA,TSLA,DIS")
    default_data_dir = os.getenv("DATA_DIR", "./data")
    default_models_dir = os.getenv("MODELS_DIR", "./models")
    default_train_period = int(
        os.getenv("ML_TRAIN_PERIOD", "24"))  # 2 anos para LSTM

    ap.add_argument("--symbols", default=default_symbols,
                    help="comma separated list")
    ap.add_argument("--data", default=default_data_dir)
    ap.add_argument("--models", default=default_models_dir)
    ap.add_argument("--months", type=int, default=default_train_period)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    os.makedirs(args.models, exist_ok=True)
    report = {}

    print(f"🚀 Iniciando treinamento diário de modelos LSTM...")
    print(f"📊 Símbolos: {', '.join(symbols)}")
    print(f"📅 Período de dados: {args.months} meses")

    for sym in symbols:
        print(f"\n🧠 Treinando modelo LSTM para {sym}...")

        try:
            # Criar predictor LSTM
            predictor = LSTMStockPredictor(symbol=sym)

            # Treinar modelo usando pipeline completo
            start_date = (
                datetime.now() - relativedelta(months=args.months)).strftime('%Y-%m-%d')
            results = predictor.full_pipeline(start_date=start_date)

            # Salvar modelo no diretório especificado
            model_key = f"lstm_{sym.lower()}"
            if not args.dry_run:
                predictor.save_model(
                    model_path=args.models,
                    model_name=model_key
                )

            print(f"✅ {sym} treinado com sucesso!")
            print(f"   - MAE: {results['metrics']['MAE']:.2f}")
            print(f"   - RMSE: {results['metrics']['RMSE']:.2f}")
            print(f"   - MAPE: {results['metrics']['MAPE']:.2f}%")

            report[sym] = {
                "model_type": "LSTM",
                "metrics": results['metrics'],
                "data_shape": results['data_shape'],
                "training_time": results.get('training_time', 0),
                "model_files": {
                    "model": f"{model_key}.keras",
                    "scaler": f"{model_key}_scaler.joblib",
                    "config": f"{model_key}_config.joblib"
                }
            }

        except Exception as e:
            print(f"❌ Erro no treinamento de {sym}: {str(e)}")
            report[sym] = {
                "model_type": "LSTM",
                "error": str(e),
                "status": "failed"
            }

    rep_path = pathlib.Path(args.models) / "lstm_training_report.json"
    if not args.dry_run:
        rep_path.write_text(json.dumps(report, indent=2))

    print(f"\n📊 Relatório de Treinamento LSTM:")
    print(json.dumps(report, indent=2))

    # Estatísticas finais
    successful = sum(1 for r in report.values() if 'error' not in r)
    failed = sum(1 for r in report.values() if 'error' in r)

    print(f"\n🎯 Resumo Final:")
    print(f"   ✅ Sucessos: {successful}")
    print(f"   ❌ Falhas: {failed}")
    print(f"   📁 Modelos salvos em: {args.models}")

    return report


def lambda_handler(event, context):
    """Handler para AWS Lambda - Treinamento LSTM diário"""
    import boto3

    # Configurar argumentos para o Lambda
    class Args:
        symbols = os.getenv(
            "SYMBOLS", "AAPL,MSFT,AMZN,GOOGL,META,NVDA,TSLA,DIS")
        data = "/tmp/data"  # Diretório temporário no Lambda
        models = "/tmp/models"
        months = int(os.getenv("ML_TRAIN_PERIOD", "24"))  # 2 anos para LSTM
        dry_run = False

    print(f"🚀 Iniciando job de treinamento LSTM diário...")
    print(f"📊 Símbolos: {Args.symbols}")

    # Configurar S3
    s3 = boto3.client("s3")

    # Criar diretórios
    os.makedirs(Args.data, exist_ok=True)
    os.makedirs(Args.models, exist_ok=True)

    try:
        # Executar treinamento usando LSTM
        symbols = [s.strip() for s in Args.symbols.split(",") if s.strip()]
        report = {}

        for sym in symbols:
            print(f"\n🧠 Treinando modelo LSTM para {sym}...")

            try:
                # Criar predictor LSTM (coleta dados automaticamente do yfinance)
                predictor = LSTMStockPredictor(symbol=sym)

                # Treinar modelo
                start_date = (
                    datetime.now() - relativedelta(months=Args.months)).strftime('%Y-%m-%d')
                results = predictor.full_pipeline(start_date=start_date)

                # Salvar modelo localmente
                model_key = f"lstm_{sym.lower()}"
                predictor.save_model(
                    model_path=Args.models,
                    model_name=model_key
                )

                print(f"✅ {sym} treinado com sucesso!")
                report[sym] = {
                    "model_type": "LSTM",
                    "status": "success",
                    "metrics": results['metrics'],
                    "data_shape": results['data_shape'],
                    "training_time": results.get('training_time', 0)
                }

            except Exception as e:
                print(f"❌ Erro no treinamento de {sym}: {str(e)}")
                report[sym] = {
                    "model_type": "LSTM",
                    "status": "failed",
                    "error": str(e)
                }

        # Upload modelos LSTM para S3
        models_bucket = os.getenv(
            "S3_MODELS_BUCKET", "fiap-fase4-finance-models")
        for sym in report:
            if report[sym].get('status') == 'success':
                model_key = f"lstm_{sym.lower()}"
                model_files = [
                    f"{model_key}.keras",
                    f"{model_key}_scaler.joblib",
                    f"{model_key}_config.joblib"
                ]

                for file_name in model_files:
                    local_path = pathlib.Path(Args.models) / file_name
                    if local_path.exists():
                        s3.upload_file(
                            str(local_path),
                            models_bucket,
                            f"daily/{file_name}"
                        )

        # Salvar relatório LSTM
        rep_path = pathlib.Path(Args.models) / "lstm_training_report.json"
        report_content = json.dumps(report, indent=2)
        rep_path.write_text(report_content)
        s3.upload_file(str(rep_path), models_bucket,
                       "daily/lstm_training_report.json")

        # Estatísticas finais
        successful = sum(1 for r in report.values()
                         if r.get('status') == 'success')
        failed = sum(1 for r in report.values() if r.get('status') == 'failed')

        print(f"\n🎯 Job concluído:")
        print(f"   ✅ Sucessos: {successful}")
        print(f"   ❌ Falhas: {failed}")

        return {
            "statusCode": 200,
            "body": {
                "message": "LSTM daily training job completed",
                "successful_models": successful,
                "failed_models": failed,
                "trained_models": list(report.keys()),
                "report": report
            }
        }

    except Exception as e:
        print(f"❌ Erro geral no job: {str(e)}")
        return {
            "statusCode": 500,
            "body": {"error": f"Training job failed: {str(e)}"}
        }


if __name__ == "__main__":
    main()

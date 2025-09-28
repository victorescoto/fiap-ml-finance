# FIAP Fase 3 — ML Finance (Serverless, Low-Cost)

Arquitetura aprovada: **Serverless (AWS) + S3 Data Lake + Glue/Athena + FastAPI (Lambda via Mangum)**  
Modelo: **Classificador Up/Down D+1 (diário)**  
Símbolos: AAPL, MSFT, AMZN, GOOGL, META, NVDA, TSLA  
Granularidade visual: **5m** (near-real-time para o dashboard estático)

## Visão Geral
- Ingestão (5m e 1d) com `yfinance` → Parquet particionado no S3.
- Treino diário (D+1): engenharia de atributos + LogisticRegression → `model.pkl` no S3.
- API (FastAPI) em Lambda (Mangum) para `/health`, `/symbols`, `/latest`, `/predict`.
- Dashboard estático (Plotly) em S3 + CloudFront, consumindo a API.
- Consultas ad hoc: Athena (Glue Data Catalog).

## Estrutura
```
infra/terraform/                 # IaC inicial (S3 buckets, Glue DB, Athena Workgroup)
app/
  fastapi_app/
    main.py                      # FastAPI + endpoints básicos (rodando local com Uvicorn)
    schemas.py
    deps.py
  jobs/
    ingest_1d.py                 # baixa candles diários e escreve Parquet (local/S3)
    ingest_5m.py                 # baixa candles 5m do dia e escreve Parquet (local/S3)
    train_daily.py               # treina classificador up/down D+1 e envia model.pkl p/ S3
  ml/
    features.py                  # geração de features
    model.py                     # treino/carregamento de modelo (sklearn)
dashboard/
  index.html                     # Plotly + fetch da API
  app.js
  styles.css
Makefile
pyproject.toml
```

## Requisitos locais
- Python 3.12+
- (Opcional) AWS CLI autenticado (`aws configure`)

## Comandos Rápidos
```bash
# 1) Instalar deps
make deps

# 2) Rodar API local (http://127.0.0.1:8000/docs)
make run-api

# 3) Fazer ingestões locais (escrevem em ./data/ por padrão)
make ingest-1d-local
make ingest-5m-local

# 4) Treinar local (salva ./models/model.pkl)
make train-local

# 5) Terraform (infra mínima: buckets + Glue DB + Athena WG)
make tf-init
make tf-apply
```

## Próximos Passos (MVP -> Serverless total)
1. Adicionar Lambdas (ingest 5m, ingest 1d, train daily, api) + EventBridge + API Gateway via Terraform.
2. Deploy da API (container/pip-layer) usando Mangum.
3. CloudFront + ACM para o site estático (`dashboard/`).

> Este repositório inicial roda 100% local para iteração rápida, e provisiona recursos base na AWS para o Data Lake e Athena.

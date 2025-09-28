# FIAP Fase 3 — ML Finance (Serverless, Low-Cost)

Sistema de análise financeira e predição de ações usando Machine Learning com arquitetura serverless na AWS.

## 📈 Sobre o Projeto

Este projeto implementa uma solução completa de análise financeira que:
- **Coleta dados** de ações em tempo real via Yahoo Finance
- **Processa e armazena** dados em Data Lake (S3)
- **Treina modelos ML** para predição de movimento de preços (Up/Down D+1)
- **Expõe API REST** para consultas e predições
- **Fornece dashboard** interativo para visualização

**Símbolos analisados:** AAPL, MSFT, AMZN, GOOGL, META, NVDA, TSLA

## 🏗️ Arquitetura

- **Backend:** FastAPI + Python
- **ML:** scikit-learn (LogisticRegression para classificação Up/Down)
- **Data Lake:** AWS S3 (Parquet particionado)
- **Consultas:** AWS Athena + Glue Data Catalog
- **API:** FastAPI com CORS habilitado
- **Frontend:** Dashboard HTML/JavaScript com Plotly
- **Deploy:** AWS Lambda via Mangum (serverless)
- **IaC:** Terraform

## 📁 Estrutura do Projeto

```
├── app/
│   ├── fastapi_app/           # API REST
│   │   ├── main.py           # FastAPI app com CORS
│   │   ├── schemas.py        # Modelos Pydantic
│   │   └── deps.py           # Dependências
│   ├── jobs/                 # Jobs de processamento
│   │   ├── ingest_1d.py      # Ingestão dados diários
│   │   ├── ingest_5m.py      # Ingestão dados 5min
│   │   └── train_daily.py    # Treinamento modelo ML
│   └── ml/                   # Módulos ML
│       ├── features.py       # Engenharia de features
│       └── model.py          # Modelo ML
├── dashboard/                # Frontend
│   ├── index.html           # Dashboard principal
│   ├── app.js               # Lógica JavaScript
│   └── styles.css           # Estilos
├── infra/terraform/         # Infraestrutura como código
│   ├── main.tf              # Recursos AWS principais
│   ├── providers.tf         # Providers Terraform
│   └── variables.tf         # Variáveis
├── Makefile                 # Scripts de automação
└── pyproject.toml          # Configuração Python moderna
```

## 🚀 Como Rodar

### Pré-requisitos

- **Python 3.8+** 
- **uv** (gerenciador de pacotes Python rápido)
- **AWS CLI** configurado (opcional, para deploy)

### Instalação do uv

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# ou via pip
pip install uv
```

### Setup do Projeto

```bash
# 1. Clone o repositório
git clone <repo-url>
cd fiap-fase3-ml-finance

# 2. Instale dependências (usa uv + pyproject.toml)
make deps

# 3. Execute a API localmente
make run-api
```

A API estará disponível em: **http://127.0.0.1:8000**
- Documentação interativa: **http://127.0.0.1:8000/docs**
- OpenAPI Schema: **http://127.0.0.1:8000/openapi.json**

## 📋 Comandos Principais

| Comando | Descrição |
|---------|-----------|
| `make deps` | Instala dependências usando uv |
| `make run-api` | Executa API FastAPI em modo desenvolvimento |
| `make ingest-1d-local` | Coleta dados diários (armazena em ./data) |
| `make ingest-5m-local` | Coleta dados 5min (armazena em ./data) |
| `make train-local` | Treina modelo ML (salva em ./models) |
| `make tf-init` | Inicializa Terraform |
| `make tf-apply` | Aplica infraestrutura AWS |
| `make tf-destroy` | Remove infraestrutura AWS |
| `make fmt` | Formata código Terraform |

## 🔌 Endpoints da API

### Saúde da API
```bash
GET /health
# Retorna: {"status": "ok"}
```

### Símbolos Disponíveis
```bash
GET /symbols
# Retorna: {"symbols": ["AAPL", "MSFT", ...]}
```

### Dados Mais Recentes
```bash
GET /latest?symbol=AAPL&interval=5m&limit=120
# Retorna: dados OHLCV dos últimos períodos
```

### Predição ML
```bash
POST /predict
Content-Type: application/json
{"symbol": "AAPL"}
# Retorna: {"symbol": "AAPL", "prob_up": 0.65, "signal": "buy", "asof": "2025-09-28T..."}
```

## 🧠 Machine Learning

O sistema implementa um **classificador binário** que prediz se o preço de uma ação vai subir ou descer no próximo dia (D+1).

**Features utilizadas:**
- Médias móveis (SMA)
- RSI (Relative Strength Index)  
- Bollinger Bands
- Volume médio
- Retornos históricos

**Modelo:** LogisticRegression (scikit-learn)
**Output:** Probabilidade de alta + sinal (buy/sell/hold)

## 📊 Dashboard

O dashboard fornece visualizações interativas:
- **Gráficos de candlestick** com dados em tempo real
- **Indicadores técnicos** (RSI, Bollinger Bands)
- **Predições ML** com probabilidades
- **Comparação entre símbolos**

Acesse o dashboard abrindo `dashboard/index.html` no navegador (certifique-se que a API esteja rodando).

## ☁️ Deploy AWS

### Infraestrutura Base
```bash
# Inicializa Terraform
make tf-init

# Provisiona recursos AWS (S3, Glue, Athena)
make tf-apply
```

**Recursos criados:**
- S3 buckets (raw data, processed data, models)
- Glue Data Catalog
- Athena Workgroup
- IAM roles e policies

### Variáveis de Ambiente

Configurar no arquivo `.env` ou variáveis de ambiente:
```bash
AWS_REGION=us-east-1
PREFIX=fiap-fase3
SYMBOLS=AAPL,MSFT,AMZN,GOOGL,META,NVDA,TSLA
```

## 🔧 Desenvolvimento

### Tecnologias Utilizadas

- **Python**: FastAPI, scikit-learn, pandas, yfinance
- **Frontend**: HTML5, JavaScript ES6, Plotly.js
- **ML**: LogisticRegression, feature engineering
- **AWS**: S3, Lambda, Athena, Glue, CloudFront
- **IaC**: Terraform
- **Package Manager**: uv (moderno e rápido)

### Estrutura de Dados

**Formato de armazenamento:** Parquet (otimizado para analytics)
**Particionamento:** Por símbolo e data
**Schema:** OHLCV + timestamp + features derivadas

## 📈 Próximos Passos

1. **Serverless Total**: Migrar jobs para AWS Lambda
2. **CI/CD**: GitHub Actions para deploy automatizado  
3. **Monitoramento**: CloudWatch + alertas
4. **Cache**: Redis para predições frequentes
5. **ML Avançado**: Modelos LSTM para séries temporais
6. **Real-time**: Streaming com Kinesis Data Streams

## 📄 Licença

Este projeto é parte do curso de Pós-graduação FIAP - Fase 3.

---
🚀 **Desenvolvido com uv + FastAPI + AWS**

# FIAP ML Finance - Sistema de Análise e Predição de Ações

[![🚀 Status](https://img.shields.io/badge/Status-Production-success)](https://github.com/victorescoto/fiap-ml-finance)
[![⚡ Serverless](https://img.shields.io/badge/AWS-Serverless-orange)](https://aws.amazon.com/lambda/)
[![🤖 ML Pipeline](https://img.shields.io/badge/ML-Automated-blue)](https://scikit-learn.org/)
[![🔒 Security](https://img.shields.io/badge/Security-Audited-green)](./SECURITY.md)

Sistema completo de análise financeira e predição de ações usando Machine Learning com arquitetura serverless na AWS. Coleta, processa e analisa dados financeiros em tempo real, fornecendo predições de movimento de preços através de uma API REST e dashboard interativo.

## 📊 Visão Geral

**FIAP ML Finance** é uma plataforma serverless que combina engenharia de dados, machine learning e visualização para análise de mercado financeiro:

### 🎯 Funcionalidades Principais

- **Coleta Automatizada**: Ingestão de dados financeiros com jobs agendados
- **Data Lake**: Armazenamento otimizado em S3 com particionamento inteligente
- **Machine Learning**: Modelos preditivos para movimento de preços (Up/Down)
- **API REST**: Endpoints para dados históricos e predições ML
- **Dashboard Interativo**: Visualizações em tempo real com gráficos candlestick
- **Pipeline Automatizado**: Jobs de ingestão, processamento e treinamento

### 📈 Símbolos Analisados

**AAPL**, **MSFT**, **AMZN**, **GOOGL**, **META**, **NVDA**, **TSLA**

### ⚡ Performance Otimizada

- **Ingestão incremental**: Processa apenas dados novos (99.7% menos dados)
- **Cache inteligente**: S3 como camada de cache para API
- **CDN global**: CloudFront para baixa latência
- **Arquitetura serverless**: Auto-scaling e alta disponibilidade

## 🏗️ Arquitetura do Sistema

### 🎯 Visão da Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Processing    │    │   Presentation  │
│                 │    │                 │    │                 │
│  yFinance API   │───▶│  Lambda Jobs    │───▶│   S3 + API      │───▶ Dashboard
│  Market Data    │    │  EventBridge    │    │   CloudFront    │    (Users)
│                 │    │  S3 Data Lake   │    │   API Gateway   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 🔧 Componentes Técnicos

#### **Data Pipeline**

- **EventBridge**: Orquestração de jobs automatizados
  - Ingestão diária (00:05 UTC) - dados incrementais
  - Ingestão horária (a cada hora) - dados recentes
  - Treinamento ML (00:30 UTC) - modelos atualizados
- **S3 Data Lake**: Armazenamento Parquet particionado por símbolo/data
- **Athena + Glue**: Consultas SQL otimizadas e catalogação de schemas

#### **API & Backend**

- **AWS Lambda**: Compute serverless para API e jobs
- **FastAPI + Mangum**: Framework web moderno com adapter para Lambda
- **API Gateway**: Exposição REST com CORS e rate limiting
- **ECR**: Registry para imagens Docker customizadas

#### **Machine Learning**

- **scikit-learn**: Modelos de classificação (LogisticRegression)
- **Feature Engineering**: Indicadores técnicos (RSI, Bollinger Bands, SMA)
- **Predições**: Probabilidade de movimento de preços (Up/Down D+1)

#### **Frontend & CDN**

- **S3 Static Hosting**: Hospedagem de arquivos estáticos
- **CloudFront**: CDN global para baixa latência
- **Plotly.js**: Gráficos financeiros interativos (candlestick)
- **Tailwind CSS**: Design system moderno e responsivo

#### **DevOps & IaC**

- **Terraform**: Infrastructure as Code (35+ recursos AWS)
- **Docker**: Containerização para ambientes Lambda
- **Make**: Automação de builds e deploys

## 📁 Estrutura do Projeto

```
├── app/
│   ├── fastapi_app/           # API REST
│   │   ├── main.py           # FastAPI app + endpoints
│   │   ├── schemas.py        # Modelos Pydantic
│   │   └── deps.py           # Dependências
│   ├── jobs/                 # Pipeline de dados
│   │   ├── ingest_1d.py      # Ingestão diária incremental
│   │   ├── ingest_1h.py      # Ingestão horária incremental
│   │   └── train_daily.py    # Treinamento automático ML
│   ├── ml/                   # Módulos Machine Learning
│   │   ├── features.py       # Feature engineering
│   │   └── model.py          # Modelos preditivos
│   └── lambda_job_handler.py # Dispatcher de jobs
├── dashboard/                # Frontend
│   ├── index.html           # Interface principal
│   ├── app.js               # Lógica JavaScript
│   ├── styles.css           # Estilos Tailwind
│   └── config.js            # Configuração (não versionado)
├── infra/terraform/         # Infrastructure as Code
│   ├── main.tf              # Recursos AWS principais
│   ├── jobs.tf              # EventBridge + Lambda jobs
│   └── variables.tf         # Configurações
├── Dockerfile.api           # Container API Lambda
├── Dockerfile.job           # Container jobs Lambda
├── Makefile                 # Automação de tarefas
└── pyproject.toml          # Configuração Python
```

## 🚀 Performance e Otimizações

### ⚡ Estratégia de Ingestão Inteligente

O sistema implementa uma abordagem híbrida que combina **dados históricos pré-carregados** com **atualizações incrementais**, resultando em alta performance:

| Métrica                   | Processamento Tradicional | Sistema Otimizado | Economia  |
| ------------------------- | ------------------------- | ----------------- | --------- |
| **Dados processados/dia** | 8,393 rows                | 28 rows           | **99.7%** |
| **Tempo de execução**     | ~120-180s                 | ~10-15s           | **92%**   |
| **Largura de banda**      | ~1.2MB/dia                | ~4KB/dia          | **99.7%** |
| **Uso Lambda mensal**     | 150min                    | 7.5min            | **95%**   |
| **Custo operacional**     | Alto                      | Otimizado         | **~95%**  |

### 🔄 Fluxo de Dados

#### **Inicialização (Uma vez)**

1. **Dados históricos diários**: 2 anos de dados OHLCV
2. **Dados históricos horários**: 30 dias de dados detalhados
3. **Armazenamento**: S3 com particionamento otimizado

#### **Operação Contínua (Automatizada)**

1. **Jobs incrementais**: Coletam apenas dados novos
2. **Merge inteligente**: Combinam com dados existentes sem duplicação
3. **Cache API**: S3 funciona como cache para consultas rápidas

### 📊 Benefícios da Arquitetura

- **Escalabilidade**: Auto-scaling nativo do Lambda
- **Disponibilidade**: Multi-AZ através da AWS
- **Custo**: Pay-per-use, sem recursos ociosos
- **Manutenção**: Zero servidor para gerenciar

## 🛠️ Desenvolvimento

### 🚀 Quick Start

```bash
# 1. Setup inicial
git clone <repo-url>
cd fiap-fase3-ml-finance
make deps

# 2. Configuração
cp dashboard/config.example.js dashboard/config.js
# Editar config.js com URLs apropriadas

# 3. Desenvolvimento local
make run-api
# API disponível em http://localhost:8000
```

### 📋 Comandos Principais

#### **Desenvolvimento**

```bash
make deps           # Instalar dependências Python
make run-api        # Executar API local (dev)
make train-local    # Treinar modelos ML localmente
```

#### **Deploy & Infraestrutura**

```bash
make tf-init        # Inicializar Terraform
make tf-apply       # Provisionar infraestrutura AWS
make deploy         # Deploy completo (infra + aplicação)
make tf-destroy     # Remover infraestrutura
```

#### **Dashboard**

```bash
make dashboard-deploy         # Deploy completo do dashboard
make dashboard-status         # Verificar status
./deploy-dashboard.sh full    # Script avançado de deploy
```

#### **Data Pipeline (Opcional)**

```bash
# Inicializações (uma vez)
make ingest-historical-s3       # Carregar 2 anos de dados diários
make ingest-hourly-historical-s3 # Carregar 30 dias de dados horários

# Jobs incrementais (automáticos em produção)
make ingest-1d-s3              # Dados diários incrementais
make ingest-1h-s3              # Dados horários incrementais
```

### 🔧 Pré-requisitos

- **Python 3.11+**
- **uv** (gerenciador de pacotes Python)
- **Docker** (para builds de produção)
- **AWS CLI** configurado com credenciais
- **Terraform** (para infraestrutura)
- **Make** (para automação)

#### Instalação do uv

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# ou via pip
pip install uv
```

## 🔌 API REST

### 📋 Endpoints Disponíveis

#### **Health Check**

```http
GET /health
```

**Resposta**: `{"status": "ok"}`

#### **Símbolos Suportados**

```http
GET /symbols
```

**Resposta**: `{"symbols": ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA"]}`

#### **Dados Históricos**

```http
GET /latest?symbol={SYMBOL}&interval={INTERVAL}&limit={LIMIT}
```

**Parâmetros**:

- `symbol`: Código da ação (ex: AAPL)
- `interval`: Período (`1h` para horário, `1d` para diário)
- `limit`: Número de períodos (padrão: 120)

**Resposta**:

```json
{
  "symbol": "AAPL",
  "interval": "1h",
  "candles": [
    {
      "timestamp": "2025-10-07T15:30:00+00:00",
      "open": 227.5,
      "high": 228.75,
      "low": 227.1,
      "close": 228.2,
      "volume": 1247600
    }
  ]
}
```

#### **Predições Machine Learning**

```http
POST /predict
Content-Type: application/json

{"symbol": "AAPL"}
```

**Resposta**:

```json
{
  "symbol": "AAPL",
  "prob_up": 0.67,
  "signal": "buy",
  "confidence": "high",
  "asof": "2025-10-07T20:00:00Z"
}
```

### 🌐 URLs de Acesso

- **Desenvolvimento**: `http://localhost:8000`
- **Produção**: Via API Gateway (URL fornecida após deploy)

## 🧠 Machine Learning

### 🎯 Modelo Preditivo

O sistema utiliza **classificação binária** para predizer movimento de preços no próximo dia (D+1), respondendo a pergunta: _"O preço vai subir ou descer amanhã?"_

### 📊 Features de Entrada

#### **Indicadores Técnicos**

- **SMA (Simple Moving Average)**: Médias móveis de 5, 10, 20 períodos
- **RSI (Relative Strength Index)**: Força relativa de compra/venda
- **Bollinger Bands**: Bandas de volatilidade (superior, inferior, média)
- **Volume Profile**: Análise de volume transacionado

#### **Features Derivadas**

- **Retornos**: Variações percentuais históricas
- **Volatilidade**: Desvio padrão dos retornos
- **Momentum**: Taxa de mudança de preços
- **Price Position**: Posição relativa às bandas de Bollinger

### 🤖 Algoritmo e Treinamento

**Modelo**: `LogisticRegression` (scikit-learn)

- **Tipo**: Classificação binária supervisionada
- **Target**: Movimento do preço (Up=1, Down=0)
- **Treinamento**: Diário automático com dados históricos
- **Validação**: Cross-validation temporal

### 📈 Output e Sinais

**Predição Retornada**:

```json
{
  "symbol": "AAPL",
  "prob_up": 0.73, // Probabilidade de alta (0-1)
  "signal": "buy", // Sinal: buy/sell/hold
  "confidence": "high", // Confiança: low/medium/high
  "asof": "2025-10-07T20:00:00Z"
}
```

**Lógica de Sinais**:

- `prob_up > 0.7`: **BUY** (alta confiança)
- `prob_up < 0.3`: **SELL** (alta confiança)
- `0.3 ≤ prob_up ≤ 0.7`: **HOLD** (incerteza)

## 📊 Dashboard Interativo

### 🎨 Interface de Usuário

Dashboard moderno e responsivo para análise técnica e visualização de predições ML:

#### **Funcionalidades Principais**

- **Gráficos Candlestick**: Visualização OHLCV com Plotly.js
- **Indicadores Técnicos**: RSI, Bollinger Bands, médias móveis
- **Predições ML**: Sinais de compra/venda com probabilidades
- **Seleção de Símbolos**: Dropdown com auto-atualização
- **Intervalos Temporais**: Visualização horária e diária
- **Design Responsivo**: Otimizado para desktop e mobile

#### **Tecnologias de Frontend**

- **HTML5 + JavaScript ES6**: Base moderna
- **Tailwind CSS**: Framework utility-first
- **Plotly.js**: Gráficos financeiros interativos
- **Lucide Icons**: Ícones SVG limpos

### 🌐 Acesso ao Dashboard

#### **Desenvolvimento**

```bash
# Executar API local
make run-api

# Abrir dashboard/index.html no navegador
# API deve estar rodando em localhost:8000
```

#### **Produção**

- **CDN**: CloudFront (URL fornecida após deploy)
- **Performance**: Cache global com baixa latência
- **HTTPS**: Certificado SSL automático

### ⚙️ Configuração

```javascript
// dashboard/config.js
window.API_BASE = 'https://sua-api.execute-api.region.amazonaws.com'
window.ENV = 'production'
window.DEBUG = false
```

> 📝 **Nota**: O arquivo `config.js` é específico do ambiente e não é versionado

## ☁️ Deploy na AWS

### 🚀 Infraestrutura Serverless

O sistema provisiona **35+ recursos AWS** automaticamente via Terraform:

#### **Recursos Principais**

| Serviço           | Componente         | Propósito                    |
| ----------------- | ------------------ | ---------------------------- |
| **Lambda**        | API + Jobs         | Compute serverless           |
| **API Gateway**   | REST endpoints     | Exposição pública da API     |
| **S3**            | 4 buckets          | Data lake + hosting + models |
| **CloudFront**    | CDN global         | Distribuição do dashboard    |
| **EventBridge**   | Jobs agendados     | Automação do pipeline        |
| **ECR**           | Container registry | Imagens Docker               |
| **Athena + Glue** | Data catalog       | Consultas SQL otimizadas     |
| **IAM**           | Security           | Roles e policies             |

#### **Jobs Automatizados**

- **Ingestão Diária** (00:05 UTC): Coleta dados incrementais
- **Ingestão Horária** (a cada hora): Dados em tempo real
- **Treinamento ML** (00:30 UTC): Atualização de modelos
- **Monitoramento**: CloudWatch logs e métricas

### 📋 Deploy Completo

#### **1. Pré-requisitos**

```bash
# Ferramentas necessárias
aws configure        # Credenciais AWS
terraform --version  # Infrastructure as Code
docker --version     # Containerização
uv --version         # Package manager Python
```

#### **2. Configuração**

```bash
# Clonar repositório
git clone <repo-url>
cd fiap-fase3-ml-finance

# Instalar dependências
make deps

# Configurar ambiente (opcional)
cp .env.example .env
# Editar .env com suas configurações
```

#### **3. Deploy de Infraestrutura**

```bash
# Inicializar Terraform
make tf-init

# Provisionar recursos AWS
make tf-apply

# Deploy da aplicação
make deploy
```

#### **4. Deploy do Dashboard**

```bash
# Configurar dashboard
cp dashboard/config.example.js dashboard/config.js
# Editar config.js com URL da API

# Deploy para S3 + CloudFront
make dashboard-deploy
```

### 🔒 Configuração de Segurança

> ⚠️ **Importante**: Consulte `SECURITY.md` para diretrizes completas

#### **Variáveis de Ambiente** (`.env`)

```bash
AWS_REGION=us-east-2
PREFIX=fiap-fase4
SYMBOLS=AAPL,MSFT,AMZN,GOOGL,META,NVDA,TSLA
```

#### **Arquivos Protegidos**

- `dashboard/config.js` - Configuração específica do ambiente
- `.env` - Variáveis sensíveis
- Credenciais AWS - Via AWS CLI ou IAM roles

## 🔧 Tecnologias Utilizadas

### **Backend & ML**

- **Python 3.11**: Runtime otimizado para Lambda
- **FastAPI + Mangum**: API REST serverless
- **scikit-learn**: Machine Learning (LogisticRegression)
- **pandas + yfinance**: Processamento de dados financeiros
- **numpy**: Computação numérica

### **AWS Cloud**

- **Lambda + API Gateway**: Compute e API serverless
- **S3 + CloudFront**: Data lake e CDN global
- **EventBridge**: Orquestração de jobs
- **Athena + Glue**: Analytics e data catalog
- **ECR**: Container registry

### **Frontend**

- **HTML5 + JavaScript ES6**: Base moderna
- **Tailwind CSS**: Framework CSS utility-first
- **Plotly.js**: Gráficos interativos avançados
- **Lucide Icons**: Ícones SVG

### **DevOps**

- **Terraform**: Infrastructure as Code
- **Docker**: Containerização
- **Make + Shell**: Automação de deploy
- **uv**: Package manager Python rápido

## 📊 Monitoramento

### 🔍 Observabilidade

- **CloudWatch Logs**: Logs centralizados de todos os componentes
- **CloudWatch Metrics**: Métricas de performance e uso
- **API Health Check**: Endpoint `/health` para monitoramento
- **EventBridge Monitoring**: Acompanhamento de execução de jobs

### 📈 Métricas Principais

- **Latência da API**: Tempo de resposta dos endpoints
- **Taxa de Sucesso**: Percentual de jobs executados com sucesso
- **Volume de Dados**: Quantidade de dados processados
- **Uso de Recursos**: Memória e CPU dos Lambda functions

## 🆘 Troubleshooting

### 🔧 Problemas Comuns

#### **API não responde**

```bash
# Verificar deploy
make deploy

# Verificar logs
aws logs tail /aws/lambda/fiap-fase4-api --since 10m
```

#### **Dashboard em branco**

```bash
# Configurar URLs corretas
cp dashboard/config.example.js dashboard/config.js
# Editar config.js com URL da API

# Verificar CORS
curl -I http://sua-api-url/health
```

#### **Jobs não executam**

```bash
# Verificar EventBridge no console AWS
# Verificar logs dos jobs
aws logs tail /aws/lambda/fiap-fase4-job --since 1h
```

#### **Modelos não carregam**

```bash
# Verificar se treinamento foi executado
make train-local

# Verificar bucket de modelos
aws s3 ls s3://seu-bucket-models/
```

## 📈 Roadmap

### ✅ Implementado

- ✅ Arquitetura serverless completa
- ✅ Pipeline de dados automatizado
- ✅ Modelos ML com treinamento automático
- ✅ Dashboard interativo com Plotly.js
- ✅ Otimização de performance (99.7% economia)
- ✅ Segurança auditada e documentada

### 🔮 Próximas Funcionalidades

- **CI/CD**: GitHub Actions para deploy automatizado
- **Alertas**: CloudWatch alarms para monitoramento
- **Cache Avançado**: ElastiCache para predições frequentes
- **ML Avançado**: Modelos LSTM para séries temporais
- **Real-time**: WebSocket para updates em tempo real
- **Multi-region**: Deploy em múltiplas regiões AWS

## 📄 Licença

Este projeto é parte do curso de **Pós-graduação FIAP - Fase 3**.

**Desenvolvido com**:

- Python 3.11 + FastAPI + scikit-learn
- AWS Serverless (Lambda, S3, CloudFront, EventBridge)
- Terraform + Docker + Make

---

🚀 **Sistema em produção com pipeline ML automatizado e arquitetura serverless**

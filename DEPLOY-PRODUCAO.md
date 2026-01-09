# 🚀 GUIA PASSO A PASSO: Deploy Produção AWS

## 📋 **PRÉ-REQUISITOS**

### **1. Ferramentas Necessárias**

```bash
# Verificar se tudo está instalado
python --version   # >= 3.9
docker --version   # >= 20.0
aws --version      # >= 2.0
terraform --version # >= 1.0
uv --version       # >= 0.1.0
make --version     # GNU Make
```

### **2. Conta AWS Configurada**

```bash
# Configurar credenciais AWS
aws configure

# Verificar acesso
aws sts get-caller-identity

# Resultado esperado:
# {
#     "UserId": "AIDACK...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/seu-usuario"
# }
```

---

## 🎯 **PASSO 1: PREPARAÇÃO DO PROJETO**

### **1.1 - Clone e Setup**

```bash
cd ~/
git clone https://github.com/victorescoto/fiap-ml-finance.git
cd fiap-ml-finance

# Instalar dependências Python
make deps

# Verificar estrutura
ls -la
```

### **1.2 - Configurar Variáveis**

```bash
# Copiar arquivo de configuração
cp .env.example .env

# Editar variáveis (opcional)
nano .env
```

**Conteúdo do `.env` (valores padrão funcionam):**

```bash
# AWS Configuration
AWS_REGION=us-east-2
PREFIX=fiap-fase4

# Símbolos suportados
SYMBOLS=AAPL,MSFT,AMZN,GOOGL,META,NVDA,TSLA,DIS

# Buckets (serão criados automaticamente)
S3_RAW_BUCKET=fiap-fase4-finance-raw
S3_MODELS_BUCKET=fiap-fase4-finance-models
S3_SITE_BUCKET=fiap-fase4-finance-site
```

---

## 🏗️ **PASSO 2: CRIAR INFRAESTRUTURA AWS**

### **2.1 - Inicializar Terraform**

```bash
# Ir para diretório Terraform
cd infra/terraform

# Inicializar (baixa providers)
terraform init

# Verificar configuração
terraform validate
```

### **2.2 - Planejar Resources**

```bash
# Ver o que será criado
terraform plan -var='aws_region=us-east-2' -var='prefix=fiap-fase4'

# Resultado esperado:
# Plan: 25+ to add, 0 to change, 0 to destroy
```

### **2.3 - Criar Infraestrutura**

```bash
# Voltar para raiz do projeto
cd ../..

# Aplicar infraestrutura via Makefile
make tf-apply

# OU manualmente:
# cd infra/terraform
# terraform apply -auto-approve -var='aws_region=us-east-2' -var='prefix=fiap-fase4'
```

**Resources criados:**

- ✅ S3 Buckets (raw, models, site)
- ✅ Lambda Functions (API + Jobs)
- ✅ API Gateway
- ✅ IAM Roles e Policies
- ✅ ECR Repositories
- ✅ EventBridge Rules
- ✅ CloudFront Distribution

---

## 🐳 **PASSO 3: BUILD E DEPLOY DOS CONTAINERS**

### **3.1 - Fazer Login no ECR**

```bash
# Login automático
make ecr-login

# OU manualmente:
# aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-2.amazonaws.com
```

### **3.2 - Build das Images**

```bash
# Build da API (LSTM)
make docker-build-api

# Build dos Jobs
make docker-build-job

# OU ambos juntos:
make docker-build
```

### **3.3 - Push para ECR**

```bash
# Push da API
make ecr-push-api

# Push dos Jobs
make ecr-push-job

# OU ambos juntos:
make ecr-push
```

---

## 🌐 **PASSO 4: DEPLOY DO DASHBOARD**

### **4.1 - Configurar Dashboard**

```bash
# Copiar config exemplo
cp dashboard/config.example.js dashboard/config.js
```

### **4.2 - Obter URL da API**

```bash
# Ver outputs do Terraform
cd infra/terraform
terraform output

# Copiar api_gateway_url
# Exemplo: https://abc123.execute-api.us-east-2.amazonaws.com/prod
```

### **4.3 - Editar Configuração do Dashboard**

```bash
nano dashboard/config.js
```

**Conteúdo exemplo:**

```javascript
// Configuração para produção AWS
const API_CONFIG = {
  BASE_URL: 'https://abc123.execute-api.us-east-2.amazonaws.com/prod',
  TIMEOUT: 30000,
  SYMBOLS: ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'NVDA', 'TSLA', 'DIS']
}
```

### **4.4 - Deploy do Dashboard**

```bash
# Deploy completo do dashboard
./deploy-dashboard.sh full

# OU via Makefile:
make dashboard-deploy
```

---

## ⚡ **PASSO 5: DEPLOY COMPLETO AUTOMATIZADO**

### **5.1 - Deploy Único (Recomendado)**

```bash
# Deploy completo: infra + containers + dashboard
make deploy
```

Este comando faz:

1. ✅ `make tf-apply` - Cria infraestrutura
2. ✅ `make ecr-push` - Build + push containers
3. ✅ Atualiza Lambda functions com novas images

### **5.2 - Aguardar Propagação**

```bash
# Aguardar ~2-3 minutos para propagação
sleep 180
```

---

## 🧪 **PASSO 6: VALIDAÇÃO DO DEPLOY**

### **6.1 - Obter URLs**

```bash
cd infra/terraform

# URL da API
echo "API URL: $(terraform output -raw api_gateway_url)"

# URL do Dashboard
echo "Dashboard URL: $(terraform output -raw cloudfront_url)"

# Exemplo de saída:
# API URL: https://abc123.execute-api.us-east-2.amazonaws.com/prod
# Dashboard URL: https://d123abc.cloudfront.net
```

### **6.2 - Testar API**

```bash
# Health check
curl https://abc123.execute-api.us-east-2.amazonaws.com/prod/health

# Símbolos suportados
curl https://abc123.execute-api.us-east-2.amazonaws.com/prod/symbols

# Documentação Swagger
open https://abc123.execute-api.us-east-2.amazonaws.com/prod/docs
```

### **6.3 - Testar Dashboard**

```bash
# Abrir dashboard
open https://d123abc.cloudfront.net

# Verificar se carrega corretamente
```

### **6.4 - Executar Testes Automatizados**

```bash
# Configurar URL para testes
export API_BASE_URL="https://abc123.execute-api.us-east-2.amazonaws.com/prod"

# Executar suite de testes
python test_final.py
```

---

## 🗂️ **PASSO 7: POPULAR DADOS INICIAIS**

### **7.1 - Dados Históricos (Opcional)**

```bash
# Carregar dados históricos direto no S3
make ingest-historical-s3

# OU via Lambda (recomendado)
aws lambda invoke \
  --function-name fiap-fase4-job \
  --payload '{"job":"ingest_historical","symbols":"AAPL,MSFT,AMZN"}' \
  response.json
```

### **7.2 - Treinar Primeiro Modelo**

```bash
# Treinar modelo AAPL via API
curl -X POST https://abc123.execute-api.us-east-2.amazonaws.com/prod/train/AAPL

# OU via Lambda
aws lambda invoke \
  --function-name fiap-fase4-job \
  --payload '{"job":"train_daily","symbols":"AAPL"}' \
  response.json
```

---

## 🎯 **URLS FINAIS DE PRODUÇÃO**

### **Serviços Disponíveis:**

| Serviço             | URL                                          | Descrição               |
| ------------------- | -------------------------------------------- | ----------------------- |
| **🌐 Dashboard**    | `https://d123abc.cloudfront.net`             | Interface web principal |
| **🔌 API Docs**     | `https://abc123.execute-api.../docs`         | Documentação Swagger    |
| **💚 Health Check** | `https://abc123.execute-api.../health`       | Status da API           |
| **📊 Predições**    | `https://abc123.execute-api.../predict/AAPL` | Endpoint de ML          |

---

## 🔄 **COMANDOS DE MANUTENÇÃO**

### **Atualizar Código**

```bash
# Build e push nova versão
git pull
make docker-build
make ecr-push

# Lambda será atualizado automaticamente
```

### **Monitoramento**

```bash
# Logs da API Lambda
aws logs tail /aws/lambda/fiap-fase4-api --follow

# Logs dos Jobs
aws logs tail /aws/lambda/fiap-fase4-job --follow
```

### **Backup**

```bash
# Backup dos modelos S3
aws s3 sync s3://fiap-fase4-finance-models ./backup-models/
```

---

## 🚨 **TROUBLESHOOTING**

### **Problemas Comuns:**

**1. Erro 403 na API:**

```bash
# Verificar IAM roles
aws iam get-role --role-name fiap-fase4-lambda-exec
```

**2. Dashboard não carrega:**

```bash
# Verificar CloudFront
aws cloudfront get-distribution --id E123ABC

# Invalidar cache
aws cloudfront create-invalidation --distribution-id E123ABC --paths "/*"
```

**3. Lambda Timeout:**

```bash
# Aumentar timeout
aws lambda update-function-configuration \
  --function-name fiap-fase4-api \
  --timeout 30
```

---

## 💰 **CUSTOS ESTIMADOS**

**Custos mensais aproximados (região us-east-2):**

- **Lambda**: $5-10/mês (uso moderado)
- **S3**: $2-5/mês (dados históricos)
- **CloudFront**: $1-3/mês (CDN)
- **API Gateway**: $3-7/mês (requests)
- **ECR**: $1/mês (imagens)

**Total estimado: $12-26/mês** 💰

---

## ✅ **CHECKLIST FINAL**

- [ ] ✅ Infraestrutura criada (`make tf-apply`)
- [ ] ✅ Containers buildados (`make docker-build`)
- [ ] ✅ Images no ECR (`make ecr-push`)
- [ ] ✅ Dashboard configurado e deployado
- [ ] ✅ API respondendo (health check)
- [ ] ✅ Dashboard carregando
- [ ] ✅ Primeiro modelo treinado
- [ ] ✅ Predições funcionando
- [ ] ✅ Testes passando (`python test_final.py`)

**🎉 DEPLOY COMPLETO! Seu sistema LSTM está em produção na AWS!**

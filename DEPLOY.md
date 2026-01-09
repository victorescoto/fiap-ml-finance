# 🚀 FIAP Tech Challenge - Fase 4: Guia de Deploy

## ✅ **Checklist Pré-Deploy**

### **1. Dependências do Sistema**

```bash
# Verificar instalações necessárias
python --version     # >= 3.9
docker --version     # >= 20.0
aws --version        # >= 2.0
terraform --version  # >= 1.0
uv --version         # >= 0.1.0
```

### **2. Configuração AWS**

```bash
# Configurar credenciais
aws configure

# Testar acesso
aws sts get-caller-identity
```

### **3. Setup do Projeto**

```bash
# Clonar e instalar
git clone <repo-url>
cd fiap-ml-finance
make deps

# Configurar ambiente
cp .env.example .env
# Editar .env conforme necessário
```

---

## 🐳 **Deploy Local (Docker)**

### **Iniciar Serviços**

```bash
# Build e start completo
docker-compose up --build

# Em background
docker-compose up -d
```

### **Verificar Serviços**

```bash
# API LSTM
curl http://localhost:8000/health

# Dashboard
open http://localhost:3000

# Jupyter (opcional)
open http://localhost:8888
```

### **Parar Serviços**

```bash
# Parar containers
docker-compose down

# Limpar volumes
docker-compose down -v
```

---

## ☁️ **Deploy AWS (Produção)**

### **1. Infraestrutura**

```bash
# Inicializar Terraform
make tf-init

# Planejar mudanças
cd infra/terraform
terraform plan

# Aplicar infraestrutura
make tf-apply
```

### **2. Build e Push de Images**

```bash
# Build containers
make docker-build-api
make docker-build-job

# Push para ECR
make docker-push-api
make docker-push-job
```

### **3. Deploy da Aplicação**

```bash
# Deploy completo
make deploy

# Deploy incremental
make deploy-api-only
```

### **4. Configurar Dashboard**

```bash
# Deploy do frontend
make dashboard-deploy

# Verificar status
make dashboard-status
```

---

## 🔧 **Troubleshooting**

### **Problemas Comuns**

**1. Erros de Dependências Python**

```bash
# Reinstalar ambiente limpo
rm -rf .venv
uv sync --refresh
```

**2. Problemas Docker**

```bash
# Limpar cache
docker system prune -af
docker volume prune -f

# Rebuild containers
docker-compose build --no-cache
```

**3. Erros AWS/Terraform**

```bash
# Verificar credenciais
aws sts get-caller-identity

# Reset do state Terraform
cd infra/terraform
terraform destroy
terraform init
terraform apply
```

**4. Dashboard não carrega**

```bash
# Verificar configuração
cat dashboard/config.js

# Testar API
curl http://localhost:8000/health
```

### **Logs e Debugging**

```bash
# Logs da API
docker-compose logs lstm-api

# Logs do Dashboard
docker-compose logs dashboard

# Logs em tempo real
docker-compose logs -f
```

---

## 🧪 **Validação do Deploy**

### **Testes Automáticos**

```bash
# Suite completa de testes
python test_final.py

# Testes unitários
python -m pytest test_lstm.py -v

# Teste da API
python test_api.py
```

### **Validação Manual**

1. ✅ Health check: `curl http://localhost:8000/health`
2. ✅ Símbolos: `curl http://localhost:8000/symbols`
3. ✅ Dashboard: Abrir http://localhost:3000
4. ✅ Predição: Testar no dashboard com AAPL
5. ✅ Métricas: Verificar exibição das métricas do modelo

---

## 📈 **Monitoramento**

### **Endpoints de Status**

- **API Health**: `/health`
- **Modelo Status**: `/models/status`
- **Métricas**: `/metrics` (se configurado)

### **Logs Estruturados**

```bash
# API logs
tail -f api.log

# Container logs
docker-compose logs --tail=100
```

---

## 🔄 **Comandos de Manutenção**

```bash
# Atualizar dados
make ingest-1d-local

# Retreinar modelo
curl -X POST http://localhost:8000/train/AAPL

# Backup de modelos
cp -r models/ backup-models-$(date +%Y%m%d)

# Atualizar containers
docker-compose pull
docker-compose up -d
```

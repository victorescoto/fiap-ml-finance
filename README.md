# 🚀 FIAP Tech Challenge - Fase 4

## 📈 Sistema de Predição de Preços de Ações com LSTM

Sistema completo de Machine Learning para predição de preços de ações utilizando redes neurais LSTM (Long Short Term Memory), desenvolvido como solução para o Tech Challenge da Fase 4 da FIAP.

### 🎯 **Objetivo**

Desenvolver um modelo de Deep Learning capaz de predizer preços futuros de ações utilizando dados históricos, implementando uma solução completa com API RESTful, interface web e deployment em containers.

---

## 🏗️ **Arquitetura da Solução**

### **1. 🧠 Modelo LSTM**

- **Framework**: TensorFlow/Keras
- **Tipo**: Deep Learning - LSTM (Long Short Term Memory)
- **Características**:
  - Captura dependências temporais em séries financeiras
  - Preprocessamento automático de dados
  - Normalização MinMaxScaler
  - Sequências de 60 dias para predição
  - Métricas de avaliação: MAE, RMSE, MAPE

### **2. 🌐 API RESTful**

- **Framework**: FastAPI
- **Funcionalidades**:
  - Predições em tempo real
  - Treinamento automatizado de modelos
  - Coleta de dados históricos
  - Monitoramento de performance
  - Documentação interativa (Swagger)

### **3. 🎨 Interface Web**

- Dashboard responsivo em HTML/CSS/JavaScript
- Visualizações interativas com Plotly.js
- Interface intuitiva para predições
- Gráficos de performance dos modelos

### **4. 🐳 Containerização**

- Docker Compose para orquestração
- Containers separados para API, Dashboard e Jupyter
- Volumes persistentes para modelos
- Health checks automatizados

---

## 🚀 **Como Executar**

### **Pré-requisitos**

- Docker e Docker Compose
- Python 3.11+ (para desenvolvimento local)
- 8GB RAM recomendado

### **🎯 Deploy Rápido com Docker**

```bash
# 1. Clone o repositório
git clone <repository-url>
cd fiap-ml-finance

# 2. Execute o script de deploy
./deploy-lstm.sh

# 3. Aguarde a inicialização (pode demorar alguns minutos)
```

### **🔧 Desenvolvimento Local**

```bash
# 1. Instalar dependências
pip install uv
uv sync

# 2. Ativar ambiente virtual
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

# 3. Iniciar API
uv run uvicorn app.fastapi_app.main:app --reload

# 4. Acessar documentação
# http://localhost:8000/docs
```

---

## 📊 **Endpoints da API**

### **🏥 Health Check**

```http
GET /health
```

### **📋 Símbolos Suportados**

```http
GET /symbols
```

**Ações disponíveis**: AAPL, MSFT, AMZN, GOOGL, META, NVDA, TSLA, DIS

### **📈 Dados Históricos**

```http
GET /historical/{symbol}?period=1y&interval=1d
```

### **🔮 Predição de Preços**

```http
POST /predict
{
  "symbol": "AAPL",
  "days": 5,
  "confidence_interval": false
}
```

### **🧠 Treinamento de Modelo**

```http
POST /train
{
  "symbol": "AAPL",
  "start_date": "2020-01-01",
  "retrain": false
}
```

### **📊 Status dos Modelos**

```http
GET /models
```

---

## 🎯 **URLs de Acesso**

Após executar o deploy:

| Serviço          | URL                        | Descrição            |
| ---------------- | -------------------------- | -------------------- |
| **API LSTM**     | http://localhost:8000      | API principal        |
| **Documentação** | http://localhost:8000/docs | Swagger UI           |
| **Dashboard**    | http://localhost:3000      | Interface web        |
| **Jupyter Lab**  | http://localhost:8888      | Notebooks de análise |

---

## 🧪 **Testando a API**

### **Script Automático**

```bash
# Executa bateria completa de testes
python test_api.py
```

### **Teste Manual com cURL**

```bash
# Health check
curl http://localhost:8000/health

# Predição para AAPL
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL","days":3}'

# Treinar modelo
curl -X POST "http://localhost:8000/train" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL","start_date":"2023-01-01"}'
```

---

## 📈 **Métricas de Performance**

O sistema avalia os modelos com as seguintes métricas:

- **MAE** (Mean Absolute Error): Erro absoluto médio
- **RMSE** (Root Mean Square Error): Raiz do erro quadrático médio
- **MAPE** (Mean Absolute Percentage Error): Erro percentual absoluto médio

### **Níveis de Confiança**

- **muito_alto** (MAPE ≤ 5%): Predição muito confiável
- **alto** (5% < MAPE ≤ 10%): Predição confiável
- **médio** (10% < MAPE ≤ 15%): Predição moderada
- **baixo** (15% < MAPE ≤ 25%): Predição com cautela
- **muito_baixo** (MAPE > 25%): Predição pouco confiável

---

## 🏗️ **Estrutura do Projeto**

```
fiap-ml-finance/
├── app/
│   ├── fastapi_app/
│   │   └── main.py              # API principal
│   └── ml/
│       └── lstm_model.py        # Implementação LSTM
├── dashboard/
│   ├── index.html              # Interface web
│   ├── app.js                  # Lógica frontend
│   └── config.js               # Configuração
├── notebooks/                  # Jupyter notebooks
├── models/                     # Modelos treinados
├── Dockerfile.lstm-api         # Container da API
├── docker-compose.yml          # Orquestração
├── deploy-lstm.sh             # Script de deploy
└── test_api.py               # Testes automatizados
```

---

## 🔧 **Comandos Docker Úteis**

```bash
# Ver logs em tempo real
docker-compose logs -f lstm-api

# Reiniciar serviços
docker-compose restart

# Parar todos os containers
docker-compose down

# Rebuild completo
docker-compose up --build --force-recreate

# Acessar container da API
docker exec -it fiap-lstm-api bash
```

---

## 📚 **Tecnologias Utilizadas**

### **Backend**

- **Python 3.11**: Linguagem principal
- **TensorFlow 2.15**: Framework de Deep Learning
- **FastAPI**: Framework web moderno e rápido
- **YFinance**: Coleta de dados financeiros
- **Pandas/Numpy**: Manipulação de dados
- **Scikit-learn**: Preprocessamento e métricas

### **Frontend**

- **HTML5/CSS3**: Estrutura e estilo
- **JavaScript ES6+**: Lógica do frontend
- **Plotly.js**: Visualizações interativas
- **Bootstrap**: Design responsivo

### **DevOps**

- **Docker**: Containerização
- **Docker Compose**: Orquestração
- **Nginx**: Proxy reverso
- **uv**: Gerenciamento de pacotes Python

---

## 🎓 **Considerações Acadêmicas**

### **Modelo LSTM**

O LSTM foi escolhido por ser ideal para séries temporais financeiras, capturando:

- **Dependências de longo prazo**: Padrões que se estendem por semanas/meses
- **Memória seletiva**: Lembrança de informações relevantes
- **Não-linearidade**: Captura relações complexas nos preços

### **Avaliação do Modelo**

- **Validação temporal**: Split cronológico dos dados
- **Multiple step prediction**: Predições para múltiplos dias
- **Métricas robustas**: MAE, RMSE e MAPE para avaliação completa

### **Deployment**

- **Containerização**: Garante reprodutibilidade
- **API RESTful**: Interface padronizada e documentada
- **Monitoramento**: Health checks e métricas de performance

---

## 📝 **Entregas do Tech Challenge**

✅ **Modelo de ML**: Implementação LSTM completa  
✅ **API RESTful**: FastAPI com documentação Swagger  
✅ **Scripts/Containers**: Docker Compose para deploy  
✅ **Link para API**: http://localhost:8000 (após deploy)  
✅ **Vídeo demonstração**: [Link para vídeo]

---

## 🤝 **Equipe**

**FIAP - Tech Challenge Fase 4**

- Sistema desenvolvido para demonstração de conhecimentos em Deep Learning
- Foco em aplicação prática de LSTM para séries temporais financeiras
- Implementação completa de pipeline MLOps

---

## 📞 **Suporte**

Para dúvidas ou problemas:

1. **Verifique os logs**: `docker-compose logs -f`
2. **Consulte a documentação**: http://localhost:8000/docs
3. **Execute os testes**: `python test_api.py`

---

## 🎉 **Conclusão**

Este projeto demonstra uma implementação completa de Machine Learning para predição de preços de ações, abrangendo desde a coleta de dados até o deployment em produção. O sistema utiliza as melhores práticas de MLOps e fornece uma base sólida para aplicações financeiras reais.

**🚀 Para começar, execute: `./deploy-lstm.sh`**

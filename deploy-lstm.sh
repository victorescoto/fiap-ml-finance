#!/bin/bash

# FIAP Tech Challenge - Fase 4
# Script de Deploy da API LSTM

echo "🚀 FIAP Tech Challenge - Fase 4: Deploy da API LSTM"
echo "=================================================="

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado. Instale o Docker primeiro."
    exit 1
fi

# Verificar se Docker Compose está instalado
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose não encontrado. Instale o Docker Compose primeiro."
    exit 1
fi

# Criar diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p models logs data notebooks

# Parar containers existentes
echo "🛑 Parando containers existentes..."
docker-compose down --remove-orphans

# Limpar imagens antigas (opcional)
read -p "🧹 Deseja limpar imagens antigas do Docker? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker system prune -f
    docker image prune -f
fi

# Build e iniciar containers
echo "🔨 Construindo e iniciando containers..."
docker-compose up --build -d

# Aguardar containers inicializarem
echo "⏳ Aguardando containers inicializarem..."
sleep 30

# Verificar status dos containers
echo "📊 Status dos containers:"
docker-compose ps

# Testar API
echo "🧪 Testando API..."
API_URL="http://localhost:8000"
HEALTH_CHECK=$(curl -s "$API_URL/health" || echo "ERRO")

if [[ $HEALTH_CHECK == *"healthy"* ]]; then
    echo "✅ API funcionando corretamente!"
    echo "🌐 API disponível em: $API_URL"
    echo "📚 Documentação em: $API_URL/docs"
    echo "🎨 Dashboard em: http://localhost:3000"
    echo "📓 Jupyter Lab em: http://localhost:8888"
else
    echo "❌ API não está respondendo corretamente"
    echo "📋 Verificando logs..."
    docker-compose logs lstm-api
fi

echo ""
echo "=================================================="
echo "🎉 Deploy concluído!"
echo ""
echo "🔗 URLs disponíveis:"
echo "   • API LSTM: http://localhost:8000"
echo "   • Documentação: http://localhost:8000/docs"
echo "   • Dashboard: http://localhost:3000"
echo "   • Jupyter Lab: http://localhost:8888"
echo ""
echo "📋 Comandos úteis:"
echo "   • Ver logs: docker-compose logs -f"
echo "   • Parar: docker-compose down"
echo "   • Reiniciar: docker-compose restart"
echo "=================================================="
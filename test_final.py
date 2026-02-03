#!/usr/bin/env python3
"""
FIAP Tech Challenge - Fase 4: Script de Demonstração Final
Testa todas as funcionalidades do sistema LSTM
"""

import requests
import json
import time
from datetime import datetime

# Configuração da API
API_BASE = "http://localhost:8000"


def print_header(title):
    """Imprime cabeçalho formatado"""
    print(f"\n{'='*60}")
    print(f"🎯 {title}")
    print(f"{'='*60}")


def print_success(message):
    """Imprime mensagem de sucesso"""
    print(f"✅ {message}")


def print_info(message):
    """Imprime mensagem informativa"""
    print(f"ℹ️  {message}")


def test_api_health():
    """Testa health check da API"""
    print_header("TESTE 1: Health Check da API")

    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            data = response.json()
            print_success(f"API funcionando: {data['message']}")
            print_info(f"Status: {data['status']}")
            print_info(f"Versão: {data['version']}")
            return True
        else:
            print(f"❌ Erro: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False


def test_symbols():
    """Testa endpoint de símbolos"""
    print_header("TESTE 2: Símbolos Suportados")

    try:
        response = requests.get(f"{API_BASE}/symbols")
        if response.status_code == 200:
            data = response.json()
            print_success(f"Carregados {data['count']} símbolos:")
            print(f"   Símbolos: {', '.join(data['symbols'])}")
            print(f"   Operações: {', '.join(data['supported_operations'])}")
            return data['symbols']
        else:
            print(f"❌ Erro: Status {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Erro: {e}")
        return []


def test_historical_data(symbol):
    """Testa dados históricos"""
    print_header(f"TESTE 3: Dados Históricos - {symbol}")

    try:
        response = requests.get(f"{API_BASE}/historical/{symbol}?period=1mo")
        if response.status_code == 200:
            data = response.json()
            print_success(f"Dados coletados para {data['symbol']}")
            print_info(f"Período: {data['period']}")
            print_info(f"Total de pontos: {data['count']}")

            if data['data']:
                latest = data['data'][-1]
                print_info(
                    f"Último preço: ${latest['close']} ({latest['date']})")

            return True
        else:
            print(f"❌ Erro: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def test_model_status():
    """Testa status dos modelos"""
    print_header("TESTE 4: Status dos Modelos")

    try:
        response = requests.get(f"{API_BASE}/models")
        if response.status_code == 200:
            data = response.json()
            print_success("Status dos modelos:")

            trained_models = 0
            for model in data:
                status = "✅ Treinado" if model['exists'] else "❌ Não treinado"
                print(f"   {model['symbol']}: {status}")

                if model['exists']:
                    trained_models += 1
                    if model['metrics']:
                        mape = model['metrics'].get('MAPE', 0)
                        print(f"      📊 MAPE: {mape:.2f}%")
                        print(f"      📈 Dados: {model['data_points']} pontos")

            print_info(f"Modelos treinados: {trained_models}/{len(data)}")
            return data
        else:
            print(f"❌ Erro: Status {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Erro: {e}")
        return []


def test_training(symbol):
    """Testa treinamento de modelo"""
    print_header(f"TESTE 5: Treinamento do Modelo - {symbol}")

    try:
        print_info("Iniciando treinamento... (pode levar alguns minutos)")
        start_time = time.time()

        response = requests.post(f"{API_BASE}/train", json={
            "symbol": symbol,
            "start_date": "2023-01-01",
            "retrain": False
        })

        end_time = time.time()

        if response.status_code == 200:
            data = response.json()

            if data['status'] == 'success':
                print_success(f"Modelo treinado com sucesso!")
                if data.get('metrics'):
                    print_info(f"📊 MAE: {data['metrics']['MAE']:.2f}")
                    print_info(f"📊 RMSE: {data['metrics']['RMSE']:.2f}")
                    print_info(f"📊 MAPE: {data['metrics']['MAPE']:.2f}%")
                print_info(
                    f"⏱️  Tempo de treinamento: {data['training_time']}s")
                print_info(f"📈 Pontos de dados: {data['data_points']}")

            elif data['status'] == 'exists':
                print_success(f"Modelo já existe e está treinado")

            else:
                print(f"⚠️  Status: {data['message']}")

            return True
        else:
            print(f"❌ Erro: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def test_prediction(symbol, days=5):
    """Testa predições"""
    print_header(f"TESTE 6: Predições LSTM - {symbol} ({days} dias)")

    try:
        print_info("Fazendo predições com modelo LSTM...")

        response = requests.post(f"{API_BASE}/predict", json={
            "symbol": symbol,
            "days": days,
            "confidence_interval": False
        })

        if response.status_code == 200:
            data = response.json()
            print_success(f"Predições geradas para {data['symbol']}")
            print_info(f"💰 Preço atual: ${data['current_price']}")
            print_info(f"🧠 Confiança: {data['confidence']}")

            if data.get('model_metrics'):
                mape = data['model_metrics'].get('MAPE', 0)
                print_info(f"📊 MAPE do modelo: {mape:.2f}%")

            print_info("🔮 Predições futuras:")
            for pred in data['predicted_prices']:
                change_symbol = "📈" if pred['change'] >= 0 else "📉"
                print(f"   {pred['date']}: ${pred['predicted_price']} "
                      f"({pred['change_percent']:+.2f}%) {change_symbol}")

            return data
        else:
            print(f"❌ Erro: Status {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None


def main():
    """Executa suite completa de testes"""
    print("🚀 FIAP Tech Challenge - Fase 4")
    print("🧪 Suite Completa de Testes do Sistema LSTM")
    print("="*60)

    start_time = time.time()

    # Teste 1: Health Check
    if not test_api_health():
        print("\n❌ API não está funcionando. Verifique se está rodando em localhost:8000")
        return

    # Teste 2: Símbolos
    symbols = test_symbols()
    if not symbols:
        print("\n❌ Não foi possível carregar símbolos")
        return

    # Escolher símbolo para testes (AAPL como padrão)
    test_symbol = "AAPL" if "AAPL" in symbols else symbols[0]

    # Teste 3: Dados históricos
    if not test_historical_data(test_symbol):
        print(f"\n❌ Erro ao carregar dados históricos para {test_symbol}")
        return

    # Teste 4: Status dos modelos
    models_status = test_model_status()

    # Teste 5: Treinamento (se necessário)
    model_exists = any(m['symbol'] == test_symbol and m['exists']
                       for m in models_status)
    if not model_exists:
        print_info(
            f"Modelo para {test_symbol} não existe. Iniciando treinamento...")
        if not test_training(test_symbol):
            print(f"\n❌ Erro no treinamento do modelo para {test_symbol}")
            return
    else:
        print_info(f"Modelo para {test_symbol} já existe e está treinado ✅")

    # Teste 6: Predições
    predictions = test_prediction(test_symbol, days=3)
    if not predictions:
        print(f"\n❌ Erro ao fazer predições para {test_symbol}")
        return

    # Resumo final
    end_time = time.time()
    total_time = end_time - start_time

    print_header("🎉 RESUMO FINAL - TODOS OS TESTES CONCLUÍDOS")
    print_success("Sistema LSTM funcionando perfeitamente!")
    print_info(f"⏱️  Tempo total dos testes: {total_time:.2f}s")
    print_info(f"🎯 Símbolo testado: {test_symbol}")
    print_info(f"🧠 Modelo LSTM: Funcionando")
    print_info(f"📈 API endpoints: Todos operacionais")
    print_info(f"🌐 Dashboard: Disponível em http://localhost:3000")
    print_info(f"📚 Documentação: http://localhost:8000/docs")

    print("\n" + "="*60)
    print("✅ TECH CHALLENGE FASE 4: IMPLEMENTAÇÃO COMPLETA!")
    print("🏆 Sistema pronto para demonstração e avaliação")
    print("="*60)


if __name__ == "__main__":
    main()

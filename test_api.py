#!/usr/bin/env python3
"""
Script de teste para a API LSTM do Tech Challenge Fase 4
Demonstra todas as funcionalidades da API
"""

import requests
import json
import time
from datetime import datetime

# Configuração da API
API_BASE = "http://localhost:8000"

def test_endpoint(name, url, method="GET", data=None):
    """Testa um endpoint da API"""
    print(f"\n{'='*20} TESTANDO: {name} {'='*20}")
    print(f"URL: {method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Sucesso!")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Erro: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

def main():
    """Executa todos os testes"""
    print("🚀 FIAP Tech Challenge - Fase 4")
    print("🧪 Teste Completo da API LSTM")
    print("="*60)
    
    # 1. Health Check
    test_endpoint("Health Check", f"{API_BASE}/health")
    
    # 2. Símbolos suportados
    test_endpoint("Símbolos Suportados", f"{API_BASE}/symbols")
    
    # 3. Dados históricos
    test_endpoint("Dados Históricos AAPL", f"{API_BASE}/historical/AAPL?period=1mo")
    
    # 4. Status dos modelos
    test_endpoint("Status dos Modelos", f"{API_BASE}/models")
    
    # 5. Treinar modelo AAPL
    train_data = {
        "symbol": "AAPL",
        "start_date": "2023-01-01",
        "retrain": False
    }
    test_endpoint("Treinar Modelo AAPL", f"{API_BASE}/train", "POST", train_data)
    
    # Aguardar o treinamento (pode demorar alguns minutos)
    print("\n⏳ Aguardando treinamento do modelo... (isso pode levar alguns minutos)")
    
    # Aguardar 2 minutos para o treinamento
    for i in range(10):
        print(f"⏱️  Aguardando... {i+1}/10")
        time.sleep(12)  # 2 minutos total
    
    # 6. Status dos modelos após treinamento
    test_endpoint("Status dos Modelos (Após Treinamento)", f"{API_BASE}/models")
    
    # 7. Fazer predição
    predict_data = {
        "symbol": "AAPL",
        "days": 5,
        "confidence_interval": False
    }
    test_endpoint("Predição AAPL (5 dias)", f"{API_BASE}/predict", "POST", predict_data)
    
    # 8. Predição com intervalo de confiança
    predict_data_confidence = {
        "symbol": "AAPL", 
        "days": 1,
        "confidence_interval": True
    }
    test_endpoint("Predição AAPL (com confiança)", f"{API_BASE}/predict", "POST", predict_data_confidence)
    
    print("\n" + "="*60)
    print("🎉 Teste completo finalizado!")
    print("✅ Verifique os resultados acima")
    print("📊 Acesse http://localhost:8000/docs para documentação interativa")

if __name__ == "__main__":
    main()
"""
FIAP Tech Challenge - Fase 4
Testes Unitários para Modelo LSTM
"""

from app.utils import validate_symbol, validate_prediction_days
from app.ml.lstm_model import LSTMStockPredictor
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
import os

# Adicionar path do app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))


class TestLSTMModel:
    """Testes para o modelo LSTM"""

    def setup_method(self):
        """Setup para cada teste"""
        self.predictor = LSTMStockPredictor(symbol='AAPL')

    def test_init(self):
        """Testa inicialização do modelo"""
        assert self.predictor.symbol == 'AAPL'
        assert self.predictor.sequence_length == 60
        assert self.predictor.model is None

    def test_validate_symbol(self):
        """Testa validação de símbolos"""
        assert validate_symbol('AAPL') == True
        assert validate_symbol('INVALID') == False
        assert validate_symbol('aapl') == True  # Case insensitive

    def test_validate_prediction_days(self):
        """Testa validação de dias de predição"""
        assert validate_prediction_days(1) == True
        assert validate_prediction_days(30) == True
        assert validate_prediction_days(0) == False
        assert validate_prediction_days(31) == False

    @patch('yfinance.download')
    def test_collect_data_success(self, mock_download):
        """Testa coleta de dados com sucesso"""
        # Mock data
        mock_data = pd.DataFrame({
            'Open': [100, 101, 102],
            'High': [105, 106, 107],
            'Low': [99, 100, 101],
            'Close': [104, 105, 106],
            'Volume': [1000, 1100, 1200]
        })
        mock_download.return_value = mock_data

        result = self.predictor.collect_data('2023-01-01', '2023-12-31')

        assert not result.empty
        assert len(result) == 3
        mock_download.assert_called_once()

    @patch('yfinance.download')
    def test_collect_data_empty(self, mock_download):
        """Testa coleta de dados sem resultado"""
        mock_download.return_value = pd.DataFrame()

        with pytest.raises(ValueError, match="Nenhum dado encontrado"):
            self.predictor.collect_data('2023-01-01', '2023-12-31')

    def test_preprocess_data(self):
        """Testa preprocessamento de dados"""
        # Criar dados de teste
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = pd.DataFrame({
            'Close': np.random.uniform(100, 200, 100)
        }, index=dates)

        X_train, y_train, X_test, y_test = self.predictor.preprocess_data(data)

        # Verificações
        assert X_train.shape[2] == 1  # Feature dimension
        assert X_train.shape[1] == 60  # Sequence length
        assert len(X_train) == len(y_train)
        assert len(X_test) == len(y_test)
        assert len(X_train) > len(X_test)  # 80/20 split


class TestAPIEndpoints:
    """Testes para endpoints da API"""

    @pytest.fixture
    def client(self):
        """Cliente de teste para FastAPI"""
        from fastapi.testclient import TestClient
        from app.fastapi_app.main import app
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Testa endpoint de health check"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy",
                                   "service": "FIAP LSTM API"}

    def test_symbols_endpoint(self, client):
        """Testa endpoint de símbolos"""
        response = client.get("/symbols")
        assert response.status_code == 200
        data = response.json()
        assert "symbols" in data
        assert "AAPL" in data["symbols"]

    @patch('app.fastapi_app.main.load_model_async')
    def test_model_status_endpoint(self, mock_load, client):
        """Testa endpoint de status dos modelos"""
        # Mock model status
        mock_load.return_value = {
            "model_exists": True,
            "last_trained": "2024-01-09T10:00:00",
            "training_samples": 753,
            "model_metrics": {
                "MAE": 6.44,
                "RMSE": 8.06,
                "MAPE": 2.61
            }
        }

        response = client.get("/models/status")
        assert response.status_code == 200


class TestDataValidation:
    """Testes para validação de dados"""

    def test_price_data_format(self):
        """Testa formato dos dados de preço"""
        # Dados válidos
        valid_data = pd.DataFrame({
            'Close': [100.0, 101.5, 99.8],
            'Open': [99.5, 100.0, 101.0],
            'High': [102.0, 103.0, 101.5],
            'Low': [99.0, 100.0, 99.5],
            'Volume': [1000, 1100, 1200]
        })

        # Verificações básicas
        assert not valid_data.empty
        assert 'Close' in valid_data.columns
        assert all(valid_data['Close'] > 0)
        assert all(valid_data['Volume'] >= 0)

    def test_sequence_length_validation(self):
        """Testa validação do comprimento de sequência"""
        predictor = LSTMStockPredictor(sequence_length=30)
        assert predictor.sequence_length == 30

        # Teste com valor inválido
        with pytest.raises(ValueError):
            LSTMStockPredictor(sequence_length=0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

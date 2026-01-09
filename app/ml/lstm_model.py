"""
FIAP Tech Challenge - Fase 4
Modelo LSTM para Predição de Preços de Ações

Este módulo implementa um modelo de deep learning usando LSTM
para capturar padrões temporais nos dados de preços das ações.
"""

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import joblib
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class LSTMStockPredictor:
    """
    Classe para implementar modelo LSTM para predição de preços de ações
    """

    def __init__(self, symbol='AAPL', sequence_length=60):
        self.symbol = symbol
        self.sequence_length = sequence_length
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model = None
        self.history = None

    def collect_data(self, start_date='2018-01-01', end_date=None):
        """
        Coleta dados históricos de preços de ações usando yfinance

        Args:
            start_date (str): Data de início no formato 'YYYY-MM-DD'
            end_date (str): Data de fim no formato 'YYYY-MM-DD'

        Returns:
            pd.DataFrame: Dados históricos da ação
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        print(f"📊 Coletando dados históricos para {self.symbol}")
        print(f"📅 Período: {start_date} até {end_date}")

        try:
            # Download dos dados usando yfinance
            data = yf.download(self.symbol, start=start_date, end=end_date)

            if data.empty:
                raise ValueError(f"Nenhum dado encontrado para {self.symbol}")

            print(f"✅ Dados coletados: {len(data)} registros")
            return data

        except Exception as e:
            print(f"❌ Erro ao coletar dados: {str(e)}")
            raise

    def preprocess_data(self, data, target_column='Close'):
        """
        Pré-processamento dos dados para treinamento do LSTM

        Args:
            data (pd.DataFrame): Dados históricos
            target_column (str): Coluna alvo para predição

        Returns:
            tuple: (X_train, y_train, X_test, y_test)
        """
        print("🔧 Iniciando pré-processamento dos dados...")

        # Usar apenas a coluna de fechamento
        prices = data[target_column].values.reshape(-1, 1)

        # Normalização dos dados
        scaled_data = self.scaler.fit_transform(prices)

        # Criar sequências para treinamento
        X, y = [], []

        for i in range(self.sequence_length, len(scaled_data)):
            X.append(scaled_data[i-self.sequence_length:i, 0])
            y.append(scaled_data[i, 0])

        X, y = np.array(X), np.array(y)

        # Reshape para formato LSTM [samples, time steps, features]
        X = np.reshape(X, (X.shape[0], X.shape[1], 1))

        # Divisão treino/teste (80/20)
        train_size = int(len(X) * 0.8)

        X_train = X[:train_size]
        y_train = y[:train_size]
        X_test = X[train_size:]
        y_test = y[train_size:]

        print(f"✅ Dados processados:")
        print(f"   - Sequências de treino: {X_train.shape}")
        print(f"   - Sequências de teste: {X_test.shape}")
        print(f"   - Tamanho da sequência: {self.sequence_length} dias")

        return X_train, y_train, X_test, y_test

    def build_model(self, units=[50, 50], dropout=0.2):
        """
        Constrói o modelo LSTM

        Args:
            units (list): Lista com número de neurônios para cada camada LSTM
            dropout (float): Taxa de dropout para regularização

        Returns:
            tensorflow.keras.Model: Modelo LSTM compilado
        """
        print("🏗️ Construindo modelo LSTM...")

        model = Sequential()

        # Primeira camada LSTM
        model.add(LSTM(units=units[0],
                       return_sequences=len(units) > 1,
                       input_shape=(self.sequence_length, 1)))
        model.add(Dropout(dropout))

        # Camadas LSTM adicionais (se especificadas)
        for i, unit in enumerate(units[1:], 1):
            return_sequences = i < len(units) - 1
            model.add(LSTM(units=unit, return_sequences=return_sequences))
            model.add(Dropout(dropout))

        # Camada de saída
        model.add(Dense(1))

        # Compilar modelo
        model.compile(optimizer=Adam(learning_rate=0.001),
                      loss='mean_squared_error',
                      metrics=['mae'])

        print("✅ Modelo LSTM construído com sucesso!")
        print(f"   - Camadas LSTM: {units}")
        print(f"   - Dropout: {dropout}")
        print(f"   - Otimizador: Adam")

        return model

    def train_model(self, X_train, y_train, X_test, y_test,
                    epochs=100, batch_size=32, validation_split=0.1):
        """
        Treina o modelo LSTM

        Args:
            X_train, y_train: Dados de treinamento
            X_test, y_test: Dados de teste
            epochs (int): Número de épocas
            batch_size (int): Tamanho do batch
            validation_split (float): Proporção para validação

        Returns:
            tensorflow.keras.callbacks.History: Histórico do treinamento
        """
        print("🚀 Iniciando treinamento do modelo...")

        # Callbacks para otimização do treinamento
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=15,
                          restore_best_weights=True),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5,
                              patience=10, min_lr=0.0001)
        ]

        # Treinar modelo
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=1,
            shuffle=False  # Importante para dados de séries temporais
        )

        self.history = history

        print("✅ Treinamento concluído!")
        return history

    def evaluate_model(self, X_test, y_test):
        """
        Avalia o modelo usando métricas apropriadas

        Args:
            X_test, y_test: Dados de teste

        Returns:
            dict: Dicionário com métricas de avaliação
        """
        print("📊 Avaliando modelo...")

        # Fazer predições
        predictions = self.model.predict(X_test)

        # Desnormalizar predições e valores reais
        predictions = self.scaler.inverse_transform(predictions)
        y_test_actual = self.scaler.inverse_transform(y_test.reshape(-1, 1))

        # Calcular métricas
        mae = mean_absolute_error(y_test_actual, predictions)
        rmse = np.sqrt(mean_squared_error(y_test_actual, predictions))
        mape = np.mean(
            np.abs((y_test_actual - predictions) / y_test_actual)) * 100

        metrics = {
            'MAE': mae,
            'RMSE': rmse,
            'MAPE': mape
        }

        print("📈 Métricas de Avaliação:")
        print(f"   - MAE (Mean Absolute Error): ${mae:.2f}")
        print(f"   - RMSE (Root Mean Square Error): ${rmse:.2f}")
        print(f"   - MAPE (Mean Absolute Percentage Error): {mape:.2f}%")

        return metrics, predictions, y_test_actual

    def save_model(self, model_path='models', model_name=None, metrics=None):
        """
        Salva o modelo treinado e o scaler

        Args:
            model_path (str): Caminho para salvar o modelo
            model_name (str): Nome do modelo (opcional)
            metrics (dict): Métricas do modelo para salvar
        """
        if model_name is None:
            model_name = f"lstm_{self.symbol.lower()}"

        # Criar diretório se não existir
        os.makedirs(model_path, exist_ok=True)

        # Salvar modelo
        model_file = os.path.join(model_path, f"{model_name}.keras")
        self.model.save(model_file)

        # Salvar scaler
        scaler_file = os.path.join(model_path, f"{model_name}_scaler.joblib")
        joblib.dump(self.scaler, scaler_file)

        # Salvar configurações com métricas
        config = {
            'symbol': self.symbol,
            'sequence_length': self.sequence_length,
            'model_path': model_file,
            'scaler_path': scaler_file,
            'created_at': datetime.now().isoformat()
        }

        # Adicionar métricas se fornecidas
        if metrics:
            config['metrics'] = metrics

        config_file = os.path.join(model_path, f"{model_name}_config.joblib")
        joblib.dump(config, config_file)

        print(f"💾 Modelo salvo com sucesso:")
        print(f"   - Modelo: {model_file}")
        print(f"   - Scaler: {scaler_file}")
        print(f"   - Config: {config_file}")
        if metrics:
            print(f"   - Métricas salvas: {metrics}")

        return model_file, scaler_file, config_file

    def load_model(self, model_path='models', model_name=None):
        """
        Carrega um modelo previamente treinado

        Args:
            model_path (str): Caminho do modelo
            model_name (str): Nome do modelo
        """
        if model_name is None:
            model_name = f"lstm_{self.symbol.lower()}"

        try:
            # Carregar modelo
            model_file = os.path.join(model_path, f"{model_name}.keras")
            self.model = tf.keras.models.load_model(model_file)

            # Carregar scaler
            scaler_file = os.path.join(
                model_path, f"{model_name}_scaler.joblib")
            self.scaler = joblib.load(scaler_file)

            # Carregar configurações
            config_file = os.path.join(
                model_path, f"{model_name}_config.joblib")
            config = joblib.load(config_file)

            self.symbol = config['symbol']
            self.sequence_length = config['sequence_length']

            print(f"✅ Modelo carregado com sucesso: {self.symbol}")
            return True

        except Exception as e:
            print(f"❌ Erro ao carregar modelo: {str(e)}")
            return False

    def predict_next_price(self, historical_data):
        """
        Prediz o próximo preço baseado em dados históricos

        Args:
            historical_data (np.array): Últimos preços para predição

        Returns:
            float: Preço predito
        """
        if self.model is None:
            raise ValueError("Modelo não foi treinado ou carregado")

        # Normalizar dados
        scaled_data = self.scaler.transform(historical_data.reshape(-1, 1))

        # Pegar últimas sequências
        if len(scaled_data) >= self.sequence_length:
            sequence = scaled_data[-self.sequence_length:]
        else:
            # Se não tem dados suficientes, pad com zeros
            sequence = np.zeros((self.sequence_length, 1))
            sequence[-len(scaled_data):] = scaled_data

        # Reshape para predição
        sequence = sequence.reshape(1, self.sequence_length, 1)

        # Fazer predição
        prediction = self.model.predict(sequence, verbose=0)

        # Desnormalizar
        predicted_price = self.scaler.inverse_transform(prediction)[0, 0]

        return predicted_price

    def full_pipeline(self, symbol=None, start_date='2018-01-01'):
        """
        Executa o pipeline completo: coleta, preprocessamento, treinamento e avaliação

        Args:
            symbol (str): Símbolo da ação
            start_date (str): Data de início para coleta

        Returns:
            dict: Resultados do pipeline
        """
        if symbol:
            self.symbol = symbol

        print(f"🚀 Iniciando pipeline completo para {self.symbol}")
        print("="*50)

        # 1. Coleta de dados
        data = self.collect_data(start_date=start_date)

        # 2. Pré-processamento
        X_train, y_train, X_test, y_test = self.preprocess_data(data)

        # 3. Construir modelo
        self.model = self.build_model()

        # 4. Treinar modelo
        history = self.train_model(X_train, y_train, X_test, y_test)

        # 5. Avaliar modelo
        metrics, predictions, y_test_actual = self.evaluate_model(
            X_test, y_test)

        # 6. Salvar modelo com métricas
        model_files = self.save_model(metrics=metrics)

        results = {
            'symbol': self.symbol,
            'data_shape': data.shape,
            'train_shape': X_train.shape,
            'test_shape': X_test.shape,
            'metrics': metrics,
            'model_files': model_files,
            'history': history,
            'predictions': predictions,
            'actual_values': y_test_actual
        }

        print("="*50)
        print(f"✅ Pipeline concluído com sucesso para {self.symbol}!")

        return results


# Função utilitária para treinar múltiplos símbolos
def train_multiple_stocks(symbols=['AAPL', 'MSFT', 'GOOGL', 'AMZN'], start_date='2018-01-01'):
    """
    Treina modelos LSTM para múltiplos símbolos

    Args:
        symbols (list): Lista de símbolos para treinar
        start_date (str): Data de início

    Returns:
        dict: Resultados de todos os treinamentos
    """
    results = {}

    for symbol in symbols:
        print(f"\n{'='*60}")
        print(f"🎯 Treinando modelo para {symbol}")
        print(f"{'='*60}")

        try:
            predictor = LSTMStockPredictor(symbol=symbol)
            result = predictor.full_pipeline(start_date=start_date)
            results[symbol] = result

        except Exception as e:
            print(f"❌ Erro ao treinar {symbol}: {str(e)}")
            results[symbol] = {'error': str(e)}

    return results


if __name__ == "__main__":
    # Exemplo de uso
    print("🎯 FIAP Tech Challenge - Fase 4")
    print("📈 Modelo LSTM para Predição de Preços de Ações")
    print("="*60)

    # Treinar modelo para AAPL
    predictor = LSTMStockPredictor(symbol='AAPL')
    results = predictor.full_pipeline(start_date='2020-01-01')

    print(f"\n🎉 Treinamento concluído!")
    print(f"📊 Métricas finais: {results['metrics']}")

from pydantic import BaseModel, Field, validator
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime


class SymbolsResponse(BaseModel):
    symbols: List[str]


class PredictResponse(BaseModel):
    symbol: str
    prob_up: float = Field(ge=0.0, le=1.0)
    signal: Literal["buy", "sell", "hold"]
    asof: str


class Candle(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class LatestResponse(BaseModel):
    symbol: str
    interval: str
    candles: List[Candle]


# =============================================================================
# SCHEMAS LSTM - FIAP Tech Challenge Fase 4
# =============================================================================

class LSTMPredictionRequest(BaseModel):
    """Requisição para predição LSTM"""
    symbol: str = Field(..., description="Símbolo da ação (ex: AAPL)")
    days: int = Field(default=5, ge=1, le=30,
                      description="Dias para predição (1-30)")

    @validator('symbol')
    def validate_symbol(cls, v):
        valid_symbols = {'AAPL', 'MSFT', 'AMZN',
                         'GOOGL', 'META', 'NVDA', 'TSLA', 'DIS'}
        if v.upper() not in valid_symbols:
            raise ValueError(
                f'Símbolo deve ser um de: {", ".join(valid_symbols)}')
        return v.upper()


class LSTMPredictionResponse(BaseModel):
    """Resposta da predição LSTM"""
    symbol: str
    days: int
    predictions: List[float] = Field(..., description="Preços preditos")
    current_price: float = Field(..., description="Preço atual")
    confidence_level: Literal["low", "medium", "high", "very_high"]
    model_metrics: Dict[str,
                        float] = Field(..., description="Métricas do modelo")
    prediction_date: str = Field(..., description="Data da predição")


class ModelMetrics(BaseModel):
    """Métricas do modelo LSTM"""
    MAE: float = Field(..., description="Mean Absolute Error")
    RMSE: float = Field(..., description="Root Mean Squared Error")
    MAPE: float = Field(..., description="Mean Absolute Percentage Error")


class ModelStatus(BaseModel):
    """Status do modelo"""
    symbol: str
    model_exists: bool
    last_trained: Optional[str] = None
    training_samples: Optional[int] = None
    model_metrics: Optional[ModelMetrics] = None
    confidence_level: str = "unknown"


class TrainingRequest(BaseModel):
    """Requisição para treinamento"""
    symbol: str = Field(..., description="Símbolo para treinar")
    retrain: bool = Field(default=False, description="Forçar retreinamento")

    @validator('symbol')
    def validate_symbol(cls, v):
        valid_symbols = {'AAPL', 'MSFT', 'AMZN',
                         'GOOGL', 'META', 'NVDA', 'TSLA', 'DIS'}
        if v.upper() not in valid_symbols:
            raise ValueError(
                f'Símbolo deve ser um de: {", ".join(valid_symbols)}')
        return v.upper()


class TrainingResponse(BaseModel):
    """Resposta do treinamento"""
    symbol: str
    status: Literal["success", "error", "skipped"]
    message: str
    training_time: Optional[float] = None
    model_metrics: Optional[ModelMetrics] = None
    trained_at: str

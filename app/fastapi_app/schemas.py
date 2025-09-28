from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any


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

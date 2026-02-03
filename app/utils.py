"""
FIAP Tech Challenge - Fase 4
Utilitários de logging e validação
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logger(name: str, log_file: str = None, level: str = "INFO"):
    """
    Configuração padronizada de logging

    Args:
        name: Nome do logger
        log_file: Arquivo de log (opcional)
        level: Nível de log (DEBUG, INFO, WARNING, ERROR)

    Returns:
        logging.Logger: Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (opcional)
    if log_file:
        log_path = Path("logs")
        log_path.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(log_path / log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def validate_symbol(symbol: str) -> bool:
    """Valida se o símbolo é válido"""
    valid_symbols = {
        'AAPL', 'MSFT', 'AMZN', 'GOOGL',
        'META', 'NVDA', 'TSLA', 'DIS'
    }
    return symbol.upper() in valid_symbols


def validate_prediction_days(days: int) -> bool:
    """Valida número de dias para predição"""
    return 1 <= days <= 30


class APIError(Exception):
    """Exceção personalizada para erros da API"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

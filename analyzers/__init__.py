"""
Analyzers Module - Analizadores especializados por tipo de activo.

Arquitectura modular para análisis de diferentes tipos de inversiones:
- EquityAnalyzer: Análisis fundamental de acciones
- ETFAnalyzer: Métricas de fondos cotizados
- CryptoAnalyzer: Análisis on-chain de criptomonedas (futuro)
- IndexAnalyzer: Análisis comparativo de índices (futuro)
"""

from .base_analyzer import BaseAnalyzer
from .equity_analyzer import EquityAnalyzer
from .etf_analyzer import ETFAnalyzer

__all__ = [
    "BaseAnalyzer",
    "EquityAnalyzer",
    "ETFAnalyzer",
]

__version__ = "1.0.0"

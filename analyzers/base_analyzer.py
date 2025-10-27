"""
Base Analyzer - Interfaz abstracta para todos los analizadores de activos.

Define el contrato que todos los analizadores especializados deben cumplir.
Facilita la extensión a nuevos tipos de activos (crypto, commodities, etc.).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAnalyzer(ABC):
    """Clase abstracta base para analizadores de activos financieros."""
    
    def __init__(self):
        """Inicializa factores de confianza."""
        self.confidence_factors = {
            "completeness": 1.0,  # Completitud de datos (0-1)
            "dispersion": 1.0,    # Concordancia entre fuentes (0-1)
            "freshness": 1.0      # Frescura de datos (0-1) - futuro
        }

    @abstractmethod
    def analyze(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Realiza análisis completo del activo.

        Args:
            metrics: Diccionario con métricas financieras del activo

        Returns:
            Diccionario con resultados del análisis completo
        """
        pass

    @abstractmethod
    def get_asset_type(self) -> str:
        """
        Retorna el tipo de activo que este analizador maneja.

        Returns:
            Tipo de activo (EQUITY, ETF, CRYPTO, etc.)
        """
        pass

    def validate_metrics(self, metrics: Dict[str, Any], required_fields: list) -> bool:
        """
        Valida que las métricas contengan los campos requeridos.

        Args:
            metrics: Diccionario de métricas
            required_fields: Lista de campos obligatorios

        Returns:
            True si todos los campos requeridos están presentes
        """
        return all(metrics.get(field) is not None for field in required_fields)

    def get_data_completeness(self, metrics: Dict[str, Any], critical_fields: list) -> float:
        """
        Calcula el porcentaje de completitud de datos.

        Args:
            metrics: Diccionario de métricas
            critical_fields: Lista de campos críticos

        Returns:
            Porcentaje de completitud (0-100)
        """
        if not critical_fields:
            return 100.0

        present = sum(1 for field in critical_fields if metrics.get(field) is not None)
        completeness_pct = (present / len(critical_fields)) * 100
        
        # Actualizar factor de confidence
        self.confidence_factors["completeness"] = completeness_pct / 100.0
        
        return completeness_pct
    
    def calculate_dispersion_confidence(self, metrics: Dict[str, Any]) -> float:
        """
        Calcula factor de confianza basado en dispersión entre fuentes.
        
        Args:
            metrics: Diccionario con campo "dispersion" (si existe)
        
        Returns:
            Factor de confianza promedio (0-1) basado en dispersión
        """
        dispersion_data = metrics.get("dispersion", {})
        
        if not dispersion_data:
            # Sin datos de dispersión, asumir confianza completa
            self.confidence_factors["dispersion"] = 1.0
            return 1.0
        
        # Calcular promedio de confidence_adj de todas las métricas
        confidence_values = []
        for metric_name, disp_info in dispersion_data.items():
            if isinstance(disp_info, dict) and "confidence_adj" in disp_info:
                confidence_values.append(disp_info["confidence_adj"])
        
        if confidence_values:
            avg_confidence = sum(confidence_values) / len(confidence_values)
            self.confidence_factors["dispersion"] = avg_confidence
            return avg_confidence
        
        # Sin datos válidos, asumir confianza completa
        self.confidence_factors["dispersion"] = 1.0
        return 1.0
    
    def get_overall_confidence(self) -> float:
        """
        Calcula score de confianza general combinando todos los factores.
        
        Returns:
            Score de confianza (0-100)
        """
        # Promedio de todos los factores
        avg_confidence = sum(self.confidence_factors.values()) / len(self.confidence_factors)
        return avg_confidence * 100

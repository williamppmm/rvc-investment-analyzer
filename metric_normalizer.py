"""
MetricNormalizer - Sistema de normalización de períodos contables y monedas.

Implementa jerarquía TTM > MRQ > MRY > 5Y > FWD para métricas financieras.
Convierte todas las métricas a USD como moneda interna.

Parte de IMPROVEMENT_PLAN.md - Mejora #2 (Prioridad P0)
"""

from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger("MetricNormalizer")


# Jerarquía de períodos (1 = máxima prioridad)
PERIOD_HIERARCHY = {
    "TTM": 1,    # Trailing Twelve Months (prioridad máxima para operativos)
    "MRQ": 2,    # Most Recent Quarter (trimestre más reciente)
    "MRY": 3,    # Most Recent Year (año fiscal más reciente)
    "5Y": 4,     # 5 Year Average (promedio 5 años)
    "FWD": 5     # Forward estimates (estimaciones futuras)
}

# Tasas de cambio a USD (placeholder - en producción usar API de forex)
# TODO: Integrar con fixer.io, exchangerate-api o similar
EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.22,
    "JPY": 0.0067,
    "CAD": 0.72,
    "MXN": 0.058,
    "BRL": 0.20,
    "CNY": 0.14,
    "INR": 0.012,
    "AUD": 0.65,
    "CHF": 1.12
}


class MetricNormalizer:
    """
    Normaliza métricas financieras a período y moneda estándar.
    
    Características:
    - Jerarquía de períodos: TTM > MRQ > MRY > 5Y > FWD
    - Conversión automática a USD
    - Tracking de fallback chain
    - Metadata de normalización
    
    Ejemplo:
        normalizer = MetricNormalizer()
        
        raw_values = {
            "roe_ttm": 22.3,
            "roe_mry": 21.8,
            "roe_5y": 19.5
        }
        
        result = normalizer.normalize_metric("roe", raw_values)
        # {"value": 22.3, "period": "TTM", "fallback_chain": ["TTM"]}
    """
    
    def __init__(self):
        """Inicializa el normalizador con configuración de períodos y monedas."""
        self.period_hierarchy = PERIOD_HIERARCHY
        self.exchange_rates = EXCHANGE_RATES
        self.normalization_stats = {
            "total_normalized": 0,
            "period_usage": {period: 0 for period in PERIOD_HIERARCHY.keys()},
            "currency_conversions": 0
        }
    
    def normalize_metric(
        self, 
        metric_name: str, 
        raw_values: Dict[str, Any],
        allowed_periods: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Normaliza una métrica siguiendo jerarquía de períodos.
        
        Args:
            metric_name: Nombre base de la métrica (ej: "roe", "revenue_growth")
            raw_values: Dict con valores crudos que pueden incluir sufijos de período
                       Ej: {"roe_ttm": 22.3, "roe_mry": 21.8, "roe": 20.0}
            allowed_periods: Lista de períodos permitidos (None = todos)
        
        Returns:
            Dict con:
                - value: Valor normalizado
                - period: Período seleccionado
                - fallback_chain: Lista de períodos intentados
                - source_key: Clave original en raw_values
            
            None si no se encuentra ningún valor válido
        
        Ejemplos:
            >>> normalize_metric("roe", {"roe_ttm": 22.3, "roe_mry": 21.8})
            {"value": 22.3, "period": "TTM", "fallback_chain": ["TTM"], "source_key": "roe_ttm"}
            
            >>> normalize_metric("roe", {"roe_5y": 19.5}, allowed_periods=["TTM", "MRQ"])
            None  # 5Y no está en allowed_periods
            
            >>> normalize_metric("roe", {"roe": 22.3})
            {"value": 22.3, "period": "TTM (assumed)", "fallback_chain": ["TTM"], "source_key": "roe"}
        """
        fallback_chain = []
        
        # Filtrar períodos permitidos
        periods_to_check = (
            [p for p in PERIOD_HIERARCHY.keys() if p in allowed_periods]
            if allowed_periods
            else list(PERIOD_HIERARCHY.keys())
        )
        
        # Ordenar por jerarquía (prioridad ascendente)
        periods_to_check.sort(key=lambda p: self.period_hierarchy[p])
        
        # Intentar cada período en orden de prioridad
        for period in periods_to_check:
            fallback_chain.append(period)
            key = f"{metric_name}_{period.lower()}"
            
            if key in raw_values and raw_values[key] is not None:
                value = raw_values[key]
                
                # Validar que es un número
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    logger.warning(f"Valor inválido para {key}: {value}")
                    continue
                
                # Actualizar stats
                self.normalization_stats["total_normalized"] += 1
                self.normalization_stats["period_usage"][period] += 1
                
                return {
                    "value": value,
                    "period": period,
                    "fallback_chain": fallback_chain,
                    "source_key": key
                }
        
        # Si no hay sufijos de período, intentar la clave base
        if metric_name in raw_values and raw_values[metric_name] is not None:
            try:
                value = float(raw_values[metric_name])
                
                self.normalization_stats["total_normalized"] += 1
                self.normalization_stats["period_usage"]["TTM"] += 1
                
                return {
                    "value": value,
                    "period": "TTM (assumed)",  # Asumimos TTM si no hay sufijo
                    "fallback_chain": ["TTM"],
                    "source_key": metric_name
                }
            except (ValueError, TypeError):
                logger.warning(f"Valor inválido para {metric_name}: {raw_values[metric_name]}")
        
        # No se encontró ningún valor válido
        logger.debug(f"No se pudo normalizar {metric_name}. Períodos intentados: {fallback_chain}")
        return None
    
    def normalize_currency(
        self, 
        value: float, 
        from_currency: str,
        to_currency: str = "USD"
    ) -> Dict[str, Any]:
        """
        Convierte un valor de una moneda a otra (por defecto a USD).
        
        Args:
            value: Valor a convertir
            from_currency: Código de moneda origen (ISO 4217)
            to_currency: Código de moneda destino (default: "USD")
        
        Returns:
            Dict con:
                - value: Valor convertido
                - original_value: Valor original
                - from_currency: Moneda origen
                - to_currency: Moneda destino
                - exchange_rate: Tasa utilizada
        
        Ejemplos:
            >>> normalize_currency(100, "EUR")
            {"value": 108.0, "original_value": 100, "from_currency": "EUR", 
             "to_currency": "USD", "exchange_rate": 1.08}
            
            >>> normalize_currency(100, "USD")
            {"value": 100.0, "original_value": 100, "from_currency": "USD", 
             "to_currency": "USD", "exchange_rate": 1.0}
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # Si son la misma moneda, no hay conversión
        if from_currency == to_currency:
            return {
                "value": value,
                "original_value": value,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "exchange_rate": 1.0
            }
        
        # Obtener tasa de cambio
        if from_currency not in self.exchange_rates:
            logger.warning(
                f"Moneda {from_currency} no soportada. "
                f"Asumiendo 1:1 con {to_currency}. "
                f"Monedas soportadas: {list(self.exchange_rates.keys())}"
            )
            exchange_rate = 1.0
        else:
            # Convertir: from_currency -> USD -> to_currency
            rate_from_to_usd = self.exchange_rates[from_currency]
            rate_to_to_usd = self.exchange_rates.get(to_currency, 1.0)
            exchange_rate = rate_from_to_usd / rate_to_to_usd
        
        converted_value = value * exchange_rate
        
        # Actualizar stats
        if from_currency != to_currency:
            self.normalization_stats["currency_conversions"] += 1
        
        return {
            "value": converted_value,
            "original_value": value,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "exchange_rate": round(exchange_rate, 6)
        }
    
    def normalize_metrics_batch(
        self,
        metrics_dict: Dict[str, Any],
        metric_names: List[str],
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """
        Normaliza múltiples métricas en lote.
        
        Args:
            metrics_dict: Dict con todas las métricas crudas
            metric_names: Lista de nombres de métricas a normalizar
            currency: Moneda de las métricas (para conversión a USD)
        
        Returns:
            Dict con métricas normalizadas y metadata:
                {
                    "roe": 22.3,
                    "roe_period": "TTM",
                    "revenue_growth": 15.2,
                    "revenue_growth_period": "MRQ",
                    "_normalization_metadata": {
                        "normalized_count": 2,
                        "failed_count": 0,
                        "currency_converted": False
                    }
                }
        
        Ejemplo:
            >>> normalize_metrics_batch(
                    {"roe_ttm": 22.3, "roe_mry": 21.8, "revenue_growth_mrq": 15.2},
                    ["roe", "revenue_growth", "debt_to_equity"]
                )
            {
                "roe": 22.3,
                "roe_period": "TTM",
                "revenue_growth": 15.2,
                "revenue_growth_period": "MRQ",
                "_normalization_metadata": {
                    "normalized_count": 2,
                    "failed_count": 1,
                    "failed_metrics": ["debt_to_equity"]
                }
            }
        """
        result = {}
        normalized_count = 0
        failed_metrics = []
        
        for metric_name in metric_names:
            normalized = self.normalize_metric(metric_name, metrics_dict)
            
            if normalized:
                result[metric_name] = normalized["value"]
                result[f"{metric_name}_period"] = normalized["period"]
                normalized_count += 1
            else:
                failed_metrics.append(metric_name)
        
        # Agregar metadata
        result["_normalization_metadata"] = {
            "normalized_count": normalized_count,
            "failed_count": len(failed_metrics),
            "failed_metrics": failed_metrics,
            "currency": currency,
            "currency_converted": currency.upper() != "USD"
        }
        
        return result
    
    def get_normalization_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas de normalización.
        
        Returns:
            Dict con:
                - total_normalized: Total de métricas normalizadas
                - period_usage: Uso de cada período
                - period_usage_pct: Porcentaje de uso de cada período
                - currency_conversions: Total de conversiones de moneda
        """
        total = self.normalization_stats["total_normalized"]
        
        period_usage_pct = {}
        if total > 0:
            for period, count in self.normalization_stats["period_usage"].items():
                period_usage_pct[period] = round((count / total) * 100, 2)
        
        return {
            "total_normalized": total,
            "period_usage": self.normalization_stats["period_usage"].copy(),
            "period_usage_pct": period_usage_pct,
            "currency_conversions": self.normalization_stats["currency_conversions"]
        }
    
    def reset_stats(self):
        """Resetea las estadísticas de normalización."""
        self.normalization_stats = {
            "total_normalized": 0,
            "period_usage": {period: 0 for period in PERIOD_HIERARCHY.keys()},
            "currency_conversions": 0
        }

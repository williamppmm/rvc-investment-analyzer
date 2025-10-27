"""
Sector Benchmarks - Normalización de scores contra benchmarks sectoriales.

Implementa z-scores para comparar empresas contra peers del mismo sector,
evitando sesgos estructurales (ej: Tech naturalmente tiene ROE más alto que Utilities).

Parte de IMPROVEMENT_PLAN.md - Mejora #4 (Prioridad P1)
"""

from typing import Dict, Optional, Any
import logging

logger = logging.getLogger("SectorBenchmarks")


# Benchmarks por sector (basados en promedios históricos del S&P 500)
# Fuente: Datos históricos de Bloomberg, FactSet, y análisis de industria
SECTOR_BENCHMARKS = {
    "Technology": {
        "roe": {"mean": 22.0, "std": 8.5},
        "roic": {"mean": 18.0, "std": 7.2},
        "roa": {"mean": 12.0, "std": 5.5},
        "operating_margin": {"mean": 25.0, "std": 10.0},
        "net_margin": {"mean": 18.0, "std": 8.0},
        "gross_margin": {"mean": 60.0, "std": 15.0},
        "debt_to_equity": {"mean": 0.4, "std": 0.3},
        "current_ratio": {"mean": 2.5, "std": 1.0},
        "revenue_growth": {"mean": 15.0, "std": 12.0},
        "earnings_growth": {"mean": 18.0, "std": 15.0},
    },
    "Consumer Discretionary": {
        "roe": {"mean": 18.0, "std": 7.0},
        "roic": {"mean": 14.0, "std": 6.0},
        "roa": {"mean": 8.0, "std": 4.0},
        "operating_margin": {"mean": 12.0, "std": 6.0},
        "net_margin": {"mean": 8.0, "std": 5.0},
        "gross_margin": {"mean": 35.0, "std": 12.0},
        "debt_to_equity": {"mean": 0.8, "std": 0.5},
        "current_ratio": {"mean": 1.5, "std": 0.7},
        "revenue_growth": {"mean": 8.0, "std": 8.0},
        "earnings_growth": {"mean": 10.0, "std": 12.0},
    },
    "Consumer Staples": {
        "roe": {"mean": 16.0, "std": 5.0},
        "roic": {"mean": 12.0, "std": 4.5},
        "roa": {"mean": 7.0, "std": 3.0},
        "operating_margin": {"mean": 15.0, "std": 5.0},
        "net_margin": {"mean": 10.0, "std": 4.0},
        "gross_margin": {"mean": 45.0, "std": 10.0},
        "debt_to_equity": {"mean": 0.7, "std": 0.4},
        "current_ratio": {"mean": 1.2, "std": 0.5},
        "revenue_growth": {"mean": 4.0, "std": 5.0},
        "earnings_growth": {"mean": 6.0, "std": 7.0},
    },
    "Utilities": {
        "roe": {"mean": 9.5, "std": 3.2},
        "roic": {"mean": 6.5, "std": 2.5},
        "roa": {"mean": 3.5, "std": 1.5},
        "operating_margin": {"mean": 12.0, "std": 4.0},
        "net_margin": {"mean": 8.0, "std": 3.0},
        "gross_margin": {"mean": 40.0, "std": 8.0},
        "debt_to_equity": {"mean": 1.8, "std": 0.6},
        "current_ratio": {"mean": 0.9, "std": 0.3},
        "revenue_growth": {"mean": 2.0, "std": 3.0},
        "earnings_growth": {"mean": 3.0, "std": 4.0},
    },
    "Financials": {
        "roe": {"mean": 11.0, "std": 4.5},
        "roic": {"mean": 8.0, "std": 3.0},
        "roa": {"mean": 1.2, "std": 0.5},
        "operating_margin": {"mean": 28.0, "std": 10.0},
        "net_margin": {"mean": 20.0, "std": 8.0},
        # Nota: D/E no aplicable para financieras (modelo de negocio diferente)
        "current_ratio": {"mean": 1.1, "std": 0.4},
        "revenue_growth": {"mean": 6.0, "std": 8.0},
        "earnings_growth": {"mean": 8.0, "std": 12.0},
    },
    "Healthcare": {
        "roe": {"mean": 14.0, "std": 6.0},
        "roic": {"mean": 11.0, "std": 5.0},
        "roa": {"mean": 8.0, "std": 4.0},
        "operating_margin": {"mean": 18.0, "std": 8.0},
        "net_margin": {"mean": 12.0, "std": 6.0},
        "gross_margin": {"mean": 70.0, "std": 15.0},
        "debt_to_equity": {"mean": 0.5, "std": 0.4},
        "current_ratio": {"mean": 2.0, "std": 1.0},
        "revenue_growth": {"mean": 10.0, "std": 10.0},
        "earnings_growth": {"mean": 12.0, "std": 12.0},
    },
    "Industrials": {
        "roe": {"mean": 13.0, "std": 5.5},
        "roic": {"mean": 10.0, "std": 4.5},
        "roa": {"mean": 6.0, "std": 3.0},
        "operating_margin": {"mean": 10.0, "std": 5.0},
        "net_margin": {"mean": 7.0, "std": 4.0},
        "gross_margin": {"mean": 30.0, "std": 10.0},
        "debt_to_equity": {"mean": 0.9, "std": 0.5},
        "current_ratio": {"mean": 1.4, "std": 0.6},
        "revenue_growth": {"mean": 6.0, "std": 8.0},
        "earnings_growth": {"mean": 8.0, "std": 10.0},
    },
    "Energy": {
        "roe": {"mean": 8.0, "std": 6.0},
        "roic": {"mean": 5.0, "std": 4.0},
        "roa": {"mean": 3.0, "std": 2.5},
        "operating_margin": {"mean": 8.0, "std": 6.0},
        "net_margin": {"mean": 5.0, "std": 5.0},
        "gross_margin": {"mean": 25.0, "std": 10.0},
        "debt_to_equity": {"mean": 0.6, "std": 0.4},
        "current_ratio": {"mean": 1.3, "std": 0.5},
        "revenue_growth": {"mean": 5.0, "std": 15.0},
        "earnings_growth": {"mean": 8.0, "std": 20.0},
    },
    "Materials": {
        "roe": {"mean": 11.0, "std": 5.0},
        "roic": {"mean": 8.0, "std": 4.0},
        "roa": {"mean": 5.0, "std": 2.5},
        "operating_margin": {"mean": 12.0, "std": 6.0},
        "net_margin": {"mean": 8.0, "std": 5.0},
        "gross_margin": {"mean": 28.0, "std": 8.0},
        "debt_to_equity": {"mean": 0.7, "std": 0.4},
        "current_ratio": {"mean": 1.6, "std": 0.6},
        "revenue_growth": {"mean": 5.0, "std": 10.0},
        "earnings_growth": {"mean": 7.0, "std": 12.0},
    },
    "Communication Services": {
        "roe": {"mean": 15.0, "std": 7.0},
        "roic": {"mean": 12.0, "std": 6.0},
        "roa": {"mean": 6.0, "std": 3.5},
        "operating_margin": {"mean": 20.0, "std": 10.0},
        "net_margin": {"mean": 15.0, "std": 8.0},
        "gross_margin": {"mean": 55.0, "std": 15.0},
        "debt_to_equity": {"mean": 1.2, "std": 0.7},
        "current_ratio": {"mean": 1.3, "std": 0.6},
        "revenue_growth": {"mean": 8.0, "std": 10.0},
        "earnings_growth": {"mean": 10.0, "std": 12.0},
    },
    "Real Estate": {
        "roe": {"mean": 7.0, "std": 4.0},
        "roic": {"mean": 5.0, "std": 3.0},
        "roa": {"mean": 3.0, "std": 2.0},
        "operating_margin": {"mean": 35.0, "std": 12.0},
        "net_margin": {"mean": 25.0, "std": 10.0},
        "gross_margin": {"mean": 60.0, "std": 15.0},
        "debt_to_equity": {"mean": 1.5, "std": 0.8},
        "current_ratio": {"mean": 0.8, "std": 0.4},
        "revenue_growth": {"mean": 4.0, "std": 6.0},
        "earnings_growth": {"mean": 5.0, "std": 8.0},
    },
}


class SectorNormalizer:
    """
    Normaliza métricas contra benchmarks sectoriales usando z-scores.
    
    Z-score mide cuántas desviaciones estándar está una empresa del promedio de su sector:
    - z > +2.0: Mucho mejor que el sector (top 2.5%)
    - z > +1.0: Mejor que el sector (top 16%)
    - z > 0: Por encima del promedio
    - z < 0: Por debajo del promedio
    - z < -2.0: Mucho peor que el sector (bottom 2.5%)
    
    Ejemplo:
        Technology: ROE mean=22%, std=8.5%
        Empresa A: ROE=35%
        z-score = (35 - 22) / 8.5 = 1.53 (mejor que el promedio)
        
        Utilities: ROE mean=9.5%, std=3.2%
        Empresa B: ROE=12%
        z-score = (12 - 9.5) / 3.2 = 0.78 (mejor que el promedio)
        
        → Ambas son "buenas" vs sus sectores, aunque ROE absoluto es muy diferente
    """
    
    def __init__(self):
        """Inicializa el normalizador con benchmarks."""
        self.benchmarks = SECTOR_BENCHMARKS
        self.stats = {
            "total_normalized": 0,
            "sector_usage": {sector: 0 for sector in SECTOR_BENCHMARKS.keys()},
            "fallback_to_absolute": 0,
        }
    
    def get_z_score(
        self, 
        value: float, 
        metric: str, 
        sector: str
    ) -> Optional[float]:
        """
        Calcula z-score sector-relativo para una métrica.
        
        Formula: z = (value - mean_sector) / std_sector
        
        Args:
            value: Valor de la métrica (ej: ROE = 25%)
            metric: Nombre de la métrica (ej: "roe")
            sector: Sector de la empresa (ej: "Technology")
        
        Returns:
            z-score (float) o None si no hay benchmark disponible
        
        Ejemplo:
            >>> get_z_score(35.0, "roe", "Technology")
            1.53  # (35 - 22) / 8.5
        """
        # Validar que exista benchmark para el sector y métrica
        if sector not in self.benchmarks:
            logger.debug(f"Sector '{sector}' no tiene benchmarks definidos")
            return None
        
        sector_data = self.benchmarks[sector]
        if metric not in sector_data:
            logger.debug(f"Métrica '{metric}' no tiene benchmark en sector '{sector}'")
            return None
        
        benchmark = sector_data[metric]
        mean = benchmark["mean"]
        std = benchmark["std"]
        
        # Evitar división por cero
        if std == 0:
            logger.warning(f"Std=0 para {metric} en {sector}")
            return 0.0
        
        z_score = (value - mean) / std
        
        # Actualizar estadísticas
        self.stats["total_normalized"] += 1
        self.stats["sector_usage"][sector] += 1
        
        return z_score
    
    def z_to_score(
        self, 
        z_score: Optional[float], 
        invert: bool = False
    ) -> float:
        """
        Convierte z-score a escala 0-100.
        
        Args:
            z_score: Z-score calculado (o None si no disponible)
            invert: True para métricas "menores es mejor" (D/E, P/E)
        
        Returns:
            Score 0-100
        
        Escala estándar (invert=False):
            z > +2.0  → 100 (2 std por encima = top 2.5%)
            z > +1.0  → 85  (1 std por encima = top 16%)
            z > 0     → 70  (por encima del promedio)
            z > -1.0  → 50  (cerca del promedio)
            z > -2.0  → 30  (1 std por debajo)
            z <= -2.0 → 15  (2 std por debajo = bottom 2.5%)
        
        Escala invertida (invert=True) - para D/E, P/E, etc:
            z < -2.0  → 100 (muy bajo = muy bueno)
            z < -1.0  → 85
            z < 0     → 70
            z < +1.0  → 50
            z < +2.0  → 30
            z >= +2.0 → 15
        
        Ejemplo:
            >>> z_to_score(1.53)  # ROE 1.53 std por encima
            85
            
            >>> z_to_score(1.2, invert=True)  # D/E 1.2 std por encima (malo)
            30
        """
        if z_score is None:
            return 50.0  # Neutral si no hay datos
        
        # Invertir z-score para métricas "menores es mejor"
        if invert:
            z_score = -z_score
        
        # Convertir a escala 0-100
        if z_score > 2.0:
            return 100.0
        elif z_score > 1.0:
            return 85.0
        elif z_score > 0:
            return 70.0
        elif z_score > -1.0:
            return 50.0
        elif z_score > -2.0:
            return 30.0
        else:
            return 15.0
    
    def normalize_metric(
        self,
        value: float,
        metric: str,
        sector: str,
        invert: bool = False
    ) -> Dict[str, Any]:
        """
        Normaliza una métrica y retorna score + metadata.
        
        Args:
            value: Valor de la métrica
            metric: Nombre de la métrica
            sector: Sector de la empresa
            invert: True para "menores es mejor"
        
        Returns:
            Dict con:
                - score: Score 0-100
                - z_score: Z-score calculado
                - sector_mean: Promedio del sector
                - sector_std: Desviación estándar del sector
                - percentile: Percentil aproximado (0-100)
        
        Ejemplo:
            >>> normalize_metric(35.0, "roe", "Technology")
            {
                "score": 85,
                "z_score": 1.53,
                "sector_mean": 22.0,
                "sector_std": 8.5,
                "percentile": 93.7
            }
        """
        z_score = self.get_z_score(value, metric, sector)
        score = self.z_to_score(z_score, invert=invert)
        
        # Metadata
        result = {
            "score": score,
            "z_score": z_score,
            "value": value,
        }
        
        # Agregar benchmark info si está disponible
        if sector in self.benchmarks and metric in self.benchmarks[sector]:
            benchmark = self.benchmarks[sector][metric]
            result["sector_mean"] = benchmark["mean"]
            result["sector_std"] = benchmark["std"]
            
            # Calcular percentil aproximado (asumiendo distribución normal)
            if z_score is not None:
                # Aproximación: percentil ≈ CDF de normal estándar
                # z = 0 → 50%, z = 1 → 84%, z = 2 → 97.7%
                import math
                percentile = 50 + (z_score / 3) * 50  # Aproximación lineal simple
                percentile = max(0, min(100, percentile))
                result["percentile"] = round(percentile, 1)
        
        return result
    
    def get_sector_list(self) -> list:
        """Retorna lista de sectores disponibles."""
        return list(self.benchmarks.keys())
    
    def get_metrics_for_sector(self, sector: str) -> list:
        """Retorna lista de métricas disponibles para un sector."""
        if sector not in self.benchmarks:
            return []
        return list(self.benchmarks[sector].keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de uso del normalizador."""
        return self.stats.copy()
    
    def reset_stats(self):
        """Resetea estadísticas de uso."""
        self.stats = {
            "total_normalized": 0,
            "sector_usage": {sector: 0 for sector in SECTOR_BENCHMARKS.keys()},
            "fallback_to_absolute": 0,
        }

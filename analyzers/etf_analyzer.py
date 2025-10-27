"""
ETF Analyzer - Análisis de fondos cotizados (ETFs).

Métricas específicas para ETFs:
- Expense Ratio (ratio de gastos)
- Premium/Discount vs NAV
- YTD Return (rendimiento año a día)
- Assets Under Management (AUM)

Migrado desde etf_analyzer.py para arquitectura modular.
"""

from __future__ import annotations

from typing import Any, Dict

from .base_analyzer import BaseAnalyzer


class ETFAnalyzer(BaseAnalyzer):
    """Analizador especializado para ETFs (Exchange-Traded Funds)."""

    def get_asset_type(self) -> str:
        """Retorna tipo de activo que analiza."""
        return "ETF"

    def analyze(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Análisis completo de ETF.

        Args:
            metrics: Métricas del ETF (expense_ratio, nav, ytd_return, etc.)

        Returns:
            Diccionario con resumen y score del ETF
        """
        nav = metrics.get("nav") or metrics.get("current_price")
        price = metrics.get("current_price")
        premium = self._calculate_premium(price, nav)

        summary = {
            "ticker": metrics.get("ticker"),
            "fund_name": metrics.get("company_name"),
            "asset_type": "ETF",
            "current_price": price,
            "nav": nav,
            "premium_discount": premium,
            "expense_ratio": metrics.get("expense_ratio"),
            "ytd_return": metrics.get("ytd_return"),
            "category": metrics.get("category"),
            "provider": metrics.get("provider"),
            "volume": metrics.get("volume"),
            "assets_under_management": metrics.get("assets_under_management"),
            "dividend_yield": metrics.get("dividend_yield"),
            "holdings_count": metrics.get("holdings_count"),
            "index": metrics.get("index_tracked"),
        }
        
        score_result = self.score(summary)
        summary["score"] = score_result
        
        return summary

    def score(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula score de calidad del ETF (0-100).

        Factores evaluados:
        - Expense Ratio (30%): Ratio de gastos anual
        - YTD Return (40%): Rendimiento año a día
        - Premium/Discount (20%): Desviación vs NAV
        - NAV disponible (10%): Disponibilidad de datos
        - AUM (10%): Tamaño del fondo

        Returns:
            Dict con total_score y label de calidad
        """
        score = 0
        max_score = 0

        # Expense Ratio (30 puntos)
        expense = summary.get("expense_ratio")
        if expense is not None:
            expense_value = expense
            if expense_value > 0.01:
                expense_value = expense_value / 100
            max_score += 30
            if expense_value < 0.001:
                score += 30
            elif expense_value < 0.0025:
                score += 25
            elif expense_value < 0.005:
                score += 18
            elif expense_value < 0.0075:
                score += 12
            else:
                score += 6

        # YTD Return (40 puntos)
        ytd_return = summary.get("ytd_return")
        if ytd_return is not None:
            ytd_value = ytd_return / 100 if ytd_return > 1 else ytd_return
            max_score += 40
            if ytd_value > 0.20:
                score += 40
            elif ytd_value > 0.10:
                score += 34
            elif ytd_value > 0.05:
                score += 26
            elif ytd_value > 0:
                score += 18
            else:
                score += 8

        # Premium/Discount (20 puntos)
        premium = summary.get("premium_discount")
        if premium is not None:
            max_score += 20
            if abs(premium) < 0.3:
                score += 20
            elif abs(premium) < 0.75:
                score += 14
            else:
                score += 8

        # NAV disponible (10 puntos)
        nav = summary.get("nav")
        if nav:
            max_score += 10
            score += 10

        # Assets Under Management (10 puntos)
        aum = summary.get("assets_under_management")
        if aum:
            max_score += 10
            if aum >= 100_000_000_000:  # >= $100B
                score += 10
            elif aum >= 10_000_000_000:  # >= $10B
                score += 8
            elif aum >= 1_000_000_000:  # >= $1B
                score += 6
            else:
                score += 3

        final = round((score / max_score) * 100, 1) if max_score else None
        label = self._label(final)
        
        return {"total_score": final, "label": label}

    def _calculate_premium(self, price: float | None, nav: float | None) -> float | None:
        """
        Calcula premium/discount del ETF respecto al NAV.

        Args:
            price: Precio de mercado del ETF
            nav: Net Asset Value (valor neto de activos)

        Returns:
            Porcentaje de premium (+) o discount (-) vs NAV
        """
        if price and nav and nav > 0:
            return ((price - nav) / nav) * 100
        return None

    def _label(self, final: float | None) -> str:
        """
        Genera etiqueta de calidad basada en el score.

        Args:
            final: Score total (0-100)

        Returns:
            Etiqueta con emoji y descripción
        """
        if final is None:
            return "Sin puntaje"
        if final >= 80:
            return "🟢 Excelente"
        if final >= 65:
            return "🟡 Bueno"
        if final >= 50:
            return "🟠 Aceptable"
        return "🔴 Revisar"

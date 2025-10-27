#!/usr/bin/env python3
"""
Equity Analyzer - Análisis fundamental de acciones individuales.

Sistema de 3 scores para evaluación completa:
1. Score de CALIDAD: ¿Qué tan buena es la empresa?
2. Score de VALORACIÓN: ¿Qué tan caro está el precio?
3. Score de INVERSIÓN: ¿Vale la pena comprar AHORA?

Migrado desde scoring_engine.py para arquitectura modular.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from .base_analyzer import BaseAnalyzer


class EquityAnalyzer(BaseAnalyzer):
    """Analizador especializado para acciones (EQUITY)."""

    def __init__(self):
        # Inicializar BaseAnalyzer (confidence_factors)
        super().__init__()
        
        # Pesos para sub-scores
        self.quality_weights = {
            "roe": 0.40,
            "roic": 0.35,
            "operating_margin": 0.15,
            "net_margin": 0.10,
        }

        self.valuation_weights = {
            "pe_ratio": 0.40,
            "peg_ratio": 0.35,
            "price_to_book": 0.25,
        }

        self.health_weights = {
            "debt_to_equity": 0.60,
            "current_ratio": 0.30,
            "quick_ratio": 0.10,
        }

        self.growth_weights = {
            "revenue_growth": 0.60,
            "earnings_growth": 0.40,
        }

    def get_asset_type(self) -> str:
        """Retorna tipo de activo que analiza."""
        return "EQUITY"

    def analyze(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Análisis completo de acción individual.

        Args:
            metrics: Métricas financieras de la acción

        Returns:
            Diccionario con scores, categoría, recomendación y breakdown
        """
        return self.calculate_all_scores(metrics)

    @staticmethod
    def _pick_metric(metrics: Dict[str, Any], keys: Iterable[str]) -> Optional[float]:
        """Return first non-None metric value following priority order."""
        for key in keys:
            value = metrics.get(key)
            if value is not None:
                return value
        return None

    def calculate_all_scores(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula todos los scores de la empresa.

        Returns:
            Dict con quality_score, valuation_score, investment_score,
            recommendation, category, y breakdown completo
        """
        # 0. CALCULAR FACTORES DE CONFIANZA
        # Completeness (ya existente)
        critical_fields = ["pe_ratio", "roe", "roic", "operating_margin"]
        data_completeness = self.get_data_completeness(metrics, critical_fields)
        
        # Dispersion (NUEVO)
        dispersion_confidence = self.calculate_dispersion_confidence(metrics)
        
        # Overall confidence
        overall_confidence = self.get_overall_confidence()
        
        # 1. CALIDAD: ¿Qué tan buena es la empresa?
        quality_result = self._calculate_quality(metrics)
        quality_score = quality_result["score"]

        # 2. VALORACIÓN: ¿Qué tan caro está el precio?
        valuation_result = self._calculate_valuation(metrics)
        valuation_score = valuation_result["score"]

        # 3. SALUD FINANCIERA
        health_result = self._calculate_health(metrics)
        health_score = health_result["score"]

        # 4. CRECIMIENTO
        growth_result = self._calculate_growth(metrics)
        growth_score = growth_result["score"]

        # 5. INVERSIÓN: ¿Vale la pena comprar AHORA?
        investment_score = self._calculate_investment(
            quality_score,
            valuation_score,
            health_score,
            growth_score,
            metrics
        )

        # 6. CATEGORIZACIÓN
        category = self._categorize(quality_score, valuation_score)

        # 7. RECOMENDACIÓN
        recommendation = self._get_recommendation(
            investment_score,
            quality_score,
            valuation_score,
            category
        )

        return {
            "quality_score": round(quality_score, 2),
            "valuation_score": round(valuation_score, 2),
            "financial_health_score": round(health_score, 2),
            "growth_score": round(growth_score, 2),
            "investment_score": round(investment_score, 2),
            "recommendation": recommendation,
            "category": category,
            "breakdown": {
                "quality": quality_result,
                "valuation": valuation_result,
                "health": health_result,
                "growth": growth_result,
            },
            "data_completeness": round(data_completeness, 2),
            "confidence_level": self._confidence(metrics),
            "confidence_factors": {
                "completeness": round(self.confidence_factors["completeness"] * 100, 2),
                "dispersion": round(self.confidence_factors["dispersion"] * 100, 2),
                "overall": round(overall_confidence, 2)
            },
            "dispersion_detail": metrics.get("dispersion", {})  # Detalle técnico para debugging
        }

    def _calculate_quality(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score de CALIDAD del negocio (0-100).

        Evalúa: ROE, ROIC, márgenes operativos y netos.
        """
        components = []
        used: List[str] = []

        # ROE (Return on Equity)
        roe = metrics.get("roe")
        if roe is not None:
            if roe > 30:
                score = 100
            elif roe > 25:
                score = 95
            elif roe > 20:
                score = 85
            elif roe > 15:
                score = 70
            elif roe > 10:
                score = 50
            elif roe > 5:
                score = 30
            else:
                score = 10
            components.append(("ROE", score, self.quality_weights["roe"]))
            used.append(f"ROE: {roe:.1f}%")

        # ROIC (Return on Invested Capital)
        roic = metrics.get("roic")
        if roic is not None:
            if roic > 25:
                score = 100
            elif roic > 20:
                score = 90
            elif roic > 15:
                score = 80
            elif roic > 10:
                score = 60
            elif roic > 8:
                score = 40
            else:
                score = 20
            components.append(("ROIC", score, self.quality_weights["roic"]))
            used.append(f"ROIC: {roic:.1f}%")

        # Operating Margin
        op_margin = metrics.get("operating_margin")
        if op_margin is not None:
            if op_margin > 30:
                score = 100
            elif op_margin > 25:
                score = 90
            elif op_margin > 20:
                score = 80
            elif op_margin > 15:
                score = 65
            elif op_margin > 10:
                score = 45
            else:
                score = 25
            components.append(("Op. Margin", score, self.quality_weights["operating_margin"]))
            used.append(f"Op. Margin: {op_margin:.1f}%")

        # Net Margin
        net_margin = metrics.get("net_margin")
        if net_margin is not None:
            if net_margin > 25:
                score = 100
            elif net_margin > 20:
                score = 85
            elif net_margin > 15:
                score = 70
            elif net_margin > 10:
                score = 50
            elif net_margin > 5:
                score = 30
            else:
                score = 15
            components.append(("Net Margin", score, self.quality_weights["net_margin"]))
            used.append(f"Net Margin: {net_margin:.1f}%")

        return self._weighted_result(components, used, "Sin datos de calidad")

    def _calculate_valuation(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score de VALORACIÓN (0-100).

        Evalúa: P/E, PEG, P/B
        Score ALTO = BARATO (buena valoración)
        Score BAJO = CARO (mala valoración)
        """
        components = []
        used: List[str] = []

        # P/E Ratio
        pe = metrics.get("pe_ratio")
        if pe is not None and pe > 0:
            if pe < 12:
                score = 100
            elif pe < 15:
                score = 90
            elif pe < 20:
                score = 75
            elif pe < 25:
                score = 60
            elif pe < 30:
                score = 45
            elif pe < 40:
                score = 30
            else:
                score = 15
            components.append(("P/E", score, self.valuation_weights["pe_ratio"]))
            used.append(f"P/E: {pe:.2f}")

        # PEG Ratio
        peg = metrics.get("peg_ratio")
        if peg is not None and peg > 0:
            if peg < 0.8:
                score = 100
            elif peg < 1.0:
                score = 90
            elif peg < 1.25:
                score = 75
            elif peg < 1.5:
                score = 60
            elif peg < 2.0:
                score = 40
            else:
                score = 20
            components.append(("PEG", score, self.valuation_weights["peg_ratio"]))
            used.append(f"PEG: {peg:.2f}")

        # P/B Ratio
        pb = metrics.get("price_to_book")
        if pb is not None and pb > 0:
            if pb < 1:
                score = 100
            elif pb < 2:
                score = 85
            elif pb < 3:
                score = 70
            elif pb < 5:
                score = 50
            elif pb < 8:
                score = 30
            else:
                score = 15
            components.append(("P/B", score, self.valuation_weights["price_to_book"]))
            used.append(f"P/B: {pb:.2f}")

        return self._weighted_result(components, used, "Sin datos de valoración")

    def _calculate_health(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Score de SALUD FINANCIERA (0-100)."""
        components = []
        used: List[str] = []

        # Debt to Equity
        debt = metrics.get("debt_to_equity")
        if debt is not None:
            if debt < 0.3:
                score = 100
            elif debt < 0.5:
                score = 90
            elif debt < 1:
                score = 75
            elif debt < 1.5:
                score = 55
            elif debt < 2:
                score = 35
            else:
                score = 15
            components.append(("Debt/Equity", score, self.health_weights["debt_to_equity"]))
            used.append(f"D/E: {debt:.2f}")

        # Current Ratio
        current = metrics.get("current_ratio")
        if current is not None:
            if current > 2.5:
                score = 100
            elif current > 2:
                score = 90
            elif current > 1.5:
                score = 75
            elif current > 1:
                score = 60
            elif current > 0.7:
                score = 40
            else:
                score = 20
            components.append(("Current Ratio", score, self.health_weights["current_ratio"]))
            used.append(f"Current: {current:.2f}")

        # Quick Ratio
        quick = metrics.get("quick_ratio")
        if quick is not None:
            if quick > 2:
                score = 100
            elif quick > 1.5:
                score = 90
            elif quick > 1.2:
                score = 75
            elif quick > 1:
                score = 60
            elif quick > 0.7:
                score = 40
            else:
                score = 20
            components.append(("Quick Ratio", score, self.health_weights["quick_ratio"]))
            used.append(f"Quick: {quick:.2f}")

        return self._weighted_result(components, used, "Sin datos de salud financiera")

    def _calculate_growth(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Score de CRECIMIENTO (0-100)."""
        components = []
        used: List[str] = []

        # Revenue Growth
        revenue_growth = self._pick_metric(
            metrics,
            (
                "revenue_growth_5y",
                "revenue_growth",
                "revenue_growth_qoq",
            ),
        )
        if revenue_growth is not None:
            if revenue_growth > 30:
                score = 100
            elif revenue_growth > 25:
                score = 90
            elif revenue_growth > 20:
                score = 80
            elif revenue_growth > 15:
                score = 65
            elif revenue_growth > 10:
                score = 50
            elif revenue_growth > 5:
                score = 35
            else:
                score = 20
            components.append(("Revenue Growth", score, self.growth_weights["revenue_growth"]))
            used.append(f"Rev. Growth: {revenue_growth:.1f}%")

        # Earnings Growth
        earnings_growth = self._pick_metric(
            metrics,
            (
                "earnings_growth_this_y",
                "earnings_growth_next_y",
                "earnings_growth_next_5y",
                "earnings_growth_qoq",
                "earnings_growth",
            ),
        )
        if earnings_growth is not None:
            if earnings_growth > 30:
                score = 100
            elif earnings_growth > 25:
                score = 90
            elif earnings_growth > 15:
                score = 75
            elif earnings_growth > 10:
                score = 60
            elif earnings_growth > 5:
                score = 45
            elif earnings_growth > 0:
                score = 30
            else:
                score = 15
            components.append(("Earnings Growth", score, self.growth_weights["earnings_growth"]))
            used.append(f"Earn. Growth: {earnings_growth:.1f}%")

        return self._weighted_result(components, used, "Sin datos de crecimiento")

    def _calculate_investment(
        self,
        quality: float,
        valuation: float,
        health: float,
        growth: float,
        metrics: Dict[str, Any]
    ) -> float:
        """
        Score de INVERSIÓN (0-100) - EL MÁS IMPORTANTE.

        Responde: "¿Compro AHORA o no?"

        Filosofía:
        - Calidad mínima 60 requerida
        - Valoración mínima 40 requerida para calidad alta
        - Balance óptimo: calidad 70-90 + valoración 60-80
        - Bonuses por salud excepcional y crecimiento
        """

        # CASO 1: Calidad insuficiente → Rechazar
        if quality < 50:
            return quality * 0.40  # Penalización muy fuerte

        if quality < 60:
            return quality * 0.50  # Penalización fuerte

        # CASO 2: Sweet Spot (calidad buena + precio justo)
        if 70 <= quality <= 95 and valuation >= 60:
            investment = (quality * 0.45) + (valuation * 0.45)

            # Bonus por salud excepcional
            if health >= 85:
                investment += 3

            # Bonus por crecimiento fuerte
            if growth >= 75:
                investment += 2

            return min(100, investment)

        # CASO 3: Calidad élite pero cara
        if quality >= 85 and valuation < 60:
            # Calidad excepcional compensa algo el precio
            investment = (quality * 0.50) + (valuation * 0.35)

            # Si además tiene crecimiento fuerte, es más tolerable
            if growth >= 70:
                investment += 5

            # Máximo 80 si es muy cara (valuation < 40)
            if valuation < 40:
                return min(75, investment)

            return min(85, investment)

        # CASO 4: Calidad media + precio muy bueno
        if 60 <= quality < 70 and valuation >= 70:
            investment = (quality * 0.40) + (valuation * 0.50)

            # Bonus si al menos tiene buena salud
            if health >= 75:
                investment += 3

            return investment

        # CASO 5: Calidad buena pero precio algo caro
        if 70 <= quality < 85 and 50 <= valuation < 60:
            investment = (quality * 0.45) + (valuation * 0.40)

            # Pequeño bonus si tiene crecimiento
            if growth >= 65:
                investment += 3

            return investment

        # CASO 6: Otros (balances no óptimos)
        investment = (quality * 0.40) + (valuation * 0.40) + (health * 0.10) + (growth * 0.10)

        return investment

    def _categorize(self, quality: float, valuation: float) -> Dict[str, str]:
        """
        Clasifica la acción en una categoría visual.

        Returns:
            Dict con 'name', 'color', 'desc', 'emoji'
        """

        # 🏆 SWEET SPOT: Lo mejor de ambos mundos
        if quality >= 75 and valuation >= 60:
            return {
                "name": "SWEET SPOT",
                "color": "green",
                "desc": "Calidad + Precio ideal",
                "emoji": "🏆"
            }

        # ⭐ PREMIUM: Excelente empresa pero cara
        elif quality >= 85 and valuation >= 40:
            return {
                "name": "PREMIUM",
                "color": "blue",
                "desc": "Excelente empresa, precio elevado",
                "emoji": "⭐"
            }

        # 💎 VALOR: Calidad decente, buen precio
        elif quality >= 60 and valuation >= 70:
            return {
                "name": "VALOR",
                "color": "cyan",
                "desc": "Calidad decente, buen precio",
                "emoji": "💎"
            }

        # ⚠️ CARA: Gran empresa pero muy cara
        elif quality >= 85 and valuation < 40:
            return {
                "name": "CARA",
                "color": "yellow",
                "desc": "Gran empresa, esperar corrección",
                "emoji": "⚠️"
            }

        # 🪤 TRAMPA: Barata pero baja calidad
        elif quality < 60 and valuation >= 60:
            return {
                "name": "TRAMPA",
                "color": "orange",
                "desc": "Barata pero baja calidad",
                "emoji": "🪤"
            }

        # 🔴 EVITAR: Ni calidad ni precio
        else:
            return {
                "name": "EVITAR",
                "color": "red",
                "desc": "Ni calidad ni precio justifican inversión",
                "emoji": "🔴"
            }

    def _get_recommendation(
        self,
        investment_score: float,
        quality_score: float,
        valuation_score: float,
        category: Dict[str, str]
    ) -> str:
        """
        Genera recomendación textual basada en el score de inversión.
        """
        cat_name = category["name"]

        if investment_score >= 75:
            if cat_name == "SWEET SPOT":
                return "🟢 COMPRAR - Excelente oportunidad de inversión"
            elif cat_name == "PREMIUM":
                return "🟢 COMPRAR - Empresa excepcional, precio aceptable"
            else:
                return "🟢 COMPRAR - Buena oportunidad de inversión"

        elif investment_score >= 60:
            if cat_name == "VALOR":
                return "🟡 CONSIDERAR - Buen precio pero verificar calidad sostenible"
            elif cat_name == "PREMIUM":
                return "🟡 CONSIDERAR - Buena empresa pero algo cara"
            else:
                return "🟡 CONSIDERAR - Analizar con más detalle antes de decidir"

        elif investment_score >= 45:
            if valuation_score < 40:
                return "⚠️ ESPERAR - Precio muy elevado, esperar corrección"
            elif quality_score < 55:
                return "⚠️ PRECAUCIÓN - Calidad del negocio insuficiente"
            else:
                return "⚠️ ESPERAR - No es el momento óptimo para invertir"

        else:
            if cat_name == "TRAMPA":
                return "🔴 NO COMPRAR - Precio bajo no compensa la baja calidad"
            elif cat_name == "EVITAR":
                return "🔴 NO COMPRAR - Ni calidad ni precio justifican la inversión"
            else:
                return "🔴 NO COMPRAR - Riesgo demasiado alto"

    def _weighted_result(
        self,
        components: List[tuple],
        used: List[str],
        fallback: str
    ) -> Dict[str, Any]:
        """Calcula score ponderado de componentes."""
        active = [(score, weight) for _, score, weight in components]

        if active:
            total_weight = sum(weight for _, _, weight in components)
            if total_weight == 0:
                average = sum(score for score, _ in active) / len(active)
            else:
                average = sum(score * weight for score, weight in active) / total_weight

            return {
                "score": round(average, 2),
                "metrics_used": used,
                "components_count": len(components)
            }

        return {
            "score": 50.0,
            "metrics_used": [fallback],
            "components_count": 0
        }

    def _confidence(self, metrics: Dict[str, Any]) -> str:
        """Calcula nivel de confianza del análisis."""
        completeness = metrics.get("data_completeness", 0)

        critical = [
            metrics.get("pe_ratio"),
            metrics.get("roe"),
            metrics.get("operating_margin"),
            metrics.get("debt_to_equity"),
        ]

        critical_available = sum(1 for value in critical if value is not None)

        if metrics.get("primary_source") == "fallback_example":
            return "Muy Baja"

        if completeness >= 80 and critical_available >= 3:
            return "Alta"
        elif completeness >= 60 and critical_available >= 2:
            return "Media"
        elif completeness >= 40 or critical_available >= 2:
            return "Baja"
        else:
            return "Muy Baja"


# Alias para compatibilidad hacia atrás
InvestmentScorer = EquityAnalyzer

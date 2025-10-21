#!/usr/bin/env python3
"""
Investment Calculator - Simulador de inversión DCA y proyecciones a largo plazo.

Características:
- Simulación Dollar Cost Averaging (DCA)
- Proyecciones conservadoras, moderadas y optimistas
- Impacto del timing (inicio en crisis vs burbuja)
- Poder del interés compuesto
- Comparación lump sum vs DCA
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import random


class InvestmentCalculator:
    """Calculadora de inversiones a largo plazo."""

    # Retornos anuales históricos del S&P 500 (ajustados por inflación)
    HISTORICAL_RETURNS = {
        "conservador": 0.07,    # 7% anual
        "moderado": 0.10,       # 10% anual
        "optimista": 0.12,      # 12% anual
    }

    # Volatilidad anual promedio
    VOLATILITY = {
        "conservador": 0.10,    # 10% desviación estándar
        "moderado": 0.15,       # 15% desviación estándar
        "optimista": 0.20,      # 20% desviación estándar
    }

    # Escenarios de mercado para timing
    MARKET_SCENARIOS = {
        "crisis": {
            "label": "Crisis (Caída 30-50%)",
            "initial_drop": -0.40,  # Caída inicial 40%
            "recovery_months": 18,  # Recuperación en 18 meses
            "description": "Inicias invirtiendo durante una crisis severa del mercado"
        },
        "normal": {
            "label": "Mercado Normal",
            "initial_drop": 0.0,
            "recovery_months": 0,
            "description": "Mercado en condiciones normales, crecimiento estable"
        },
        "burbuja": {
            "label": "Burbuja (Sobrevaluado +40%)",
            "initial_drop": 0.40,   # Mercado sobrevalorado
            "recovery_months": 24,  # Corrección tarda 24 meses
            "description": "Inicias invirtiendo en un mercado sobrevaluado"
        }
    }

    def __init__(self):
        """Inicializa la calculadora."""
        pass

    def calculate_dca(
        self,
        monthly_amount: float,
        years: int,
        scenario: str = "moderado",
        market_timing: str = "normal",
        include_simulation: bool = True
    ) -> Dict[str, Any]:
        """
        Calcula proyección de inversión con DCA.

        Args:
            monthly_amount: Cantidad a invertir mensualmente
            years: Años de inversión
            scenario: conservador, moderado u optimista
            market_timing: crisis, normal o burbuja
            include_simulation: Si incluir simulación mes a mes

        Returns:
            Diccionario con resultados de la simulación
        """
        if scenario not in self.HISTORICAL_RETURNS:
            scenario = "moderado"

        if market_timing not in self.MARKET_SCENARIOS:
            market_timing = "normal"

        annual_return = self.HISTORICAL_RETURNS[scenario]
        monthly_return = annual_return / 12
        total_months = years * 12
        total_invested = monthly_amount * total_months

        # Simulación mes a mes
        portfolio_value = 0.0
        monthly_values = []
        shares_accumulated = 0.0

        market_info = self.MARKET_SCENARIOS[market_timing]

        for month in range(1, total_months + 1):
            # Simular precio de la acción considerando timing y volatilidad
            price_factor = self._calculate_price_factor(
                month,
                market_timing,
                market_info,
                annual_return
            )

            # Comprar acciones con el monto mensual
            # Precio base = 100, ajustado por factor
            share_price = 100 * price_factor
            shares_bought = monthly_amount / share_price
            shares_accumulated += shares_bought

            # Valor del portafolio
            portfolio_value = shares_accumulated * share_price

            if include_simulation:
                monthly_values.append({
                    "month": month,
                    "invested_to_date": monthly_amount * month,
                    "portfolio_value": round(portfolio_value, 2),
                    "gain": round(portfolio_value - (monthly_amount * month), 2),
                    "return_pct": round(
                        ((portfolio_value / (monthly_amount * month)) - 1) * 100, 2
                    ) if month > 0 else 0.0,
                    "share_price": round(share_price, 2),
                    "shares_accumulated": round(shares_accumulated, 4)
                })

        # Cálculo simplificado (interés compuesto puro)
        simple_final_value = self._calculate_compound_interest(
            monthly_amount,
            monthly_return,
            total_months
        )

        # Estadísticas finales
        final_value = portfolio_value
        total_gain = final_value - total_invested
        total_return_pct = ((final_value / total_invested) - 1) * 100

        result = {
            "input": {
                "monthly_amount": monthly_amount,
                "years": years,
                "total_months": total_months,
                "scenario": scenario,
                "market_timing": market_timing,
                "market_timing_label": market_info["label"],
                "expected_annual_return": annual_return * 100,
            },
            "results": {
                "total_invested": round(total_invested, 2),
                "final_value": round(final_value, 2),
                "total_gain": round(total_gain, 2),
                "total_return_pct": round(total_return_pct, 2),
                "simple_projection": round(simple_final_value, 2),
            },
            "breakdown": {
                "years_5": self._calculate_milestone(monthly_amount, 5, monthly_return) if years >= 5 else None,
                "years_10": self._calculate_milestone(monthly_amount, 10, monthly_return) if years >= 10 else None,
                "years_15": self._calculate_milestone(monthly_amount, 15, monthly_return) if years >= 15 else None,
                "years_20": self._calculate_milestone(monthly_amount, 20, monthly_return) if years >= 20 else None,
            },
            "monthly_simulation": monthly_values if include_simulation else [],
            "insights": self._generate_insights(
                monthly_amount,
                years,
                final_value,
                total_invested,
                scenario,
                market_timing
            )
        }

        return result

    def compare_lump_sum_vs_dca(
        self,
        total_amount: float,
        years: int,
        scenario: str = "moderado"
    ) -> Dict[str, Any]:
        """
        Compara inversión lump sum (todo de una vez) vs DCA.

        Args:
            total_amount: Monto total disponible
            years: Período de comparación
            scenario: Escenario de retorno

        Returns:
            Comparación entre ambas estrategias
        """
        annual_return = self.HISTORICAL_RETURNS.get(scenario, 0.10)
        monthly_return = annual_return / 12
        total_months = years * 12

        # Estrategia 1: Lump Sum (todo al inicio)
        lump_sum_final = total_amount * ((1 + annual_return) ** years)

        # Estrategia 2: DCA (distribuido mensualmente)
        monthly_amount = total_amount / total_months
        dca_result = self.calculate_dca(
            monthly_amount,
            years,
            scenario,
            "normal",
            include_simulation=False
        )
        dca_final = dca_result["results"]["final_value"]

        # Comparación
        difference = lump_sum_final - dca_final
        difference_pct = (difference / lump_sum_final) * 100

        return {
            "total_amount": total_amount,
            "years": years,
            "scenario": scenario,
            "lump_sum": {
                "strategy": "Inversión Inicial Completa",
                "final_value": round(lump_sum_final, 2),
                "total_gain": round(lump_sum_final - total_amount, 2),
                "return_pct": round(((lump_sum_final / total_amount) - 1) * 100, 2)
            },
            "dca": {
                "strategy": "Dollar Cost Averaging",
                "monthly_amount": round(monthly_amount, 2),
                "final_value": round(dca_final, 2),
                "total_gain": round(dca_final - total_amount, 2),
                "return_pct": dca_result["results"]["total_return_pct"]
            },
            "comparison": {
                "winner": "Lump Sum" if lump_sum_final > dca_final else "DCA",
                "difference": round(abs(difference), 2),
                "difference_pct": round(abs(difference_pct), 2),
                "recommendation": self._lump_sum_vs_dca_recommendation(difference_pct)
            }
        }

    def calculate_compound_interest_impact(
        self,
        initial_amount: float,
        monthly_contribution: float,
        years: int,
        annual_return: float = 0.10
    ) -> Dict[str, Any]:
        """
        Demuestra el poder del interés compuesto.

        Args:
            initial_amount: Inversión inicial
            monthly_contribution: Aporte mensual
            years: Años de inversión
            annual_return: Retorno anual esperado

        Returns:
            Desglose del impacto del interés compuesto
        """
        monthly_return = annual_return / 12
        total_months = years * 12

        # Calcular sin interés compuesto (solo suma)
        total_contributed = initial_amount + (monthly_contribution * total_months)

        # Calcular con interés compuesto
        fv = initial_amount
        for month in range(total_months):
            fv = (fv + monthly_contribution) * (1 + monthly_return)

        interest_earned = fv - total_contributed

        return {
            "initial_amount": initial_amount,
            "monthly_contribution": monthly_contribution,
            "years": years,
            "annual_return_pct": annual_return * 100,
            "total_contributed": round(total_contributed, 2),
            "final_value": round(fv, 2),
            "interest_earned": round(interest_earned, 2),
            "interest_contribution_pct": round((interest_earned / fv) * 100, 2),
            "message": f"El {round((interest_earned / fv) * 100, 1)}% de tu riqueza final proviene del interés compuesto"
        }

    def _calculate_price_factor(
        self,
        month: int,
        market_timing: str,
        market_info: Dict[str, Any],
        annual_return: float
    ) -> float:
        """Calcula el factor de precio considerando timing y volatilidad."""
        base_growth = (1 + annual_return / 12) ** month

        # Aplicar efecto de timing
        if market_timing == "crisis":
            # Inicio en crisis: caída inicial pero luego recuperación rápida
            if month <= market_info["recovery_months"]:
                timing_factor = 1 + market_info["initial_drop"] * (1 - month / market_info["recovery_months"])
            else:
                timing_factor = 1.0
        elif market_timing == "burbuja":
            # Inicio en burbuja: corrección en los primeros meses
            if month <= market_info["recovery_months"]:
                timing_factor = 1 + market_info["initial_drop"] * (1 - month / market_info["recovery_months"])
            else:
                timing_factor = 1.0
        else:
            timing_factor = 1.0

        return base_growth * timing_factor

    def _calculate_compound_interest(
        self,
        monthly_amount: float,
        monthly_return: float,
        total_months: int
    ) -> float:
        """Calcula valor final con interés compuesto."""
        fv = 0.0
        for month in range(total_months):
            fv = (fv + monthly_amount) * (1 + monthly_return)
        return fv

    def _calculate_milestone(
        self,
        monthly_amount: float,
        years: int,
        monthly_return: float
    ) -> Dict[str, float]:
        """Calcula milestone en un año específico."""
        months = years * 12
        total_invested = monthly_amount * months
        final_value = self._calculate_compound_interest(monthly_amount, monthly_return, months)

        return {
            "years": years,
            "invested": round(total_invested, 2),
            "value": round(final_value, 2),
            "gain": round(final_value - total_invested, 2)
        }

    def _generate_insights(
        self,
        monthly_amount: float,
        years: int,
        final_value: float,
        total_invested: float,
        scenario: str,
        market_timing: str
    ) -> List[str]:
        """Genera insights educativos sobre la inversión."""
        insights = []

        # Insight 1: Poder del tiempo
        if years >= 10:
            insights.append(
                f"En {years} años, tu inversión mensual de ${monthly_amount:,.0f} "
                f"se convierte en ${final_value:,.0f}"
            )

        # Insight 2: Disciplina
        insights.append(
            f"Invertir consistentemente es clave: aportas ${monthly_amount:,.0f} cada mes sin falta"
        )

        # Insight 3: Timing del mercado
        if market_timing == "crisis":
            insights.append(
                "Iniciar en una crisis puede ser ventajoso: compras más acciones cuando están baratas"
            )
        elif market_timing == "burbuja":
            insights.append(
                "Iniciar en una burbuja penaliza los primeros años, pero DCA suaviza el impacto"
            )

        # Insight 4: Interés compuesto
        total_gain = final_value - total_invested
        if total_gain > 0:
            gain_pct = (total_gain / total_invested) * 100
            insights.append(
                f"El interés compuesto genera ${total_gain:,.0f} adicionales ({gain_pct:.1f}% de ganancia)"
            )

        # Insight 5: Escenario
        if scenario == "conservador":
            insights.append("Escenario conservador: resultados realistas para bonos o fondos indexados de bajo riesgo")
        elif scenario == "optimista":
            insights.append("Escenario optimista: requiere selección activa de acciones de alto crecimiento")

        return insights

    def _lump_sum_vs_dca_recommendation(self, difference_pct: float) -> str:
        """Genera recomendación basada en la diferencia."""
        if difference_pct > 10:
            return "Históricamente, Lump Sum supera significativamente a DCA en mercados alcistas largos"
        elif difference_pct > 5:
            return "Lump Sum tiene ventaja moderada, pero DCA reduce riesgo emocional"
        else:
            return "Resultados similares: DCA ofrece tranquilidad psicológica con rendimiento comparable"

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

    MAX_PORTFOLIO_VALUE = 1_000_000

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

    def _monthly_rate(self, annual_rate: float) -> float:
        """
        Calcula la tasa mensual usando capitalización geométrica.
        
        Usa: r_m = (1 + r)^(1/12) - 1
        En lugar de: r_m = r / 12 (menos preciso)
        
        Args:
            annual_rate: Tasa anual (ej: 0.10 para 10%)
            
        Returns:
            Tasa mensual equivalente
        """
        return (1 + annual_rate) ** (1/12) - 1

    def calculate_dca(
        self,
        monthly_amount: float,
        years: int,
        scenario: str = "moderado",
        market_timing: str = "normal",
        include_simulation: bool = True,
        initial_amount: float = 0.0,
        annual_inflation: float = 0.0,
        max_portfolio_value: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calcula proyeccion de inversion con DCA considerando ajuste por inflacion
        y un limite superior de capital.

        Args:
            monthly_amount: Aporte mensual inicial en dolares.
            years: Cantidad de anos planificados.
            scenario: conservador, moderado u optimista.
            market_timing: crisis, normal o burbuja.
            include_simulation: Si incluir simulacion mes a mes.
            initial_amount: Capital inicial invertido antes del primer mes.
            annual_inflation: Incremento anual esperado de los aportes (en fraccion).
            max_portfolio_value: Limite superior del valor del portafolio.

        Returns:
            Diccionario con resultados de la simulacion.
        """
        if scenario not in self.HISTORICAL_RETURNS:
            scenario = "moderado"

        if market_timing not in self.MARKET_SCENARIOS:
            market_timing = "normal"

        annual_return = self.HISTORICAL_RETURNS[scenario]
        total_months_planned = years * 12
        max_value = max_portfolio_value or self.MAX_PORTFOLIO_VALUE

        portfolio_value = 0.0
        shares_accumulated = 0.0
        monthly_values: List[Dict[str, Any]] = []
        total_invested = initial_amount
        invested_to_date = initial_amount
        months_executed = 0
        cap_reached: Optional[Dict[str, Any]] = None

        market_info = self.MARKET_SCENARIOS[market_timing]

        for month in range(1, total_months_planned + 1):
            months_executed += 1

            price_factor = self._calculate_price_factor(
                month,
                market_timing,
                market_info,
                annual_return
            )
            share_price = 100 * price_factor

            if month == 1 and initial_amount > 0:
                initial_shares = initial_amount / share_price
                shares_accumulated += initial_shares
                portfolio_value = shares_accumulated * share_price

            inflation_factor = (1 + annual_inflation) ** ((month - 1) // 12)
            adjusted_monthly = monthly_amount * inflation_factor

            if adjusted_monthly > 0:
                total_invested += adjusted_monthly
                invested_to_date += adjusted_monthly
                shares_bought = adjusted_monthly / share_price if share_price > 0 else 0.0
                shares_accumulated += shares_bought
                portfolio_value = shares_accumulated * share_price

            if include_simulation:
                monthly_values.append({
                    "month": month,
                    "monthly_contribution": round(adjusted_monthly, 2),
                    "invested_to_date": round(invested_to_date, 2),
                    "portfolio_value": round(portfolio_value, 2),
                    "gain": round(portfolio_value - invested_to_date, 2),
                    "return_pct": round(
                        ((portfolio_value / invested_to_date) - 1) * 100, 2
                    ) if invested_to_date > 0 else 0.0,
                    "share_price": round(share_price, 2),
                    "shares_accumulated": round(shares_accumulated, 4)
                })

            if max_value and portfolio_value >= max_value:
                portfolio_value = max_value
                invested_to_date = min(invested_to_date, max_value)
                total_invested = min(total_invested, max_value)
                cap_reached = {
                    "amount": max_value,
                    "month": month,
                    "years_elapsed": round(month / 12, 2)
                }
                if include_simulation and monthly_values:
                    monthly_values[-1]["portfolio_value"] = round(portfolio_value, 2)
                    monthly_values[-1]["gain"] = round(portfolio_value - invested_to_date, 2)
                    monthly_values[-1]["capped"] = True
                break

        projection_baseline = self._calculate_with_inflation(
            initial_amount=initial_amount,
            monthly_contribution=monthly_amount,
            years=years,
            annual_return=annual_return,
            annual_inflation=annual_inflation,
            max_portfolio_value=max_value
        )

        final_value = portfolio_value
        total_gain = final_value - total_invested
        total_return_pct = (
            ((final_value / total_invested) - 1) * 100 if total_invested > 0 else 0.0
        )
        effective_years = months_executed / 12 if months_executed else 0.0

        # Calcular valores reales (deflactados)
        final_value_real = None
        total_invested_real = None
        total_gain_real = None
        total_return_real_pct = None
        
        if annual_inflation > 0 and effective_years > 0:
            # Deflactar al poder adquisitivo actual
            deflation_factor = (1 + annual_inflation) ** effective_years
            final_value_real = final_value / deflation_factor
            total_invested_real = total_invested / deflation_factor
            total_gain_real = final_value_real - total_invested_real
            total_return_real_pct = (
                ((final_value_real / total_invested_real) - 1) * 100 
                if total_invested_real > 0 else 0.0
            )

        result = {
            "input": {
                "initial_amount": initial_amount,
                "monthly_amount": monthly_amount,
                "years": years,
                "total_months_planned": total_months_planned,
                "effective_months": months_executed,
                "annual_inflation_pct": round(annual_inflation * 100, 2),
                "index_contributions_annually": annual_inflation > 0,
                "scenario": scenario,
                "market_timing": market_timing,
                "market_timing_label": market_info["label"],
                "expected_annual_return": round(annual_return * 100, 2),
                "max_portfolio_value": max_value,
            },
            "results": {
                "total_invested": round(total_invested, 2),
                "final_value": round(final_value, 2),
                "total_gain": round(total_gain, 2),
                "total_return_pct": round(total_return_pct, 2),
                "final_value_real": round(final_value_real, 2) if final_value_real is not None else None,
                "total_invested_real": round(total_invested_real, 2) if total_invested_real is not None else None,
                "total_gain_real": round(total_gain_real, 2) if total_gain_real is not None else None,
                "total_return_real_pct": round(total_return_real_pct, 2) if total_return_real_pct is not None else None,
                "simple_projection": round(projection_baseline["final_value"], 2),
                "baseline_projection": projection_baseline,
                "cap_reached": cap_reached,
            },
            "breakdown": {
                "years_5": self._calculate_milestone(
                    initial_amount,
                    monthly_amount,
                    5,
                    annual_return,
                    annual_inflation,
                    max_value
                ) if effective_years >= 5 else None,
                "years_10": self._calculate_milestone(
                    initial_amount,
                    monthly_amount,
                    10,
                    annual_return,
                    annual_inflation,
                    max_value
                ) if effective_years >= 10 else None,
                "years_15": self._calculate_milestone(
                    initial_amount,
                    monthly_amount,
                    15,
                    annual_return,
                    annual_inflation,
                    max_value
                ) if effective_years >= 15 else None,
                "years_20": self._calculate_milestone(
                    initial_amount,
                    monthly_amount,
                    20,
                    annual_return,
                    annual_inflation,
                    max_value
                ) if effective_years >= 20 else None,
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

        if include_simulation:
            result["monthly_simulation"] = monthly_values

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
        difference_value = abs(lump_sum_final - dca_final)
        winner = "Lump Sum" if lump_sum_final >= dca_final else "DCA"
        baseline = lump_sum_final if winner == "Lump Sum" else dca_final
        difference_pct = (difference_value / baseline) * 100 if baseline > 0 else 0.0
        recommendation = self._lump_sum_vs_dca_recommendation(difference_pct, winner)

        return {
            "total_amount": total_amount,
            "years": years,
            "scenario": scenario,
            "annual_return": annual_return,  # Tasa anual para gráficos
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
                "winner": winner,
                "difference": round(difference_value, 2),
                "difference_pct": round(difference_pct, 2),
                "recommendation": recommendation
            }
        }

    def calculate_retirement_plan(
        self,
        current_age: int,
        retirement_age: int,
        initial_amount: float,
        monthly_contribution: float,
        annual_return: float = 0.10,
        annual_inflation: float = 0.03,
        include_yearly_detail: bool = True,
        max_portfolio_value: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calcula plan de jubilación con ajuste por inflación.

        Args:
            current_age: Edad actual
            retirement_age: Edad de jubilación deseada
            initial_amount: Inversión inicial (capital inicial)
            monthly_contribution: Aporte mensual inicial
            annual_return: Retorno anual esperado
            annual_inflation: Inflación anual esperada
            include_yearly_detail: Si incluir desglose año por año
            max_portfolio_value: Limite superior del portafolio (default 1M)

        Returns:
            Proyección completa hasta jubilación con ajuste por inflación
        """
        # Validaciones
        if current_age < 18 or current_age > 75:
            raise ValueError("Edad actual debe estar entre 18 y 75 años")
        if retirement_age < current_age or retirement_age > 75:
            raise ValueError("Edad de jubilación debe ser mayor a la edad actual y máximo 75 años")
        if annual_return < -0.10 or annual_return > 0.20:
            raise ValueError("Rendimiento anual debe estar entre -10% y +20%")

        years = retirement_age - current_age
        total_months = years * 12
        monthly_return = annual_return / 12
        max_value = max_portfolio_value or self.MAX_PORTFOLIO_VALUE

        # Calcular proyección año por año
        yearly_projections = []
        portfolio_value = initial_amount
        total_contributions_accumulated = initial_amount
        total_interest_accumulated = 0.0
        cap_reached: Optional[Dict[str, Any]] = None
        months_executed = 0

        for year in range(1, years + 1):
            # Aportación anual ajustada por inflación
            inflation_factor = (1 + annual_inflation) ** (year - 1)
            adjusted_monthly_contribution = monthly_contribution * inflation_factor
            annual_contribution_real = 0.0

            # Simular mes a mes para este año
            year_start_value = portfolio_value
            for month in range(1, 13):
                months_executed += 1
                portfolio_value += adjusted_monthly_contribution
                total_contributions_accumulated += adjusted_monthly_contribution
                annual_contribution_real += adjusted_monthly_contribution

                # Aplicar rendimiento mensual
                interest_this_month = portfolio_value * monthly_return
                portfolio_value += interest_this_month
                total_interest_accumulated += interest_this_month
                if max_value and portfolio_value >= max_value:
                    overflow = portfolio_value - max_value
                    if overflow > 0:
                        portfolio_value = max_value
                        total_interest_accumulated -= overflow
                    total_contributions_accumulated = min(total_contributions_accumulated, max_value)
                    cap_reached = {
                        "amount": max_value,
                        "year": year,
                        "month": month,
                        "age": round(current_age + year - 1 + month / 12, 2)
                    }
                    break

            year_interest = portfolio_value - year_start_value - annual_contribution_real

            if include_yearly_detail:
                yearly_projections.append({
                    "year": year,
                    "age": current_age + year,
                    "annual_contribution": round(annual_contribution_real, 2),
                    "contributions_accumulated": round(total_contributions_accumulated, 2),
                    "interest_this_year": round(year_interest, 2),
                    "interest_accumulated": round(total_interest_accumulated, 2),
                    "portfolio_value": round(portfolio_value, 2)
                })

            if cap_reached:
                break

        # Calcular escenarios múltiples (±2%)
        scenarios = {}
        for scenario_name, return_adjustment in [
            ("conservador", -0.02),
            ("realista", 0.00),
            ("optimista", 0.02)
        ]:
            scenario_return = annual_return + return_adjustment
            scenario_result = self._calculate_with_inflation(
                initial_amount,
                monthly_contribution,
                years,
                scenario_return,
                annual_inflation,
                max_value
            )
            scenarios[scenario_name] = scenario_result

        # Hitos importantes
        milestones = self._find_milestones(
            initial_amount,
            monthly_contribution,
            annual_return,
            annual_inflation,
            years,
            current_age,
            max_value
        )

        effective_years = years
        if cap_reached:
            effective_years = round((cap_reached["year"] - 1) + cap_reached["month"] / 12, 2)

        final_capital = round(portfolio_value, 2)
        total_contributions_nominal = round(total_contributions_accumulated - initial_amount, 2)
        total_interest_nominal = round(total_interest_accumulated, 2)
        composition = {"initial_pct": 0.0, "contributions_pct": 0.0, "interest_pct": 0.0}
        if final_capital > 0:
            composition = {
                "initial_pct": round((initial_amount / final_capital) * 100, 2),
                "contributions_pct": round((total_contributions_nominal / final_capital) * 100, 2),
                "interest_pct": round((total_interest_nominal / final_capital) * 100, 2)
            }

        # Calcular valores reales (deflactados)
        final_capital_real = None
        total_contributions_real = None
        total_interest_real = None
        
        if annual_inflation > 0 and effective_years > 0:
            deflation_factor = (1 + annual_inflation) ** effective_years
            final_capital_real = final_capital / deflation_factor
            total_contributions_real = (total_contributions_nominal + initial_amount) / deflation_factor
            total_interest_real = final_capital_real - total_contributions_real

        return {
            "input": {
                "current_age": current_age,
                "retirement_age": retirement_age,
                "years_to_retirement": years,
                "effective_years": effective_years,
                "initial_amount": initial_amount,
                "monthly_contribution": monthly_contribution,
                "annual_return_pct": round(annual_return * 100, 2),
                "annual_inflation": annual_inflation,
                "annual_inflation_pct": round(annual_inflation * 100, 2),
                "index_contributions_annually": annual_inflation > 0,
                "max_portfolio_value": max_value
            },
            "results": {
                "final_capital": final_capital,
                "initial_capital": initial_amount,
                "total_contributions": total_contributions_nominal,
                "total_interest": total_interest_nominal,
                "final_capital_real": round(final_capital_real, 2) if final_capital_real is not None else None,
                "total_contributions_real": round(total_contributions_real, 2) if total_contributions_real is not None else None,
                "total_interest_real": round(total_interest_real, 2) if total_interest_real is not None else None,
                "average_return_pct": round(annual_return * 100, 2),
                "cap_reached": cap_reached
            },
            "scenarios": scenarios,
            "yearly_projections": yearly_projections,
            "milestones": milestones,
            "composition": composition,
            "limit": {
                "max_value": max_value,
                "reached": cap_reached is not None,
                "details": cap_reached
            }
        }

    def _calculate_with_inflation(
        self,
        initial_amount: float,
        monthly_contribution: float,
        years: int,
        annual_return: float,
        annual_inflation: float,
        max_portfolio_value: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calcula proyección con inflación y límite opcional.
        Usa tasa mensual geométrica para mayor precisión.
        """
        r_m = self._monthly_rate(annual_return)  # Tasa mensual geométrica
        portfolio_value = initial_amount
        total_contributions = initial_amount
        total_interest = 0.0
        months_executed = 0
        cap_reached = False
        max_value = max_portfolio_value or self.MAX_PORTFOLIO_VALUE

        for year in range(1, years + 1):
            inflation_factor = (1 + annual_inflation) ** (year - 1)
            adjusted_monthly = monthly_contribution * inflation_factor

            for _ in range(12):
                months_executed += 1
                portfolio_value += adjusted_monthly
                total_contributions += adjusted_monthly

                interest_this_month = portfolio_value * r_m  # Usa tasa geométrica
                portfolio_value += interest_this_month
                total_interest += interest_this_month

                if max_value and portfolio_value >= max_value:
                    overflow = portfolio_value - max_value
                    if overflow > 0:
                        portfolio_value = max_value
                        total_interest -= overflow
                    total_contributions = min(total_contributions, max_value)
                    cap_reached = True
                    break

            if cap_reached:
                break

        return {
            "final_value": round(portfolio_value, 2),
            "total_contributions": round(total_contributions, 2),
            "total_interest": round(total_interest, 2),
            "return_pct": round(
                ((portfolio_value / total_contributions) - 1) * 100, 2
            ) if total_contributions > 0 else 0.0,
            "months_executed": months_executed,
            "capped": cap_reached
        }

    def _find_milestones(
        self,
        initial_amount: float,
        monthly_contribution: float,
        annual_return: float,
        annual_inflation: float,
        total_years: int,
        current_age: int,
        max_portfolio_value: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Encuentra hitos importantes (primer 100k, 500k, etc.)."""
        milestones = []
        targets = [100000, 250000, 500000, 1000000]

        r_m = self._monthly_rate(annual_return)  # Tasa mensual geométrica
        portfolio_value = initial_amount
        max_value = max_portfolio_value or self.MAX_PORTFOLIO_VALUE
        cap_reached = False

        for year in range(1, total_years + 1):
            inflation_factor = (1 + annual_inflation) ** (year - 1)
            adjusted_monthly = monthly_contribution * inflation_factor

            for month in range(12):
                portfolio_value += adjusted_monthly
                portfolio_value *= (1 + r_m)  # Usa tasa geométrica

                for target in targets[:]:
                    if portfolio_value >= target:
                        milestones.append({
                            "amount": target,
                            "year": year,
                            "age": current_age + year,
                            "label": f"${target:,.0f}"
                        })
                        targets.remove(target)

                if max_value and portfolio_value >= max_value:
                    portfolio_value = max_value
                    cap_reached = True
                    break

            if cap_reached or not targets:
                break

        return milestones

    def calculate_compound_interest_impact(
        self,
        initial_amount: float,
        monthly_contribution: float,
        years: int,
        annual_return: float = 0.10
    ) -> Dict[str, Any]:
        """
        Demuestra el poder del interés compuesto (modo determinista).

        Args:
            initial_amount: Inversión inicial
            monthly_contribution: Aporte mensual
            years: Años de inversión
            annual_return: Retorno anual esperado

        Returns:
            Desglose del impacto del interés compuesto con serie temporal anual
        """
        monthly_return = annual_return / 12
        total_months = years * 12
        max_value = self.MAX_PORTFOLIO_VALUE

        total_contributed = initial_amount
        fv = initial_amount
        capped = False
        yearly_series = []

        for month in range(1, total_months + 1):
            fv += monthly_contribution
            total_contributed += monthly_contribution
            fv *= (1 + monthly_return)
            
            if max_value and fv >= max_value:
                fv = max_value
                capped = True
                break
            
            # Guardar snapshot anual
            if month % 12 == 0:
                year = month // 12
                interest_so_far = fv - total_contributed
                yearly_series.append({
                    "year": year,
                    "contributions_accumulated": round(total_contributed, 2),
                    "interest_accumulated": round(interest_so_far, 2),
                    "portfolio_value": round(fv, 2),
                    "interest_share_pct": round((interest_so_far / fv) * 100, 2) if fv > 0 else 0.0
                })

        interest_earned = fv - total_contributed

        return {
            "mode": "deterministic",
            "initial_amount": initial_amount,
            "monthly_contribution": monthly_contribution,
            "years": years,
            "annual_return_pct": annual_return * 100,
            "total_contributed": round(total_contributed, 2),
            "final_value": round(fv, 2),
            "interest_earned": round(interest_earned, 2),
            "interest_contribution_pct": round((interest_earned / fv) * 100, 2) if fv > 0 else 0.0,
            "yearly_series": yearly_series,
            "message": (
                f"El {round((interest_earned / fv) * 100, 1)}% de tu riqueza final proviene del interes compuesto"
                if fv > 0 else "Ingresa un monto o plazo valido para ver el efecto del interes compuesto."
            ),
            "cap_reached": capped,
            "max_portfolio_value": max_value
        }

    def calculate_compound_interest_simulation(
        self,
        initial_amount: float,
        monthly_contribution: float,
        years: int,
        annual_return: float = 0.10,
        scenario: str = "moderado",
        use_stochastic: bool = True,
        num_paths: int = 1
    ) -> Dict[str, Any]:
        """
        Simulación del interés compuesto con volatilidad (modo realista).
        
        Args:
            initial_amount: Inversión inicial
            monthly_contribution: Aporte mensual
            years: Años de inversión
            annual_return: Retorno anual esperado (promedio)
            scenario: conservador/moderado/optimista (define volatilidad)
            use_stochastic: Si False, es determinista (sin ruido)
            num_paths: Número de simulaciones (para visualizar rango)
            
        Returns:
            Resultados con series temporales y múltiples caminos
        """
        r_m = self._monthly_rate(annual_return)
        months = years * 12
        max_value = self.MAX_PORTFOLIO_VALUE
        volatility = self.VOLATILITY.get(scenario, 0.15)
        monthly_vol = volatility / (12 ** 0.5)
        
        # Almacenar múltiples caminos simulados
        paths = []
        
        for path_idx in range(num_paths):
            value = initial_amount
            aportes_acum = initial_amount
            interes_acum = 0.0
            series = []
            capped = False
            
            for m in range(1, months + 1):
                # Aporte mensual
                value += monthly_contribution
                aportes_acum += monthly_contribution
                
                # Retorno mensual con volatilidad
                bump = (1 + r_m)
                if use_stochastic:
                    noise = random.gauss(0.0, monthly_vol)
                    bump *= (1 + noise)
                
                prev_value = value
                value *= bump
                interes_mes = value - prev_value
                interes_acum += interes_mes
                
                # Aplicar tope si existe
                if max_value and value >= max_value:
                    value = max_value
                    capped = True
                    break
                
                # Guardar snapshots anuales
                if m % 12 == 0:
                    year = m // 12
                    series.append({
                        "year": year,
                        "month": m,
                        "annual_contribution": monthly_contribution * 12,
                        "contributions_accumulated": round(aportes_acum, 2),
                        "interest_accumulated": round(interes_acum, 2),
                        "portfolio_value": round(value, 2),
                        "interest_share_pct": round((interes_acum / value) * 100, 2) if value > 0 else 0.0
                    })
            
            paths.append({
                "path_id": path_idx + 1,
                "final_value": round(value, 2),
                "total_contributed": round(aportes_acum, 2),
                "interest_earned": round(value - aportes_acum, 2),
                "capped": capped,
                "yearly_series": series
            })
        
        # Estadísticas agregadas (promedio de todos los caminos)
        avg_final = sum(p["final_value"] for p in paths) / num_paths
        avg_interest = sum(p["interest_earned"] for p in paths) / num_paths
        min_final = min(p["final_value"] for p in paths)
        max_final = max(p["final_value"] for p in paths)
        
        return {
            "mode": "simulation",
            "stochastic": use_stochastic,
            "num_paths": num_paths,
            "initial_amount": initial_amount,
            "monthly_contribution": monthly_contribution,
            "years": years,
            "annual_return_pct": round(annual_return * 100, 2),
            "volatility_pct": round(volatility * 100, 2),
            "scenario": scenario,
            "avg_final_value": round(avg_final, 2),
            "avg_interest_earned": round(avg_interest, 2),
            "avg_interest_contribution_pct": round((avg_interest / avg_final) * 100, 2) if avg_final > 0 else 0.0,
            "min_final_value": round(min_final, 2),
            "max_final_value": round(max_final, 2),
            "range_pct": round(((max_final - min_final) / avg_final) * 100, 2) if avg_final > 0 else 0.0,
            "paths": paths,
            "message": (
                f"En promedio, el {round((avg_interest / avg_final) * 100, 1)}% de tu riqueza final proviene del interés compuesto. "
                f"Con volatilidad del {round(volatility * 100, 1)}%, el rango de resultados es ${round(min_final):,} - ${round(max_final):,}."
                if avg_final > 0 else "Ingresa un monto o plazo válido."
            )
        }

    def _calculate_price_factor(
        self,
        month: int,
        market_timing: str,
        market_info: Dict[str, Any],
        annual_return: float
    ) -> float:
        """
        Calcula el factor de precio considerando timing y volatilidad.
        
        - Crisis: precio deprimido al inicio (-40%), recupera linealmente a 1
        - Burbuja: precio inflado al inicio (+40%), corrige linealmente a 1  
        - Normal: crecimiento base sin ajuste
        """
        # Crecimiento base con tasa mensual geométrica
        r_m = self._monthly_rate(annual_return)
        base = (1 + r_m) ** month

        # Aplicar efecto de timing
        if market_timing == "crisis":
            # Precio deprimido al inicio, recupera hacia 1
            if month <= market_info["recovery_months"]:
                drop = abs(market_info["initial_drop"])  # 0.40
                # Arranca en (1 - drop) y sube linealmente a 1
                phase = month / market_info["recovery_months"]
                timing = (1 - drop) + drop * phase
            else:
                timing = 1.0

        elif market_timing == "burbuja":
            # Precio inflado al inicio, corrige hacia 1
            if month <= market_info["recovery_months"]:
                premium = abs(market_info["initial_drop"])  # 0.40
                start = (1 + premium)  # 1.40
                phase = month / market_info["recovery_months"]
                timing = start - premium * phase  # Decae linealmente a 1
            else:
                timing = 1.0

        else:
            timing = 1.0

        return base * timing

    def _calculate_compound_interest(
        self,
        monthly_amount: float,
        monthly_return: float,
        total_months: int
    ) -> float:
        """
        Calcula valor final con interés compuesto.
        Nota: monthly_return debe venir de _monthly_rate() para precisión geométrica.
        """
        fv = 0.0
        for month in range(total_months):
            fv = (fv + monthly_amount) * (1 + monthly_return)
        return fv

    def _calculate_milestone(
        self,
        initial_amount: float,
        monthly_amount: float,
        years: int,
        annual_return: float,
        annual_inflation: float,
        max_portfolio_value: Optional[float] = None
    ) -> Dict[str, float]:
        """Calcula el valor acumulado en un hito especifico."""
        projection = self._calculate_with_inflation(
            initial_amount=initial_amount,
            monthly_contribution=monthly_amount,
            years=years,
            annual_return=annual_return,
            annual_inflation=annual_inflation,
            max_portfolio_value=max_portfolio_value
        )
        invested = projection["total_contributions"]
        value = projection["final_value"]

        return {
            "years": years,
            "invested": round(invested, 2),
            "value": round(value, 2),
            "gain": round(value - invested, 2)
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

    def _lump_sum_vs_dca_recommendation(self, difference_pct: float, winner: str) -> str:
        """Genera una recomendacion en lenguaje sencillo."""
        gap = abs(difference_pct)
        if gap <= 2:
            return "Resultados muy similares: elige la estrategia que puedas sostener con disciplina."

        if winner == "Lump Sum":
            if gap >= 10:
                return "Invertir todo al inicio maximiza el tiempo en el mercado, pero exige tolerancia a la volatilidad."
            return "Aprovechar un Lump Sum te da ventaja moderada cuando el mercado mantiene una tendencia alcista."

        if gap >= 10:
            return "DCA domina ampliamente porque amortigua caidas tempranas; ideal si el mercado luce volatil."
        return "DCA gana con margen moderado al repartir riesgos y evitar comprar todo en un pico."

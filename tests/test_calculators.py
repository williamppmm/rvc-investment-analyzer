#!/usr/bin/env python3
"""
Tests for InvestmentCalculator: retirement plan, DCA deflation, and retirement API endpoint.

Consolidates:
  - test_retirement_calculator.py
  - test_deflation.py
  - test_api_retirement.py
"""

import json
import pytest
from investment_calculator import InvestmentCalculator


# ---------------------------------------------------------------------------
# Retirement plan (unit tests)
# ---------------------------------------------------------------------------

class TestRetirementPlan:
    def setup_method(self):
        self.calc = InvestmentCalculator()

    def test_basic(self):
        result = self.calc.calculate_retirement_plan(
            current_age=35,
            retirement_age=65,
            initial_amount=10000,
            monthly_contribution=500,
            annual_return=0.07,
            annual_inflation=0.03,
            include_yearly_detail=True,
        )

        assert "input" in result
        assert "results" in result
        assert "scenarios" in result
        assert "yearly_projections" in result
        assert "milestones" in result
        assert "composition" in result

        assert result["input"]["current_age"] == 35
        assert result["input"]["retirement_age"] == 65
        assert result["input"]["years_to_retirement"] == 30

        assert result["results"]["final_capital"] > 0
        assert result["results"]["total_contributions"] > 0
        assert result["results"]["total_interest"] > 0

        total = (
            result["results"]["initial_capital"]
            + result["results"]["total_contributions"]
            + result["results"]["total_interest"]
        )
        assert abs(total - result["results"]["final_capital"]) < 1.0

        assert result["scenarios"]["optimista"]["final_value"] > result["scenarios"]["realista"]["final_value"]
        assert result["scenarios"]["realista"]["final_value"] > result["scenarios"]["conservador"]["final_value"]

        assert len(result["yearly_projections"]) <= 30
        last_year = result["yearly_projections"][-1]
        assert abs(last_year["portfolio_value"] - result["results"]["final_capital"]) < 1.0

        composition_total = (
            result["composition"]["initial_pct"]
            + result["composition"]["contributions_pct"]
            + result["composition"]["interest_pct"]
        )
        assert abs(composition_total - 100.0) < 0.1

    def test_inflation_adjustment(self):
        result = self.calc.calculate_retirement_plan(
            current_age=30,
            retirement_age=40,
            initial_amount=0,
            monthly_contribution=1000,
            annual_return=0.07,
            annual_inflation=0.03,
            include_yearly_detail=True,
        )

        yearly = result["yearly_projections"]
        year1 = yearly[0]["annual_contribution"]
        year10 = yearly[9]["annual_contribution"]
        expected = year1 * (1.03 ** 9)
        assert abs(year10 - expected) < 100

    def test_validations(self):
        with pytest.raises(ValueError, match="Edad actual debe estar entre 18 y 75"):
            self.calc.calculate_retirement_plan(
                current_age=17, retirement_age=65,
                initial_amount=10000, monthly_contribution=500,
                annual_return=0.07, annual_inflation=0.03,
            )

        with pytest.raises(ValueError, match="mayor a la edad actual"):
            self.calc.calculate_retirement_plan(
                current_age=65, retirement_age=60,
                initial_amount=10000, monthly_contribution=500,
                annual_return=0.07, annual_inflation=0.03,
            )

        with pytest.raises(ValueError, match="Rendimiento anual debe estar entre -10% y \\+20%"):
            self.calc.calculate_retirement_plan(
                current_age=35, retirement_age=65,
                initial_amount=10000, monthly_contribution=500,
                annual_return=0.25, annual_inflation=0.03,
            )

    def test_milestones(self):
        result = self.calc.calculate_retirement_plan(
            current_age=25,
            retirement_age=65,
            initial_amount=50000,
            monthly_contribution=1000,
            annual_return=0.08,
            annual_inflation=0.03,
            include_yearly_detail=True,
        )

        milestones = result["milestones"]
        assert len(milestones) > 0

        for i in range(len(milestones) - 1):
            assert milestones[i]["amount"] < milestones[i + 1]["amount"]
            assert milestones[i]["year"] <= milestones[i + 1]["year"]

        for m in milestones:
            for field in ("amount", "year", "age", "label"):
                assert field in m
            assert 25 <= m["age"] <= 65

    def test_no_inflation(self):
        result = self.calc.calculate_retirement_plan(
            current_age=40,
            retirement_age=50,
            initial_amount=0,
            monthly_contribution=1000,
            annual_return=0.06,
            annual_inflation=0.0,
            include_yearly_detail=True,
        )

        expected_annual = 1000 * 12
        for year_data in result["yearly_projections"]:
            assert abs(year_data["annual_contribution"] - expected_annual) < 1.0

    def test_scenarios_difference(self):
        result = self.calc.calculate_retirement_plan(
            current_age=30,
            retirement_age=60,
            initial_amount=20000,
            monthly_contribution=800,
            annual_return=0.08,
            annual_inflation=0.03,
        )

        scenarios = result["scenarios"]
        conservador = scenarios["conservador"]["final_value"]
        realista = scenarios["realista"]["final_value"]
        optimista = scenarios["optimista"]["final_value"]

        assert (realista - conservador) / conservador > 0.05
        assert (optimista - realista) / realista > 0.05


# ---------------------------------------------------------------------------
# Deflation / real-value calculations (unit tests)
# ---------------------------------------------------------------------------

class TestDeflation:
    def setup_method(self):
        self.calc = InvestmentCalculator()

    def test_dca_zero_inflation_no_real_values(self):
        result = self.calc.calculate_dca(
            monthly_amount=1000, years=10,
            scenario="moderado", market_timing="normal",
            annual_inflation=0.0,
        )
        assert result["results"]["final_value_real"] is None
        assert result["results"]["total_invested_real"] is None
        assert result["results"]["total_gain_real"] is None
        assert result["results"]["total_return_real_pct"] is None

    def test_dca_with_inflation(self):
        result = self.calc.calculate_dca(
            monthly_amount=1000, years=10,
            scenario="moderado", market_timing="normal",
            annual_inflation=0.03,
        )
        assert result["results"]["final_value_real"] is not None
        assert result["results"]["final_value_real"] < result["results"]["final_value"]
        assert result["results"]["total_invested_real"] < result["results"]["total_invested"]

        expected = 1.03 ** 10
        actual = result["results"]["final_value"] / result["results"]["final_value_real"]
        assert abs(actual - expected) / expected < 0.01

    def test_dca_deflation_factor_precision(self):
        result = self.calc.calculate_dca(
            monthly_amount=500, years=20,
            scenario="conservador", market_timing="normal",
            annual_inflation=0.05,
        )
        expected = 1.05 ** 20
        actual = result["results"]["final_value"] / result["results"]["final_value_real"]
        assert abs(actual - expected) / expected < 0.005

    def test_retirement_zero_inflation_no_real_values(self):
        result = self.calc.calculate_retirement_plan(
            current_age=30, retirement_age=65,
            initial_amount=10000, monthly_contribution=1000,
            annual_return=0.10, annual_inflation=0.0,
        )
        assert result["results"]["final_capital_real"] is None
        assert result["results"]["total_contributions_real"] is None
        assert result["results"]["total_interest_real"] is None

    def test_retirement_with_inflation(self):
        result = self.calc.calculate_retirement_plan(
            current_age=25, retirement_age=60,
            initial_amount=5000, monthly_contribution=800,
            annual_return=0.10, annual_inflation=0.025,
        )
        assert result["results"]["final_capital_real"] is not None
        assert result["results"]["final_capital_real"] < result["results"]["final_capital"]
        assert result["results"]["total_interest_real"] < result["results"]["total_interest"]

    def test_retirement_deflation_consistency(self):
        result = self.calc.calculate_retirement_plan(
            current_age=40, retirement_age=65,
            initial_amount=20000, monthly_contribution=1500,
            annual_return=0.10, annual_inflation=0.03,
        )
        years = result["input"]["effective_years"]
        expected_real = result["results"]["final_capital"] / (1.03 ** years)
        error = abs(result["results"]["final_capital_real"] - expected_real) / expected_real
        assert error < 0.01

    def test_high_inflation_impact(self):
        result = self.calc.calculate_dca(
            monthly_amount=500, years=15,
            scenario="optimista", market_timing="normal",
            annual_inflation=0.08,
        )
        expected_ratio = 1 / (1.08 ** 15)
        actual_ratio = result["results"]["final_value_real"] / result["results"]["final_value"]
        assert abs(actual_ratio - expected_ratio) / expected_ratio < 0.15

    def test_indexing_effect(self):
        result_with = self.calc.calculate_dca(
            monthly_amount=1000, years=15,
            scenario="moderado", market_timing="normal",
            annual_inflation=0.03,
        )
        result_without = self.calc.calculate_dca(
            monthly_amount=1000, years=15,
            scenario="moderado", market_timing="normal",
            annual_inflation=0.0,
        )
        assert result_with["results"]["final_value_real"] is not None
        assert result_without["results"]["final_value_real"] is None

    def test_real_gain_calculation(self):
        result = self.calc.calculate_dca(
            monthly_amount=2000, years=8,
            scenario="realista", market_timing="normal",
            annual_inflation=0.04,
        )
        expected = result["results"]["final_value_real"] - result["results"]["total_invested_real"]
        assert abs(result["results"]["total_gain_real"] - expected) < 1.0

    def test_real_return_percentage(self):
        result = self.calc.calculate_dca(
            monthly_amount=1500, years=12,
            scenario="moderado", market_timing="normal",
            annual_inflation=0.025,
        )
        expected = (
            (result["results"]["final_value_real"] / result["results"]["total_invested_real"]) - 1
        ) * 100
        assert abs(result["results"]["total_return_real_pct"] - expected) < 0.1


# ---------------------------------------------------------------------------
# Retirement API endpoint (integration test)
# ---------------------------------------------------------------------------

class TestRetirementAPIEndpoint:
    def setup_method(self):
        from app import app
        self.client = app.test_client()

    def test_retirement_endpoint_success(self):
        payload = {
            "calculation_type": "retirement_plan",
            "current_age": 35,
            "retirement_age": 65,
            "initial_amount": 10000,
            "monthly_amount": 500,
            "scenario": "moderado",
            "annual_inflation": 0.03,
        }
        response = self.client.post(
            "/api/calcular-inversion",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200

        data = json.loads(response.data)
        assert data.get("calculation_type") == "retirement_plan"

        result = data.get("result", {})
        assert "results" in result
        assert result["results"]["final_capital"] > 0
        assert "scenarios" in result
        assert "milestones" in result
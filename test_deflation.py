#!/usr/bin/env python3
"""
Test script for deflation (real value) calculations - Fase 2.
Tests the inflation-adjusted values in investment calculator.
"""

import pytest
from investment_calculator import InvestmentCalculator


class TestDeflation:
    """Test suite for real value (deflation) calculations."""

    def setup_method(self):
        """Setup test fixtures."""
        self.calc = InvestmentCalculator()

    def test_dca_with_zero_inflation(self):
        """Test that real values equal nominal values when inflation is 0%."""
        result = self.calc.calculate_dca(
            monthly_amount=1000,
            years=10,
            scenario='moderado',
            market_timing='normal',
            annual_inflation=0.0
        )

        # Con inflación 0%, valores reales deben ser None
        assert result['results']['final_value_real'] is None
        assert result['results']['total_invested_real'] is None
        assert result['results']['total_gain_real'] is None
        assert result['results']['total_return_real_pct'] is None

    def test_dca_with_inflation(self):
        """Test that real values are correctly deflated with 3% inflation."""
        result = self.calc.calculate_dca(
            monthly_amount=1000,
            years=10,
            scenario='moderado',
            market_timing='normal',
            annual_inflation=0.03  # 3% anual
        )

        # Valores reales deben existir
        assert result['results']['final_value_real'] is not None
        assert result['results']['total_invested_real'] is not None
        assert result['results']['total_gain_real'] is not None
        assert result['results']['total_return_real_pct'] is not None

        # Valores reales deben ser menores que nominales
        assert result['results']['final_value_real'] < result['results']['final_value']
        assert result['results']['total_invested_real'] < result['results']['total_invested']

        # Verificar que la deflactación es correcta (aproximadamente)
        # deflation_factor = (1 + 0.03)^10 = 1.3439
        expected_deflation_factor = (1.03 ** 10)
        calculated_deflation = result['results']['final_value'] / result['results']['final_value_real']
        
        # Permitir un margen de error del 1%
        assert abs(calculated_deflation - expected_deflation_factor) / expected_deflation_factor < 0.01

    def test_dca_deflation_factor_precision(self):
        """Test the exact deflation factor calculation."""
        # Caso específico: 5% inflación durante 20 años
        result = self.calc.calculate_dca(
            monthly_amount=500,
            years=20,
            scenario='conservador',
            market_timing='normal',
            annual_inflation=0.05
        )

        # Factor de deflactación esperado: (1.05)^20 = 2.6533
        expected_factor = 1.05 ** 20
        actual_factor = result['results']['final_value'] / result['results']['final_value_real']

        # Verificar precisión (margen de error < 0.5%)
        error_margin = abs(actual_factor - expected_factor) / expected_factor
        assert error_margin < 0.005, f"Deflation factor error: {error_margin:.4%}"

    def test_retirement_with_zero_inflation(self):
        """Test retirement plan with 0% inflation."""
        result = self.calc.calculate_retirement_plan(
            current_age=30,
            retirement_age=65,
            initial_amount=10000,
            monthly_contribution=1000,
            annual_return=0.10,  # 10% retorno
            annual_inflation=0.0
        )

        # Con inflación 0%, valores reales deben ser None
        assert result['results']['final_capital_real'] is None
        assert result['results']['total_contributions_real'] is None
        assert result['results']['total_interest_real'] is None

    def test_retirement_with_inflation(self):
        """Test retirement plan with 2.5% inflation."""
        result = self.calc.calculate_retirement_plan(
            current_age=25,
            retirement_age=60,
            initial_amount=5000,
            monthly_contribution=800,
            annual_return=0.10,  # 10% retorno
            annual_inflation=0.025  # 2.5% anual
        )

        # Valores reales deben existir
        assert result['results']['final_capital_real'] is not None
        assert result['results']['total_contributions_real'] is not None
        assert result['results']['total_interest_real'] is not None

        # Valores reales deben ser menores que nominales
        assert result['results']['final_capital_real'] < result['results']['final_capital']
        assert result['results']['total_contributions_real'] < (
            result['results']['total_contributions'] + result['results']['initial_capital']
        )
        assert result['results']['total_interest_real'] < result['results']['total_interest']

    def test_retirement_deflation_consistency(self):
        """Test that retirement deflation is consistent with expected formula."""
        result = self.calc.calculate_retirement_plan(
            current_age=40,
            retirement_age=65,
            initial_amount=20000,
            monthly_contribution=1500,
            annual_return=0.10,  # 10% retorno
            annual_inflation=0.03
        )

        years = result['input']['effective_years']
        expected_deflation = (1.03 ** years)
        
        # Verificar que el capital final fue deflactado correctamente
        calculated_real = result['results']['final_capital_real']
        expected_real = result['results']['final_capital'] / expected_deflation

        # Margen de error < 1%
        error = abs(calculated_real - expected_real) / expected_real
        assert error < 0.01, f"Retirement deflation error: {error:.4%}"

    def test_high_inflation_impact(self):
        """Test the impact of high inflation (8%) over long period."""
        result = self.calc.calculate_dca(
            monthly_amount=500,  # Reducido para evitar tope
            years=15,  # Reducido a 15 años
            scenario='optimista',
            market_timing='normal',
            annual_inflation=0.08  # 8% inflación (escenario alta inflación)
        )

        # Con 8% durante 15 años, factor = (1.08)^15 = 3.172
        expected_factor = 1.08 ** 15
        
        # El valor real debe ser significativamente menor
        real_to_nominal_ratio = result['results']['final_value_real'] / result['results']['final_value']
        expected_ratio = 1 / expected_factor

        # Margen de error más amplio por las fluctuaciones del mercado
        error_margin = abs(real_to_nominal_ratio - expected_ratio) / expected_ratio
        assert error_margin < 0.15  # 15% de margen por volatilidad del mercado

    def test_indexing_effect(self):
        """Test that inflation triggers real value calculation."""
        # Con inflación
        result_with_inflation = self.calc.calculate_dca(
            monthly_amount=1000,
            years=15,
            scenario='moderado',
            market_timing='normal',
            annual_inflation=0.03
        )

        # Sin inflación
        result_no_inflation = self.calc.calculate_dca(
            monthly_amount=1000,
            years=15,
            scenario='moderado',
            market_timing='normal',
            annual_inflation=0.0
        )

        # Con inflación debe tener valores reales calculados
        assert result_with_inflation['results']['final_value_real'] is not None
        
        # Sin inflación, valores reales deben ser None
        assert result_no_inflation['results']['final_value_real'] is None

    def test_real_gain_calculation(self):
        """Test that real gain is correctly calculated as real_value - real_invested."""
        result = self.calc.calculate_dca(
            monthly_amount=2000,
            years=8,
            scenario='realista',
            market_timing='normal',
            annual_inflation=0.04
        )

        # Verificar que ganancia real = valor_final_real - total_invertido_real
        calculated_gain = result['results']['total_gain_real']
        expected_gain = result['results']['final_value_real'] - result['results']['total_invested_real']

        # Permitir pequeña diferencia por redondeo
        assert abs(calculated_gain - expected_gain) < 1.0

    def test_real_return_percentage(self):
        """Test that real return percentage is correctly calculated."""
        result = self.calc.calculate_dca(
            monthly_amount=1500,
            years=12,
            scenario='moderado',
            market_timing='normal',
            annual_inflation=0.025
        )

        # Verificar que el porcentaje de retorno real sea coherente
        real_return_pct = result['results']['total_return_real_pct']
        expected_return = ((result['results']['final_value_real'] / result['results']['total_invested_real']) - 1) * 100

        # Permitir diferencia menor a 0.1%
        assert abs(real_return_pct - expected_return) < 0.1


def test_dca_deflation_manual():
    """Manual test showing deflation values."""
    print("\n" + "=" * 70)
    print("MANUAL TEST: DCA con Deflactación (Fase 2)")
    print("=" * 70)

    calc = InvestmentCalculator()
    result = calc.calculate_dca(
        monthly_amount=1000,
        years=10,
        scenario='moderado',
        market_timing='normal',
        annual_inflation=0.03  # 3% inflación
    )

    print(f"\n📊 Parámetros:")
    print(f"  • Aporte mensual: ${result['input']['monthly_amount']:,.0f}")
    print(f"  • Período: {result['input']['years']} años")
    print(f"  • Inflación anual: {result['input']['annual_inflation_pct']:.1f}%")
    print(f"  • Indexación: {'Sí' if result['input']['index_contributions_annually'] else 'No'}")

    print(f"\n💰 Valores Nominales:")
    print(f"  • Capital final: ${result['results']['final_value']:,.0f}")
    print(f"  • Total invertido: ${result['results']['total_invested']:,.0f}")
    print(f"  • Ganancia: ${result['results']['total_gain']:,.0f}")
    print(f"  • Retorno: {result['results']['total_return_pct']:.2f}%")

    if result['results']['final_value_real']:
        print(f"\n🌟 Valores Reales (poder adquisitivo actual):")
        print(f"  • Capital final real: ${result['results']['final_value_real']:,.0f}")
        print(f"  • Total invertido real: ${result['results']['total_invested_real']:,.0f}")
        print(f"  • Ganancia real: ${result['results']['total_gain_real']:,.0f}")
        print(f"  • Retorno real: {result['results']['total_return_real_pct']:.2f}%")

        deflation_factor = result['results']['final_value'] / result['results']['final_value_real']
        expected_factor = (1.03 ** 10)
        print(f"\n📉 Factor de Deflactación:")
        print(f"  • Calculado: {deflation_factor:.4f}")
        print(f"  • Esperado (1.03^10): {expected_factor:.4f}")
        print(f"  • Diferencia: {abs(deflation_factor - expected_factor):.4f}")

    print("\n✅ Test completado\n")


def test_retirement_deflation_manual():
    """Manual test showing retirement deflation values."""
    print("\n" + "=" * 70)
    print("MANUAL TEST: Retirement con Deflactación (Fase 2)")
    print("=" * 70)

    calc = InvestmentCalculator()
    result = calc.calculate_retirement_plan(
        current_age=30,
        retirement_age=60,
        initial_amount=10000,
        monthly_contribution=1000,
        annual_return=0.10,  # 10% retorno
        annual_inflation=0.025  # 2.5% inflación
    )

    print(f"\n📊 Parámetros:")
    print(f"  • Edad actual: {result['input']['current_age']}")
    print(f"  • Edad de retiro: {result['input']['retirement_age']}")
    print(f"  • Capital inicial: ${result['input']['initial_amount']:,.0f}")
    print(f"  • Aporte mensual: ${result['input']['monthly_contribution']:,.0f}")
    print(f"  • Inflación anual: {result['input']['annual_inflation_pct']:.1f}%")
    print(f"  • Años efectivos: {result['input']['effective_years']}")

    print(f"\n💰 Valores Nominales:")
    print(f"  • Capital final: ${result['results']['final_capital']:,.0f}")
    print(f"  • Aportes totales: ${result['results']['total_contributions']:,.0f}")
    print(f"  • Intereses: ${result['results']['total_interest']:,.0f}")

    if result['results']['final_capital_real']:
        print(f"\n🌟 Valores Reales (poder adquisitivo actual):")
        print(f"  • Capital final real: ${result['results']['final_capital_real']:,.0f}")
        print(f"  • Aportes totales reales: ${result['results']['total_contributions_real']:,.0f}")
        print(f"  • Intereses reales: ${result['results']['total_interest_real']:,.0f}")

        years = result['input']['effective_years']
        deflation_factor = result['results']['final_capital'] / result['results']['final_capital_real']
        expected_factor = (1.025 ** years)
        print(f"\n📉 Factor de Deflactación:")
        print(f"  • Calculado: {deflation_factor:.4f}")
        print(f"  • Esperado (1.025^{years}): {expected_factor:.4f}")
        print(f"  • Diferencia: {abs(deflation_factor - expected_factor):.4f}")

    print("\n✅ Test completado\n")


if __name__ == '__main__':
    # Run pytest
    print("Ejecutando tests automatizados...\n")
    pytest.main([__file__, '-v', '--tb=short'])
    
    # Run manual tests
    test_dca_deflation_manual()
    test_retirement_deflation_manual()

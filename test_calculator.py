#!/usr/bin/env python3
"""
Test script for investment calculator.
"""

from investment_calculator import InvestmentCalculator

def test_dca():
    """Test DCA calculation."""
    print("=" * 60)
    print("TEST 1: Dollar Cost Averaging (DCA)")
    print("=" * 60)

    ic = InvestmentCalculator()
    result = ic.calculate_dca(500, 10, 'moderado', 'normal', False)

    print(f"Inversión mensual: ${result['input']['monthly_amount']:,.0f}")
    print(f"Años: {result['input']['years']}")
    print(f"Escenario: {result['input']['scenario']}")
    print(f"Total invertido: ${result['results']['total_invested']:,.0f}")
    print(f"Valor final: ${result['results']['final_value']:,.0f}")
    print(f"Ganancia: ${result['results']['total_gain']:,.0f}")
    print(f"Retorno: {result['results']['total_return_pct']:.1f}%")
    print()
    print("Insights:")
    for insight in result['insights']:
        print(f"  - {insight}")
    print()


def test_lump_sum_vs_dca():
    """Test Lump Sum vs DCA comparison."""
    print("=" * 60)
    print("TEST 2: Lump Sum vs DCA")
    print("=" * 60)

    ic = InvestmentCalculator()
    result = ic.compare_lump_sum_vs_dca(10000, 10, 'moderado')

    print(f"Monto total: ${result['total_amount']:,.0f}")
    print(f"Años: {result['years']}")
    print()
    print("Lump Sum (Todo al inicio):")
    print(f"  Valor final: ${result['lump_sum']['final_value']:,.0f}")
    print(f"  Ganancia: ${result['lump_sum']['total_gain']:,.0f}")
    print(f"  Retorno: {result['lump_sum']['return_pct']:.1f}%")
    print()
    print("DCA (Mensual):")
    print(f"  Monto mensual: ${result['dca']['monthly_amount']:,.2f}")
    print(f"  Valor final: ${result['dca']['final_value']:,.0f}")
    print(f"  Ganancia: ${result['dca']['total_gain']:,.0f}")
    print(f"  Retorno: {result['dca']['return_pct']:.1f}%")
    print()
    print(f"Ganador: {result['comparison']['winner']}")
    print(f"Diferencia: ${result['comparison']['difference']:,.0f} ({result['comparison']['difference_pct']:.1f}%)")
    print(f"Recomendación: {result['comparison']['recommendation']}")
    print()


def test_compound_interest():
    """Test compound interest impact."""
    print("=" * 60)
    print("TEST 3: Interés Compuesto")
    print("=" * 60)

    ic = InvestmentCalculator()
    result = ic.calculate_compound_interest_impact(5000, 300, 20, 0.10)

    print(f"Inversión inicial: ${result['initial_amount']:,.0f}")
    print(f"Aporte mensual: ${result['monthly_contribution']:,.0f}")
    print(f"Años: {result['years']}")
    print(f"Retorno anual: {result['annual_return_pct']:.0f}%")
    print()
    print(f"Total aportado: ${result['total_contributed']:,.0f}")
    print(f"Valor final: ${result['final_value']:,.0f}")
    print(f"Intereses ganados: ${result['interest_earned']:,.0f}")
    print(f"Contribución del interés: {result['interest_contribution_pct']:.1f}%")
    print()
    print(f"Mensaje: {result['message']}")
    print()


def test_scenarios():
    """Test different scenarios."""
    print("=" * 60)
    print("TEST 4: Comparación de Escenarios")
    print("=" * 60)

    ic = InvestmentCalculator()
    scenarios = ['conservador', 'moderado', 'optimista']

    print("DCA: $500/mes durante 10 años\n")

    for scenario in scenarios:
        result = ic.calculate_dca(500, 10, scenario, 'normal', False)
        print(f"{scenario.upper():12} ({ic.HISTORICAL_RETURNS[scenario]*100:.0f}% anual):")
        print(f"  Valor final: ${result['results']['final_value']:,.0f}")
        print(f"  Ganancia: ${result['results']['total_gain']:,.0f} ({result['results']['total_return_pct']:.1f}%)")
        print()


def test_market_timing():
    """Test market timing scenarios."""
    print("=" * 60)
    print("TEST 5: Impacto del Timing de Mercado")
    print("=" * 60)

    ic = InvestmentCalculator()
    timings = ['crisis', 'normal', 'burbuja']

    print("DCA: $500/mes durante 10 años (escenario moderado)\n")

    for timing in timings:
        result = ic.calculate_dca(500, 10, 'moderado', timing, False)
        timing_label = ic.MARKET_SCENARIOS[timing]['label']
        print(f"{timing_label}:")
        print(f"  Valor final: ${result['results']['final_value']:,.0f}")
        print(f"  Ganancia: ${result['results']['total_gain']:,.0f} ({result['results']['total_return_pct']:.1f}%)")
        print()


if __name__ == '__main__':
    test_dca()
    test_lump_sum_vs_dca()
    test_compound_interest()
    test_scenarios()
    test_market_timing()

    print("=" * 60)
    print("✅ TODOS LOS TESTS COMPLETADOS")
    print("=" * 60)

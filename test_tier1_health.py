#!/usr/bin/env python3
"""
Tests para Mejora #6: Net Debt/EBITDA (Sistema TIER1/TIER2 para Health)

Verificaciones:
1. TIER1 Health con Net Debt/EBITDA + Interest Coverage
2. TIER2 Health fallback cuando faltan métricas TIER1
3. Cálculo de métricas derivadas (Net Debt/EBITDA, Interest Coverage)
4. Comparación TIER1 vs TIER2
5. Casos edge: caja neta, cobertura insuficiente
"""

import sys
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from analyzers.equity_analyzer import EquityAnalyzer


def test_tier1_health():
    """Test 1: Health TIER1 con Net Debt/EBITDA + Interest Coverage."""
    print("\n" + "=" * 60)
    print("TEST 1: Health TIER1 (Net Debt/EBITDA + Interest Coverage)")
    print("=" * 60)
    
    analyzer = EquityAnalyzer()
    
    # Empresa con salud TIER1 excelente
    # Net Debt/EBITDA = 1.2x (bajo), Interest Coverage = 12x (alto)
    metrics = {
        "net_debt_to_ebitda": 1.2,
        "interest_coverage": 12.0,
        "total_debt": 500_000_000,
        "cash_and_equivalents": 200_000_000,
        "ebitda": 250_000_000,
        "ebit": 180_000_000,
        "interest_expense": 15_000_000,
    }
    
    scores = analyzer.calculate_all_scores(metrics)
    health = scores["breakdown"]["health"]
    
    print(f"\n✅ Empresa con salud TIER1 excelente:")
    print(f"   - Net Debt/EBITDA: {metrics['net_debt_to_ebitda']:.2f}x")
    print(f"   - Interest Coverage: {metrics['interest_coverage']:.2f}x")
    print(f"   - Health Score: {health['score']:.2f}/100")
    print(f"   - Método: {health.get('method', 'N/A')}")
    print(f"   - Tier: {health.get('tier', 'N/A')}")
    print(f"   - Used: {health.get('used_metrics', [])}")
    
    assert health["score"] >= 85, f"Esperado score >= 85, got {health['score']}"
    assert health.get("method") == "tier1_health", "Debería usar TIER1"
    assert health.get("tier") == "TIER1", "Tier debería ser TIER1"
    print("   ✅ Test 1 pasó: TIER1 health funcionando correctamente")


def test_tier2_health_fallback():
    """Test 2: Fallback a TIER2 cuando faltan métricas TIER1."""
    print("\n" + "=" * 60)
    print("TEST 2: Fallback a TIER2 Health (D/E + Current + Quick)")
    print("=" * 60)
    
    analyzer = EquityAnalyzer()
    
    # Empresa SIN métricas TIER1, solo TIER2
    metrics = {
        "debt_to_equity": 0.5,
        "current_ratio": 2.0,
        "quick_ratio": 1.5,
    }
    
    scores = analyzer.calculate_all_scores(metrics)
    health = scores["breakdown"]["health"]
    
    print(f"\n✅ Empresa sin métricas TIER1:")
    print(f"   - D/E: {metrics['debt_to_equity']:.2f}")
    print(f"   - Current Ratio: {metrics['current_ratio']:.2f}")
    print(f"   - Quick Ratio: {metrics['quick_ratio']:.2f}")
    print(f"   - Health Score: {health['score']:.2f}/100")
    print(f"   - Método: {health.get('method', 'N/A')}")
    print(f"   - Tier: {health.get('tier', 'N/A')}")
    
    assert health.get("method") == "tier2_health", "Debería usar TIER2"
    assert health.get("tier") == "TIER2", "Tier debería ser TIER2"
    print("   ✅ Test 2 pasó: Fallback a TIER2 funcionando")


def test_net_debt_calculation():
    """Test 3: Cálculo de Net Debt/EBITDA desde componentes."""
    print("\n" + "=" * 60)
    print("TEST 3: Cálculo de Net Debt/EBITDA Derivada")
    print("=" * 60)
    
    from data_agent import DataAgent
    
    agent = DataAgent()
    
    # Métricas base
    base_metrics = {
        "total_debt": 1_000_000_000,        # $1B deuda
        "cash_and_equivalents": 400_000_000, # $400M caja
        "ebitda": 200_000_000,              # $200M EBITDA
    }
    
    # Calcular derivada
    derived = agent._calculate_derived_metrics(base_metrics.copy())
    
    net_debt = base_metrics["total_debt"] - base_metrics["cash_and_equivalents"]
    expected_nd_ebitda = net_debt / base_metrics["ebitda"]  # (1000-400)/200 = 3.0
    
    print(f"\n✅ Cálculo de Net Debt/EBITDA:")
    print(f"   - Total Debt: ${base_metrics['total_debt']:,.0f}")
    print(f"   - Cash: ${base_metrics['cash_and_equivalents']:,.0f}")
    print(f"   - Net Debt: ${net_debt:,.0f}")
    print(f"   - EBITDA: ${base_metrics['ebitda']:,.0f}")
    print(f"   - Net Debt/EBITDA calculado: {derived.get('net_debt_to_ebitda', 0):.2f}x")
    print(f"   - Esperado: {expected_nd_ebitda:.2f}x")
    
    assert "net_debt_to_ebitda" in derived, "Debería calcular net_debt_to_ebitda"
    assert abs(derived["net_debt_to_ebitda"] - expected_nd_ebitda) < 0.01, "Cálculo incorrecto"
    print("   ✅ Test 3 pasó: Net Debt/EBITDA calculada correctamente")


def test_interest_coverage_calculation():
    """Test 4: Cálculo de Interest Coverage desde componentes."""
    print("\n" + "=" * 60)
    print("TEST 4: Cálculo de Interest Coverage Derivada")
    print("=" * 60)
    
    from data_agent import DataAgent
    
    agent = DataAgent()
    
    # Métricas base
    base_metrics = {
        "ebit": 180_000_000,        # $180M EBIT
        "interest_expense": 15_000_000,  # $15M intereses
    }
    
    # Calcular derivada
    derived = agent._calculate_derived_metrics(base_metrics.copy())
    
    expected_coverage = base_metrics["ebit"] / base_metrics["interest_expense"]  # 180/15 = 12.0x
    
    print(f"\n✅ Cálculo de Interest Coverage:")
    print(f"   - EBIT: ${base_metrics['ebit']:,.0f}")
    print(f"   - Interest Expense: ${base_metrics['interest_expense']:,.0f}")
    print(f"   - Interest Coverage calculado: {derived.get('interest_coverage', 0):.2f}x")
    print(f"   - Esperado: {expected_coverage:.2f}x")
    
    assert "interest_coverage" in derived, "Debería calcular interest_coverage"
    assert abs(derived["interest_coverage"] - expected_coverage) < 0.01, "Cálculo incorrecto"
    print("   ✅ Test 4 pasó: Interest Coverage calculada correctamente")


def test_net_cash_company():
    """Test 5: Empresa con caja neta (Net Debt < 0)."""
    print("\n" + "=" * 60)
    print("TEST 5: Empresa con Caja Neta (Net Debt < 0)")
    print("=" * 60)
    
    analyzer = EquityAnalyzer()
    
    # Empresa con más caja que deuda (tech giant)
    metrics = {
        "net_debt_to_ebitda": -0.5,  # Caja neta
        "interest_coverage": 50.0,    # Cobertura muy alta
    }
    
    scores = analyzer.calculate_all_scores(metrics)
    health = scores["breakdown"]["health"]
    
    print(f"\n✅ Empresa con caja neta:")
    print(f"   - Net Debt/EBITDA: {metrics['net_debt_to_ebitda']:.2f}x (CAJA NETA)")
    print(f"   - Interest Coverage: {metrics['interest_coverage']:.2f}x")
    print(f"   - Health Score: {health['score']:.2f}/100")
    
    assert health["score"] >= 95, f"Caja neta debería tener score >= 95, got {health['score']}"
    assert health.get("method") == "tier1_health", "Debería usar TIER1"
    print("   ✅ Test 5 pasó: Caja neta detectada correctamente")


def test_comparison_tier1_vs_tier2():
    """Test 6: Comparación TIER1 vs TIER2 para misma empresa."""
    print("\n" + "=" * 60)
    print("TEST 6: Comparación TIER1 vs TIER2")
    print("=" * 60)
    
    analyzer = EquityAnalyzer()
    
    # Empresa con TODAS las métricas (TIER1 + TIER2)
    metrics_full = {
        # TIER1
        "net_debt_to_ebitda": 2.5,  # Moderado
        "interest_coverage": 6.0,    # Bueno
        # TIER2
        "debt_to_equity": 1.2,       # Moderado-alto
        "current_ratio": 1.8,        # Aceptable
        "quick_ratio": 1.3,          # Aceptable
    }
    
    # Forzar TIER1
    scores_tier1 = analyzer.calculate_all_scores(metrics_full)
    health_tier1 = scores_tier1["breakdown"]["health"]
    
    # Forzar TIER2 (eliminar métricas TIER1)
    metrics_tier2 = {
        "debt_to_equity": 1.2,
        "current_ratio": 1.8,
        "quick_ratio": 1.3,
    }
    scores_tier2 = analyzer.calculate_all_scores(metrics_tier2)
    health_tier2 = scores_tier2["breakdown"]["health"]
    
    print(f"\n📊 Comparación para misma empresa:")
    print(f"   - TIER1 Score: {health_tier1['score']:.2f}/100 (método: {health_tier1.get('method')})")
    print(f"   - TIER2 Score: {health_tier2['score']:.2f}/100 (método: {health_tier2.get('method')})")
    print(f"   - Diferencia: {abs(health_tier1['score'] - health_tier2['score']):.2f} puntos")
    
    assert health_tier1.get("method") == "tier1_health", "TIER1 debería usarse cuando está disponible"
    assert health_tier2.get("method") == "tier2_health", "TIER2 debería usarse cuando falta TIER1"
    print("   ✅ Test 6 pasó: Sistema TIER1/TIER2 funciona correctamente")


def test_high_leverage_company():
    """Test 7: Empresa con alto apalancamiento (riesgo)."""
    print("\n" + "=" * 60)
    print("TEST 7: Empresa con Alto Apalancamiento")
    print("=" * 60)
    
    analyzer = EquityAnalyzer()
    
    # Empresa sobre-apalancada
    metrics = {
        "net_debt_to_ebitda": 6.5,  # Muy alto (riesgo)
        "interest_coverage": 1.2,    # Débil (apenas cubre intereses)
    }
    
    scores = analyzer.calculate_all_scores(metrics)
    health = scores["breakdown"]["health"]
    
    print(f"\n⚠️ Empresa sobre-apalancada:")
    print(f"   - Net Debt/EBITDA: {metrics['net_debt_to_ebitda']:.2f}x (MUY ALTO)")
    print(f"   - Interest Coverage: {metrics['interest_coverage']:.2f}x (DÉBIL)")
    print(f"   - Health Score: {health['score']:.2f}/100")
    
    assert health["score"] <= 50, f"Alto apalancamiento debería tener score <= 50, got {health['score']}"
    print("   ✅ Test 7 pasó: Riesgo de apalancamiento detectado")


def test_derived_metrics_integration():
    """Test 8: Integración completa con métricas derivadas."""
    print("\n" + "=" * 60)
    print("TEST 8: Integración Completa (Derivadas + TIER1)")
    print("=" * 60)
    
    from data_agent import DataAgent
    
    agent = DataAgent()
    analyzer = EquityAnalyzer()
    
    # Solo métricas base (sin derivadas)
    base_metrics = {
        "total_debt": 800_000_000,
        "cash_and_equivalents": 300_000_000,
        "ebitda": 250_000_000,
        "ebit": 200_000_000,
        "interest_expense": 20_000_000,
    }
    
    # Calcular derivadas
    full_metrics = agent._calculate_derived_metrics(base_metrics.copy())
    
    print(f"\n✅ Métricas base:")
    print(f"   - Total Debt: ${base_metrics['total_debt']:,.0f}")
    print(f"   - Cash: ${base_metrics['cash_and_equivalents']:,.0f}")
    print(f"   - EBITDA: ${base_metrics['ebitda']:,.0f}")
    print(f"   - EBIT: ${base_metrics['ebit']:,.0f}")
    print(f"   - Interest: ${base_metrics['interest_expense']:,.0f}")
    
    print(f"\n✅ Métricas derivadas calculadas:")
    print(f"   - Net Debt/EBITDA: {full_metrics.get('net_debt_to_ebitda', 'N/A')}")
    print(f"   - Interest Coverage: {full_metrics.get('interest_coverage', 'N/A')}")
    
    # Calcular scores con métricas completas
    scores = analyzer.calculate_all_scores(full_metrics)
    health = scores["breakdown"]["health"]
    
    print(f"\n✅ Scoring TIER1 con derivadas:")
    print(f"   - Health Score: {health['score']:.2f}/100")
    print(f"   - Método: {health.get('method', 'N/A')}")
    
    assert "net_debt_to_ebitda" in full_metrics, "Debería tener Net Debt/EBITDA"
    assert "interest_coverage" in full_metrics, "Debería tener Interest Coverage"
    assert health.get("method") == "tier1_health", "Debería usar TIER1 con derivadas"
    print("   ✅ Test 8 pasó: Integración completa funcionando")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TEST MEJORA #6: Net Debt/EBITDA (TIER1/TIER2 Health)")
    print("=" * 60)
    
    test_tier1_health()
    test_tier2_health_fallback()
    test_net_debt_calculation()
    test_interest_coverage_calculation()
    test_net_cash_company()
    test_comparison_tier1_vs_tier2()
    test_high_leverage_company()
    test_derived_metrics_integration()
    
    print("\n" + "=" * 60)
    print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
    print("=" * 60)
    
    print("\n🎉 Resumen:")
    print("   ✅ Health TIER1 con Net Debt/EBITDA + Interest Coverage")
    print("   ✅ Fallback a TIER2 (D/E + Current + Quick)")
    print("   ✅ Cálculo de métricas derivadas correcto")
    print("   ✅ Detección de caja neta (score 100)")
    print("   ✅ Detección de alto apalancamiento (score bajo)")
    print("   ✅ Integración completa DataAgent + EquityAnalyzer")
    print("\n   📊 Mejora #6 completada exitosamente!")

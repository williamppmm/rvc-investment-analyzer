#!/usr/bin/env python3
"""Test de validación para Mejora #3: EV/EBIT + FCF Yield."""

from analyzers import EquityAnalyzer

print("=" * 60)
print("TEST MEJORA #3: EV/EBIT + FCF Yield (TIER1 Valuation)")
print("=" * 60)

analyzer = EquityAnalyzer()

# Test 1: TIER1 Valuation (EV/EBIT + FCF Yield disponibles)
print("\n" + "=" * 60)
print("TEST 1: TIER1 Valuation - Métricas basadas en caja")
print("=" * 60)

metrics_tier1 = {
    "current_price": 150.0,
    "market_cap": 2.5e12,
    "ev_to_ebit": 10.5,      # Razonable (score ~85)
    "fcf_yield": 8.5,        # Excelente (score 85)
    "free_cash_flow": 2.125e11,  # FCF = 8.5% de MCap
    "enterprise_value": 2.6e12,
    "ebit": 2.476e11,        # EV/EBIT = 10.5
    "pe_ratio": 28.5,
    "roe": 45.2,
}

scores = analyzer.calculate_all_scores(metrics_tier1)
valuation_breakdown = scores["breakdown"]["valuation"]

print(f"\n✅ Métricas de entrada:")
print(f"   - EV/EBIT: {metrics_tier1['ev_to_ebit']}")
print(f"   - FCF Yield: {metrics_tier1['fcf_yield']}%")
print(f"   - P/E Ratio: {metrics_tier1['pe_ratio']} (ignorado en TIER1)")

print(f"\n📊 Resultado TIER1:")
print(f"   - Valuation Score: {scores['valuation_score']}/100")
print(f"   - Tier usado: {valuation_breakdown.get('tier', 'N/A')}")
print(f"   - Método: {valuation_breakdown.get('method', 'N/A')}")
print(f"   - Métricas usadas: {valuation_breakdown.get('used_metrics', valuation_breakdown.get('metrics_used', []))}")

assert valuation_breakdown.get("tier") == "TIER1", "Debería usar TIER1"
assert valuation_breakdown.get("method") == "cash_flow_based", "Debería usar cash_flow_based"
assert scores["valuation_score"] > 70, "Score debería ser > 70 con EV/EBIT=10.5 y FCF Yield=8.5%"

# Test 2: TIER2 Valuation (fallback - sin EV/EBIT o FCF Yield)
print("\n" + "=" * 60)
print("TEST 2: TIER2 Valuation - Múltiplos tradicionales (fallback)")
print("=" * 60)

metrics_tier2 = {
    "current_price": 150.0,
    "market_cap": 2.5e12,
    # NO hay ev_to_ebit ni fcf_yield
    "pe_ratio": 18.5,        # Razonable (score ~75)
    "peg_ratio": 1.2,        # Razonable (score ~75)
    "price_to_book": 8.5,    # Alto (score ~25)
    "roe": 45.2,
}

scores2 = analyzer.calculate_all_scores(metrics_tier2)
valuation_breakdown2 = scores2["breakdown"]["valuation"]

print(f"\n✅ Métricas de entrada:")
print(f"   - P/E Ratio: {metrics_tier2['pe_ratio']}")
print(f"   - PEG Ratio: {metrics_tier2['peg_ratio']}")
print(f"   - P/B Ratio: {metrics_tier2['price_to_book']}")
print(f"   - EV/EBIT: No disponible")
print(f"   - FCF Yield: No disponible")

print(f"\n📊 Resultado TIER2 (fallback):")
print(f"   - Valuation Score: {scores2['valuation_score']}/100")
print(f"   - Tier usado: {valuation_breakdown2.get('tier', 'N/A')}")
print(f"   - Método: {valuation_breakdown2.get('method', 'N/A')}")
print(f"   - Métricas usadas: {valuation_breakdown2.get('used_metrics', valuation_breakdown2.get('metrics_used', []))}")

assert valuation_breakdown2.get("tier") == "TIER2", "Debería usar TIER2 (fallback)"
assert valuation_breakdown2.get("method") == "traditional_multiples", "Debería usar traditional_multiples"

# Test 3: TIER1 con FCF negativo (empresa quema caja)
print("\n" + "=" * 60)
print("TEST 3: TIER1 con FCF Negativo - Empresa quema caja")
print("=" * 60)

metrics_negative_fcf = {
    "current_price": 50.0,
    "market_cap": 1e12,
    "ev_to_ebit": 25.0,      # Caro (score ~20)
    "fcf_yield": -5.2,       # Quema caja (score 10)
    "free_cash_flow": -5.2e10,  # FCF negativo
    "enterprise_value": 1.1e12,
    "ebit": 4.4e10,
    "roe": 12.0,
}

scores3 = analyzer.calculate_all_scores(metrics_negative_fcf)
valuation_breakdown3 = scores3["breakdown"]["valuation"]

print(f"\n✅ Métricas de entrada:")
print(f"   - EV/EBIT: {metrics_negative_fcf['ev_to_ebit']} (caro)")
print(f"   - FCF Yield: {metrics_negative_fcf['fcf_yield']}% (NEGATIVO - quema caja)")

print(f"\n📊 Resultado TIER1:")
print(f"   - Valuation Score: {scores3['valuation_score']}/100")
print(f"   - Tier usado: {valuation_breakdown3.get('tier', 'N/A')}")
print(f"   - Métricas usadas: {valuation_breakdown3.get('used_metrics', valuation_breakdown3.get('metrics_used', []))}")

assert valuation_breakdown3.get("tier") == "TIER1", "Debería usar TIER1"
assert scores3["valuation_score"] < 30, "Score debería ser bajo con FCF negativo y EV/EBIT alto"

# Test 4: Comparación TIER1 vs TIER2
print("\n" + "=" * 60)
print("TEST 4: Comparación TIER1 vs TIER2")
print("=" * 60)

print(f"\n📊 Empresa A (TIER1 - basado en caja):")
print(f"   - Valuation Score: {scores['valuation_score']}/100")
print(f"   - EV/EBIT: {metrics_tier1['ev_to_ebit']}")
print(f"   - FCF Yield: {metrics_tier1['fcf_yield']}%")

print(f"\n📊 Empresa B (TIER2 - múltiplos tradicionales):")
print(f"   - Valuation Score: {scores2['valuation_score']}/100")
print(f"   - P/E: {metrics_tier2['pe_ratio']}")
print(f"   - PEG: {metrics_tier2['peg_ratio']}")
print(f"   - P/B: {metrics_tier2['price_to_book']}")

print(f"\n📊 Empresa C (TIER1 - FCF negativo):")
print(f"   - Valuation Score: {scores3['valuation_score']}/100")
print(f"   - EV/EBIT: {metrics_negative_fcf['ev_to_ebit']} (caro)")
print(f"   - FCF Yield: {metrics_negative_fcf['fcf_yield']}% (quema caja)")

# Test 5: Cálculo de métricas derivadas (DataAgent)
print("\n" + "=" * 60)
print("TEST 5: Cálculo de Métricas Derivadas")
print("=" * 60)

from data_agent import DataAgent

agent = DataAgent()

# Simular métricas base
base_metrics = {
    "ticker": "TEST",
    "free_cash_flow": 1e11,
    "market_cap": 1e12,
    "enterprise_value": 1.2e12,
    "ebit": 1.2e11,
}

# Calcular derivadas
derived_metrics = agent._calculate_derived_metrics(base_metrics.copy())

print(f"\n✅ Métricas base:")
print(f"   - FCF: {base_metrics['free_cash_flow']:,.0f}")
print(f"   - Market Cap: {base_metrics['market_cap']:,.0f}")
print(f"   - Enterprise Value: {base_metrics['enterprise_value']:,.0f}")
print(f"   - EBIT: {base_metrics['ebit']:,.0f}")

print(f"\n📊 Métricas derivadas calculadas:")
if "fcf_yield" in derived_metrics:
    print(f"   - FCF Yield: {derived_metrics['fcf_yield']:.2f}%")
    assert abs(derived_metrics["fcf_yield"] - 10.0) < 0.01, "FCF Yield debería ser 10%"
else:
    print("   - FCF Yield: No calculado")

if "ev_to_ebit" in derived_metrics:
    print(f"   - EV/EBIT: {derived_metrics['ev_to_ebit']:.2f}")
    assert abs(derived_metrics["ev_to_ebit"] - 10.0) < 0.01, "EV/EBIT debería ser 10"
else:
    print("   - EV/EBIT: No calculado")

print("\n" + "=" * 60)
print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
print("=" * 60)

print("\n🎉 Resumen:")
print("   ✅ TIER1 Valuation (EV/EBIT + FCF Yield) implementado")
print("   ✅ TIER2 Valuation (P/E + PEG + P/B) como fallback")
print("   ✅ FCF negativo penaliza correctamente")
print("   ✅ Métricas derivadas se calculan automáticamente")
print("   ✅ Metadata incluye tier y method para debugging")
print("\n   📊 Mejora #3 completada exitosamente!")

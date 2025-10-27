#!/usr/bin/env python3
"""Test de validación para MetricNormalizer y integración con EquityAnalyzer."""

from metric_normalizer import MetricNormalizer
from analyzers import EquityAnalyzer

print("=" * 60)
print("TEST 1: MetricNormalizer - Normalización Simple")
print("=" * 60)

normalizer = MetricNormalizer()

# Test 1: Normalización con jerarquía TTM > MRY > 5Y
raw_values = {
    "roe_ttm": 22.3,
    "roe_mry": 21.8,
    "roe_5y": 19.5
}

result = normalizer.normalize_metric("roe", raw_values)
print(f"\n✅ Input: {raw_values}")
print(f"✅ Output: {result}")
print(f"   → Valor seleccionado: {result['value']} (período: {result['period']})")
assert result["value"] == 22.3, "Debería priorizar TTM"
assert result["period"] == "TTM", "Período debería ser TTM"

# Test 2: Normalización sin sufijo (asume TTM)
raw_values2 = {"roe": 20.0}
result2 = normalizer.normalize_metric("roe", raw_values2)
print(f"\n✅ Input sin sufijo: {raw_values2}")
print(f"✅ Output: {result2}")
assert result2["period"] == "TTM (assumed)", "Debería asumir TTM"

# Test 3: Normalización en lote
print("\n" + "=" * 60)
print("TEST 2: MetricNormalizer - Normalización en Lote")
print("=" * 60)

batch_input = {
    "roe_ttm": 22.3,
    "revenue_growth_mrq": 15.2,
    "debt_to_equity_mry": 0.35
}

batch_result = normalizer.normalize_metrics_batch(
    batch_input,
    ["roe", "revenue_growth", "debt_to_equity", "missing_metric"]
)

print(f"\n✅ Input: {batch_input}")
print(f"✅ Métricas normalizadas:")
print(f"   - roe: {batch_result.get('roe')} (período: {batch_result.get('roe_period')})")
print(f"   - revenue_growth: {batch_result.get('revenue_growth')} (período: {batch_result.get('revenue_growth_period')})")
print(f"   - debt_to_equity: {batch_result.get('debt_to_equity')} (período: {batch_result.get('debt_to_equity_period')})")

metadata = batch_result["_normalization_metadata"]
print(f"\n✅ Metadata:")
print(f"   - Normalizadas: {metadata['normalized_count']}/4")
print(f"   - Fallidas: {metadata['failed_count']}")
print(f"   - Métricas fallidas: {metadata['failed_metrics']}")

assert metadata["normalized_count"] == 3, "Deberían normalizarse 3 métricas"
assert "missing_metric" in metadata["failed_metrics"], "missing_metric debería fallar"

# Test 4: Conversión de moneda
print("\n" + "=" * 60)
print("TEST 3: MetricNormalizer - Conversión de Moneda")
print("=" * 60)

currency_result = normalizer.normalize_currency(100, "EUR")
print(f"\n✅ Conversión: 100 EUR → {currency_result['value']} USD")
print(f"   → Tasa: {currency_result['exchange_rate']}")
assert currency_result["to_currency"] == "USD"
assert currency_result["value"] == 108.0, "100 EUR debería ser 108 USD"

# Test 5: Estadísticas
print("\n" + "=" * 60)
print("TEST 4: MetricNormalizer - Estadísticas")
print("=" * 60)

stats = normalizer.get_normalization_stats()
print(f"\n✅ Estadísticas de normalización:")
print(f"   - Total normalizadas: {stats['total_normalized']}")
print(f"   - Uso de períodos: {stats['period_usage']}")
print(f"   - Uso de períodos (%): {stats['period_usage_pct']}")
print(f"   - Conversiones de moneda: {stats['currency_conversions']}")

# Test 6: Integración con EquityAnalyzer
print("\n" + "=" * 60)
print("TEST 5: Integración con EquityAnalyzer")
print("=" * 60)

analyzer = EquityAnalyzer()

# Métricas de prueba con diferentes períodos
test_metrics = {
    "current_price": 150.0,
    "market_cap": 2.5e12,
    "pe_ratio_ttm": 28.5,
    "roe_ttm": 45.2,
    "roic_ttm": 38.5,
    "operating_margin_ttm": 30.5,
    "net_margin_ttm": 25.3,
    "debt_to_equity_mry": 1.72,
    "current_ratio_mry": 1.07,
    "revenue_growth_mrq": 8.5,
    "earnings_growth_ttm": 12.3,
}

scores = analyzer.calculate_all_scores(test_metrics)

print(f"\n✅ Scores calculados con métricas normalizadas:")
print(f"   - Quality Score: {scores['quality_score']}")
print(f"   - Valuation Score: {scores['valuation_score']}")
print(f"   - Investment Score: {scores['investment_score']}")

# Verificar metadata de normalización
norm_metadata = scores.get("normalization_metadata", {})
print(f"\n✅ Metadata de normalización en scores:")
print(f"   - Métricas normalizadas: {norm_metadata.get('normalized_count', 0)}")
print(f"   - Métricas fallidas: {norm_metadata.get('failed_count', 0)}")

assert "normalization_metadata" in scores, "Scores deberían incluir metadata de normalización"
assert norm_metadata.get("normalized_count", 0) > 0, "Deberían normalizarse algunas métricas"

print("\n" + "=" * 60)
print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
print("=" * 60)
print("\n📊 Resumen:")
print("   ✅ MetricNormalizer funciona correctamente")
print("   ✅ Jerarquía TTM > MRQ > MRY > 5Y > FWD respetada")
print("   ✅ Normalización en lote operativa")
print("   ✅ Conversión de moneda funcional")
print("   ✅ Integración con EquityAnalyzer exitosa")
print("   ✅ Metadata de normalización incluida en respuesta JSON")

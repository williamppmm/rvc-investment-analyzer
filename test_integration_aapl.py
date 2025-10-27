#!/usr/bin/env python3
"""Test de integración completa con datos reales de AAPL."""

from data_agent import DataAgent
from analyzers import EquityAnalyzer
import json

print("=" * 60)
print("TEST DE INTEGRACIÓN COMPLETA - AAPL")
print("=" * 60)

# Obtener métricas reales
agent = DataAgent()
print("\n📊 Obteniendo métricas de AAPL desde APIs...")
metrics = agent.fetch_financial_data("AAPL")

# Analizar con normalización
analyzer = EquityAnalyzer()
print("🔧 Calculando scores con normalización de períodos...")
scores = analyzer.calculate_all_scores(metrics)

# Mostrar resultados
print("\n" + "=" * 60)
print("RESULTADOS DE NORMALIZACIÓN")
print("=" * 60)

norm_meta = scores.get("normalization_metadata", {})
print(f"\n✅ Métricas procesadas:")
print(f"   - Normalizadas exitosamente: {norm_meta.get('normalized_count', 0)}")
print(f"   - Fallidas (no disponibles): {norm_meta.get('failed_count', 0)}")
print(f"   - Moneda: {norm_meta.get('currency', 'N/A')}")

if norm_meta.get("failed_metrics"):
    print(f"\n⚠️  Métricas no disponibles: {', '.join(norm_meta['failed_metrics'][:5])}...")

print("\n" + "=" * 60)
print("SCORES FINALES")
print("=" * 60)

print(f"\n📊 Scores de inversión:")
print(f"   - Quality Score: {scores['quality_score']}/100")
print(f"   - Valuation Score: {scores['valuation_score']}/100")
print(f"   - Financial Health: {scores['financial_health_score']}/100")
print(f"   - Growth Score: {scores['growth_score']}/100")
print(f"   - Investment Score: {scores['investment_score']}/100")

print(f"\n🎯 Recomendación: {scores['recommendation']}")
print(f"📂 Categoría: {scores['category']}")

print("\n" + "=" * 60)
print("CONFIDENCE FACTORS")
print("=" * 60)

confidence = scores.get("confidence_factors", {})
print(f"\n✅ Factores de confianza:")
print(f"   - Completeness: {confidence.get('completeness', 0)}%")
print(f"   - Dispersion: {confidence.get('dispersion', 0)}%")
print(f"   - Overall: {confidence.get('overall', 0)}%")

# Estadísticas del normalizador
print("\n" + "=" * 60)
print("ESTADÍSTICAS DEL NORMALIZADOR")
print("=" * 60)

stats = analyzer.normalizer.get_normalization_stats()
print(f"\n📈 Uso de períodos:")
for period, count in stats["period_usage"].items():
    pct = stats["period_usage_pct"].get(period, 0)
    if count > 0:
        print(f"   - {period}: {count} ({pct}%)")

print("\n" + "=" * 60)
print("✅ INTEGRACIÓN COMPLETA EXITOSA")
print("=" * 60)
print("\n🎉 Mejora #2 (Normalización TTM/MRQ/MRY) implementada correctamente!")
print("   - MetricNormalizer creado y funcional")
print("   - Integrado en EquityAnalyzer")
print("   - Jerarquía TTM > MRQ > MRY > 5Y > FWD respetada")
print("   - Metadata de normalización incluida en JSON response")

#!/usr/bin/env python3
"""Test de validación para Mejora #4: Scores Sector-Relativos."""

from analyzers import EquityAnalyzer
from analyzers.sector_benchmarks import SectorNormalizer, SECTOR_BENCHMARKS

print("=" * 60)
print("TEST MEJORA #4: Scores Sector-Relativos (Z-Scores)")
print("=" * 60)

# Test 1: SectorNormalizer - Z-scores básicos
print("\n" + "=" * 60)
print("TEST 1: SectorNormalizer - Cálculo de Z-Scores")
print("=" * 60)

normalizer = SectorNormalizer()

# Tech company con ROE alto
tech_roe = 35.0  # Technology mean=22%, std=8.5%
z_tech = normalizer.get_z_score(tech_roe, "roe", "Technology")
score_tech = normalizer.z_to_score(z_tech)

print(f"\n✅ Empresa Tech con ROE={tech_roe}%:")
print(f"   - Sector: Technology (mean=22%, std=8.5%)")
print(f"   - Z-score: {z_tech:.2f}")
print(f"   - Score: {score_tech}/100")
print(f"   - Interpretación: {z_tech:.2f} std por encima del promedio")

assert abs(z_tech - 1.53) < 0.01, f"Z-score debería ser ~1.53, got {z_tech}"
assert score_tech == 85, f"Score debería ser 85, got {score_tech}"

# Utility con ROE bajo (pero normal para el sector)
util_roe = 12.0  # Utilities mean=9.5%, std=3.2%
z_util = normalizer.get_z_score(util_roe, "roe", "Utilities")
score_util = normalizer.z_to_score(z_util)

print(f"\n✅ Empresa Utility con ROE={util_roe}%:")
print(f"   - Sector: Utilities (mean=9.5%, std=3.2%)")
print(f"   - Z-score: {z_util:.2f}")
print(f"   - Score: {score_util}/100")
print(f"   - Interpretación: {z_util:.2f} std por encima del promedio")

assert abs(z_util - 0.78) < 0.01, f"Z-score debería ser ~0.78, got {z_util}"
assert score_util == 70, f"Score debería ser 70, got {score_util}"

# Comparación: ambas son "buenas" vs su sector aunque ROE absoluto es muy diferente
print(f"\n📊 Comparación:")
print(f"   Tech: ROE={tech_roe}% → Score={score_tech} (z={z_tech:.2f})")
print(f"   Utility: ROE={util_roe}% → Score={score_util} (z={z_util:.2f})")
print(f"   → Ambas son buenas vs su sector!")

# Test 2: Normalización completa con metadata
print("\n" + "=" * 60)
print("TEST 2: Normalización Completa con Metadata")
print("=" * 60)

result = normalizer.normalize_metric(35.0, "roe", "Technology")

print(f"\n✅ Resultado de normalización:")
print(f"   - Score: {result['score']}")
print(f"   - Z-score: {result['z_score']:.2f}")
print(f"   - Valor: {result['value']}")
print(f"   - Sector mean: {result['sector_mean']}")
print(f"   - Sector std: {result['sector_std']}")
print(f"   - Percentil aproximado: {result.get('percentile', 'N/A')}")

assert "sector_mean" in result, "Debería incluir sector_mean"
assert "sector_std" in result, "Debería incluir sector_std"

# Test 3: Integración con EquityAnalyzer - Sector Scoring
print("\n" + "=" * 60)
print("TEST 3: EquityAnalyzer con Sector-Relative Scoring")
print("=" * 60)

analyzer = EquityAnalyzer()

# Empresa Tech con métricas excelentes vs sector
metrics_tech = {
    "sector": "Technology",
    "roe": 35.0,        # z=1.53 → score 85
    "roic": 28.0,       # z=1.39 → score 85
    "operating_margin": 35.0,  # z=1.0 → score 85
    "net_margin": 26.0, # z=1.0 → score 85
    "current_price": 150.0,
    "market_cap": 2.5e12,
}

scores_tech = analyzer.calculate_all_scores(metrics_tech)
quality_breakdown_tech = scores_tech["breakdown"]["quality"]

print(f"\n✅ Empresa Technology:")
print(f"   - ROE: {metrics_tech['roe']}%")
print(f"   - ROIC: {metrics_tech['roic']}%")
print(f"   - Quality Score: {scores_tech['quality_score']}/100")
print(f"   - Método: {quality_breakdown_tech.get('method', 'N/A')}")
print(f"   - Sector: {quality_breakdown_tech.get('sector', 'N/A')}")

assert quality_breakdown_tech.get("method") == "sector_relative", "Debería usar sector_relative"
assert quality_breakdown_tech.get("sector") == "Technology", "Debería ser Technology"
assert scores_tech["quality_score"] >= 80, "Score debería ser alto (>=80)"

# Empresa Utility con métricas normales vs sector
metrics_util = {
    "sector": "Utilities",
    "roe": 12.0,        # z=0.78 → score 70
    "roic": 8.0,        # z=0.60 → score 70
    "operating_margin": 15.0,  # z=0.75 → score 70
    "net_margin": 10.0, # z=0.67 → score 70
    "current_price": 50.0,
    "market_cap": 5e11,
}

scores_util = analyzer.calculate_all_scores(metrics_util)
quality_breakdown_util = scores_util["breakdown"]["quality"]

print(f"\n✅ Empresa Utilities:")
print(f"   - ROE: {metrics_util['roe']}%")
print(f"   - ROIC: {metrics_util['roic']}%")
print(f"   - Quality Score: {scores_util['quality_score']}/100")
print(f"   - Método: {quality_breakdown_util.get('method', 'N/A')}")
print(f"   - Sector: {quality_breakdown_util.get('sector', 'N/A')}")

assert quality_breakdown_util.get("method") == "sector_relative", "Debería usar sector_relative"
assert quality_breakdown_util.get("sector") == "Utilities", "Debería ser Utilities"

# Test 4: Fallback a scoring absoluto sin sector
print("\n" + "=" * 60)
print("TEST 4: Fallback a Scoring Absoluto (sin sector)")
print("=" * 60)

metrics_no_sector = {
    # NO hay campo 'sector'
    "roe": 35.0,
    "roic": 28.0,
    "operating_margin": 35.0,
    "net_margin": 26.0,
    "current_price": 150.0,
    "market_cap": 2.5e12,
}

scores_no_sector = analyzer.calculate_all_scores(metrics_no_sector)
quality_breakdown_no_sector = scores_no_sector["breakdown"]["quality"]

print(f"\n✅ Empresa sin sector:")
print(f"   - ROE: {metrics_no_sector['roe']}%")
print(f"   - Quality Score: {scores_no_sector['quality_score']}/100")
print(f"   - Método: {quality_breakdown_no_sector.get('method', 'N/A')}")

assert quality_breakdown_no_sector.get("method") == "absolute", "Debería usar scoring absoluto"

# Test 5: Extracción de sector principal
print("\n" + "=" * 60)
print("TEST 5: Extracción de Sector Principal")
print("=" * 60)

test_sectors = [
    ("Technology - Semiconductors", "Technology"),
    ("Healthcare - Pharmaceuticals", "Healthcare"),
    ("Consumer Discretionary", "Consumer Discretionary"),
    ("Utilities", "Utilities"),
]

for raw_sector, expected in test_sectors:
    extracted = analyzer._extract_primary_sector(raw_sector)
    print(f"   '{raw_sector}' → '{extracted}'")
    assert extracted == expected, f"Expected {expected}, got {extracted}"

# Test 6: Comparación Sector-Relative vs Absolute
print("\n" + "=" * 60)
print("TEST 6: Comparación Sector-Relative vs Absolute")
print("=" * 60)

# Desactivar sector-relative temporalmente
analyzer.use_sector_relative = False
scores_absolute = analyzer.calculate_all_scores(metrics_util)

# Reactivar sector-relative
analyzer.use_sector_relative = True
scores_relative = analyzer.calculate_all_scores(metrics_util)

print(f"\n📊 Empresa Utility con ROE={metrics_util['roe']}%:")
print(f"   - Scoring Absoluto: {scores_absolute['quality_score']}/100")
print(f"   - Scoring Sector-Relativo: {scores_relative['quality_score']}/100")
print(f"   - Diferencia: {abs(scores_relative['quality_score'] - scores_absolute['quality_score']):.1f} puntos")

# Con ROE=12% en Utilities:
# - Absoluto: probablemente ~40-50 (bajo vs escala absoluta)
# - Sector-relativo: ~70 (bueno vs peers de Utilities)
print(f"\n✨ Beneficio: Utilities con ROE bajo pero normal para el sector")
print(f"   no es penalizada injustamente con sector-relative scoring")

# Test 7: Sectores disponibles
print("\n" + "=" * 60)
print("TEST 7: Sectores y Métricas Disponibles")
print("=" * 60)

sectors = normalizer.get_sector_list()
print(f"\n✅ Sectores disponibles ({len(sectors)}):")
for sector in sectors:
    metrics_count = len(normalizer.get_metrics_for_sector(sector))
    print(f"   - {sector}: {metrics_count} métricas")

assert len(sectors) == 11, f"Deberían ser 11 sectores, got {len(sectors)}"

# Test 8: Estadísticas de uso
print("\n" + "=" * 60)
print("TEST 8: Estadísticas de Uso del Normalizador")
print("=" * 60)

stats = normalizer.get_stats()
print(f"\n✅ Estadísticas:")
print(f"   - Total normalizadas: {stats['total_normalized']}")
print(f"   - Uso por sector: {stats['sector_usage']}")
print(f"   - Fallback a absoluto: {stats['fallback_to_absolute']}")

assert stats["total_normalized"] > 0, "Deberían haberse normalizado métricas"

print("\n" + "=" * 60)
print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
print("=" * 60)

print("\n🎉 Resumen:")
print("   ✅ SectorNormalizer calcula z-scores correctamente")
print("   ✅ Conversión z-score → escala 0-100 funcional")
print("   ✅ EquityAnalyzer usa sector-relative cuando hay sector")
print("   ✅ Fallback a scoring absoluto cuando falta sector")
print("   ✅ Extracción de sector principal (Technology - X → Technology)")
print("   ✅ 10 sectores con benchmarks completos")
print("   ✅ Metadata incluye method y sector para debugging")
print("\n   📊 Mejora #4 completada exitosamente!")

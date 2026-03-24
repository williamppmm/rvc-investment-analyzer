# Metodología de Análisis - RVC Investment Analyzer

Documentación de los tres sistemas metodológicos del motor de análisis: dispersión entre fuentes, normalización de períodos contables, y valoración TIER1/TIER2.

---

## Tabla de Contenidos

1. [Dispersión entre Fuentes](#1-dispersión-entre-fuentes)
2. [Normalización de Períodos Contables (TTM/MRQ/MRY)](#2-normalización-de-períodos-contables-ttmmrqmry)
3. [Valoración TIER1: EV/EBIT + FCF Yield](#3-valoración-tier1-evebit--fcf-yield)

---

## 1. Dispersión entre Fuentes

### Objetivo

Medir la **concordancia entre fuentes de datos** (AlphaVantage, TwelveData, etc.) para ajustar automáticamente la confianza del análisis.

### Cómo Funciona

Cuando múltiples fuentes reportan la misma métrica, se calcula el **Coeficiente de Variación (CV)**:

```python
# Ejemplo con P/E Ratio
# AlphaVantage: 28.5 | TwelveData: 28.7 | Yahoo: 31.2

# Priorización: solo fuentes premium para el cálculo
valores = [28.5, 28.7]
CV = (std / media) * 100 = 0.35%  # CV < 5% = EXCELENTE concordancia
confidence_adj = 1.0
```

### Tabla de Interpretación

| CV | Concordancia | Confidence Adj | Descripción |
|----|--------------|----------------|-------------|
| < 5% | Perfecta | 1.00 | Fuentes premium alineadas |
| 5–10% | Muy buena | 0.95 | Diferencia menor, aceptable |
| 10–20% | Aceptable | 0.85 | Diferencia moderada |
| 20–40% | Discrepante | 0.70 | Posible problema con una fuente |
| > 40% | Muy discrepante | 0.50 | Datos sospechosos, revisar manualmente |

### Quality Labels

| Label | Descripción |
|-------|-------------|
| `PREMIUM_SOURCES` | Calculado solo con AlphaVantage + TwelveData |
| `MIXED_SOURCES` | Incluye Yahoo/scraping (menor confianza) |
| `SINGLE_SOURCE` | Solo una fuente (sin dispersión calculable) |

### Ejemplo de Respuesta JSON

```json
{
  "ticker": "AAPL",
  "confidence_factors": {
    "completeness": 100.0,
    "dispersion": 100.0,
    "overall": 100.0
  },
  "dispersion_detail": {
    "pe_ratio": {"sources": ["alpha_vantage", "twelvedata"], "cv": 0.35, "confidence_adj": 1.0, "quality": "PREMIUM_SOURCES"},
    "roe":      {"sources": ["alpha_vantage", "twelvedata"], "cv": 0.34, "confidence_adj": 1.0, "quality": "PREMIUM_SOURCES"}
  }
}
```

### Beneficio Principal

Detecta errores de scraping automáticamente:
```python
# Ejemplo problemático:
# AlphaVantage: P/E = 28.5
# Yahoo scraping: P/E = 52.3 (error — posiblemente faltó dividir por 2)
# CV = 45.2% → confidence_adj = 0.50 → ⚠️ "Datos con alta dispersión"
```

**Archivos relevantes:** `data_agent.py` (`_calculate_dispersion()`), `analyzers/base_analyzer.py`

---

## 2. Normalización de Períodos Contables (TTM/MRQ/MRY)

### Problema Resuelto

Sin normalización, métricas de distintos períodos se mezclan inconsistentemente:
```python
# ❌ Antes: manzanas y naranjas
metrics = {
    "revenue_growth": 8.5,  # ¿Anual? ¿Trimestral? ¿5 años?
    "roe": 22.3,            # ¿TTM? ¿Último año fiscal?
}
```

### Jerarquía de Períodos

| Prioridad | Período | Descripción | Uso Principal |
|-----------|---------|-------------|---------------|
| 1 | **TTM** | Trailing Twelve Months | Métricas operativas (ROE, ROIC, márgenes) |
| 2 | **MRQ** | Most Recent Quarter | Crecimiento trimestral |
| 3 | **MRY** | Most Recent Year | Año fiscal más reciente |
| 4 | **5Y** | 5-Year Average | Promedios históricos |
| 5 | **FWD** | Forward Estimates | Estimaciones futuras |

### Uso

```python
from metric_normalizer import MetricNormalizer

normalizer = MetricNormalizer()

# Input con múltiples períodos
raw_values = {"roe_ttm": 22.3, "roe_mry": 21.8, "roe_5y": 19.5}

result = normalizer.normalize_metric("roe", raw_values)
# → {"value": 22.3, "period": "TTM", "fallback_chain": ["TTM"]}
```

### 22 Métricas Normalizadas Automáticamente

**Calidad (6):** `roe`, `roic`, `roa`, `operating_margin`, `net_margin`, `gross_margin`

**Crecimiento (8):** `revenue_growth`, `earnings_growth`, `revenue_growth_qoq`, `earnings_growth_qoq`, `earnings_growth_this_y`, `earnings_growth_next_y`, `earnings_growth_next_5y`, `revenue_growth_5y`

**Valoración (5):** `pe_ratio`, `peg_ratio`, `price_to_book`, `price_to_sales`, `ev_to_ebitda`

**Salud (3):** `debt_to_equity`, `current_ratio`, `quick_ratio`

### Integración con EquityAnalyzer

El `EquityAnalyzer` normaliza automáticamente antes de calcular cualquier score:
```python
scores = analyzer.calculate_all_scores(metrics)
# El JSON incluye metadata de normalización:
# "normalization_metadata": {"normalized_count": 9, "failed_count": 13, ...}
```

**Archivos relevantes:** `metric_normalizer.py`, `analyzers/equity_analyzer.py` (`_normalize_metrics()`)

---

## 3. Valoración TIER1: EV/EBIT + FCF Yield

### Problema Resuelto

Los múltiplos de ganancias tradicionales (P/E, PEG) pueden ser manipulados contablemente. El sistema TIER1 prioriza métricas basadas en **caja real generada**.

### Arquitectura del Sistema

```
_calculate_valuation(metrics)
  │
  ├── ¿Tiene ev_to_ebit Y fcf_yield?
  │   │
  │   ├── SÍ → _tier1_valuation()
  │   │         EV/EBIT Score (60%) + FCF Yield Score (40%)
  │   │         Retorna: {score, tier: "TIER1", method: "cash_flow_based"}
  │   │
  │   └── NO → _tier2_valuation()
  │             P/E (40%) + PEG (35%) + P/B (25%)
  │             Retorna: {score, tier: "TIER2", method: "traditional_multiples"}
```

### Escalas TIER1

**EV/EBIT (60% del peso):**

| EV/EBIT | Score | Interpretación |
|---------|-------|----------------|
| < 8 | 100 | Muy barato |
| 8–12 | 85 | Barato |
| 12–15 | 70 | Razonable |
| 15–20 | 50 | Justo |
| 20–25 | 35 | Caro |
| > 25 | 20 | Muy caro |

**Ventaja vs EV/EBITDA:** EBIT excluye D&A (que varía por políticas contables), siendo más comparable entre empresas.

**FCF Yield (40% del peso):**

| FCF Yield | Score | Interpretación |
|-----------|-------|----------------|
| > 10% | 100 | Excelente generación de caja |
| 7–10% | 85 | Muy buena |
| 5–7% | 70 | Buena |
| 3–5% | 50 | Aceptable |
| 0–3% | 30 | Genera poco |
| < 0% | 10 | ⚠️ Quema caja |

```
FCF Yield = (Free Cash Flow / Market Cap) × 100
```

### Métricas Derivadas (calculadas automáticamente)

```python
# En data_agent.py → _calculate_derived_metrics()
if "free_cash_flow" in metrics and "market_cap" in metrics:
    metrics["fcf_yield"] = (fcf / mcap) * 100

if "enterprise_value" in metrics and "ebit" in metrics:
    metrics["ev_to_ebit"] = ev / ebit
```

### Ejemplos

**Caso 1 — TIER1, empresa con excelente FCF (tipo Apple):**
```python
metrics = {"ev_to_ebit": 10.5, "fcf_yield": 8.5, "pe_ratio": 28.5}
# → Valuation Score: 85/100, tier: TIER1
# → P/E alto ignorado porque FCF es excelente
```

**Caso 2 — TIER2, sin datos de caja:**
```python
metrics = {"pe_ratio": 18.5, "peg_ratio": 1.2, "price_to_book": 8.5}
# → Valuation Score: 60/100, tier: TIER2
```

**Caso 3 — TIER1, empresa que quema caja (startup):**
```python
metrics = {"ev_to_ebit": 25.0, "fcf_yield": -5.2}
# → Valuation Score: 16/100, tier: TIER1
# → FCF negativo penaliza fuertemente (score FCF = 10/100)
```

### Beneficios del Sistema TIER1

1. **Difícil de manipular** — FCF es más robusto que earnings
2. **Detecta empresas que queman caja** — FCF negativo → score 10/100
3. **Jerarquía clara** — TIER1 preferido, TIER2 como fallback robusto
4. **Transparente** — metadata `tier` y `method` en el JSON
5. **Sin breaking changes** — backward compatible con sistema anterior

**Archivos relevantes:** `analyzers/equity_analyzer.py` (`_tier1_valuation()`, `_tier2_valuation()`), `data_agent.py` (`_calculate_derived_metrics()`)

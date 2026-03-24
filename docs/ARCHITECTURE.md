# Arquitectura Técnica - RVC Investment Analyzer

Documentación técnica del sistema de análisis, motor de scoring y fuentes de datos.

---

## Tabla de Contenidos

1. [Arquitectura Modular de Analizadores](#1-arquitectura-modular-de-analizadores)
2. [Flujo de Análisis Completo](#2-flujo-de-análisis-completo)
3. [Sistema de Scoring (4 Dimensiones)](#3-sistema-de-scoring-4-dimensiones)
4. [Categorización de Empresas](#4-categorización-de-empresas)
5. [Fuentes de Datos y Fallback](#5-fuentes-de-datos-y-fallback)
6. [Métricas Soportadas](#6-métricas-soportadas)
7. [Endpoints de la Aplicación](#7-endpoints-de-la-aplicación)
8. [Cache y Provenance](#8-cache-y-provenance)
9. [Plan de Migración a APIs Pagadas](#9-plan-de-migración-a-apis-pagadas)

---

## 1. Arquitectura Modular de Analizadores

El sistema usa una **arquitectura basada en herencia** que facilita escalar a nuevos tipos de activos.

```
analyzers/
├── __init__.py              # Exports: BaseAnalyzer, EquityAnalyzer, ETFAnalyzer
├── base_analyzer.py         # Clase abstracta con analyze(), get_asset_type()
├── equity_analyzer.py       # EquityAnalyzer para acciones
└── etf_analyzer.py          # ETFAnalyzer para fondos cotizados

┌─────────────────────────────────────────────────────────────┐
│                     BaseAnalyzer (ABC)                       │
│  • analyze() → Dict[str, Any]                               │
│  • get_asset_type() → str                                   │
│  • validate_metrics() → bool                                │
└──────────────┬──────────────────────────────────────────────┘
               │
       ┌───────┴────────┬──────────────────┐
       │                │                  │
   EquityAnalyzer   ETFAnalyzer    [CryptoAnalyzer - futuro]
   (701 líneas)     (173 líneas)   [IndexAnalyzer - futuro]
```

**Compatibilidad hacia atrás:**
- `scoring_engine.py` → Wrapper que exporta `InvestmentScorer = EquityAnalyzer`

---

## 2. Flujo de Análisis Completo

```
ENTRADA: Ticker (ej: AAPL)
    │
    ▼
PASO 1: CLASIFICACIÓN (AssetClassifier)
    • Determina tipo: EQUITY, ETF, CRYPTO, FOREX
    • Usa overrides manuales + heurísticas del símbolo
    │
    ▼
PASO 2: RECOLECCIÓN DE DATOS (DataAgent)
    Cascada con fallback:
    1. AlphaVantage  (API premium)
    2. TwelveData    (API premium)
    3. FMP           (API premium)
    4. Yahoo Finance (scraping)
    5. Finviz        (scraping)
    6. MarketWatch   (scraping)
    7. Datos ejemplo (último recurso)
    │
    ▼
PASO 3: NORMALIZACIÓN
    • Merge de fuentes con prioridad
    • Conversión de formatos (%, M, B)
    • Provenance tracking (qué fuente dio qué dato)
    • Normalización TTM/MRQ/MRY (ver docs/METHODOLOGY.md)
    │
    ▼
PASO 4: SELECCIÓN DE ANALIZADOR (Factory Pattern)
    if EQUITY → EquityAnalyzer
    if ETF    → ETFAnalyzer
    │
    ▼
PASO 5: ANÁLISIS Y SCORING
    EquityAnalyzer → 4 scores independientes (ver sección 3)
    ETFAnalyzer    → Resumen informativo (NAV, Expense Ratio, etc.)
    │
    ▼
PASO 6: INVESTMENT SCORE FINAL (solo EQUITY)
    • Calidad mínima 60 requerida
    • Balance óptimo: calidad 70-90 + valoración 60-80
    • Bonuses por salud/crecimiento excepcionales
    │
    ▼
PASO 7: CATEGORIZACIÓN
    SWEET SPOT / PREMIUM / VALOR / QUALITY / RISKY / OVERVALUED / AVOID
    │
    ▼
SALIDA: JSON con scores, categoría y recomendación
```

---

## 3. Sistema de Scoring (4 Dimensiones)

### A) Quality Score (0–100)

Evalúa la calidad del negocio:

| Métrica | Peso |
|---------|------|
| ROE | 40% |
| ROIC | 35% |
| Operating Margin | 15% |
| Net Margin | 10% |

### B) Valuation Score (0–100) — Sistema TIER1/TIER2

**TIER1 (preferido):** Métricas basadas en caja — más difíciles de manipular contablemente.

| Métrica | Peso | Escala |
|---------|------|--------|
| EV/EBIT | 60% | < 8 → 100pts, 8–12 → 85, 12–15 → 70, 15–20 → 50, > 25 → 20 |
| FCF Yield | 40% | > 10% → 100, 7–10% → 85, 5–7% → 70, < 0% → 10 |

**TIER2 (fallback):** Múltiplos tradicionales cuando faltan métricas TIER1.

| Métrica | Peso |
|---------|------|
| P/E Ratio | 40% |
| PEG Ratio | 35% |
| Price to Book | 25% |

El breakdown del JSON indica qué nivel se usó: `"tier": "TIER1"` / `"tier": "TIER2"`.

### C) Health Score (0–100)

Evalúa la solidez financiera:

| Métrica | Peso |
|---------|------|
| Debt to Equity | 60% |
| Current Ratio | 30% |
| Quick Ratio | 10% |

### D) Growth Score (0–100)

| Métrica | Peso |
|---------|------|
| Revenue Growth | 60% |
| Earnings Growth | 40% |

---

## 4. Categorización de Empresas

| Categoría | Condición | Interpretación |
|-----------|-----------|----------------|
| SWEET SPOT 🏆 | calidad ≥ 75, valoración ≥ 60 | Calidad alta a buen precio |
| PREMIUM ⭐ | calidad ≥ 85, valoración ≥ 40 | Empresa excelente, precio justo |
| VALOR 💎 | calidad ≥ 60, valoración ≥ 70 | Calidad decente, buen precio |
| QUALITY ✅ | calidad ≥ 70, valoración ≥ 40 | Buena empresa |
| RISKY 🎲 | calidad < 60, valoración ≥ 60 | Barata pero de baja calidad |
| OVERVALUED 🚨 | calidad < 70, valoración < 50 | Cara y de calidad media |
| AVOID ⛔ | otras combinaciones | No recomendada |

---

## 5. Fuentes de Datos y Fallback

### Fuentes Actuales (scraping gratuito)

El `DataAgent` implementa una **cascada con fusión prioritaria**:

```python
def get_company_metrics(ticker):
    # 1. Yahoo Finance (prioridad 1)
    # 2. Finviz       (si cobertura < 60%)
    # 3. MarketWatch  (si aún insuficiente)
    # Fusión: Yahoo > Finviz > MarketWatch
    # Si cobertura final < 40% → datos insuficientes
```

| Fuente | URL Base | Prioridad | Costo |
|--------|----------|-----------|-------|
| Yahoo Finance | `finance.yahoo.com/quote/{ticker}` | 1ª | Gratuito |
| Finviz | `finviz.com/quote.ashx?t={ticker}` | 2ª | Gratuito |
| MarketWatch | `marketwatch.com/investing/stock/{ticker}` | 3ª | Gratuito |

### Restricciones del Scraping

- ⚠️ Cambios de HTML pueden romper el parsing sin previo aviso
- ⚠️ Uso excesivo puede resultar en bloqueos temporales por IP
- ⚠️ Sin garantías de exactitud en los datos
- ⚠️ Latencia alta: ~2–5 segundos por ticker
- ⚠️ Sin datos históricos (solo snapshot actual)

### Ejemplo de Provenance

```python
{
    "ticker": "AAPL",
    "metrics": {"pe_ratio": 28.5, "roe": 0.45},
    "provenance": {"pe_ratio": "yahoo", "roe": "finviz"},
    "coverage": 85   # 85% de métricas obtenidas
}
```

---

## 6. Métricas Soportadas

### Valoración (9 métricas)
`current_price`, `market_cap`, `pe_ratio`, `forward_pe`, `peg_ratio`, `price_to_book`, `price_to_sales`, `ev_to_ebitda`, `dividend_yield`

### Rentabilidad / Calidad (6 métricas)
`roe`, `roic`, `roa`, `gross_margin`, `operating_margin`, `net_margin`

### Salud Financiera (5 métricas)
`debt_to_equity`, `current_ratio`, `quick_ratio`, `interest_coverage`, `free_cash_flow`

### Crecimiento (8 métricas)
`revenue_growth`, `revenue_growth_qoq`, `revenue_growth_5y`, `earnings_growth`, `earnings_growth_this_y`, `earnings_growth_next_y`, `earnings_growth_next_5y`, `earnings_growth_qoq`

### Métricas derivadas (calculadas automáticamente)
```python
# En data_agent.py → _calculate_derived_metrics()
fcf_yield   = (free_cash_flow / market_cap) * 100
ev_to_ebit  = enterprise_value / ebit
```

Ver `data_agent.py:44–69` para lista completa de `MANUAL_EDITABLE_FIELDS`.

---

## 7. Endpoints de la Aplicación

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `GET /` | GET | Página principal (Analyzer) |
| `POST /analyze` | POST | Análisis individual de ticker |
| `GET /comparador` | GET | Interfaz comparador |
| `POST /compare` | POST | Comparación múltiple (hasta 5 tickers) |
| `GET /calculadora` | GET | Calculadora DCA/Jubilación |
| `POST /calculate` | POST | Cálculo de simulación de inversión |
| `GET /api/top-opportunities` | GET | Ranking de mejores oportunidades |
| `POST /api/check-limit` | POST | Verificar límite de uso freemium |
| `POST /api/validate-license` | POST | Validar licencia PRO |
| `GET /api/usage-stats` | GET | Estadísticas globales de uso |
| `POST /cache/clear` | POST | Limpiar caché (solo desarrollo) |

### Ejemplo: POST /analyze

**Request:**
```json
{"ticker": "AAPL"}
```

**Response (200):**
```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "current_price": 178.50,
  "asset_type": "stock",
  "rvc_score": {
    "total_score": 76,
    "classification": "🟢 Razonable o mejor",
    "breakdown": {
      "valoracion": {"score": 72, "tier": "TIER1"},
      "calidad":    {"score": 88},
      "salud":      {"score": 81},
      "crecimiento":{"score": 65}
    }
  },
  "investment_scores": {
    "investment_score": 76,
    "category": {"name": "SWEET SPOT", "emoji": "🏆"}
  },
  "provenance": {"pe_ratio": "yahoo", "roe": "finviz"},
  "coverage": 85
}
```

### Ejemplo: GET /api/top-opportunities

**Parámetros query:** `min_score`, `sector`, `sort_by`, `limit`

```
GET /api/top-opportunities?min_score=70&limit=10&sort_by=rvc_score
```

---

## 8. Cache y Provenance

### Cache SQLite

**Ubicación:** `data/cache.db` (ignorado por .gitignore)
**TTL:** 7 días

```sql
CREATE TABLE company_cache (
    ticker      TEXT PRIMARY KEY,
    data        TEXT,     -- JSON serializado
    timestamp   INTEGER,
    provenance  TEXT,     -- JSON con fuente de cada métrica
    coverage    INTEGER   -- Porcentaje de cobertura
);
```

### Lógica

```python
def get_company_metrics(ticker):
    cached = self._get_from_cache(ticker)
    if cached and not self._is_expired(cached):
        return cached
    fresh_data = self._scrape_all_sources(ticker)
    self._save_to_cache(ticker, fresh_data)
    return fresh_data
```

---

## 9. Plan de Migración a APIs Pagadas

Cuando el proyecto esté en producción se recomienda migrar a **Financial Modeling Prep (FMP)**.

| Escenario | Método | Costo/mes | Calidad |
|-----------|--------|-----------|---------|
| MVP Local (actual) | Scraping | $0 | 60–90% cobertura |
| Producción inicial | FMP Starter | $29 | 100% + históricos |
| Producción escalada | FMP Professional | $99 | 100% + real-time |

**Cronograma:** Fases 0–8 con scraping → Fase 9 migrar a FMP Starter.

**Endpoints FMP a implementar:**
```python
GET /api/v3/profile/{ticker}?apikey={key}
GET /api/v3/ratios/{ticker}?apikey={key}
GET /api/v3/key-metrics/{ticker}?apikey={key}
GET /api/v3/financial-growth/{ticker}?apikey={key}
```

**Variables de entorno futuras (`.env`):**
```bash
FMP_API_KEY=your_key
ALPHA_VANTAGE_KEY=your_key
TWELVE_DATA_KEY=your_key
DATABASE_URL=sqlite:///data/cache.db
FLASK_ENV=production
SECRET_KEY=your_secret_key
```

# API DOCUMENTATION - RVC Analyzer

**Versión**: 1.0
**Última actualización**: Octubre 2025
**Estado**: MVP Local con APIs Gratuitas

---

## TABLA DE CONTENIDOS

1. [Resumen General](#resumen-general)
2. [Fuentes de Datos Actuales](#fuentes-de-datos-actuales)
3. [Sistema de Fallback](#sistema-de-fallback)
4. [Métricas Soportadas](#métricas-soportadas)
5. [Endpoints de la Aplicación](#endpoints-de-la-aplicación)
6. [Cache y Provenance](#cache-y-provenance)
7. [Límites y Restricciones](#límites-y-restricciones)
8. [Plan de Migración a APIs Pagadas](#plan-de-migración-a-apis-pagadas)

---

## RESUMEN GENERAL

RVC Analyzer actualmente funciona con **scraping web** de fuentes públicas gratuitas y sin requerir API keys. El sistema implementa un robusto mecanismo de fallback que consulta múltiples fuentes hasta obtener una cobertura aceptable de métricas.

### Arquitectura Actual

```
DataAgent (data_agent.py)
    │
    ├─► Yahoo Finance (scraping)
    ├─► Finviz (scraping)
    ├─► MarketWatch (scraping)
    │
    └─► Merge Strategy (priority-based)
         └─► SQLite Cache (7 días TTL)
```

### Estado de Implementación

- ✅ **Scraping Web**: Totalmente funcional
- ✅ **Sistema de Fallback**: 3 fuentes con prioridad
- ✅ **Cache Local**: SQLite con TTL de 7 días
- ✅ **Provenance Tracking**: Seguimiento de origen de cada métrica
- ⚠️ **API Clients**: Importados pero NO implementados (AlphaVantageClient, FMPClient, TwelveDataClient)
- ❌ **Rate Limiting**: No implementado (no necesario para scraping)
- ❌ **Autenticación API**: No implementado (no hay API keys)

---

## FUENTES DE DATOS ACTUALES

### 1. Yahoo Finance

**URL Base**: `https://finance.yahoo.com/quote/{ticker}`
**Método**: Web Scraping (BeautifulSoup)
**Prioridad**: 1 (Primera opción)
**Límites**: Sin límite oficial, pero requiere User-Agent válido
**Costo**: Gratuito

#### Métricas Disponibles

```python
YAHOO_METRICS = [
    "current_price",      # Precio actual
    "market_cap",         # Capitalización de mercado
    "pe_ratio",           # P/E Ratio (TTM)
    "forward_pe",         # Forward P/E
    "peg_ratio",          # PEG Ratio
    "price_to_book",      # P/B Ratio
    "price_to_sales",     # P/S Ratio
    "ev_to_ebitda",       # EV/EBITDA
    "roe",                # Return on Equity
    "roa",                # Return on Assets
    "gross_margin",       # Margen Bruto
    "operating_margin",   # Margen Operativo
    "net_margin",         # Margen Neto (como "Profit Margin")
    "debt_to_equity",     # Deuda/Capital
    "current_ratio",      # Current Ratio
    "quick_ratio",        # Quick Ratio
    "revenue_growth",     # Crecimiento de Ingresos
    "earnings_growth",    # Crecimiento de Ganancias
]
```

#### Estructura de Respuesta

Yahoo Finance utiliza dos secciones principales:
- **Key Statistics**: Métricas de valoración y ratios financieros
- **Financial Highlights**: Márgenes y rentabilidad

```html
<!-- Ejemplo de estructura HTML parseada -->
<td class="label">P/E Ratio (TTM)</td>
<td class="value">25.34</td>
```

#### Implementación

```python
def _fetch_yahoo(self, ticker: str) -> Optional[SourceResult]:
    """
    Extrae métricas de Yahoo Finance mediante scraping.

    Returns:
        SourceResult con data dict y source="yahoo"
    """
    url = f"https://finance.yahoo.com/quote/{ticker}"
    # ... parsing logic
```

**Archivo**: `data_agent.py:567`

---

### 2. Finviz

**URL Base**: `https://finviz.com/quote.ashx?t={ticker}`
**Método**: Web Scraping (BeautifulSoup)
**Prioridad**: 2 (Segunda opción si Yahoo falla)
**Límites**: Sin límite oficial
**Costo**: Gratuito

#### Métricas Disponibles

Finviz utiliza una tabla de "snapshot" con métricas clave:

```python
FINVIZ_METRICS = [
    "market_cap",
    "pe_ratio",
    "forward_pe",
    "peg_ratio",
    "price_to_book",
    "price_to_sales",
    "debt_to_equity",
    "current_ratio",
    "quick_ratio",
    "roe",
    "roa",
    "gross_margin",
    "operating_margin",
    "net_margin",
    "revenue_growth_qoq",     # Crecimiento trimestral de ventas
    "earnings_growth_qoq",    # Crecimiento trimestral de ganancias
    "earnings_growth_this_y", # Crecimiento esperado este año
    "earnings_growth_next_y", # Crecimiento esperado próximo año
    "earnings_growth_next_5y",# Crecimiento esperado 5 años
]
```

#### Estructura de Respuesta

Finviz usa una tabla con pares clave-valor:

```html
<td class="snapshot-td2-cp" align="left">
    <b>P/E</b>
</td>
<td class="snapshot-td2" align="left">
    <b>25.34</b>
</td>
```

#### Implementación

```python
def _fetch_finviz(self, ticker: str) -> Optional[SourceResult]:
    """
    Extrae métricas de Finviz mediante scraping de tabla snapshot.

    Returns:
        SourceResult con data dict y source="finviz"
    """
    url = f"https://finviz.com/quote.ashx?t={ticker}"
    # ... parsing logic
```

**Archivo**: `data_agent.py:666`

---

### 3. MarketWatch

**URL Base**: `https://www.marketwatch.com/investing/stock/{ticker}`
**Método**: Web Scraping (BeautifulSoup)
**Prioridad**: 3 (Tercera opción si Yahoo y Finviz fallan)
**Límites**: Sin límite oficial
**Costo**: Gratuito

#### Métricas Disponibles

```python
MARKETWATCH_METRICS = [
    "current_price",
    "pe_ratio",
    "market_cap",
    "revenue_growth",
    "earnings_growth",
    # MarketWatch tiene menos cobertura que Yahoo/Finviz
]
```

#### Implementación

```python
def _fetch_marketwatch(self, ticker: str) -> Optional[SourceResult]:
    """
    Fallback final: extrae métricas básicas de MarketWatch.

    Returns:
        SourceResult con data dict y source="marketwatch"
    """
    url = f"https://www.marketwatch.com/investing/stock/{ticker}"
    # ... parsing logic
```

**Archivo**: `data_agent.py:742`

---

## SISTEMA DE FALLBACK

El DataAgent implementa un sistema de **cascada con fusión prioritaria** de datos:

### Algoritmo de Fallback

```python
def get_company_metrics(ticker: str) -> dict:
    """
    1. Intenta Yahoo Finance (prioridad 1)
    2. Si falla o cobertura < 60%, intenta Finviz (prioridad 2)
    3. Si aún falla, intenta MarketWatch (prioridad 3)
    4. Fusiona resultados con prioridad: Yahoo > Finviz > MarketWatch
    5. Si cobertura final < 40%, marca como datos insuficientes
    """
```

### Estrategia de Merge

Cuando múltiples fuentes proveen la misma métrica:

- **Yahoo tiene prioridad** sobre Finviz y MarketWatch
- **Finviz tiene prioridad** sobre MarketWatch
- Solo se sobrescribe si la métrica previa es `None`

### Ejemplo de Provenance

```python
{
    "ticker": "AAPL",
    "metrics": {
        "pe_ratio": 28.5,
        "roe": 0.45,
        "market_cap": 2800000000000
    },
    "provenance": {
        "pe_ratio": "yahoo",
        "roe": "finviz",
        "market_cap": "yahoo"
    },
    "coverage": 85  # 85% de métricas obtenidas
}
```

---

## MÉTRICAS SOPORTADAS

El sistema soporta **69 métricas** diferentes clasificadas en 5 categorías:

### 1. Métricas de Valoración (9 métricas)

| Métrica | Alias | Fuentes | Prioridad |
|---------|-------|---------|-----------|
| `current_price` | Price, Current Price | Yahoo, MarketWatch | Yahoo |
| `market_cap` | Market Cap, Market Capitalization | Yahoo, Finviz, MarketWatch | Yahoo |
| `pe_ratio` | P/E, PE Ratio (TTM), Trailing P/E | Yahoo, Finviz, MarketWatch | Yahoo |
| `forward_pe` | Forward P/E | Yahoo, Finviz | Yahoo |
| `peg_ratio` | PEG, PEG ratio | Yahoo, Finviz | Yahoo |
| `price_to_book` | P/B, Price/Book | Yahoo, Finviz | Yahoo |
| `price_to_sales` | P/S | Yahoo, Finviz | Yahoo |
| `ev_to_ebitda` | EV/EBITDA | Yahoo | Yahoo |
| `dividend_yield` | Dividend Yield | Yahoo | Yahoo |

### 2. Métricas de Rentabilidad (6 métricas)

| Métrica | Alias | Fuentes | Prioridad |
|---------|-------|---------|-----------|
| `roe` | ROE, Return on Equity | Yahoo, Finviz | Yahoo |
| `roic` | ROI, ROIC, Return on Invested Capital | Yahoo | Yahoo |
| `roa` | ROA, Return on Assets | Yahoo, Finviz | Yahoo |
| `gross_margin` | Gross Margin | Yahoo, Finviz | Yahoo |
| `operating_margin` | Operating Margin, Oper. Margin | Yahoo, Finviz | Yahoo |
| `net_margin` | Profit Margin, Net Profit Margin | Yahoo, Finviz | Yahoo |

### 3. Métricas de Salud Financiera (5 métricas)

| Métrica | Alias | Fuentes | Prioridad |
|---------|-------|---------|-----------|
| `debt_to_equity` | Debt/Eq, Debt to Equity | Yahoo, Finviz | Yahoo |
| `current_ratio` | Current Ratio | Yahoo, Finviz | Yahoo |
| `quick_ratio` | Quick Ratio | Yahoo, Finviz | Yahoo |
| `interest_coverage` | Interest Coverage | Yahoo | Yahoo |
| `free_cash_flow` | FCF, Free Cash Flow | Yahoo | Yahoo |

### 4. Métricas de Crecimiento (8 métricas)

| Métrica | Alias | Fuentes | Prioridad |
|---------|-------|---------|-----------|
| `revenue_growth` | Revenue Growth (YoY) | Yahoo, MarketWatch | Yahoo |
| `revenue_growth_qoq` | Quarterly Revenue Growth | Finviz | Finviz |
| `revenue_growth_5y` | 5Y Revenue Growth | Yahoo | Yahoo |
| `earnings_growth` | Earnings Growth (YoY) | Yahoo, MarketWatch | Yahoo |
| `earnings_growth_this_y` | EPS this Y | Finviz | Finviz |
| `earnings_growth_next_y` | EPS next Y | Finviz | Finviz |
| `earnings_growth_next_5y` | EPS next 5Y | Finviz | Finviz |
| `earnings_growth_qoq` | Quarterly Earnings Growth | Finviz | Finviz |

### 5. Otras Métricas (41 métricas adicionales)

Ver `data_agent.py:44-69` para lista completa de `MANUAL_EDITABLE_FIELDS`.

---

## ENDPOINTS DE LA APLICACIÓN

La aplicación Flask expone los siguientes endpoints:

### 1. `GET /` - Página Principal (Analyzer)

**Descripción**: Interfaz principal del analizador RVC
**Template**: `templates/index.html`
**JavaScript**: `static/script.js`

**Parámetros Query**:
- `ticker` (opcional): Símbolo de ticker a analizar automáticamente

**Funcionalidad**:
- Renderiza formulario de entrada de ticker
- Muestra resultados de análisis (scores, radar, tabla de métricas)
- Usa DataAgent para obtener métricas
- Usa InvestmentScorer + RVCCalculator para scoring

---

### 2. `POST /analyze` - Análisis de Empresa

**Descripción**: Endpoint AJAX para analizar un ticker
**Método**: POST
**Content-Type**: application/json

**Request Body**:
```json
{
  "ticker": "AAPL"
}
```

**Response Success (200)**:
```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "current_price": 178.50,
  "asset_type": "stock",
  "metrics": {
    "pe_ratio": 28.5,
    "roe": 0.45,
    "market_cap": 2800000000000,
    // ... más métricas
  },
  "scores": {
    "valuation_score": 72,
    "quality_score": 88,
    "growth_score": 65,
    "safety_score": 81,
    "overall_score": 76
  },
  "rvc": {
    "rvc_r": 7.2,
    "rvc_v": 6.5,
    "rvc_c": 8.1,
    "rvc_total": 7.3
  },
  "provenance": {
    "pe_ratio": "yahoo",
    "roe": "finviz"
  },
  "coverage": 85,
  "category": "Investment Grade"
}
```

**Response Error (400)**:
```json
{
  "error": "No se pudo obtener suficientes datos para INVALID"
}
```

**Implementación**: `app.py:analyze()`

---

### 3. `GET /comparador` - Comparador de Empresas

**Descripción**: Interfaz para comparar múltiples empresas
**Template**: `templates/comparador.html`
**JavaScript**: `static/comparador.js`

**Funcionalidad**:
- Permite comparar 2-5 empresas simultáneamente
- Muestra tabla comparativa de métricas
- Genera radar comparativo
- **Reutiliza 100%** la lógica de `/analyze` para cada ticker

---

### 4. `POST /compare` - Comparación Múltiple

**Descripción**: Endpoint AJAX para comparar múltiples tickers
**Método**: POST
**Content-Type**: application/json

**Request Body**:
```json
{
  "tickers": ["AAPL", "MSFT", "GOOGL"]
}
```

**Response Success (200)**:
```json
{
  "companies": [
    {
      "ticker": "AAPL",
      "metrics": { /* ... */ },
      "scores": { /* ... */ }
    },
    {
      "ticker": "MSFT",
      "metrics": { /* ... */ },
      "scores": { /* ... */ }
    },
    // ...
  ],
  "comparison": {
    "best_valuation": "AAPL",
    "best_quality": "MSFT",
    "best_growth": "GOOGL"
  }
}
```

**Implementación**: `app.py:compare()`

---

### 5. `GET /calculadora` - Calculadora de Inversión

**Descripción**: Herramienta de simulación de inversión
**Template**: `templates/calculadora.html`
**JavaScript**: `static/calculadora.js`

**Funcionalidad**:
- Tab 1: Simulación DCA vs Lump Sum
- Tab 2: Calculadora de Jubilación
- Tab 3: Análisis de Correlaciones
- **No requiere APIs externas** (cálculos locales)

---

### 6. `POST /calculate` - Cálculo de Inversión

**Descripción**: Endpoint AJAX para simulaciones de inversión
**Método**: POST
**Content-Type**: application/json

**Request Body Ejemplo (DCA)**:
```json
{
  "type": "dca",
  "monthly_investment": 500,
  "years": 30,
  "annual_return": 10,
  "inflation": 3
}
```

**Response Success (200)**:
```json
{
  "total_invested": 180000,
  "final_value": 1131000,
  "real_value": 592000,
  "total_gain": 951000,
  "annual_breakdown": [
    { "year": 1, "value": 6300 },
    { "year": 2, "value": 13200 },
    // ...
  ]
}
```

**Implementación**: `investment_calculator.py`

---

## CACHE Y PROVENANCE

### Sistema de Cache SQLite

**Ubicación**: `data/cache.db` (ignorado por .gitignore)
**TTL**: 7 días
**Esquema**:

```sql
CREATE TABLE company_cache (
    ticker TEXT PRIMARY KEY,
    data TEXT,  -- JSON serializado
    timestamp INTEGER,
    provenance TEXT,  -- JSON con fuentes de cada métrica
    coverage INTEGER  -- Porcentaje de cobertura
);
```

### Lógica de Cache

```python
def get_company_metrics(ticker: str) -> dict:
    # 1. Verificar cache
    cached = self._get_from_cache(ticker)
    if cached and not self._is_expired(cached):
        return cached

    # 2. Si no hay cache o expiró, scrape
    fresh_data = self._scrape_all_sources(ticker)

    # 3. Guardar en cache
    self._save_to_cache(ticker, fresh_data)

    return fresh_data
```

### Provenance Tracking

Cada métrica incluye metadatos de origen:

```python
self.provenance = {
    "pe_ratio": "yahoo",
    "roe": "finviz",
    "debt_to_equity": "yahoo",
    "earnings_growth_next_5y": "finviz"
}
```

**Ventajas**:
- Debugging de calidad de datos
- Auditoría de fuentes
- Priorización de fuentes más confiables
- Identificación de métricas problemáticas

---

## LÍMITES Y RESTRICCIONES

### Límites Actuales (APIs Gratuitas)

| Fuente | Tipo | Límite Diario | Límite por Minuto | Costo |
|--------|------|---------------|-------------------|-------|
| Yahoo Finance | Scraping | Sin límite oficial | ~100 requests/min (recomendado) | $0 |
| Finviz | Scraping | Sin límite oficial | ~60 requests/min (recomendado) | $0 |
| MarketWatch | Scraping | Sin límite oficial | ~60 requests/min (recomendado) | $0 |

### Restricciones Técnicas

1. **User-Agent Requerido**: Todas las fuentes requieren User-Agent válido
2. **Sin Rate Limiting**: No implementado porque scraping no tiene límites estrictos
3. **Parsing Frágil**: Cambios en HTML de las fuentes pueden romper el scraping
4. **Latencia Alta**: ~2-5 segundos por ticker (scraping es lento)
5. **Sin Datos Históricos**: Solo datos actuales (snapshot)
6. **Cobertura Variable**: 60-90% de métricas dependiendo de la fuente

### Riesgos del Scraping

- ⚠️ **Cambios de HTML**: Sitios pueden cambiar estructura sin aviso
- ⚠️ **Bloqueos por IP**: Uso excesivo puede resultar en bloqueos temporales
- ⚠️ **Legal**: Scraping puede violar ToS (uso educativo/personal solamente)
- ⚠️ **Calidad de Datos**: Sin garantías de exactitud

---

## PLAN DE MIGRACIÓN A APIS PAGADAS

Cuando el proyecto esté listo para despliegue, se recomienda migrar a **Financial Modeling Prep (FMP)**.

### Financial Modeling Prep (Recomendado)

**Plan**: Starter ($29/mes)
**Límites**: 15,000 requests/mes (~500/día)
**Cobertura**: 100% de métricas + datos históricos + earnings calls

#### Endpoints FMP a Implementar

```python
# 1. Company Profile
GET https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={key}

# 2. Financial Ratios (métricas actuales)
GET https://financialmodelingprep.com/api/v3/ratios/{ticker}?apikey={key}

# 3. Key Metrics (valoración)
GET https://financialmodelingprep.com/api/v3/key-metrics/{ticker}?apikey={key}

# 4. Financial Growth
GET https://financialmodelingprep.com/api/v3/financial-growth/{ticker}?apikey={key}

# 5. Historical Data (para Phase 3: Market Context)
GET https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?apikey={key}
```

#### Código de Migración (Preparado)

```python
class FMPClient:
    """Cliente para Financial Modeling Prep API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://financialmodelingprep.com/api/v3"

    def get_company_metrics(self, ticker: str) -> dict:
        """
        Obtiene todas las métricas de una empresa.

        Returns:
            Dict con todas las métricas en formato estandarizado
        """
        profile = self._get_profile(ticker)
        ratios = self._get_ratios(ticker)
        metrics = self._get_key_metrics(ticker)
        growth = self._get_growth(ticker)

        return self._merge_fmp_data(profile, ratios, metrics, growth)
```

**Archivo a crear**: `services/fmp_client.py` (Phase 9 del roadmap)

### Comparación de Costos

| Escenario | Método | Costo Mensual | Límites | Calidad |
|-----------|--------|---------------|---------|---------|
| **MVP Local (Actual)** | Scraping | $0 | Sin límites oficiales | 60-90% cobertura |
| **Producción Inicial** | FMP Starter | $29 | 15,000 calls/mes | 100% cobertura + históricos |
| **Producción Escalada** | FMP Professional | $99 | 100,000 calls/mes | 100% + real-time |

### Cronograma de Migración

Según DEVELOPMENT_ROADMAP.md:

- **Fase 0-8**: Scraping gratuito (desarrollo local)
- **Fase 9**: Migrar a FMP Starter cuando:
  - MVP completo con todas las features
  - Desplegado en Railway.app free tier
  - Testers activos probando la aplicación
  - Presupuesto de $40/mes disponible (Railway $10 + FMP $29)

---

## NOTAS ADICIONALES

### Variables de Entorno (Futuro)

Cuando se migre a APIs pagadas, crear `.env`:

```bash
# Financial Modeling Prep
FMP_API_KEY=your_api_key_here

# Alpha Vantage (backup)
ALPHA_VANTAGE_KEY=your_backup_key

# Twelve Data (backup)
TWELVE_DATA_KEY=your_backup_key

# Database
DATABASE_URL=sqlite:///data/cache.db

# Flask
FLASK_ENV=production
SECRET_KEY=your_secret_key
```

**IMPORTANTE**: `.env` está incluido en .gitignore para evitar exponer API keys.

### Logging de API Calls

Cuando se implementen APIs pagadas, agregar logging:

```python
import logging

logger = logging.getLogger("APIUsage")

def track_api_call(source: str, endpoint: str):
    logger.info(f"API Call: {source} - {endpoint}")
    # Incrementar contador para monitorear límites
```

### Monitoreo de Límites

Implementar dashboard de uso de API en futuro:

```python
def get_api_usage_stats() -> dict:
    return {
        "fmp_calls_today": 234,
        "fmp_calls_month": 4521,
        "fmp_limit_month": 15000,
        "percentage_used": 30.14
    }
```

---

## CONTACTO Y SOPORTE

Para dudas sobre APIs:
- **Yahoo Finance**: Sin soporte oficial (scraping)
- **Finviz**: Sin soporte oficial (scraping)
- **FMP**: support@financialmodelingprep.com
- **Documentación FMP**: https://site.financialmodelingprep.com/developer/docs

---

**Fin de Documentación API v1.0**

# 📊 Sistema de Evaluación de Acciones - Documentación Técnica

## 🎯 Visión General

El sistema RVC (Risk-Value-Confidence) es un motor de análisis fundamental que evalúa acciones mediante **3 scores independientes** combinados en un **score de inversión final**. Utiliza datos de múltiples fuentes con sistema de fallback y provenance tracking.

---

## 🏗️ Arquitectura del Sistema

### 📦 Arquitectura Modular de Analizadores

El sistema utiliza una **arquitectura modular** basada en herencia de clases abstractas, permitiendo escalar fácilmente a nuevos tipos de activos (CRYPTO, INDEX, etc.).

```
analyzers/
├── __init__.py              # Exports: BaseAnalyzer, EquityAnalyzer, ETFAnalyzer
├── base_analyzer.py         # Clase abstracta con métodos analyze(), get_asset_type()
├── equity_analyzer.py       # EquityAnalyzer (antes InvestmentScorer)
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
- `etf_analyzer.py` → Wrapper que exporta `ETFAnalyzer` desde el módulo

### 🔄 Flujo de Análisis

```
┌─────────────────────────────────────────────────────────────┐
│                    ENTRADA: Ticker (ej: AAPL)               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  PASO 1: CLASIFICACIÓN DE ACTIVO (AssetClassifier)          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ • Determina tipo: EQUITY, ETF, CRYPTO, FOREX, etc.  │   │
│  │ • Decide si es analizable (EQUITY, ETF soportados)  │   │
│  │ • Usa overrides manuales + heurísticas del símbolo │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  PASO 2: RECOLECCIÓN DE DATOS (DataAgent)                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ PRIORIDAD DE FUENTES (cascada con fallback):        │   │
│  │ 1. AlphaVantage  (API premium - requiere key)      │   │
│  │ 2. TwelveData    (API premium - requiere key)      │   │
│  │ 3. FMP           (API premium - requiere key)      │   │
│  │ 4. Yahoo Finance (scraping - gratis)               │   │
│  │ 5. Finviz        (scraping - gratis)               │   │
│  │ 6. MarketWatch   (scraping - gratis)               │   │
│  │ 7. Datos ejemplo (fallback final)                  │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  PASO 3: NORMALIZACIÓN DE MÉTRICAS                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ • Merge de datos de múltiples fuentes               │   │
│  │ • Conversión de formatos (%, M, B, etc.)            │   │
│  │ • Tracking de provenance (qué fuente dio qué dato)  │   │
│  │ • Validación de rangos razonables                   │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  PASO 4: SELECCIÓN DE ANALIZADOR (Factory Pattern)          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ if asset_type == "EQUITY":                          │   │
│  │     analyzer = EquityAnalyzer()                     │   │
│  │ elif asset_type == "ETF":                           │   │
│  │     analyzer = ETFAnalyzer()                        │   │
│  │ # Futuro: CryptoAnalyzer, IndexAnalyzer, etc.       │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  PASO 5: ANÁLISIS ESPECÍFICO POR TIPO                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ EquityAnalyzer.analyze() → 4 SCORES                 │   │
│  │    A) QUALITY SCORE (0-100)                         │   │
│  │       - ROE (40%)                                   │   │
│  │       - ROIC (35%)                                  │   │
│  │       - Operating Margin (15%)                      │   │
│  │       - Net Margin (10%)                            │   │
│  │                                                      │   │
│  │    B) VALUATION SCORE (0-100)                       │   │
│  │       - P/E Ratio (40%)                             │   │
│  │       - PEG Ratio (35%)                             │   │
│  │       - Price to Book (25%)                         │   │
│  │                                                      │   │
│  │    C) HEALTH SCORE (0-100)                          │   │
│  │       - Debt to Equity (60%)                        │   │
│  │       - Current Ratio (30%)                         │   │
│  │       - Quick Ratio (10%)                           │   │
│  │                                                      │   │
│  │    D) GROWTH SCORE (0-100)                          │   │
│  │       - Revenue Growth (60%)                        │   │
│  │       - Earnings Growth (40%)                       │   │
│  │                                                      │   │
│  │ ETFAnalyzer.analyze() → RESUMEN INFORMATIVO         │   │
│  │    - NAV, Premium/Discount, Expense Ratio           │   │
│  │    - Score: 0-100 basado en 5 factores             │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  PASO 6: INVESTMENT SCORE (SCORE FINAL - Solo EQUITY)       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ FILOSOFÍA:                                          │   │
│  │ • Calidad mínima 60 requerida                       │   │
│  │ • Balance óptimo: calidad 70-90 + valoración 60-80 │   │
│  │ • Bonuses por salud excepcional y crecimiento       │   │
│  │ • Penalización fuerte si calidad < 50               │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  PASO 7: CATEGORIZACIÓN Y RECOMENDACIÓN                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ • SWEET SPOT 🏆   (calidad ≥75, valoración ≥60)    │   │
│  │ • PREMIUM ⭐      (calidad ≥85, valoración ≥40)    │   │
│  │ • VALUE 💎        (calidad ≥60, valoración ≥70)    │   │
│  │ • QUALITY ✅      (calidad ≥70, valoración ≥40)    │   │
│  │ • RISKY 🎲        (calidad <60, valoración ≥60)    │   │
│  │ • OVERVALUED 🚨   (calidad <70, valoración <50)    │   │
│  │ • AVOID ⛔        (otras combinaciones)             │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  SALIDA: JSON con scores, categoría y recomendación         │
└─────────────────────────────────────────────────────────────┘
```

---

## 📥 1. RECOLECCIÓN DE DATOS (DataAgent)

### 🔄 Sistema de Cascada con Fallback

El `DataAgent` intenta obtener datos en este orden estricto:

```python
PRIORIDAD DE FUENTES:
1. AlphaVantage  → API premium (requiere ALPHA_VANTAGE_KEY)
2. TwelveData    → API premium (requiere TWELVEDATA_API_KEY)
3. FMP           → API premium (requiere FMP_API_KEY)
4. Yahoo Finance → Web scraping (gratis, sin límites)
5. Finviz        → Web scraping (gratis, sin límites)
6. MarketWatch   → Web scraping (gratis, sin límites)
7. Ejemplo       → Datos hardcodeados (último recurso)
```

### 🎯 Métricas Recolectadas

```python
CATEGORÍAS DE MÉTRICAS:
├── VALORACIÓN
│   ├── current_price      # Precio actual
│   ├── market_cap         # Capitalización de mercado
│   ├── pe_ratio           # P/E (Trailing)
│   ├── forward_pe         # P/E Forward
│   ├── peg_ratio          # PEG (P/E to Growth)
│   ├── price_to_book      # P/B (Precio sobre valor en libros)
│   ├── price_to_sales     # P/S
│   └── ev_to_ebitda       # EV/EBITDA
│
├── RENTABILIDAD (CALIDAD)
│   ├── roe                # Return on Equity
│   ├── roic               # Return on Invested Capital
│   ├── roa                # Return on Assets
│   ├── gross_margin       # Margen Bruto
│   ├── operating_margin   # Margen Operativo
│   └── net_margin         # Margen Neto
│
├── SALUD FINANCIERA
│   ├── debt_to_equity     # Deuda sobre Capital
│   ├── current_ratio      # Ratio Corriente (liquidez)
│   └── quick_ratio        # Ratio Rápido (liquidez estricta)
│
└── CRECIMIENTO
    ├── revenue_growth         # Crecimiento ingresos anual
    ├── revenue_growth_qoq     # Crecimiento ingresos trimestral
    ├── revenue_growth_5y      # Crecimiento ingresos 5 años
    ├── earnings_growth        # Crecimiento ganancias anual
    ├── earnings_growth_this_y # Estimado este año
    ├── earnings_growth_next_y # Estimado próximo año
    ├── earnings_growth_next_5y# Estimado 5 años
    └── earnings_growth_qoq    # Crecimiento ganancias trimestral
```

### 🔍 Proceso de Scraping (Ejemplo: Yahoo Finance)

```python
def _fetch_yahoo(self, ticker: str) -> SourceResult:
    """
    1. Construye URL: https://finance.yahoo.com/quote/{ticker}
    2. Hace request HTTP con User-Agent simulado
    3. Parsea HTML con BeautifulSoup
    4. Busca tablas de "Statistics", "Valuation", "Financial"
    5. Extrae valores con regex para limpiar formatos ($, M, B, %)
    6. Convierte unidades (M → millones, B → billones)
    7. Retorna dict con métricas encontradas
    """
    url = f"https://finance.yahoo.com/quote/{ticker}"
    resp = self._get(url)
    
    # Extrae tablas del DOM
    soup = BeautifulSoup(resp.text, 'html.parser')
    stats_table = soup.find('table', class_='W(100%) M(0)')
    
    # Procesa cada fila
    for row in stats_table.find_all('tr'):
        label = row.find('td').text.strip()
        value = row.find_all('td')[1].text.strip()
        
        # Normaliza labels con aliases
        if label in self.metric_aliases["pe_ratio"]:
            metrics["pe_ratio"] = self._parse_number(value)
    
    return SourceResult(data=metrics, source="yahoo", coverage=len(metrics))
```

### 🧩 Merge de Múltiples Fuentes

```python
def _merge_sources(self, results: List[SourceResult]) -> Dict:
    """
    Estrategia de merge con provenance tracking:
    
    1. Para cada métrica:
       - Usa PRIMERA fuente que la tenga (orden de prioridad)
       - Guarda en self.provenance[métrica] = "fuente_X"
    
    2. Métricas críticas (pe_ratio, roe, etc.):
       - Si faltan, busca en TODAS las fuentes disponibles
    
    3. Data Completeness:
       - Calcula % de métricas críticas obtenidas
       - Ej: 6 de 7 métricas = 85.7% completeness
    """
    merged = {}
    
    for metric in self.critical_metrics:
        for source_result in results:  # Orden de prioridad
            if metric in source_result.data:
                merged[metric] = source_result.data[metric]
                self.provenance[metric] = source_result.source
                break  # Usa primera que encuentre
    
    # Agrega campo de provenance al resultado final
    merged["data_provenance"] = self.provenance
    merged["data_completeness"] = (len(merged) / len(self.critical_metrics)) * 100
    
    return merged
```

---

## 🎯 2. CLASIFICACIÓN DE ACTIVOS (AssetClassifier)

### 🔖 Tipos de Activos Soportados

```python
ASSET_TYPES = {
    "EQUITY": "Acción individual",      # ✅ Analizable
    "ETF": "Fondo cotizado (ETF)",      # ℹ️ Informativo
    "INDEX": "Índice de mercado",       # ❌ No analizable
    "CRYPTO": "Criptomoneda",           # ❌ No analizable
    "FOREX": "Par de divisas",          # ❌ No analizable
    "COMMODITY": "Materia prima",       # ❌ No analizable
    "BOND": "Bono",                     # ❌ No analizable
    "MUTUAL_FUND": "Fondo mutuo",       # ❌ No analizable
    "UNKNOWN": "Tipo desconocido"       # ❌ No analizable
}
```

### 🧠 Lógica de Clasificación

```python
def classify(self, ticker: str, metrics: Dict) -> AssetClassification:
    """
    ORDEN DE PRIORIDAD:
    
    1. MANUAL OVERRIDES (hardcodeados)
       Ej: "SPY" → ETF, "BTC-USD" → CRYPTO
    
    2. HEURÍSTICAS DEL SÍMBOLO
       - Contiene "-USD" → CRYPTO
       - Contiene "=" → FOREX
       - Termina en ".X" → INDEX
       - Longitud 1-3 → Probable INDEX
    
    3. METADATOS DE APIs
       - FMP: field "type" en Overview
       - AlphaVantage: field "AssetType"
    
    4. ANÁLISIS DE MÉTRICAS
       - Tiene expense_ratio pero no roe → ETF
       - Tiene holdings_count → ETF
       - Tiene crypto_* fields → CRYPTO
    
    5. DEFAULT → EQUITY
       Si nada indica otra cosa, asume acción
    """
    
    # Paso 1: Overrides
    if ticker in MANUAL_OVERRIDES:
        return MANUAL_OVERRIDES[ticker]
    
    # Paso 2: Heurísticas
    if "-USD" in ticker:
        return "CRYPTO"
    if len(ticker) <= 3 and ticker.startswith("^"):
        return "INDEX"
    
    # Paso 3: Metadatos
    if metrics.get("asset_type") == "ETF":
        return "ETF"
    
    # Paso 4: Análisis de métricas
    if metrics.get("expense_ratio") and not metrics.get("roe"):
        return "ETF"
    
    # Paso 5: Default
    return "EQUITY"
```

### 🎓 Métricas Especiales por Tipo

```python
SPECIAL_METRICS = {
    "ETF": [
        "expense_ratio",      # Ratio de gastos
        "aum",                # Assets Under Management
        "holdings_count",     # Número de holdings
        "dividend_yield",     # Rendimiento de dividendos
        "tracking_error"      # Error de seguimiento
    ],
    "CRYPTO": [
        "circulating_supply",
        "max_supply",
        "market_dominance"
    ]
}
```

---

## 📊 3. MOTOR DE SCORING

### 🎯 Arquitectura Modular de Analizadores

El sistema utiliza **analizadores especializados** que heredan de `BaseAnalyzer` (clase abstracta):

```python
# analyzers/base_analyzer.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAnalyzer(ABC):
    """Clase base abstracta para todos los analizadores de activos."""
    
    @abstractmethod
    def analyze(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza las métricas y retorna resultados específicos del tipo de activo."""
        pass
    
    @abstractmethod
    def get_asset_type(self) -> str:
        """Retorna el tipo de activo que este analizador maneja."""
        pass
    
    def validate_metrics(self, metrics: Dict[str, Any], required: list) -> bool:
        """Valida que las métricas requeridas estén presentes."""
        return all(metrics.get(metric) is not None for metric in required)
```

### 📈 A) EquityAnalyzer (Análisis de Acciones)

**Ubicación:** `analyzers/equity_analyzer.py` (701 líneas)

**Herencia:** `class EquityAnalyzer(BaseAnalyzer)`

**Método principal:** `analyze(metrics: Dict) -> Dict`

#### 🏆 QUALITY SCORE (Score de Calidad)

**¿Qué tan buena es la empresa operativamente?**

```python
PONDERACIONES:
├── ROE (Return on Equity) ············ 40%
│   Mide rentabilidad sobre capital propio
│   
├── ROIC (Return on Invested Capital) · 35%
│   Mide eficiencia en uso de capital
│   
├── Operating Margin ·················· 15%
│   Mide eficiencia operativa
│   
└── Net Margin ···················· 10%
    Mide rentabilidad final

ESCALA DE EVALUACIÓN (ROE):
ROE > 20%  → Score 100 (excelente)
ROE > 15%  → Score 85  (muy bueno)
ROE > 10%  → Score 70  (bueno)
ROE > 5%   → Score 50  (aceptable)
ROE > 0%   → Score 30  (pobre)
ROE ≤ 0%   → Score 10  (muy pobre)

RESULTADO FINAL:
Score = Σ (score_métrica × peso_métrica) / Σ pesos_usados
```

**Ejemplo de Cálculo:**

```python
# Empresa hipotética
metrics = {
    "roe": 18.5,              # Score: 85
    "roic": 14.2,             # Score: 80
    "operating_margin": 22.3, # Score: 90
    "net_margin": 15.1        # Score: 95
}

# Cálculo ponderado
quality_score = (
    (85 × 0.40) +   # ROE
    (80 × 0.35) +   # ROIC
    (90 × 0.15) +   # Operating Margin
    (95 × 0.10)     # Net Margin
) = 85.0

# Interpretación
if quality_score >= 85:
    return "Empresa de calidad excepcional"
elif quality_score >= 70:
    return "Empresa de buena calidad"
elif quality_score >= 60:
    return "Empresa de calidad aceptable"
else:
    return "Empresa de baja calidad"
```

### 💰 B) VALUATION SCORE (Score de Valoración)

**¿Qué tan caro está el precio?**

```python
PONDERACIONES:
├── P/E Ratio (Price to Earnings) ····· 40%
│   Cuánto pagas por $1 de ganancias
│   
├── PEG Ratio (P/E to Growth) ········· 35%
│   P/E ajustado por crecimiento
│   
└── P/B (Price to Book) ··············· 25%
    Precio sobre valor en libros

ESCALA DE EVALUACIÓN (P/E):
P/E < 12   → Score 100 (muy barato)
P/E < 15   → Score 90  (barato)
P/E < 20   → Score 75  (justo)
P/E < 25   → Score 60  (algo caro)
P/E < 30   → Score 45  (caro)
P/E < 40   → Score 30  (muy caro)
P/E ≥ 40   → Score 15  (extremadamente caro)

⚠️ IMPORTANTE:
Score ALTO = BARATO (buena oportunidad)
Score BAJO = CARO (precio elevado)
```

**Ejemplo de Cálculo:**

```python
# Empresa hipotética
metrics = {
    "pe_ratio": 18.5,    # Score: 75 (justo)
    "peg_ratio": 1.2,    # Score: 75 (justo)
    "price_to_book": 2.8 # Score: 70 (razonable)
}

# Cálculo ponderado
valuation_score = (
    (75 × 0.40) +   # P/E
    (75 × 0.35) +   # PEG
    (70 × 0.25)     # P/B
) = 73.75

# Interpretación
if valuation_score >= 70:
    return "Valoración atractiva"
elif valuation_score >= 50:
    return "Valoración razonable"
else:
    return "Sobrevalorada"
```

### 🏥 C) HEALTH SCORE (Score de Salud Financiera)

**¿Qué tan sólida está financieramente?**

```python
PONDERACIONES:
├── Debt to Equity ···················· 60%
│   Nivel de endeudamiento
│   
├── Current Ratio ····················· 30%
│   Liquidez a corto plazo
│   
└── Quick Ratio ······················· 10%
    Liquidez inmediata

ESCALA (Debt to Equity):
D/E < 0.3  → Score 100 (muy saludable)
D/E < 0.5  → Score 90  (saludable)
D/E < 1.0  → Score 75  (aceptable)
D/E < 1.5  → Score 55  (moderado riesgo)
D/E < 2.0  → Score 35  (alto riesgo)
D/E ≥ 2.0  → Score 15  (muy alto riesgo)
```

### 📈 D) GROWTH SCORE (Score de Crecimiento)

**¿Qué tan rápido está creciendo?**

```python
PONDERACIONES:
├── Revenue Growth ···················· 60%
│   Crecimiento de ingresos
│   
└── Earnings Growth ··················· 40%
    Crecimiento de ganancias

PRIORIDAD DE MÉTRICAS (Revenue):
1. revenue_growth_next_5y   (proyección 5 años)
2. revenue_growth_5y        (histórico 5 años)
3. revenue_growth           (anual)
4. revenue_growth_qoq       (trimestral)

ESCALA (Revenue Growth %):
Growth > 25%  → Score 100 (hiper-crecimiento)
Growth > 15%  → Score 85  (crecimiento fuerte)
Growth > 10%  → Score 70  (crecimiento sólido)
Growth > 5%   → Score 55  (crecimiento moderado)
Growth > 0%   → Score 40  (crecimiento lento)
Growth ≤ 0%   → Score 15  (decrecimiento)
```

### 📊 B) ETFAnalyzer (Análisis de ETFs)

**Ubicación:** `analyzers/etf_analyzer.py` (173 líneas)

**Herencia:** `class ETFAnalyzer(BaseAnalyzer)`

**Método principal:** `analyze(metrics: Dict) -> Dict`

**Enfoque:** Análisis informativo (no genera Investment Score como acciones)

```python
# Ejemplo de uso
from analyzers import ETFAnalyzer

analyzer = ETFAnalyzer()
result = analyzer.analyze(metrics)

# Resultado incluye:
{
    "asset_type": "ETF",
    "analysis_type": "informative",
    "summary": {
        "nav": 450.23,
        "premium_discount": -0.15,  # -0.15% descuento
        "expense_ratio": 0.03,       # 0.03% anual
        "total_score": 85.0          # 0-100 basado en 5 factores
    },
    "label": "🟢",  # 🟢🟡🟠🔴 según score
    "scores": {
        "expense_score": 95,     # Menor = mejor
        "tracking_score": 90,    # Error de seguimiento
        "liquidity_score": 85,   # Volumen de trading
        "size_score": 80,        # AUM
        "dividend_score": 75     # Rendimiento de dividendos
    }
}
```

**Factores de evaluación:**

```python
ETF_SCORING_FACTORS = {
    "expense_ratio": {
        "weight": 0.30,
        "scale": {
            "< 0.05%": 100,
            "< 0.10%": 90,
            "< 0.20%": 75,
            "< 0.50%": 60,
            ">= 0.50%": 30
        }
    },
    "tracking_error": {
        "weight": 0.25,
        "scale": {
            "< 0.50%": 100,
            "< 1.00%": 85,
            "< 2.00%": 70,
            ">= 2.00%": 40
        }
    },
    "aum": {
        "weight": 0.20,
        "scale": {
            "> $10B": 100,
            "> $5B": 85,
            "> $1B": 70,
            "> $500M": 50,
            "<= $500M": 30
        }
    },
    "liquidity": {
        "weight": 0.15,
        "scale": "avg_volume > 1M shares = 100"
    },
    "dividend_yield": {
        "weight": 0.10,
        "scale": "> 3% = 100, > 2% = 80, etc."
    }
}
```

---

## 🎯 4. INVESTMENT SCORE (Score Final de Inversión - Solo EQUITY)

### 🧮 Algoritmo de Cálculo

**Pregunta central: ¿Compro AHORA o no?**

```python
FILOSOFÍA:
1. Calidad mínima 60 requerida
2. Valoración mínima 40 requerida para calidad alta
3. Balance óptimo: calidad 70-90 + valoración 60-80
4. Bonuses por salud excepcional y crecimiento
5. Penalizaciones fuertes por baja calidad

CASOS DE EVALUACIÓN:

CASO 1: Calidad insuficiente (quality < 60)
├── Si quality < 50:
│   └── investment = quality × 0.40  (penalización muy fuerte)
└── Si 50 ≤ quality < 60:
    └── investment = quality × 0.50  (penalización fuerte)

CASO 2: Sweet Spot (70 ≤ quality ≤ 95 AND valuation ≥ 60)
├── Base: (quality × 0.45) + (valuation × 0.45)
├── Bonus: +3 si health ≥ 85
├── Bonus: +2 si growth ≥ 75
└── Máximo: 100

CASO 3: Calidad élite pero cara (quality ≥ 85 AND valuation < 60)
├── Base: (quality × 0.50) + (valuation × 0.35)
├── Bonus: +5 si growth ≥ 70
├── Límite: 75 si valuation < 40
└── Máximo: 85

CASO 4: Calidad media + precio muy bueno (60 ≤ quality < 70 AND valuation ≥ 70)
├── Base: (quality × 0.40) + (valuation × 0.50)
├── Bonus: +3 si health ≥ 75
└── Sin límite

CASO 5: Calidad buena pero precio algo caro (70 ≤ quality < 85 AND 50 ≤ valuation < 60)
├── Base: (quality × 0.45) + (valuation × 0.40)
├── Bonus: +3 si growth ≥ 65
└── Sin límite

CASO 6: Otros (balances no óptimos)
└── Base: (quality × 0.40) + (valuation × 0.40) + (health × 0.10) + (growth × 0.10)
```

**Ejemplo Real:**

```python
# Apple (AAPL) - Ejemplo hipotético
scores = {
    "quality": 88,      # Excelente ROE, ROIC, márgenes
    "valuation": 55,    # P/E ~28 (algo cara)
    "health": 90,       # Debt/Equity bajo, alta liquidez
    "growth": 72        # Crecimiento sólido pero no explosivo
}

# Entra en CASO 3 (calidad élite pero cara)
investment = (88 × 0.50) + (55 × 0.35)  # = 63.25
investment += 5  # Bonus por growth ≥ 70  # = 68.25
investment = min(85, 68.25)  # Límite CASO 3 # = 68.25

# Recomendación
if investment >= 75:
    return "🟢 COMPRAR"
elif investment >= 60:
    return "🟡 CONSIDERAR"  # ← Apple entraría aquí
elif investment >= 45:
    return "🟠 ESPERAR"
else:
    return "🔴 EVITAR"
```

---

## 🏷️ 5. CATEGORIZACIÓN

### 🎨 Categorías de Inversión

```python
MATRIZ DE CATEGORIZACIÓN:

           │ Valoración Alta (≥60) │ Valoración Media (≥40) │ Valoración Baja (<40)
───────────┼────────────────────────┼────────────────────────┼─────────────────────
Calidad    │                        │                        │
Alta (≥75) │ 🏆 SWEET SPOT          │ ⭐ PREMIUM             │ ⭐ PREMIUM
           │ "Lo mejor de ambos"    │ "Excelente pero cara" │ "Excelente pero cara"
───────────┼────────────────────────┼────────────────────────┼─────────────────────
Calidad    │ 💎 VALUE               │ ✅ QUALITY             │ 🎲 RISKY
Media      │ "Buena oportunidad"    │ "Empresa sólida"       │ "Riesgo moderado"
(60-74)    │                        │                        │
───────────┼────────────────────────┼────────────────────────┼─────────────────────
Calidad    │ 🎲 RISKY               │ 🚨 OVERVALUED          │ ⛔ AVOID
Baja (<60) │ "Alto riesgo"          │ "Cara y débil"         │ "No recomendada"
           │                        │                        │

DETALLES DE CATEGORÍAS:

🏆 SWEET SPOT
├── Condición: quality ≥ 75 AND valuation ≥ 60
├── Color: Verde
├── Descripción: "Calidad + Precio ideal"
└── Recomendación típica: 🟢 COMPRAR

⭐ PREMIUM
├── Condición: quality ≥ 85 AND valuation ≥ 40
├── Color: Azul
├── Descripción: "Excelente empresa, precio elevado"
└── Recomendación típica: 🟡 CONSIDERAR

💎 VALUE
├── Condición: quality ≥ 60 AND valuation ≥ 70
├── Color: Dorado
├── Descripción: "Precio atractivo, calidad aceptable"
└── Recomendación típica: 🟡 CONSIDERAR

✅ QUALITY
├── Condición: quality ≥ 70 AND valuation ≥ 40
├── Color: Verde claro
├── Descripción: "Empresa sólida, valoración razonable"
└── Recomendación típica: 🟡 CONSIDERAR

🎲 RISKY
├── Condición: quality < 60 AND valuation ≥ 60
├── Color: Naranja
├── Descripción: "Barata pero débil fundamentalmente"
└── Recomendación típica: 🟠 ESPERAR

🚨 OVERVALUED
├── Condición: quality < 70 AND valuation < 50
├── Color: Rojo
├── Descripción: "Cara y calidad cuestionable"
└── Recomendación típica: 🔴 EVITAR

⛔ AVOID
├── Condición: Otras combinaciones negativas
├── Color: Rojo oscuro
├── Descripción: "No cumple criterios mínimos"
└── Recomendación típica: 🔴 EVITAR
```

---

## 💡 6. RECOMENDACIONES FINALES

### 🎯 Lógica de Recomendación

```python
def _get_recommendation(investment, quality, valuation, category):
    """
    ESCALA DE INVESTMENT SCORE:
    
    ≥ 75  → 🟢 COMPRAR
    60-74 → 🟡 CONSIDERAR
    45-59 → 🟠 ESPERAR
    < 45  → 🔴 EVITAR
    
    CASOS ESPECIALES:
    - Calidad < 50: Siempre EVITAR (override)
    - SWEET SPOT: Siempre COMPRAR (override)
    - PREMIUM + investment ≥ 70: COMPRAR
    """
    
    # Override 1: Baja calidad
    if quality < 50:
        return {
            "action": "🔴 EVITAR",
            "reasoning": "Calidad fundamental insuficiente",
            "risk_level": "Alto"
        }
    
    # Override 2: Sweet Spot
    if category["name"] == "SWEET SPOT":
        return {
            "action": "🟢 COMPRAR",
            "reasoning": "Balance ideal de calidad y precio",
            "risk_level": "Bajo"
        }
    
    # Escala estándar
    if investment >= 75:
        return {"action": "🟢 COMPRAR", "risk_level": "Bajo-Medio"}
    elif investment >= 60:
        return {"action": "🟡 CONSIDERAR", "risk_level": "Medio"}
    elif investment >= 45:
        return {"action": "🟠 ESPERAR", "risk_level": "Medio-Alto"}
    else:
        return {"action": "🔴 EVITAR", "risk_level": "Alto"}
```

### 📋 Estructura de Respuesta JSON

```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "current_price": 178.45,
  "asset_type": "EQUITY",
  "analysis_allowed": true,
  
  "scores": {
    "quality_score": 88,
    "valuation_score": 55,
    "health_score": 90,
    "growth_score": 72,
    "investment_score": 68
  },
  
  "category": {
    "name": "PREMIUM",
    "color": "blue",
    "desc": "Excelente empresa, precio elevado",
    "emoji": "⭐"
  },
  
  "recommendation": {
    "action": "🟡 CONSIDERAR",
    "reasoning": "Empresa de calidad excepcional pero valoración elevada. Esperar corrección o comprar gradualmente.",
    "risk_level": "Medio",
    "confidence": "Alta"
  },
  
  "breakdown": {
    "quality": {
      "score": 88,
      "components": [
        {"metric": "ROE", "value": 147.3, "score": 100, "weight": 0.40},
        {"metric": "ROIC", "value": 38.2, "score": 100, "weight": 0.35},
        {"metric": "Operating Margin", "value": 29.8, "score": 100, "weight": 0.15},
        {"metric": "Net Margin", "value": 25.3, "score": 100, "weight": 0.10}
      ]
    },
    "valuation": {
      "score": 55,
      "components": [
        {"metric": "P/E", "value": 28.5, "score": 50, "weight": 0.40},
        {"metric": "PEG", "value": 2.1, "score": 35, "weight": 0.35},
        {"metric": "P/B", "value": 42.8, "score": 15, "weight": 0.25}
      ]
    }
  },
  
  "data_completeness": 92,
  "data_provenance": {
    "current_price": "yahoo",
    "pe_ratio": "finviz",
    "roe": "alpha_vantage",
    "roic": "fmp"
  },
  
  "warnings": [
    "P/B muy elevado (42.8) - típico en empresas tech",
    "PEG > 2.0 indica valoración exigente"
  ]
}
```

---

## 🔧 7. CASOS EDGE Y MANEJO DE ERRORES

### ⚠️ Datos Incompletos

```python
ESTRATEGIAS:

1. Sub-Score con datos parciales:
   - Calcula solo con métricas disponibles
   - Ajusta pesos proporcionalmente
   - Marca "confidence": "Media" o "Baja"

2. Métricas faltantes críticas:
   - Si faltan > 50% de métricas críticas:
     → Retorna warning "Datos insuficientes"
   - Permite análisis parcial pero marca:
     → "data_completeness": 45

3. Sin datos de ninguna fuente:
   - Retorna mensaje educativo
   - Sugiere ticker alternativo
   - Ofrece datos de ejemplo
```

### 🚫 Activos No Analizables

```python
if asset_type != "EQUITY":
    return {
        "analysis_allowed": False,
        "message": "Solo se evalúan acciones individuales",
        "asset_type_label": AssetClassifier.ASSET_NAMES[asset_type],
        "alternative": "Consulte métricas específicas para ETFs/Cryptos"
    }
```

### 🔄 Rate Limits de APIs

```python
MANEJO:
1. AlphaVantage: 5 calls/min, 500 calls/day
   → Implementa cache de 24h
   → Fallback a TwelveData si excede

2. Scraping (Yahoo, Finviz):
   → Retry con exponential backoff
   → User-Agent rotation
   → Sleep entre requests (1.2s)

3. Cache SQLite:
   → Guarda resultados por 24h
   → Evita llamadas innecesarias
   → Mejora velocidad de respuesta
```

---

## 📊 8. MÉTRICAS DE CONFIANZA

### 🎯 Data Completeness

```python
CÁLCULO:
completeness = (métricas_obtenidas / métricas_críticas_totales) × 100

CLASIFICACIÓN:
≥ 85% → Confidence: "Alta"
70-84% → Confidence: "Media"
50-69% → Confidence: "Baja"
< 50% → Confidence: "Muy Baja" (no recomendable)

MÉTRICAS CRÍTICAS (mínimo para análisis):
1. current_price
2. pe_ratio
3. roe
4. roic
5. operating_margin
6. debt_to_equity
7. revenue_growth
```

### 🔍 Source Provenance

```python
TRACKING:
Para cada métrica, se guarda:
- Fuente que la proveyó
- Timestamp de obtención
- Versión del schema

USOS:
1. Debugging: "¿De dónde salió este P/E?"
2. Validación: "¿Es confiable esta fuente?"
3. Auditoría: "¿Cuándo se actualizó?"

EJEMPLO:
{
  "pe_ratio": 28.5,
  "pe_ratio_source": "finviz",
  "pe_ratio_timestamp": "2025-10-26T18:00:00",
  "pe_ratio_method": "scraping"
}
```

---

## 🎓 9. EJEMPLOS DE EVALUACIÓN COMPLETA

### Ejemplo 1: AAPL (Apple) - Calidad Alta, Cara

```plaintext
DATOS:
├── P/E: 28.5 (algo caro)
├── PEG: 2.1 (caro para crecimiento)
├── ROE: 147% (excepcional)
├── ROIC: 38% (excepcional)
├── Debt/Equity: 1.8 (moderado)
└── Revenue Growth: 8% (moderado)

SCORES:
├── Quality: 88 (ROE/ROIC compensan márgenes)
├── Valuation: 55 (P/E alto, PEG alto)
├── Health: 72 (deuda moderada)
└── Growth: 68 (crecimiento estable)

INVESTMENT: 68
CATEGORY: ⭐ PREMIUM
RECOMMENDATION: 🟡 CONSIDERAR
REASONING: "Empresa excepcional pero valoración elevada. 
            Esperar corrección a P/E < 25 o comprar gradualmente."
```

### Ejemplo 2: Stock Hipotético - Sweet Spot

```plaintext
DATOS:
├── P/E: 14.2 (barato)
├── PEG: 0.9 (muy barato)
├── ROE: 22% (excelente)
├── ROIC: 18% (excelente)
├── Debt/Equity: 0.4 (saludable)
└── Revenue Growth: 18% (fuerte)

SCORES:
├── Quality: 85
├── Valuation: 88
├── Health: 90
└── Growth: 85

INVESTMENT: 92
CATEGORY: 🏆 SWEET SPOT
RECOMMENDATION: 🟢 COMPRAR
REASONING: "Balance ideal de calidad y precio. 
            Empresa sólida con valoración atractiva."
```

### Ejemplo 3: Stock Especulativo - Risky

```plaintext
DATOS:
├── P/E: 8.5 (muy barato - señal de alerta)
├── PEG: 1.5 (razonable)
├── ROE: 3% (muy pobre)
├── ROIC: 2% (muy pobre)
├── Debt/Equity: 2.8 (muy alto)
└── Revenue Growth: -5% (decrecimiento)

SCORES:
├── Quality: 25 (fundamentales débiles)
├── Valuation: 82 (muy barata - value trap)
├── Health: 22 (alto riesgo)
└── Growth: 18 (decreciendo)

INVESTMENT: 18 (calidad × 0.40 = penalización)
CATEGORY: 🎲 RISKY
RECOMMENDATION: 🔴 EVITAR
REASONING: "Valoración barata pero fundamentales muy débiles. 
            Posible value trap. Alto riesgo de pérdida permanente."
```

---

## 🛠️ 10. CONFIGURACIÓN Y PERSONALIZACIÓN

### ⚙️ Ajuste de Pesos

```python
# En scoring_engine.py

# OPCIÓN 1: Enfoque conservador (prioriza calidad)
self.quality_weights = {
    "roe": 0.50,              # ↑ Más peso a ROE
    "roic": 0.30,             # ↓ Menos a ROIC
    "operating_margin": 0.15,
    "net_margin": 0.05
}

# OPCIÓN 2: Enfoque value (prioriza precio)
self.valuation_weights = {
    "pe_ratio": 0.50,         # ↑ Más peso a P/E
    "peg_ratio": 0.30,
    "price_to_book": 0.20
}

# OPCIÓN 3: Enfoque growth (prioriza crecimiento)
self.growth_weights = {
    "revenue_growth": 0.40,   # ↓ Menos a revenue
    "earnings_growth": 0.60   # ↑ Más a earnings
}
```

### 🎚️ Ajuste de Umbrales

```python
# Cambiar umbrales de categorización

def _categorize(self, quality, valuation):
    # MÁS CONSERVADOR (requiere mayor calidad)
    if quality >= 80 and valuation >= 65:  # ↑ Subió de 75/60
        return "SWEET SPOT"
    
    # MÁS AGRESIVO (acepta menor calidad)
    if quality >= 65 and valuation >= 70:  # ↓ Bajó de 70/75
        return "VALUE"
```

---

## 📚 GLOSARIO DE MÉTRICAS

| Métrica | Definición | Rango Ideal | Interpretación |
|---------|-----------|-------------|----------------|
| **P/E Ratio** | Precio / Ganancias por acción | 12-20 | Cuántos años de ganancias pagas |
| **PEG Ratio** | P/E / Tasa de crecimiento | 0.8-1.5 | P/E ajustado por crecimiento |
| **P/B Ratio** | Precio / Valor en libros | 1-3 | Sobreprecio vs activos netos |
| **ROE** | Ganancia / Capital accionistas | 15-25% | Rentabilidad sobre equity |
| **ROIC** | Ganancia / Capital invertido | 12-20% | Eficiencia en uso de capital |
| **Operating Margin** | EBIT / Revenue | 15-25% | Eficiencia operativa |
| **Debt/Equity** | Deuda / Capital propio | 0.3-1.0 | Nivel de apalancamiento |
| **Current Ratio** | Activos / Pasivos corrientes | 1.5-3.0 | Liquidez a corto plazo |

---

## ✅ RESUMEN EJECUTIVO

### Flujo Completo en 7 Pasos

1. **ENTRADA**: Usuario ingresa ticker (ej: AAPL)
2. **CLASIFICACIÓN**: Sistema determina tipo de activo → EQUITY ✅
3. **RECOLECCIÓN**: DataAgent consulta 7 fuentes con fallback
4. **NORMALIZACIÓN**: Merge de datos + provenance tracking
5. **SCORING**: Cálculo de 4 scores (Quality, Valuation, Health, Growth)
6. **INVERSIÓN**: Combina scores en Investment Score (0-100)
7. **SALIDA**: Categoría + Recomendación + Breakdown completo

### Fortalezas del Sistema

✅ **Multi-fuente** con fallback automático
✅ **Provenance tracking** (trazabilidad de datos)
✅ **Scoring ponderado** basado en fundamentales
✅ **Categorización intuitiva** (Sweet Spot, Premium, etc.)
✅ **Manejo de datos incompletos** con degradación elegante
✅ **Extensible** (fácil agregar nuevas fuentes/métricas)

### Limitaciones Conocidas

⚠️ Análisis completo solo para **EQUITY** (acciones)
⚠️ ETFs: análisis informativo (sin Investment Score)
⚠️ Depende de **datos públicos** (puede tener lag)
⚠️ **No considera** aspectos cualitativos (management, moats)
⚠️ **Scraping** puede fallar si sitios cambian estructura
⚠️ **Rate limits** en APIs gratuitas/premium

---

## 🚀 PRÓXIMOS PASOS / MEJORAS FUTURAS

### 🔧 Arquitectura Modular (Completado ✅)

- ✅ **Estructura `analyzers/`** creada
- ✅ **BaseAnalyzer abstracto** implementado
- ✅ **EquityAnalyzer** migrado (701 líneas)
- ✅ **ETFAnalyzer** migrado (173 líneas)
- ✅ **Wrappers de compatibilidad** (`scoring_engine.py`, `etf_analyzer.py`)
- ✅ **Imports actualizados** en `app.py`

**Beneficios logrados:**
- Separación de responsabilidades clara
- Fácil agregar nuevos tipos de activos (CryptoAnalyzer, IndexAnalyzer)
- Testing independiente por analizador
- Mantenibilidad mejorada

### 🎯 Próximas Mejoras

**📋 Plan Detallado:** Ver [IMPROVEMENT_PLAN.md](./IMPROVEMENT_PLAN.md) para análisis técnico completo.

#### 🔴 Fase 1 (P0): Fundamentos de Confianza
**Timeline:** 1-2 semanas
1. **Dispersión entre fuentes** - Ajustar confidence basado en discrepancia entre APIs
2. **Normalización TTM/MRQ/MRY** - Jerarquía clara de períodos contables + USD

#### 🟡 Fase 2 (P1): Valoración y Salud Avanzada
**Timeline:** 2-3 semanas
3. **EV/EBIT + FCF Yield** - Métricas de valoración basadas en caja libre
4. **Scores sector-relativos** - Normalización vs peers (z-scores)
5. **Net Debt/EBITDA** - Métrica principal de salud financiera

#### 🟢 Fase 3 (P2): Refinamiento
**Timeline:** 2-3 semanas
6. **Estabilidad de calidad** - Penalización por volatilidad de ROE/ROIC
7. **Jerarquía de crecimiento** - Prioridad 5y > anual > próximo año
8. **Winsorización de outliers** - Caps por métrica para evitar distorsión
9. **Confidence-aware recommendations** - Modular acciones por confidence

#### 🟠 Fase 4 (P3): Comparación Competitiva
**Timeline:** 4-6 semanas
10. **Normalización a peers** - Comparar vs top 10 competidores directos

#### 🚀 Nuevos Analizadores
11. **CryptoAnalyzer** - Análisis de criptomonedas
    - Métricas on-chain (supply, dominance, hash rate)
    - Scoring basado en: adopción, tecnología, equipo, tokenomics
    - Integración con APIs crypto (CoinGecko, CoinMarketCap)

12. **IndexAnalyzer** - Análisis de índices
    - Composición sectorial
    - Tracking histórico
    - Comparación vs benchmarks

#### 🔮 Futuro
13. **Análisis técnico** (RSI, MACD, Bollinger)
14. **Sentiment analysis** de noticias/redes sociales
15. **Backtesting** de recomendaciones históricas
16. **Alertas** cuando una acción entra en Sweet Spot
17. **Portfolio optimizer** (combinación óptima de activos)

---

## 📝 CHANGELOG DE ARQUITECTURA

### v3.1.0 - Modularización de Analizadores (26 Oct 2025)

**Cambios estructurales:**
- Creada carpeta `analyzers/` con arquitectura modular
- `BaseAnalyzer` (ABC) como interfaz común para todos los analizadores
- `EquityAnalyzer` migrado desde `InvestmentScorer` (scoring_engine.py)
- `ETFAnalyzer` migrado y mejorado con herencia de `BaseAnalyzer`

**Backward compatibility:**
- `scoring_engine.py` → wrapper que exporta `InvestmentScorer = EquityAnalyzer`
- `etf_analyzer.py` → wrapper que exporta `ETFAnalyzer` desde módulo
- Código existente funciona sin cambios

**Preparado para:**
- `CryptoAnalyzer` (criptomonedas)
- `IndexAnalyzer` (índices de mercado)
- Factory pattern para selección automática de analizador

---

**Documentación generada**: 26 de octubre de 2025
**Versión del sistema**: 3.1.0
**Última actualización**: Arquitectura modular de analizadores + 4 scores + Investment Score

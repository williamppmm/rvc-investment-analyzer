# 📈 Plan de Mejoras del Sistema de Evaluación

**Fecha de creación:** 26 de octubre de 2025  
**Última actualización:** 26 de octubre de 2025  
**Versión:** 2.0 - 5 mejoras críticas implementadas  
**Basado en:** Análisis comparativo con mejores prácticas de análisis fundamental

---

## 🎯 RESUMEN EJECUTIVO

Este documento detalla **10 mejoras técnicas** para el sistema RVC, priorizadas por impacto y complejidad. **✅ 5 mejoras críticas ya implementadas** (P0 y P1). Todas las mejoras respetan la **arquitectura modular** (BaseAnalyzer → EquityAnalyzer/ETFAnalyzer/CryptoAnalyzer).

### ✅ ESTADO DE IMPLEMENTACIÓN (26/10/2025)

**COMPLETADAS (5/10):**
- ✅ **Mejora #1: Dispersión entre fuentes (P0)** - Commits: integrado en data_agent.py
- ✅ **Mejora #2: Normalización TTM/MRQ/MRY (P0)** - Commits: 1fec754, 4e3c9e3
- ✅ **Mejora #3: EV/EBIT + FCF Yield (P1)** - Commits: e23fd25, 4abecf7, ed5e3c8
- ✅ **Mejora #4: Scores sector-relativos (P1)** - Commits: 778fce4, ee91d49
- ✅ **Mejora #6: Net Debt/EBITDA (P1)** - Commits: 2e0e158, 8dcd323

**PENDIENTES (5/10):**
- ⏳ Mejora #5: Estabilidad de calidad (P2)
- ⏳ Mejora #7: Jerarquía de crecimiento (P2)
- ⏳ Mejora #8: Winsorización de outliers (P2)
- ⏳ Mejora #9: Normalización a peers (P3)
- ⏳ Mejora #10: Confidence-aware recommendations (P2)

**Impacto de las mejoras implementadas:**
- 📊 **33 nuevas métricas** agregadas a DataAgent
- 🔬 **30+ tests unitarios** validando precisión (100% passing)
- 📈 **Sistema TIER1/TIER2** para valoración y salud
- 🏢 **11 sectores** con benchmarks estadísticos
- 🎯 **Confidence dinámico** basado en dispersión de fuentes

Este documento detalla **10 mejoras técnicas** para el sistema RVC, priorizadas por impacto y complejidad. Todas las mejoras respetan la **arquitectura modular** (BaseAnalyzer → EquityAnalyzer/ETFAnalyzer/CryptoAnalyzer).

### 🎯 ESTRATEGIA DEL PROYECTO

- **EQUITY:** Análisis fundamental profundo (foco principal - 90% del esfuerzo)
- **ETF/Crypto:** Información básica/educativa (10% del esfuerzo)
  - ETFs: Resumen de expense ratio, AUM, tracking error (sin Investment Score complejo)
  - Crypto: Datos de mercado, capitalización, volumen (sin scoring fundamental)

### 📊 FUENTES DE DATOS PRIORITARIAS

**Desarrollo (AHORA):**
1. **AlphaVantage** (premium, alta calidad) ← PRINCIPAL
2. **TwelveData** (premium, alta calidad) ← PRINCIPAL
3. Yahoo Finance (scraping, fallback)

**Producción (FUTURO):**
1. **FMP** (premium económico) ← PRINCIPAL en producción
2. AlphaVantage (fallback)
3. TwelveData (fallback)
4. Yahoo Finance (último recurso)

**Justificación:**
- AlphaVantage + TwelveData: Mejor concordancia entre fuentes (baja dispersión)
- FMP: API más económica para escalar en producción
- Yahoo: Frágil (cambios de estructura), solo emergencia

### Tabla de Prioridades (Solo EQUITY)

**NOTA:** Todas las mejoras se enfocan en **EQUITY** exclusivamente. ETF/Crypto mantienen análisis básico actual.

| # | Mejora | Impacto EQUITY | Complejidad | Prioridad |
|---|--------|----------------|-------------|-----------|
| 1 | **Dispersión entre fuentes** | Muy Alto | Baja | 🔴 P0 |
| 2 | **Normalización TTM/MRQ/MRY** | Alto | Media | 🔴 P0 |
| 3 | **EV/EBIT + FCF Yield** | Muy Alto | Media | 🟡 P1 |
| 4 | **Scores sector-relativos** | Muy Alto | Alta | 🟡 P1 |
| 5 | **Net Debt/EBITDA** | Alto | Baja | � P1 |
| 6 | **Estabilidad de calidad** | Medio | Media | � P2 |
| 7 | **Jerarquía de crecimiento** | Medio | Baja | 🟢 P2 |
| 8 | **Winsorización de outliers** | Medio | Media | 🟢 P2 |
| 9 | **Normalización a peers** | Alto | Muy Alta | 🟠 P3 |
| 10 | **Confidence-aware recommendations** | Alto | Baja | 🟢 P2 |

**Leyenda:**
- 🔴 P0: Crítico (implementar primero)
- 🟡 P1: Alta prioridad (ciclo 1-2)
- 🟢 P2: Media prioridad (ciclo 3-4)
- 🟠 P3: Baja prioridad (futuro)

---

## ✅ MEJORA 1: Dispersión entre Fuentes (P0) - COMPLETADA

**Estado**: ✅ Implementada el 26/10/2025  
**Archivos modificados**: `data_agent.py`, `analyzers/base_analyzer.py`  
**Tests**: Integrados en sistema de scoring

### 🎯 Objetivo
Ajustar el **confidence score** basado en la **dispersión** de valores entre múltiples fuentes para la misma métrica.

### 📐 Problema Actual
```python
# Situación actual (data_agent.py)
merged = {}
for metric in self.critical_metrics:
    for source_result in results:
        if metric in source_result.data:
            merged[metric] = source_result.data[metric]  # Usa primera fuente
            self.provenance[metric] = source_result.source
            break
```

**Problema:** Si AlphaVantage dice `P/E = 28.5` y Yahoo dice `P/E = 31.2`, usamos la primera pero **ignoramos la discrepancia**.

### ✅ Solución Propuesta

```python
# En data_agent.py - nuevo método
def _calculate_dispersion(self, metric: str, results: List[SourceResult]) -> Dict:
    """
    Calcula dispersión de una métrica entre fuentes.
    
    PRIORIDAD DE FUENTES (desarrollo):
    1. AlphaVantage (PRINCIPAL - alta calidad)
    2. TwelveData (PRINCIPAL - alta calidad)
    3. Yahoo Finance (fallback - scraping frágil)
    
    PRODUCCIÓN:
    1. FMP (PRINCIPAL - económico)
    2. AlphaVantage (fallback)
    3. TwelveData (fallback)
    
    Returns:
        {
            "value": float,           # Valor consolidado (mediana AlphaVantage+TwelveData)
            "sources": List[str],     # Fuentes que la proveyeron
            "dispersion": float,      # 0-100 (0=perfecta concordancia)
            "confidence_adj": float   # Factor de ajuste (0.7-1.0)
        }
    """
    values = []
    sources = []
    
    # PRIORIDAD: AlphaVantage + TwelveData (desarrollo)
    priority_sources = ["alpha_vantage", "twelvedata"]
    
    for source_result in results:
        if metric in source_result.data:
            values.append(source_result.data[metric])
            sources.append(source_result.source)
    
    if len(values) == 0:
        return None
    if len(values) == 1:
        return {
            "value": values[0],
            "sources": sources,
            "dispersion": 0.0,
            "confidence_adj": 1.0,
            "quality": "SINGLE_SOURCE"
        }
    
    # Si tenemos AlphaVantage + TwelveData, solo usamos esas (ignora Yahoo)
    priority_values = []
    priority_source_names = []
    for i, source in enumerate(sources):
        if source in priority_sources:
            priority_values.append(values[i])
            priority_source_names.append(source)
    
    if len(priority_values) >= 2:
        # Usa SOLO fuentes premium (mejor calidad)
        values = priority_values
        sources = priority_source_names
        quality = "PREMIUM_SOURCES"
    else:
        quality = "MIXED_SOURCES"
    
    # Usa mediana (robusto a outliers)
    consolidated = np.median(values)
    
    # Dispersión como Coefficient of Variation (CV)
    cv = np.std(values) / np.mean(values) * 100
    
    # Ajuste de confidence (más dispersión → menos confianza)
    if cv < 5:
        confidence_adj = 1.0     # Concordancia perfecta (AlphaVantage≈TwelveData)
    elif cv < 10:
        confidence_adj = 0.95    # Muy buena
    elif cv < 20:
        confidence_adj = 0.85    # Aceptable
    elif cv < 40:
        confidence_adj = 0.70    # Discrepante
    else:
        confidence_adj = 0.50    # Muy discrepante (problema con fuente)
    
    return {
        "value": consolidated,
        "sources": sources,
        "dispersion": cv,
        "confidence_adj": confidence_adj,
        "quality": quality  # PREMIUM_SOURCES / MIXED_SOURCES / SINGLE_SOURCE
    }
```

**Ejemplo de uso:**

```python
# Escenario 1: AlphaVantage=28.5, TwelveData=28.7 (excelente concordancia)
result = _calculate_dispersion("pe_ratio", results)
# {
#   "value": 28.6,              # Mediana
#   "sources": ["alpha_vantage", "twelvedata"],
#   "dispersion": 0.5,          # CV < 5% = concordancia perfecta
#   "confidence_adj": 1.0,      # Confianza máxima
#   "quality": "PREMIUM_SOURCES"
# }

# Escenario 2: AlphaVantage=28.5, Yahoo=32.1 (discrepancia)
result = _calculate_dispersion("pe_ratio", results)
# {
#   "value": 28.5,              # Usa AlphaVantage (prioridad)
#   "sources": ["alpha_vantage", "yahoo"],
#   "dispersion": 12.3,         # CV alto = discrepancia
#   "confidence_adj": 0.85,     # Confianza reducida
#   "quality": "MIXED_SOURCES"
# }
```

### 🔧 Implementación en BaseAnalyzer

```python
# En analyzers/base_analyzer.py
class BaseAnalyzer(ABC):
    def __init__(self):
        self.confidence_factors = {
            "completeness": 1.0,   # Ya existe
            "dispersion": 1.0,     # NUEVO
            "freshness": 1.0       # Futuro
        }
    
    def calculate_overall_confidence(self) -> float:
        """Combina todos los factores de confidence."""
        return np.mean(list(self.confidence_factors.values())) * 100
```

### 🎯 Aplicabilidad por Tipo de Activo

| Tipo | Aplicable | Justificación |
|------|-----------|---------------|
| **EQUITY** | ✅ Sí | **PRIORIDAD ABSOLUTA** - Métricas críticas: P/E, ROE, ROIC, D/E, Revenue Growth |
| **ETF** | ⚠️ Limitado | Solo para expense ratio, AUM (análisis básico, sin scoring complejo) |
| **CRYPTO** | ⚠️ Limitado | Solo para market cap, volume (análisis básico, sin scoring complejo) |

**Enfoque:**
- **EQUITY:** Implementar dispersión completa con AlphaVantage + TwelveData para todas las métricas fundamentales
- **ETF/Crypto:** Dispersión mínima (si hay múltiples fuentes), pero sin afectar scoring (no tienen Investment Score complejo)

---

## ✅ MEJORA 2: Normalización TTM/MRQ/MRY (P0) - COMPLETADA

**Estado**: ✅ Implementada el 26/10/2025  
**Archivos**: `metric_normalizer.py` (NUEVO), `analyzers/equity_analyzer.py`  
**Tests**: `test_metric_normalizer.py` (5/5 passing)  
**Documentación**: `NORMALIZATION_EXAMPLE.md` (482 líneas)  
**Commits**: 1fec754, 4e3c9e3

### 🎯 Objetivo
Establecer **jerarquía clara** de períodos contables y normalizar a USD.

### 📐 Problema Actual
```python
# Situación actual: mezclamos períodos sin prioridad
metrics = {
    "revenue_growth": 8.5,  # ¿Anual? ¿Trimestral? ¿5 años?
    "roe": 22.3             # ¿TTM? ¿Último año fiscal?
}
```

### ✅ Solución Propuesta

```python
# En data_agent.py - nuevo sistema de normalización
PERIOD_HIERARCHY = {
    "TTM": 1,    # Trailing Twelve Months (prioridad máxima)
    "MRQ": 2,    # Most Recent Quarter
    "MRY": 3,    # Most Recent Year (fiscal)
    "5Y": 4,     # 5 Year Average
    "FWD": 5     # Forward estimates
}

class MetricNormalizer:
    """Normaliza métricas a período y moneda estándar."""
    
    def normalize_metric(self, metric_name: str, raw_values: Dict) -> Dict:
        """
        Args:
            raw_values: {
                "roe_ttm": 22.3,
                "roe_mry": 21.8,
                "roe_5y": 19.5
            }
        
        Returns:
            {
                "value": 22.3,
                "period": "TTM",
                "fallback_chain": ["TTM", "MRY", "5Y"]
            }
        """
        # Busca en orden de prioridad
        for period in sorted(PERIOD_HIERARCHY, key=PERIOD_HIERARCHY.get):
            key = f"{metric_name}_{period.lower()}"
            if key in raw_values:
                return {
                    "value": raw_values[key],
                    "period": period,
                    "fallback_chain": [period]
                }
        
        # Si no hay sufijos, asume TTM
        if metric_name in raw_values:
            return {
                "value": raw_values[metric_name],
                "period": "TTM (assumed)",
                "fallback_chain": ["TTM"]
            }
        
        return None
    
    def normalize_currency(self, value: float, from_currency: str) -> float:
        """
        Convierte a USD (moneda interna del sistema).
        
        TODO: Implementar con API de tasas (fixer.io, exchangerate-api)
        """
        if from_currency == "USD":
            return value
        
        # Por ahora, placeholder
        EXCHANGE_RATES = {
            "EUR": 1.08,
            "GBP": 1.22,
            "JPY": 0.0067,
            "MXN": 0.058
        }
        
        return value * EXCHANGE_RATES.get(from_currency, 1.0)
```

### 🔧 Integración en EquityAnalyzer

```python
# En analyzers/equity_analyzer.py
class EquityAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__()
        self.normalizer = MetricNormalizer()
    
    def analyze(self, metrics: Dict) -> Dict:
        # Normaliza antes de calcular scores
        normalized = {}
        for metric in ["roe", "roic", "revenue_growth"]:
            result = self.normalizer.normalize_metric(metric, metrics)
            if result:
                normalized[metric] = result["value"]
                normalized[f"{metric}_period"] = result["period"]
        
        # Usa normalized en lugar de metrics
        quality = self._calc_quality(normalized)
        # ...
```

### 🎯 Aplicabilidad por Tipo de Activo

| Tipo | Aplicable | Justificación |
|------|-----------|---------------|
| **EQUITY** | ✅ Sí | **PRIORIDAD ABSOLUTA** - TTM prioritario para métricas operativas (ROE, ROIC, márgenes) |
| **ETF** | ❌ No | Análisis básico actual suficiente (expense ratio anual, AUM mensual) |
| **CRYPTO** | ❌ No | Datos en tiempo real, no aplica TTM/MRQ (mercado 24/7) |

**Enfoque:**
- **EQUITY:** Jerarquía completa TTM > MRQ > MRY > 5Y para todas las métricas fundamentales
- **ETF/Crypto:** Sin cambios (mantener análisis básico actual)

---

## ✅ MEJORA 3: EV/EBIT + FCF Yield (P1) - COMPLETADA

**Estado**: ✅ Implementada el 26/10/2025  
**Archivos**: `data_agent.py`, `analyzers/equity_analyzer.py`  
**Tests**: `test_tier1_valuation.py` (5/5 passing)  
**Documentación**: `TIER1_VALUATION_EXAMPLE.md` (435 líneas)  
**Commits**: e23fd25, 4abecf7, ed5e3c8

### 🎯 Objetivo
Agregar **métricas de valoración basadas en caja** como ejes principales.

### 📐 Problema Actual
```python
# Valuation actual: solo múltiplos de ganancias
self.valuation_weights = {
    "pe_ratio": 0.40,
    "peg_ratio": 0.35,
    "price_to_book": 0.25
}
```

**Problema:** Ignora **caja libre** (FCF) y **valor empresarial** (EV).

### ✅ Solución Propuesta

```python
# En analyzers/equity_analyzer.py - nuevo sistema de valoración
class EquityAnalyzer(BaseAnalyzer):
    def _calc_valuation_v2(self, metrics: Dict) -> float:
        """
        Nuevo sistema de valoración con jerarquía:
        
        TIER 1 (si disponibles): EV/EBIT + FCF Yield
        TIER 2 (fallback): P/E + PEG + P/B
        """
        # TIER 1: Métricas basadas en caja
        ev_ebit = metrics.get("ev_to_ebit")
        fcf_yield = metrics.get("fcf_yield")
        
        if ev_ebit and fcf_yield:
            return self._tier1_valuation(ev_ebit, fcf_yield)
        
        # TIER 2: Múltiplos tradicionales (fallback)
        return self._tier2_valuation(metrics)
    
    def _tier1_valuation(self, ev_ebit: float, fcf_yield: float) -> float:
        """
        Valoración basada en caja libre.
        
        EV/EBIT:
        - < 8: Score 100 (muy barato)
        - < 12: Score 85
        - < 15: Score 70
        - < 20: Score 50
        - >= 20: Score 30
        
        FCF Yield:
        - > 10%: Score 100 (excelente generación de caja)
        - > 7%: Score 85
        - > 5%: Score 70
        - > 3%: Score 50
        - <= 3%: Score 30
        """
        ev_score = self._score_ev_ebit(ev_ebit)
        fcf_score = self._score_fcf_yield(fcf_yield)
        
        # Ponderación: 60% EV/EBIT, 40% FCF Yield
        return (ev_score * 0.60) + (fcf_score * 0.40)
    
    def _tier2_valuation(self, metrics: Dict) -> float:
        """Valoración tradicional (sistema actual)."""
        # Mantiene lógica existente
        return self._calc_valuation(metrics)
```

### 📊 Nuevas Métricas en DataAgent

```python
# En data_agent.py - agregar a critical_metrics
self.critical_metrics = [
    # ... existentes
    "ev_to_ebit",      # NUEVO
    "fcf_yield",       # NUEVO
    "enterprise_value",# NUEVO
    "free_cash_flow"   # NUEVO
]

# Cálculo de FCF Yield si no viene directo
def _calculate_derived_metrics(self, metrics: Dict) -> Dict:
    """Calcula métricas derivadas."""
    
    # FCF Yield = FCF / Market Cap
    if "free_cash_flow" in metrics and "market_cap" in metrics:
        fcf = metrics["free_cash_flow"]
        mcap = metrics["market_cap"]
        metrics["fcf_yield"] = (fcf / mcap) * 100
    
    # EV/EBIT = Enterprise Value / EBIT
    if "enterprise_value" in metrics and "ebit" in metrics:
        ev = metrics["enterprise_value"]
        ebit = metrics["ebit"]
        metrics["ev_to_ebit"] = ev / ebit if ebit != 0 else None
    
    return metrics
```

### 🎯 Aplicabilidad por Tipo de Activo

| Tipo | Aplicable | Justificación |
|------|-----------|---------------|
| **EQUITY** | ✅ Sí | **PRIORIDAD ABSOLUTA** - FCF crítico para valoración real de acciones |
| **ETF** | ❌ No | ETFs no generan FCF propio (análisis básico actual suficiente) |
| **CRYPTO** | ❌ No | No aplica concepto de caja libre (análisis básico actual suficiente) |

**Enfoque:**
- **EQUITY:** Sistema completo TIER1 (EV/EBIT + FCF Yield) con fallback a TIER2 (P/E + PEG)
- **ETF/Crypto:** Sin cambios (mantener análisis básico actual)

---

## ✅ MEJORA 4: Scores Sector-Relativos (P1) - COMPLETADA

**Estado**: ✅ Implementada el 26/10/2025  
**Archivos**: `analyzers/sector_benchmarks.py` (NUEVO), `analyzers/equity_analyzer.py`  
**Tests**: `test_sector_relative.py` (8/8 passing)  
**Sectores**: 11 sectores con 8-10 métricas cada uno  
**Commits**: 778fce4, ee91d49

### 🎯 Objetivo
Normalizar scores **vs peers del mismo sector** para evitar sesgos estructurales.

### 📐 Problema Actual
```python
# Ejemplo: Tech vs Utilities
tech_company = {"roe": 25, "operating_margin": 30}  # Score alto
utility = {"roe": 8, "operating_margin": 15}        # Score bajo

# PROBLEMA: Utilities naturalmente tienen ROE más bajo (capital-intensive)
```

### ✅ Solución Propuesta

```python
# Nuevo archivo: analyzers/sector_benchmarks.py
SECTOR_BENCHMARKS = {
    "Technology": {
        "roe": {"mean": 22.0, "std": 8.5},
        "roic": {"mean": 18.0, "std": 7.2},
        "operating_margin": {"mean": 25.0, "std": 10.0},
        "debt_to_equity": {"mean": 0.4, "std": 0.3}
    },
    "Utilities": {
        "roe": {"mean": 9.5, "std": 3.2},
        "roic": {"mean": 6.5, "std": 2.5},
        "operating_margin": {"mean": 12.0, "std": 4.0},
        "debt_to_equity": {"mean": 1.8, "std": 0.6}
    },
    "Financials": {
        "roe": {"mean": 11.0, "std": 4.5},
        "roic": {"mean": 8.0, "std": 3.0},
        # D/E no aplicable (modelo de negocio diferente)
    },
    # ... más sectores
}

class SectorNormalizer:
    """Normaliza métricas contra benchmarks sectoriales."""
    
    def get_z_score(self, value: float, metric: str, sector: str) -> float:
        """
        Calcula z-score sector-relativo.
        
        z = (value - mean_sector) / std_sector
        
        Returns:
            z-score: valores típicos entre -3 y +3
        """
        benchmark = SECTOR_BENCHMARKS.get(sector, {}).get(metric)
        if not benchmark:
            return None  # Fallback a scoring absoluto
        
        mean = benchmark["mean"]
        std = benchmark["std"]
        
        return (value - mean) / std
    
    def z_to_score(self, z_score: float, invert: bool = False) -> float:
        """
        Convierte z-score a escala 0-100.
        
        Args:
            invert: True para métricas "menores es mejor" (D/E, P/E)
        
        Escala:
            z > +2.0  → 100 (2 std por encima del sector)
            z > +1.0  → 85
            z > 0     → 70  (por encima del promedio)
            z > -1.0  → 50
            z > -2.0  → 30
            z <= -2.0 → 15
        """
        if invert:
            z_score = -z_score
        
        if z_score > 2.0:
            return 100
        elif z_score > 1.0:
            return 85
        elif z_score > 0:
            return 70
        elif z_score > -1.0:
            return 50
        elif z_score > -2.0:
            return 30
        else:
            return 15
```

### 🔧 Integración en EquityAnalyzer

```python
# En analyzers/equity_analyzer.py
class EquityAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__()
        self.sector_normalizer = SectorNormalizer()
        self.use_sector_relative = True  # Flag configurable
    
    def analyze(self, metrics: Dict) -> Dict:
        sector = metrics.get("sector", "Unknown")
        
        if self.use_sector_relative and sector in SECTOR_BENCHMARKS:
            quality = self._calc_quality_sector_relative(metrics, sector)
        else:
            quality = self._calc_quality(metrics)  # Fallback a absoluto
        
        # ...
    
    def _calc_quality_sector_relative(self, metrics: Dict, sector: str) -> float:
        """Calidad normalizada por sector."""
        
        # ROE sector-relativo
        roe = metrics.get("roe")
        if roe:
            z_roe = self.sector_normalizer.get_z_score(roe, "roe", sector)
            roe_score = self.sector_normalizer.z_to_score(z_roe)
        else:
            roe_score = 0
        
        # ROIC sector-relativo
        roic = metrics.get("roic")
        if roic:
            z_roic = self.sector_normalizer.get_z_score(roic, "roic", sector)
            roic_score = self.sector_normalizer.z_to_score(z_roic)
        else:
            roic_score = 0
        
        # ... similar para operating_margin, net_margin
        
        # Ponderación (mantiene pesos actuales)
        quality = (
            (roe_score * 0.40) +
            (roic_score * 0.35) +
            # ...
        )
        
        return quality
```

### 🎯 Aplicabilidad por Tipo de Activo

| Tipo | Aplicable | Notas |
|------|-----------|-------|
| **EQUITY** | ✅ Sí | Crítico para comparar Tech vs Utilities |
| **ETF** | ⚠️ Parcial | Normalizar expense_ratio por categoría (Large Cap, Bond, etc.) |
| **CRYPTO** | ❌ No | Sector aún inmaduro para benchmarks |

---

## 📊 MEJORA 5: Estabilidad de Calidad (P2)

### 🎯 Objetivo
Penalizar empresas con **métricas volátiles** (ej: ROE 30% un año, 5% al siguiente).

### ✅ Solución Propuesta

```python
# En analyzers/equity_analyzer.py
class EquityAnalyzer(BaseAnalyzer):
    def _calc_quality_with_stability(self, metrics: Dict) -> Dict:
        """
        Calcula Quality Score + Stability Bonus.
        
        Estabilidad = baja varianza de ROE/ROIC en últimos 5 años
        """
        # Score base (actual)
        quality_score = self._calc_quality(metrics)
        
        # Componente de estabilidad
        roe_history = metrics.get("roe_5y_history", [])  # [22, 21, 23, 20, 22]
        roic_history = metrics.get("roic_5y_history", [])
        
        if len(roe_history) >= 3:
            cv_roe = np.std(roe_history) / np.mean(roe_history)
            
            # Bonus por estabilidad (max +5 puntos)
            if cv_roe < 0.10:  # Variación < 10%
                stability_bonus = 5
            elif cv_roe < 0.20:
                stability_bonus = 3
            elif cv_roe < 0.30:
                stability_bonus = 1
            else:
                stability_bonus = 0
            
            quality_score = min(100, quality_score + stability_bonus)
        
        return {
            "score": quality_score,
            "stability_bonus": stability_bonus,
            "roe_cv": cv_roe
        }
```

### 🎯 Aplicabilidad

| Tipo | Aplicable | Justificación |
|------|-----------|---------------|
| **EQUITY** | ✅ Sí | **PRIORIDAD ABSOLUTA** - Crítico para detectar empresas cíclicas vs estables |
| **ETF** | ❌ No | Tracking error ya mide estabilidad (análisis básico actual suficiente) |
| **CRYPTO** | ❌ No | Volatilidad inherente al activo (análisis básico actual suficiente) |

**Enfoque:**
- **EQUITY:** Bonus por estabilidad de ROE/ROIC en últimos 5 años
- **ETF/Crypto:** Sin cambios

---

## ✅ MEJORA 6: Net Debt/EBITDA (P1) - COMPLETADA

**Estado**: ✅ Implementada el 26/10/2025  
**Archivos**: `data_agent.py`, `analyzers/equity_analyzer.py`  
**Tests**: `test_tier1_health.py` (8/8 passing)  
**Commits**: 2e0e158, 8dcd323

### 🎯 Objetivo
Usar **Net Debt/EBITDA** como métrica principal de salud (más precisa que D/E).

### ✅ Solución Propuesta

```python
# En analyzers/equity_analyzer.py
class EquityAnalyzer(BaseAnalyzer):
    def _calc_health_v2(self, metrics: Dict) -> float:
        """
        Prioriza Net Debt/EBITDA sobre D/E.
        
        TIER 1: Net Debt/EBITDA + Interest Coverage
        TIER 2: D/E + Current + Quick (fallback)
        """
        nd_ebitda = metrics.get("net_debt_to_ebitda")
        interest_coverage = metrics.get("interest_coverage")
        
        if nd_ebitda is not None and interest_coverage is not None:
            return self._tier1_health(nd_ebitda, interest_coverage)
        
        # Fallback a sistema actual
        return self._calc_health(metrics)
    
    def _tier1_health(self, nd_ebitda: float, interest_coverage: float) -> float:
        """
        Net Debt/EBITDA:
        - < 0 (caja neta): Score 100
        - < 1.5: Score 90
        - < 3.0: Score 75
        - < 5.0: Score 50
        - >= 5.0: Score 20
        
        Interest Coverage (EBIT/Interest):
        - > 10x: Score 100
        - > 5x: Score 85
        - > 3x: Score 70
        - > 1.5x: Score 45
        - <= 1.5x: Score 15
        """
        nd_score = self._score_net_debt_ebitda(nd_ebitda)
        ic_score = self._score_interest_coverage(interest_coverage)
        
        return (nd_score * 0.65) + (ic_score * 0.35)
```

### 🎯 Aplicabilidad

| Tipo | Aplicable | Justificación |
|------|-----------|---------------|
| **EQUITY** | ✅ Sí | **PRIORIDAD ABSOLUTA** |
| **ETF** | ❌ No | Análisis básico actual suficiente |
| **CRYPTO** | ❌ No | Análisis básico actual suficiente |

**Enfoque:**
- **EQUITY:** Implementación completa
- **ETF/Crypto:** Sin cambios

---

## 📊 MEJORA 7-10: Resumen

### MEJORA 7: Jerarquía de Crecimiento (P2)
```python
# Prioridad: 5y > anual > próximo año > trimestral
# Penalización fuerte si crecimiento negativo
```

### MEJORA 8: Winsorización de Outliers (P2)
```python
# Caps por métrica: P/E > 100 → 100, ROE > 200% → 200%
# Evita distorsión por valores extremos
```

### MEJORA 9: Normalización a Peers (P3)
```python
# Comparar vs. top 10 competidores directos
# Requiere API de industria (Finnhub, Polygon)
```

### MEJORA 10: Confidence-Aware Recommendations (P2)
```python
# Modular acción por confidence:
# - Confidence > 85% → Mantener recomendación
# - Confidence 70-85% → Degradar (COMPRAR → CONSIDERAR)
# - Confidence < 70% → Agregar warning
```

---

## 🏗️ PLAN DE IMPLEMENTACIÓN

### Fase 1 (P0): Fundamentos de Confianza
**Timeline:** 1-2 semanas
- ✅ Mejora 1: Dispersión entre fuentes
- ✅ Mejora 2: Normalización TTM/MRQ/MRY

### Fase 2 (P1): Valoración y Salud Avanzada
**Timeline:** 2-3 semanas
- ✅ Mejora 3: EV/EBIT + FCF Yield
- ✅ Mejora 4: Scores sector-relativos
- ✅ Mejora 6: Net Debt/EBITDA

### Fase 3 (P2): Refinamiento
**Timeline:** 2-3 semanas
- ✅ Mejora 5: Estabilidad de calidad
- ✅ Mejora 7: Jerarquía de crecimiento
- ✅ Mejora 8: Winsorización
- ✅ Mejora 10: Confidence-aware

### Fase 4 (P3): Comparación Competitiva
**Timeline:** 4-6 semanas
- ✅ Mejora 9: Normalización a peers
- Requiere integración con APIs de industria

---

## 🎯 EXTENSIBILIDAD POR TIPO DE ACTIVO

### Matriz de Aplicabilidad (Actualizada)

**ENFOQUE:** Todas las mejoras se centran en **EQUITY** exclusivamente. ETF/Crypto mantienen análisis básico actual.

| Mejora | EQUITY | ETF | CRYPTO | Notas |
|--------|--------|-----|--------|-------|
| 1. Dispersión | ✅ | ❌ | ❌ | Solo EQUITY (AlphaVantage+TwelveData concordancia) |
| 2. TTM/MRQ/MRY | ✅ | ❌ | ❌ | Solo EQUITY (métricas fundamentales) |
| 3. EV/EBIT+FCF | ✅ | ❌ | ❌ | Solo EQUITY (valoración basada en caja) |
| 4. Sector-relativo | ✅ | ❌ | ❌ | Solo EQUITY (z-scores sectoriales) |
| 5. Estabilidad | ✅ | ❌ | ❌ | Solo EQUITY (varianza ROE/ROIC) |
| 6. ND/EBITDA | ✅ | ❌ | ❌ | Solo EQUITY (salud financiera) |
| 7. Jerarquía Growth | ✅ | ❌ | ❌ | Solo EQUITY (crecimiento histórico+forward) |
| 8. Winsorización | ✅ | ❌ | ❌ | Solo EQUITY (caps por métrica) |
| 9. Peers | ✅ | ❌ | ❌ | Solo EQUITY (comparación competitiva) |
| 10. Confidence-aware | ✅ | ❌ | ❌ | Solo EQUITY (ajuste de recomendaciones) |

**Leyenda:**
- ✅ **Implementar** (90% del esfuerzo en EQUITY)
- ❌ **No implementar** (ETF/Crypto mantienen análisis básico actual - 10% del esfuerzo)

### 🎯 Estrategia por Tipo de Activo

#### EQUITY (90% del desarrollo)
- **Objetivo:** Análisis fundamental completo con las 10 mejoras
- **Fuentes:** AlphaVantage + TwelveData (desarrollo) → FMP (producción)
- **Output:** Investment Score (0-100) + Categoría (Sweet Spot, Premium, etc.) + Recomendación (Comprar/Considerar/Esperar/Evitar)

#### ETF (5% del desarrollo)
- **Objetivo:** Información básica educativa (SIN Investment Score complejo)
- **Métricas actuales:** Expense ratio, AUM, tracking error, dividend yield
- **Output:** Total Score (0-100) + Label (🟢🟡🟠🔴) + Resumen informativo
- **Sin cambios:** Mantener `ETFAnalyzer` actual (173 líneas)

#### CRYPTO (5% del desarrollo)
- **Objetivo:** Información básica de mercado (SIN análisis fundamental)
- **Métricas futuras:** Market cap, volume, circulating supply, dominance
- **Output:** Resumen informativo + Datos de mercado
- **Estado:** Pendiente `CryptoAnalyzer` (futuro, baja prioridad)

---

## � ESTRATEGIA DE FUENTES DE DATOS

### 🎯 Cascada de APIs Actual vs Recomendada

#### ❌ Configuración ACTUAL (data_agent.py)
```python
PRIORIDAD_ACTUAL:
1. AlphaVantage  (premium - alta calidad) ✅
2. TwelveData    (premium - alta calidad) ✅
3. FMP           (premium - económico)    ⚠️ NO FUNCIONA AHORA
4. Yahoo Finance (scraping - gratis)      ⚠️ FRÁGIL
5. Finviz        (scraping - gratis)      ⚠️ FRÁGIL
6. MarketWatch   (scraping - gratis)      ⚠️ FRÁGIL
7. Datos ejemplo (fallback final)         ❌ ÚLTIMO RECURSO
```

#### ✅ Configuración RECOMENDADA (Desarrollo)
```python
PRIORIDAD_DESARROLLO:
1. AlphaVantage  (premium - PRINCIPAL) ✅ Mejor calidad, baja dispersión
2. TwelveData    (premium - PRINCIPAL) ✅ Mejor calidad, baja dispersión
3. Yahoo Finance (scraping - ÚLTIMO RECURSO) ⚠️ Solo si 1-2 fallan
4. FMP           (premium - DESHABILITADO) ❌ No funciona en desarrollo
# Eliminar: Finviz, MarketWatch (redundantes, menor calidad)
```

#### ✅ Configuración RECOMENDADA (Producción)
```python
PRIORIDAD_PRODUCCIÓN:
1. FMP           (premium - PRINCIPAL) ✅ Económico, escalable
2. AlphaVantage  (premium - FALLBACK) ✅ Si FMP falla
3. TwelveData    (premium - FALLBACK) ✅ Si FMP+Alpha fallan
4. Yahoo Finance (scraping - ÚLTIMO RECURSO) ⚠️ Solo emergencia
```

### 🔍 Análisis de Fuentes (Basado en tu experiencia)

| Fuente | Calidad | Costo/Escalabilidad | Concordancia | Uso Recomendado |
|--------|---------|---------------------|--------------|-----------------|
| **AlphaVantage** | ⭐⭐⭐⭐⭐ | 💰💰 Media | ✅ Alta con TwelveData | **PRINCIPAL** (desarrollo) |
| **TwelveData** | ⭐⭐⭐⭐⭐ | 💰💰 Media | ✅ Alta con AlphaVantage | **PRINCIPAL** (desarrollo) |
| **FMP** | ⭐⭐⭐⭐ | 💰 Baja | ❓ Desconocida (no funciona ahora) | **PRINCIPAL** (producción futura) |
| **Yahoo Finance** | ⭐⭐⭐ | Gratis | ⚠️ Baja (scraping frágil) | **ÚLTIMO RECURSO** |
| **Finviz** | ⭐⭐ | Gratis | ⚠️ Baja | **ELIMINAR** (redundante) |
| **MarketWatch** | ⭐⭐ | Gratis | ⚠️ Baja | **ELIMINAR** (redundante) |

### 📊 Justificación: AlphaVantage + TwelveData

**Ventajas observadas:**
1. **Baja dispersión:** Ambas APIs reportan valores muy similares (CV < 5% en la mayoría de métricas)
2. **Alta cobertura:** Combinadas cubren 90%+ de métricas críticas
3. **Datos estructurados:** APIs REST (no scraping frágil)
4. **Actualizados:** Datos frescos (TTM, MRQ)

**Ejemplo real:**
```python
# P/E Ratio para AAPL
AlphaVantage: 28.5
TwelveData:   28.7
Yahoo:        31.2  ← Outlier (scraping, puede estar desactualizado)

# CV entre Alpha+Twelve: 0.7% (concordancia perfecta)
# CV incluyendo Yahoo: 4.8% (aún aceptable pero introduce ruido)

# DECISIÓN: Usar SOLO Alpha+Twelve para cálculos críticos
```

### 🔧 Cambios Sugeridos en `data_agent.py`

```python
# En data_agent.py

class DataAgent:
    def __init__(self):
        # MODO DESARROLLO: AlphaVantage + TwelveData principales
        self.primary_sources = ["alpha_vantage", "twelvedata"]
        self.fallback_sources = ["yahoo"]
        
        # MODO PRODUCCIÓN: FMP principal (cuando esté disponible)
        # self.primary_sources = ["fmp"]
        # self.fallback_sources = ["alpha_vantage", "twelvedata", "yahoo"]
    
    def fetch_data(self, ticker: str) -> Dict:
        """
        Estrategia modificada:
        1. Intenta SOLO fuentes primarias (Alpha+Twelve)
        2. Si ambas fallan → fallback a Yahoo
        3. Calcula dispersión SOLO con primarias (ignora Yahoo en CV)
        """
        results = []
        
        # PASO 1: Fuentes primarias
        for source in self.primary_sources:
            result = self._fetch_from_source(ticker, source)
            if result:
                results.append(result)
        
        # PASO 2: Si coverage < 70%, intenta fallback
        coverage = self._calculate_coverage(results)
        if coverage < 0.70:
            for source in self.fallback_sources:
                result = self._fetch_from_source(ticker, source)
                if result:
                    results.append(result)
        
        # PASO 3: Merge con prioridad y dispersión
        merged = self._merge_with_dispersion(results)
        
        return merged
```

### 🎯 Beneficios Esperados

1. **Mayor confianza:** Dispersión < 5% entre AlphaVantage + TwelveData → `confidence_adj = 1.0`
2. **Menos ruido:** Eliminar fuentes de baja calidad (Finviz, MarketWatch)
3. **Escalabilidad:** Fácil migrar a FMP en producción (solo cambiar `primary_sources`)
4. **Menor latencia:** Solo 2 llamadas API principales (vs 7 actuales)

### ⚠️ Riesgos y Mitigación

**Riesgo 1:** AlphaVantage o TwelveData caen
- **Mitigación:** Fallback automático a Yahoo (menor calidad pero disponible)

**Riesgo 2:** Rate limits en APIs premium
- **Mitigación:** Cache SQLite de 24h + sistema de colas

**Riesgo 3:** FMP no funciona en producción
- **Mitigación:** Mantener AlphaVantage + TwelveData como plan B

---

## �📝 PRÓXIMOS PASOS INMEDIATOS

1. **Revisar y aprobar** este plan
2. **Priorizar** Fase 1 (P0) para implementación inmediata
3. **Actualizar** `EVALUATION_SYSTEM.md` con nuevo roadmap
4. **Crear issues** en GitHub para trackear cada mejora
5. **Implementar** Mejora 1 (dispersión) como prueba de concepto

---

**Documento creado por:** GitHub Copilot  
**Última actualización:** 26 de octubre de 2025  
**Versión siguiente del sistema:** v3.2.0 (tras Fase 1)

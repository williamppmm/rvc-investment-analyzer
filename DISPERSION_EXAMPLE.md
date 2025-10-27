# 📊 Ejemplo: Sistema de Dispersión entre Fuentes

**Implementado:** 26 de octubre de 2025  
**Mejora #1 (P0):** Dispersión entre fuentes para EQUITY

---

## 🎯 Objetivo

Medir la **concordancia entre fuentes de datos** (AlphaVantage + TwelveData) para ajustar la confianza del análisis automáticamente.

---

## 📐 Cómo Funciona

### 1. Recolección de Datos con Provenance

Cuando analizamos una acción (ej: AAPL), cada fuente provee sus valores:

```python
# AlphaVantage dice:
{"pe_ratio": 28.5, "roe": 147.3, "roic": 38.2}

# TwelveData dice:
{"pe_ratio": 28.7, "roe": 146.8, "roic": 38.5}

# Yahoo dice:
{"pe_ratio": 31.2, "roe": 145.0, "roic": 37.8}
```

### 2. Cálculo de Dispersión (Coefficient of Variation)

Para cada métrica crítica, calculamos:

**P/E Ratio:**
- AlphaVantage: 28.5
- TwelveData: 28.7
- Yahoo: 31.2

```python
# Priorización: Usar SOLO AlphaVantage + TwelveData (fuentes premium)
valores = [28.5, 28.7]
mediana = 28.6
media = 28.6
std = 0.1
CV = (0.1 / 28.6) * 100 = 0.35%  # CV < 5% = EXCELENTE concordancia
confidence_adj = 1.0  # Confianza máxima
```

**ROE:**
```python
valores = [147.3, 146.8]
CV = 0.34%  # CV < 5% = EXCELENTE
confidence_adj = 1.0
```

**ROIC:**
```python
valores = [38.2, 38.5]
CV = 0.78%  # CV < 5% = EXCELENTE
confidence_adj = 1.0
```

### 3. Confidence Score Final

```python
# Promedio de todos los factores
confidence_factors = {
    "completeness": 1.0,   # 100% de métricas críticas obtenidas
    "dispersion": 1.0,     # 0% de dispersión (concordancia perfecta)
    "freshness": 1.0       # (futuro - frescura de datos)
}

overall_confidence = (1.0 + 1.0 + 1.0) / 3 * 100 = 100%
```

---

## 📊 Resultado en el JSON de Respuesta

```json
{
  "ticker": "AAPL",
  "quality_score": 88,
  "valuation_score": 55,
  "investment_score": 68,
  
  "confidence_factors": {
    "completeness": 100.0,
    "dispersion": 100.0,
    "overall": 100.0
  },
  
  "dispersion_detail": {
    "pe_ratio": {
      "sources": ["alpha_vantage", "twelvedata"],
      "cv": 0.35,
      "confidence_adj": 1.0,
      "quality": "PREMIUM_SOURCES"
    },
    "roe": {
      "sources": ["alpha_vantage", "twelvedata"],
      "cv": 0.34,
      "confidence_adj": 1.0,
      "quality": "PREMIUM_SOURCES"
    },
    "roic": {
      "sources": ["alpha_vantage", "twelvedata"],
      "cv": 0.78,
      "confidence_adj": 1.0,
      "quality": "PREMIUM_SOURCES"
    }
  }
}
```

---

## 🎓 Interpretación de Valores

### Coefficient of Variation (CV)

| CV | Concordancia | Confidence Adj | Calidad de Dato |
|----|--------------|----------------|-----------------|
| < 5% | ⭐⭐⭐⭐⭐ Perfecta | 1.0 | AlphaVantage ≈ TwelveData (excelente) |
| 5-10% | ⭐⭐⭐⭐ Muy buena | 0.95 | Diferencia menor (aceptable) |
| 10-20% | ⭐⭐⭐ Aceptable | 0.85 | Diferencia moderada (usable) |
| 20-40% | ⭐⭐ Discrepante | 0.70 | Posible problema con una fuente |
| > 40% | ⭐ Muy discrepante | 0.50 | Datos sospechosos (revisar) |

### Quality Label

| Label | Descripción |
|-------|-------------|
| `PREMIUM_SOURCES` | Valor consolidado solo de AlphaVantage + TwelveData (mejor calidad) |
| `MIXED_SOURCES` | Incluye Yahoo/scraping (menor confianza) |
| `SINGLE_SOURCE` | Solo una fuente disponible (sin dispersión calculable) |

---

## 🚀 Beneficios

### 1. Detección Automática de Problemas
```python
# Escenario problemático:
# AlphaVantage: P/E = 28.5
# Yahoo: P/E = 52.3 (scraping erróneo - faltó dividir por 2)

dispersion = {
    "cv": 45.2,  # CV > 40% = MUY DISCREPANTE
    "confidence_adj": 0.50,  # Confianza reducida a 50%
    "quality": "MIXED_SOURCES"
}

# Sistema automáticamente marca baja confianza
# Usuario ve: "⚠️ Datos con alta dispersión - revisar"
```

### 2. Priorización de Fuentes Premium

```python
# Antes (Mejora #1):
# Usaba CUALQUIER fuente en orden de prioridad
merged["pe_ratio"] = 28.5  # AlphaVantage (primera que encontró)

# Después (Mejora #1):
# Calcula dispersión entre AlphaVantage + TwelveData
# Usa MEDIANA si ambas concuerdan (más robusto que primera fuente)
merged["pe_ratio"] = 28.6  # Mediana de [28.5, 28.7]
```

### 3. Confianza Granular

```python
# Antes:
"data_completeness": 85.7  # Solo métrica global

# Después:
"confidence_factors": {
    "completeness": 85.7,  # % de métricas obtenidas
    "dispersion": 92.3,    # Concordancia entre fuentes
    "overall": 89.0        # Promedio ponderado
}
```

---

## 🔍 Ejemplo Real: Comparación NVDA vs AMD

### NVDA (Alta Confianza)
```json
{
  "ticker": "NVDA",
  "confidence_factors": {
    "completeness": 100.0,
    "dispersion": 98.5,
    "overall": 99.25
  },
  "dispersion_detail": {
    "pe_ratio": {"cv": 1.2, "quality": "PREMIUM_SOURCES"},
    "roe": {"cv": 0.8, "quality": "PREMIUM_SOURCES"}
  },
  "recommendation": "🟡 CONSIDERAR"
}
```

### Stock Hipotético (Baja Confianza)
```json
{
  "ticker": "XYZ",
  "confidence_factors": {
    "completeness": 71.4,
    "dispersion": 68.2,
    "overall": 69.8
  },
  "dispersion_detail": {
    "pe_ratio": {"cv": 28.5, "quality": "MIXED_SOURCES"},
    "roe": {"cv": 35.2, "quality": "MIXED_SOURCES"}
  },
  "recommendation": "⚠️ DATOS INSUFICIENTES - Revisar manualmente"
}
```

---

## 📝 Implementación Técnica

### Archivos Modificados

1. **`data_agent.py`**
   - Método `_calculate_dispersion()` (líneas ~1602-1700)
   - Modificado `fetch_financial_data()` para calcular dispersión

2. **`analyzers/base_analyzer.py`**
   - Agregado `confidence_factors` dict
   - Métodos `calculate_dispersion_confidence()` y `get_overall_confidence()`

3. **`analyzers/equity_analyzer.py`**
   - Modificado `__init__()` para llamar `super().__init__()`
   - Modificado `calculate_all_scores()` para calcular confidence factors

### Compatibilidad

- ✅ Backward compatible (ETFAnalyzer no afectado)
- ✅ Solo aplica a EQUITY (ETF/Crypto sin cambios)
- ✅ Tests existentes pasan sin modificación

---

## 🎯 Próximos Pasos

1. **Mejora #2 (P0):** Normalización TTM/MRQ/MRY
2. **Mejora #3 (P1):** EV/EBIT + FCF Yield
3. **Mejora #10 (P2):** Confidence-aware recommendations
   - Degradar recomendación si overall_confidence < 70%
   - Ejemplo: COMPRAR → CONSIDERAR si dispersión alta

---

**Conclusión:** El sistema ahora tiene **visibilidad completa** de la calidad de sus datos y puede advertir al usuario cuando hay discrepancias entre fuentes.

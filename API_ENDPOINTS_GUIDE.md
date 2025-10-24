# 📊 Documentación API - RVC Investment Analyzer

## 🎯 Resumen de la API

**RVC Investment Analyzer** es una API REST que proporciona análisis financiero automatizado de acciones y ETFs, calculando puntuaciones RVC (Riesgo, Valor, Crecimiento) basadas en métricas fundamentales.

### 📈 Datos actuales en la base de datos
- **23 tickers** con datos financieros en caché
- **18 tickers** con puntuaciones RVC calculadas  
- **Última actualización**: 24/10/2025 11:48:26
- **Mejor puntuación**: SCHW (77.32) 🟢
- **🆕 NUEVO**: Endpoint `/api/top-opportunities` para rankings

---

## 🛠️ Endpoints Disponibles

### 1. 🏆 **GET /api/top-opportunities** - Ranking de Mejores Oportunidades (NUEVO)

**Descripción**: Retorna un ranking de las mejores oportunidades de inversión basado en RVC scores y métricas financieras actuales.

**URL**: `http://127.0.0.1:5000/api/top-opportunities`

**Método**: `GET`

**Parámetros de consulta**:
- `min_score` (opcional): Score mínimo RVC para filtrar (default: 50.0)
- `sector` (opcional): Filtro por sector específico
- `sort_by` (opcional): Campo de ordenamiento - rvc_score, market_cap, pe_ratio, ticker (default: rvc_score)
- `limit` (opcional): Máximo número de resultados (default: 50, max: 100)

**Ejemplo de URL**:
```
GET /api/top-opportunities?min_score=70&limit=10&sort_by=rvc_score
```

**Respuesta exitosa (200)**:
```json
{
  "status": "success",
  "data": {
    "opportunities": [
      {
        "ticker": "SCHW",
        "company_name": "Charles Schwab Corp",
        "rvc_score": 77.32,
        "classification": "🟢 Razonable o mejor",
        "sector": "FINANCIAL SERVICES",
        "market_cap": 171193336000.0,
        "pe_ratio": 33.3,
        "current_price": 94.6,
        "last_updated": "2025-10-24T01:06:22",
        "breakdown": {
          "growth_score": 100.0,
          "quality_score": 78.9,
          "value_score": 53.0
        }
      },
      {
        "ticker": "NVO",
        "company_name": "Novo Nordisk A/S",
        "rvc_score": 75.9,
        "classification": "🟢 Razonable o mejor",
        "sector": "HEALTHCARE",
        "market_cap": 462774462726.0,
        "pe_ratio": 32.1,
        "current_price": 99.12,
        "last_updated": "2025-10-24T00:57:33",
        "breakdown": {
          "growth_score": 95.2,
          "quality_score": 85.1,
          "value_score": 47.4
        }
      }
    ],
    "metadata": {
      "total_count": 16,
      "average_score": 63.45,
      "sectors_available": [
        "FINANCIAL SERVICES",
        "HEALTHCARE", 
        "TECHNOLOGY",
        "BASIC MATERIALS",
        "COMMUNICATION SERVICES",
        "CONSUMER DEFENSIVE"
      ],
      "filters_applied": {
        "min_score": 70.0,
        "sector": null,
        "sort_by": "rvc_score",
        "limit": 10
      },
      "generated_at": "2025-10-24T11:48:26"
    }
  }
}
```

**Casos de uso**:
- 🔍 Ver ranking completo de mejores acciones
- 📊 Filtrar por score mínimo deseado  
- 🏢 Buscar oportunidades por sectores específicos
- 📈 Ordenar por diferentes métricas (cap. mercado, P/E, etc.)
- 🎯 Identificar rápidamente las mejores inversiones disponibles

**Errores posibles**:
- `400 Bad Request`: Parámetros inválidos
- `500 Internal Server Error`: Error interno del servidor

---

### 2. 📊 **POST /analyze** - Análisis Individual de Ticker

**Descripción**: Analiza un ticker específico y devuelve métricas financieras completas con puntuación RVC.

**URL**: `http://127.0.0.1:5000/analyze`

**Método**: `POST`

**Headers**:
```
Content-Type: application/json
```

**Body de ejemplo**:
```json
{
  "ticker": "SCHW"
}
```

**Respuesta exitosa (200)**:
```json
{
  "ticker": "SCHW",
  "company_name": "Charles Schwab Corp",
  "sector": "FINANCIAL SERVICES",
  "industry": "CAPITAL MARKETS",
  "currency": "USD",
  "current_price": 94.6,
  "market_cap": 171193336000.0,
  
  "rvc_score": {
    "total_score": 77.32,
    "classification": "🟢 Razonable o mejor",
    "confidence_level": "Alta",
    "data_completeness": 100.0,
    "recommendation": "Equilibrio atractivo con crecimiento dinámico",
    "breakdown": {
      "valoracion": {
        "score": 72.25,
        "metrics_used": ["P/E: 22.09", "PEG: 0.69", "P/B: 3.94"]
      },
      "calidad": {
        "score": 78.91,
        "metrics_used": ["ROE: 15.6%", "ROIC: 10.9%", "Op. Margin: 49.2%", "Net Margin: 28.6%"]
      },
      "salud": {
        "score": 72.0,
        "metrics_used": ["D/E: 0.56", "Current: 1.18", "Quick: 1.18"]
      },
      "crecimiento": {
        "score": 100.0,
        "metrics_used": ["Rev. Growth: 26.6%", "Earn. Growth: 47.1%"]
      }
    }
  },
  
  "investment_scores": {
    "investment_score": 67.48,
    "valuation_score": 71.5,
    "quality_score": 74.0,
    "financial_health_score": 69.0,
    "growth_score": 94.0,
    "recommendation": "🟡 CONSIDERAR - Buen precio pero verificar calidad sostenible",
    "category": {
      "name": "VALOR",
      "emoji": "💎",
      "desc": "Calidad decente, buen precio",
      "color": "cyan"
    }
  },
  
  "metrics": {
    "pe_ratio": 22.09,
    "peg_ratio": 0.685,
    "price_to_book": 3.942,
    "debt_to_equity": 0.56,
    "current_ratio": 1.18,
    "roe": 15.6,
    "revenue_growth": 26.6,
    "earnings_growth": 77.5
  },
  
  "timestamp": "2025-10-24T01:07:02"
}
```

**Casos de uso**:
- ✅ Ticker existente en caché: Respuesta inmediata (< 500ms)
- 🔄 Ticker nuevo: Análisis en tiempo real (5-15 segundos)
- ❌ Ticker inválido: Error 404

**Tickers recomendados para pruebas**:
- `SCHW` (Score: 77.32) - Mejor puntuación actual
- `NVO` (Score: 75.9) - Segundo mejor
- `ADBE` (Score: 75.0) - Tercero

---

### 4. 📈 **GET /history/{ticker}** - Historial de Análisis

**Descripción**: Obtiene el historial de análisis previos para un ticker específico.

**URL**: `http://127.0.0.1:5000/history/SCHW`

**Método**: `GET`

**Parámetros**:
- `ticker` (path): Símbolo del ticker (ej: SCHW, AAPL, MSFT)

**Respuesta exitosa (200)**:
```json
{
  "ticker": "SCHW",
  "score": 77.32,
  "classification": "🟢 Razonable o mejor",
  "breakdown": "{\"valoracion\": {\"score\": 72.25}, \"calidad\": {\"score\": 78.91}, \"salud\": {\"score\": 72.0}, \"crecimiento\": {\"score\": 100.0}}",
  "last_calculated": "2025-10-24T01:07:02"
}
```

**Casos de uso**:
- Ver evolución de puntuaciones
- Comparar análisis históricos
- Validar consistencia de datos

---

### 3. � **POST /api/comparar** - Comparación de Múltiples Tickers

**Descripción**: Compara múltiples tickers y devuelve análisis comparativo.

**URL**: `http://127.0.0.1:5000/api/comparar`

**Método**: `POST`

**Headers**:
```
Content-Type: application/json
```

**Body de ejemplo**:
```json
{
  "tickers": ["SCHW", "NVO", "ADBE"]
}
```

**Respuesta esperada (200)**:
```json
{
  "comparisons": [
    {
      "ticker": "SCHW",
      "score": 77.32,
      "classification": "🟢 Razonable o mejor",
      "rank": 1
    },
    {
      "ticker": "NVO", 
      "score": 75.9,
      "classification": "🟢 Razonable o mejor",
      "rank": 2
    },
    {
      "ticker": "ADBE",
      "score": 75.0,
      "classification": "🟢 Razonable o mejor", 
      "rank": 3
    }
  ],
  "summary": {
    "best_performer": "SCHW",
    "average_score": 76.07,
    "recommendation": "Excelente selección con puntuaciones altas"
  }
}
```

**Mejores combinaciones para probar**:
- Top 3: `["SCHW", "NVO", "ADBE"]`
- Tech: `["NVDA", "TSM", "ADBE"]`
- Diversificado: `["SCHW", "NVO", "NVDA"]`

---

### 5. 🧮 **POST /api/calcular-inversion** - Calculadora de Inversión DCA

**Descripción**: Calcula proyecciones de inversión usando Dollar Cost Averaging (DCA).

**URL**: `http://127.0.0.1:5000/api/calcular-inversion`

**Método**: `POST`

**Headers**:
```
Content-Type: application/json
```

**Body de ejemplo**:
```json
{
  "calculation_type": "dca",
  "monthly_amount": 500,
  "years": 20,
  "scenario": "moderado",
  "market_timing": "normal"
}
```

**Parámetros**:
- `calculation_type`: "dca" (Dollar Cost Averaging)
- `monthly_amount`: Cantidad mensual a invertir (número)
- `years`: Período de inversión en años (número)
- `scenario`: "conservador" | "moderado" | "agresivo"
- `market_timing`: "normal" | "optimista" | "pesimista"

**Respuesta esperada (200)**:
```json
{
  "calculation_type": "dca",
  "parameters": {
    "monthly_amount": 500,
    "years": 20,
    "scenario": "moderado"
  },
  "results": {
    "total_invested": 120000,
    "final_value": 285000,
    "total_return": 165000,
    "annual_return": 6.8,
    "compound_growth": 137.5
  },
  "breakdown": {
    "principal": 120000,
    "interest": 165000,
    "growth_percentage": 137.5
  },
  "recommendation": "Estrategia DCA sólida para objetivos a largo plazo"
}
```

**Escenarios disponibles**:
- **Conservador**: 4-6% anual
- **Moderado**: 6-8% anual  
- **Agresivo**: 8-12% anual

---

### 6. 🗑️ **POST /cache/clear** - Limpiar Caché

**Descripción**: Elimina todos los datos de caché de la base de datos.

**URL**: `http://127.0.0.1:5000/cache/clear`

**Método**: `POST`

**Headers**:
```
Content-Type: application/json
```

**Body**:
```json
{}
```

**Respuesta esperada (200)**:
```json
{
  "message": "Cache cleared successfully",
  "records_deleted": {
    "financial_cache": 21,
    "rvc_scores": 16
  },
  "timestamp": "2025-10-24T01:10:00"
}
```

**⚠️ PRECAUCIÓN**: Este endpoint elimina TODOS los datos. Usar solo para:
- Desarrollo y testing
- Problemas de datos obsoletos
- Reset completo del sistema

---

## 🔧 Configuración de Testing

### Variables de entorno recomendadas:
```
baseUrl: http://127.0.0.1:5000
ticker_test: SCHW
ticker_test_2: NVO  
ticker_test_3: ADBE
dca_monthly: 500
dca_years: 20
```

### 🧪 Tests automatizados incluidos:

```javascript
// Test básico de status
pm.test('Status code is 200', function () {
    pm.response.to.have.status(200);
});

// Test de estructura de respuesta
pm.test('Response has required fields', function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('ticker');
    pm.expect(jsonData).to.have.property('rvc_score');
});

// Test de validación de datos
pm.test('RVC Score is valid', function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData.rvc_score.total_score).to.be.a('number');
    pm.expect(jsonData.rvc_score.total_score).to.be.above(0);
    pm.expect(jsonData.rvc_score.total_score).to.be.below(100);
});
```

---

## 📊 Métricas de Rendimiento

| Endpoint | Tiempo esperado | Datos requeridos |
|----------|----------------|------------------|
| `/analyze` (cached) | < 500ms | Ticker en caché |
| `/analyze` (new) | 5-15s | APIs externas |
| `/history` | < 100ms | Ticker con historial |
| `/api/comparar` | < 2s | Múltiples tickers |
| `/api/calcular-inversion` | < 100ms | Parámetros válidos |
| `/cache/clear` | < 200ms | N/A |

---

## 🎯 Casos de Uso Principales

### 1. **Análisis de Inversión Individual**
```
POST /analyze → ticker específico
GET /history/{ticker} → evolución histórica
```

### 2. **Comparación de Portafolio**
```
POST /api/comparar → múltiples tickers
POST /analyze → análisis detallado de cada uno
```

### 3. **Planificación Financiera**
```
POST /api/calcular-inversion → proyecciones DCA
POST /analyze → análisis de activos objetivo
```

### 4. **Mantenimiento del Sistema**
```
POST /cache/clear → limpiar datos obsoletos
POST /analyze → regenerar análisis frescos
```

---

## 🔍 Troubleshooting

### Errores comunes:

**404 - Ticker not found**
- Verificar símbolo del ticker
- Confirmar que el ticker existe en los mercados

**500 - Internal Server Error**
- Revisar logs del servidor Flask
- Verificar conexión a APIs externas
- Comprobar base de datos SQLite

**Timeout**
- APIs externas lentas
- Reintentar con ticker en caché
- Verificar conectividad de red

### Comandos útiles:
```bash
# Verificar servidor
netstat -an | findstr 5000

# Ver logs en tiempo real
# (revisar terminal donde ejecutaste python app.py)

# Reiniciar servidor
python app.py
```

---

## 📈 Roadmap de Mejoras

- [ ] Autenticación API
- [ ] Rate limiting
- [ ] Cache inteligente con TTL
- [ ] Websockets para análisis en tiempo real
- [ ] Exportación de reportes PDF
- [ ] API de alertas por email
- [ ] Dashboard en tiempo real
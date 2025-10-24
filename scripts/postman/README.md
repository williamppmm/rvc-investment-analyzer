# 📮 Postman Collection - RVC Investment Analyzer

## 📁 Archivos

### `RVC_Collection.json`
- **Propósito**: Colección completa de Postman para la API RVC
- **Endpoints incluidos**: 7 requests organizados en 4 carpetas
- **Variables**: `baseUrl`, `ticker_test`, `ticker_new`
- **Tests**: Scripts automatizados para validación

### `ADBE_ENDPOINT_COMPLETE_DOCUMENTATION.md`
- **Propósito**: Documentación detallada del análisis de Adobe Inc. (ADBE)
- **Score RVC**: 75.0 puntos (3er lugar)
- **Incluye**: Análisis financiero, fortalezas competitivas, tests automatizados
- **Creado via**: MCP Postman integration

## 🚀 Uso

### Importar en Postman
1. Abrir Postman
2. Click en "Import"
3. Seleccionar `RVC_Collection.json`
4. Configurar environment con:
   - `baseUrl`: `http://127.0.0.1:5000`
   - `ticker_test`: `SCHW`
   - `ticker_new`: `MSFT`

### Ejecutar Tests
- **Individual**: Seleccionar request específico → Send
- **Colección completa**: Click en colección → Run collection
- **ADBE específico**: Usar documentación detallada como referencia

## 📊 Endpoints Disponibles

1. **POST /analyze** - Analizar ticker individual
2. **POST /api/comparar** - Comparar múltiples tickers  
3. **GET /history/{ticker}** - Historial de análisis
4. **POST /api/calcular-inversion** - Calculadora DCA
5. **POST /cache/clear** - Limpiar caché

## 🎯 Endpoint ADBE Destacado

El endpoint de Adobe (ADBE) está completamente documentado con:
- ✅ Score: 75.0 puntos
- ✅ Tests automatizados específicos
- ✅ Análisis de fortalezas competitivas
- ✅ Configuración completa del request

Ver `ADBE_ENDPOINT_COMPLETE_DOCUMENTATION.md` para detalles completos.
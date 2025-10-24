#!/usr/bin/env python3
"""
Script de pruebas de API usando datos de MCP SQLite
Simula las pruebas que harías en Postman pero usando datos reales de la caché
"""

import requests
import json
import sqlite3
from typing import List, Dict, Any

# Configuración
BASE_URL = "http://127.0.0.1:5000"
DB_PATH = "C:/rcv_proyecto/data/cache.db"

def get_available_tickers() -> List[str]:
    """Obtener tickers disponibles en la caché usando SQLite directo"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT ticker FROM financial_cache ORDER BY ticker")
    tickers = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tickers

def get_scored_tickers() -> List[str]:
    """Obtener tickers con scores RVC calculados"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT ticker FROM rvc_scores ORDER BY score DESC")
    tickers = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tickers

def test_analyze_endpoint(ticker: str) -> Dict[str, Any]:
    """Probar el endpoint /analyze"""
    print(f"\n🧪 Probando /analyze con ticker: {ticker}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/analyze",
            json={"ticker": ticker},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Éxito: Recibido análisis para {ticker}")
            print(f"Score: {data.get('score', 'N/A')}")
            print(f"Clasificación: {data.get('classification', 'N/A')}")
            return {"success": True, "data": data}
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return {"success": False, "error": str(e)}

def test_compare_endpoint(tickers: List[str]) -> Dict[str, Any]:
    """Probar el endpoint /api/comparar"""
    print(f"\n🧪 Probando /api/comparar con tickers: {tickers}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/comparar",
            json={"tickers": tickers},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Éxito: Comparación completada")
            print(f"Número de resultados: {len(data.get('comparisons', []))}")
            return {"success": True, "data": data}
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return {"success": False, "error": str(e)}

def test_history_endpoint(ticker: str) -> Dict[str, Any]:
    """Probar el endpoint /history/{ticker}"""
    print(f"\n🧪 Probando /history/{ticker}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/history/{ticker}",
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Éxito: Historial obtenido para {ticker}")
            print(f"Registros: {len(data) if isinstance(data, list) else 1}")
            return {"success": True, "data": data}
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return {"success": False, "error": str(e)}

def test_calculator_endpoint() -> Dict[str, Any]:
    """Probar el endpoint /api/calcular-inversion"""
    print(f"\n🧪 Probando /api/calcular-inversion")
    
    payload = {
        "calculation_type": "dca",
        "monthly_amount": 500,
        "years": 20,
        "scenario": "moderado",
        "market_timing": "normal"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/calcular-inversion",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Éxito: Cálculo completado")
            print(f"Resultado: {data.get('total_final', 'N/A')}")
            return {"success": True, "data": data}
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return {"success": False, "error": str(e)}

def run_full_test_suite():
    """Ejecutar suite completa de pruebas"""
    print("🚀 Iniciando suite de pruebas de API RVC")
    print("=" * 50)
    
    # Obtener datos de prueba
    available_tickers = get_available_tickers()
    scored_tickers = get_scored_tickers()
    
    print(f"📊 Datos disponibles:")
    print(f"   - Tickers en caché: {len(available_tickers)}")
    print(f"   - Tickers con scores: {len(scored_tickers)}")
    
    results = []
    
    # Test 1: Analyze endpoint
    if available_tickers:
        test_ticker = available_tickers[0]  # Usar el primer ticker disponible
        result = test_analyze_endpoint(test_ticker)
        results.append(("analyze", result))
    
    # Test 2: History endpoint  
    if scored_tickers:
        test_ticker = scored_tickers[0]  # Usar el ticker con mejor score
        result = test_history_endpoint(test_ticker)
        results.append(("history", result))
    
    # Test 3: Compare endpoint
    if len(scored_tickers) >= 3:
        test_tickers = scored_tickers[:3]  # Top 3 tickers
        result = test_compare_endpoint(test_tickers)
        results.append(("compare", result))
    
    # Test 4: Calculator endpoint
    result = test_calculator_endpoint()
    results.append(("calculator", result))
    
    # Resumen
    print(f"\n📋 RESUMEN DE PRUEBAS")
    print("=" * 50)
    
    for endpoint, result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{endpoint:12} - {status}")
    
    successful_tests = sum(1 for _, result in results if result["success"])
    total_tests = len(results)
    
    print(f"\n🎯 Resultado final: {successful_tests}/{total_tests} pruebas exitosas")
    
    return results

if __name__ == "__main__":
    run_full_test_suite()
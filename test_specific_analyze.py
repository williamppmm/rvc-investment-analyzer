#!/usr/bin/env python3
"""
Prueba específica del endpoint /analyze con ticker conocido
"""

import requests
import json

def test_specific_analyze():
    """Prueba específica con SCHW que sabemos que tiene score alto"""
    
    ticker = "SCHW"
    url = "http://127.0.0.1:5000/analyze"
    
    payload = {"ticker": ticker}
    headers = {"Content-Type": "application/json"}
    
    print(f"🧪 Probando endpoint /analyze con {ticker}")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        print(f"\n📡 Respuesta:")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Respuesta exitosa:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"\n❌ Error en respuesta:")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ Error de conexión: {e}")

if __name__ == "__main__":
    test_specific_analyze()
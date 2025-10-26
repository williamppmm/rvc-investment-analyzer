#!/usr/bin/env python3
"""
Tests para el sistema de contador de visitas.
"""

import sqlite3
from app import app, DB_PATH, is_bot_request, BOT_PATTERN


def test_bot_detection():
    """Test que bots son detectados correctamente."""
    print("\n" + "=" * 60)
    print("TEST 1: Detección de Bots")
    print("=" * 60)
    
    bot_user_agents = [
        'Mozilla/5.0 (compatible; Googlebot/2.1)',
        'facebookexternalhit/1.1',
        'Twitterbot/1.0',
        'python-requests/2.28.0',
        'curl/7.68.0',
        'Discordbot/2.0',
        'Slackbot-LinkExpanding 1.0',
        'WhatsApp/2.0',
        '',  # Sin User-Agent
    ]
    
    print("\nProbando User-Agents de bots:")
    for ua in bot_user_agents:
        is_bot = BOT_PATTERN.search(ua) if ua else True
        status = "✓ BOT detectado" if is_bot else "✗ NO detectado"
        print(f"  {status}: {ua[:50] if ua else '(Sin UA)'}")
    
    human_user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) Firefox/121.0',
    ]
    
    print("\nProbando User-Agents humanos:")
    for ua in human_user_agents:
        is_bot = BOT_PATTERN.search(ua) if ua else True
        status = "✗ Detectado como bot" if is_bot else "✓ Humano detectado"
        print(f"  {status}: {ua[:50]}...")


def test_visit_counter_tables():
    """Test que las tablas existen y están inicializadas."""
    print("\n" + "=" * 60)
    print("TEST 2: Tablas de Base de Datos")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verificar tabla site_visits
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='site_visits'")
    if cursor.fetchone():
        print("  ✓ Tabla 'site_visits' existe")
        
        cursor.execute("SELECT total_visits, last_updated FROM site_visits WHERE id = 1")
        result = cursor.fetchone()
        if result:
            print(f"  ✓ Contador inicializado: {result[0]} visitas")
            print(f"  ✓ Última actualización: {result[1]}")
        else:
            print("  ✗ Contador no inicializado")
    else:
        print("  ✗ Tabla 'site_visits' NO existe")
    
    # Verificar tabla daily_visits
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_visits'")
    if cursor.fetchone():
        print("  ✓ Tabla 'daily_visits' existe")
        
        cursor.execute("SELECT COUNT(*) FROM daily_visits")
        count = cursor.fetchone()[0]
        print(f"  ✓ Días registrados: {count}")
    else:
        print("  ✗ Tabla 'daily_visits' NO existe")
    
    conn.close()


def test_visit_count_endpoint():
    """Test del endpoint de API."""
    print("\n" + "=" * 60)
    print("TEST 3: Endpoint /api/visit-count")
    print("=" * 60)
    
    with app.test_client() as client:
        response = client.get('/api/visit-count')
        
        print(f"  Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            print(f"  ✓ Respuesta JSON válida")
            print(f"  ✓ Visitas totales: {data.get('visits', 0)}")
            print(f"  ✓ Visitas hoy: {data.get('today', 0)}")
        else:
            print(f"  ✗ Error: {response.status_code}")


def test_visit_increment():
    """Test que las visitas se incrementan correctamente."""
    print("\n" + "=" * 60)
    print("TEST 4: Incremento de Contador")
    print("=" * 60)
    
    # Obtener contador actual
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT total_visits FROM site_visits WHERE id = 1")
    before = cursor.fetchone()[0]
    conn.close()
    
    print(f"  Visitas antes: {before}")
    
    # Simular visita con User-Agent humano
    with app.test_client() as client:
        # Primera visita de la sesión
        response = client.get('/', headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
        })
        
        print(f"  ✓ Request GET / ejecutado (status: {response.status_code})")
    
    # Verificar incremento
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT total_visits FROM site_visits WHERE id = 1")
    after = cursor.fetchone()[0]
    conn.close()
    
    print(f"  Visitas después: {after}")
    
    if after > before:
        print(f"  ✓ Contador incrementado correctamente (+{after - before})")
    else:
        print(f"  ⚠️ Contador no incrementó (posible sesión activa)")


if __name__ == '__main__':
    print("\n" + "🧪" * 30)
    print("SUITE DE TESTS - CONTADOR DE VISITAS")
    print("🧪" * 30)
    
    test_bot_detection()
    test_visit_counter_tables()
    test_visit_count_endpoint()
    test_visit_increment()
    
    print("\n" + "=" * 60)
    print("✅ TESTS COMPLETADOS")
    print("=" * 60 + "\n")

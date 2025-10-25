#!/usr/bin/env python3
"""
Script de administración para gestionar licencias PRO de RVC Analyzer.
Uso:
    python manage_licenses.py create email@example.com
    python manage_licenses.py list
    python manage_licenses.py validate RVC-PRO-XXX
    python manage_licenses.py deactivate RVC-PRO-XXX
"""

import sys
from usage_limiter import get_limiter
from datetime import datetime

def create_license(email: str):
    """Crear una nueva licencia de 30 días por $3 USD."""
    limiter = get_limiter()
    
    print(f"\n🔑 Generando licencia PRO para: {email}")
    print(f"💰 Costo: $3 USD")
    print(f"⏱️  Duración: 30 días")
    
    confirm = input("\n¿Confirmar creación? (s/n): ")
    if confirm.lower() != 's':
        print("❌ Cancelado")
        return
    
    try:
        license_key = limiter.create_license(
            email=email,
            plan_type="PRO",
            duration_days=30
        )
        
        print(f"\n✅ ¡Licencia creada exitosamente!")
        print(f"\n{'='*50}")
        print(f"LICENCIA: {license_key}")
        print(f"EMAIL: {email}")
        
        # Calcular fecha de expiración correctamente
        from datetime import timedelta
        expiry_date = datetime.now() + timedelta(days=30)
        print(f"VÁLIDA HASTA: {expiry_date.strftime('%d/%m/%Y')}")
        print(f"{'='*50}\n")
        print(f"📧 Envía esta licencia al cliente vía email:")
        print(f"   williamppmm@hotmail.com → {email}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def list_licenses():
    """Listar todas las licencias activas."""
    import sqlite3
    limiter = get_limiter()
    
    conn = sqlite3.connect(limiter.db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT license_key, email, plan_type, created_at, expires_at, is_active
        FROM pro_licenses
        ORDER BY created_at DESC
    """)
    
    licenses = cursor.fetchall()
    conn.close()
    
    if not licenses:
        print("\n📋 No hay licencias registradas")
        return
    
    print(f"\n📋 LICENCIAS REGISTRADAS ({len(licenses)})")
    print("="*100)
    
    for lic in licenses:
        key, email, plan, created, expires, active = lic
        
        status = "✅ Activa" if active else "❌ Inactiva"
        
        created_dt = datetime.fromisoformat(created)
        expires_dt = datetime.fromisoformat(expires) if expires else None
        
        if expires_dt:
            days_left = (expires_dt - datetime.now()).days
            if days_left < 0:
                status = "⏰ Expirada"
            elif days_left <= 3:
                status = f"⚠️  Expira en {days_left} días"
        
        print(f"\n🔑 {key}")
        print(f"   Email: {email}")
        print(f"   Plan: {plan}")
        print(f"   Creada: {created_dt.strftime('%d/%m/%Y %H:%M')}")
        print(f"   Expira: {expires_dt.strftime('%d/%m/%Y') if expires_dt else 'Permanente'}")
        print(f"   Estado: {status}")
    
    print("\n" + "="*100)


def validate_license_cmd(license_key: str):
    """Validar una licencia."""
    limiter = get_limiter()
    
    print(f"\n🔍 Validando licencia: {license_key}")
    
    result = limiter.validate_license(license_key)
    
    if result["valid"]:
        print(f"\n✅ LICENCIA VÁLIDA")
        print(f"\n{'='*50}")
        print(f"Plan: {result['plan']}")
        print(f"Email: {result['email']}")
        print(f"Expira: {result['expires_at']}")
        if result.get('days_left'):
            print(f"Días restantes: {result['days_left']}")
        print(f"{'='*50}\n")
    else:
        print(f"\n❌ LICENCIA INVÁLIDA")
        print(f"Razón: {result.get('reason', 'Desconocida')}\n")


def deactivate_license(license_key: str):
    """Desactivar una licencia."""
    import sqlite3
    limiter = get_limiter()
    
    print(f"\n⚠️  Desactivando licencia: {license_key}")
    
    confirm = input("¿Confirmar desactivación? (s/n): ")
    if confirm.lower() != 's':
        print("❌ Cancelado")
        return
    
    try:
        conn = sqlite3.connect(limiter.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE pro_licenses
            SET is_active = 0
            WHERE license_key = ?
        """, (license_key,))
        
        if cursor.rowcount == 0:
            print(f"\n❌ Licencia no encontrada")
        else:
            conn.commit()
            print(f"\n✅ Licencia desactivada exitosamente")
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def show_stats():
    """Mostrar estadísticas de uso."""
    limiter = get_limiter()
    stats = limiter.get_usage_stats()
    
    print(f"\n📊 ESTADÍSTICAS DE USO")
    print("="*50)
    print(f"Total consultas: {stats.get('total_queries', 0)}")
    print(f"Usuarios únicos: {stats.get('unique_metric', 0)}")
    print(f"Primera consulta: {stats.get('first_query', 'N/A')}")
    print(f"Última consulta: {stats.get('last_query', 'N/A')}")
    print("="*50 + "\n")


def main():
    if len(sys.argv) < 2:
        print("\n🔐 RVC Analyzer - Gestor de Licencias PRO")
        print("\nUso:")
        print("  python manage_licenses.py create <email>       - Crear licencia ($3 USD / 30 días)")
        print("  python manage_licenses.py list                 - Listar todas las licencias")
        print("  python manage_licenses.py validate <key>       - Validar una licencia")
        print("  python manage_licenses.py deactivate <key>     - Desactivar una licencia")
        print("  python manage_licenses.py stats                - Ver estadísticas de uso")
        print("\nEjemplos:")
        print("  python manage_licenses.py create usuario@gmail.com")
        print("  python manage_licenses.py validate RVC-PRO-ABC123XYZ\n")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "create":
        if len(sys.argv) < 3:
            print("❌ Error: Debes proporcionar un email")
            print("Uso: python manage_licenses.py create <email>")
            sys.exit(1)
        create_license(sys.argv[2])
    
    elif command == "list":
        list_licenses()
    
    elif command == "validate":
        if len(sys.argv) < 3:
            print("❌ Error: Debes proporcionar una clave de licencia")
            print("Uso: python manage_licenses.py validate <license_key>")
            sys.exit(1)
        validate_license_cmd(sys.argv[2])
    
    elif command == "deactivate":
        if len(sys.argv) < 3:
            print("❌ Error: Debes proporcionar una clave de licencia")
            print("Uso: python manage_licenses.py deactivate <license_key>")
            sys.exit(1)
        deactivate_license(sys.argv[2])
    
    elif command == "stats":
        show_stats()
    
    else:
        print(f"❌ Comando desconocido: {command}")
        print("Comandos válidos: create, list, validate, deactivate, stats")
        sys.exit(1)


if __name__ == "__main__":
    main()

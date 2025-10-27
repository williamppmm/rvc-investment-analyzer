#!/usr/bin/env python3
"""
Script de migración para agregar campos de renovación a la tabla pro_licenses.

EJECUTA ESTE SCRIPT UNA SOLA VEZ para actualizar tu base de datos existente
con los nuevos campos necesarios para el sistema de renovación.

Campos agregados:
- last_renewed_at: Fecha de la última renovación
- renewal_count: Contador de renovaciones (0 = nunca renovada)

Uso:
    python migrate_licenses_db.py

Seguridad:
- ✅ Verifica si las columnas ya existen antes de agregar
- ✅ No modifica datos existentes
- ✅ Solo agrega columnas nuevas
- ✅ Reversible (pero no incluye script de rollback)
"""

import sqlite3
import os

def migrate_database():
    """Agregar campos last_renewed_at y renewal_count a la tabla pro_licenses."""
    
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'rvc_database.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        print("   No es necesario migrar. Los campos se crearán automáticamente.")
        return
    
    print(f"📂 Base de datos encontrada: {db_path}")
    print("\n🔄 Iniciando migración...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si las columnas ya existen
        cursor.execute("PRAGMA table_info(pro_licenses)")
        columns = [col[1] for col in cursor.fetchall()]
        
        columns_to_add = []
        
        if 'last_renewed_at' not in columns:
            columns_to_add.append(('last_renewed_at', 'DATETIME'))
        
        if 'renewal_count' not in columns:
            columns_to_add.append(('renewal_count', 'INTEGER DEFAULT 0'))
        
        if not columns_to_add:
            print("\n✅ La base de datos ya está actualizada.")
            print("   Las columnas last_renewed_at y renewal_count ya existen.")
            conn.close()
            return
        
        # Agregar columnas faltantes
        for column_name, column_type in columns_to_add:
            print(f"   ➕ Agregando columna: {column_name} ({column_type})")
            cursor.execute(f"ALTER TABLE pro_licenses ADD COLUMN {column_name} {column_type}")
        
        conn.commit()
        
        # Verificar que se agregaron correctamente
        cursor.execute("PRAGMA table_info(pro_licenses)")
        new_columns = [col[1] for col in cursor.fetchall()]
        
        print("\n✅ Migración completada exitosamente!")
        print(f"\n📋 Columnas actuales en pro_licenses:")
        for col in new_columns:
            print(f"   • {col}")
        
        # Mostrar cuántas licencias existen
        cursor.execute("SELECT COUNT(*) FROM pro_licenses")
        count = cursor.fetchone()[0]
        print(f"\n📊 Licencias en la base de datos: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error durante la migración: {e}")
        return

if __name__ == "__main__":
    print("="*60)
    print("  MIGRACIÓN DE BASE DE DATOS - Sistema de Licencias RVC")
    print("="*60)
    migrate_database()
    print("\n" + "="*60)
    print("💡 Ahora puedes usar el comando 'renew' para renovar licencias")
    print("="*60 + "\n")

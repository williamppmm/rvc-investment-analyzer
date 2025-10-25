#!/usr/bin/env python3
"""
Sistema de límite de uso para modelo freemium.
Controla consultas gratuitas y valida licencias PRO.
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

class UsageLimiter:
    """Gestor de límites de uso y licencias."""
    
    # Límites por plan
    FREE_DAILY_LIMIT = 20  # 20 consultas por día
    PRO_LIMIT = -1  # Ilimitado
    LICENSE_DURATION_DAYS = 30  # Licencias válidas por 30 días
    LICENSE_PRICE_USD = 3  # Precio sugerido por licencia mensual
    
    def __init__(self, db_path="data/rvc_database.db"):
        """Inicializar limiter con base de datos."""
        self.db_path = db_path
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Crear tablas si no existen."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de uso por IP/sesión
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_agent TEXT,
                response_status INTEGER
            )
        """)
        
        # Tabla de licencias PRO
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pro_licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_key TEXT UNIQUE NOT NULL,
                email TEXT,
                plan_type TEXT DEFAULT 'PRO',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                is_active INTEGER DEFAULT 1,
                max_monthly_queries INTEGER DEFAULT -1,
                notes TEXT
            )
        """)
        
        # Índices para performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_usage_identifier 
            ON usage_tracking(identifier, timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_license_key 
            ON pro_licenses(license_key, is_active)
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Tablas de usage limiter inicializadas")
    
    def track_usage(self, identifier: str, endpoint: str, user_agent: str = None, status: int = 200):
        """
        Registrar una consulta.
        
        Args:
            identifier: IP o session ID del usuario
            endpoint: Endpoint usado (/analyze, /api/comparar, etc.)
            user_agent: User agent del navegador
            status: HTTP status de la respuesta
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO usage_tracking (identifier, endpoint, user_agent, response_status)
                VALUES (?, ?, ?, ?)
            """, (identifier, endpoint, user_agent, status))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"📊 Uso registrado: {identifier} → {endpoint}")
            
        except Exception as e:
            logger.error(f"❌ Error al registrar uso: {e}")
    
    def get_usage_count(self, identifier: str, period: str = "daily") -> int:
        """
        Obtener cantidad de consultas de un usuario en un período.
        
        Args:
            identifier: IP o session ID
            period: 'daily' (default)
        
        Returns:
            Número de consultas en el período
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calcular fecha límite (últimas 24 horas)
            now = datetime.now()
            cutoff = now - timedelta(days=1)
            
            cursor.execute("""
                SELECT COUNT(*) FROM usage_tracking
                WHERE identifier = ?
                AND timestamp >= ?
                AND endpoint IN ('/analyze', '/api/comparar')
            """, (identifier, cutoff.isoformat()))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            logger.error(f"❌ Error al obtener uso: {e}")
            return 0
    
    def check_limit(self, identifier: str, license_key: str = None) -> dict:
        """
        Verificar si el usuario ha alcanzado el límite.
        
        Args:
            identifier: IP o session ID
            license_key: Licencia PRO (opcional)
        
        Returns:
            {
                "allowed": bool,
                "remaining": int,
                "limit": int,
                "plan": "FREE" | "PRO",
                "reset_in": str,
                "license_days_left": int (solo PRO)
            }
        """
        # Verificar si tiene licencia PRO
        if license_key:
            license_info = self.validate_license(license_key)
            if license_info["valid"]:
                return {
                    "allowed": True,
                    "remaining": -1,  # Ilimitado
                    "limit": -1,
                    "plan": "PRO",
                    "reset_in": "N/A",
                    "license_days_left": license_info.get("days_left", 0),
                    "expires_at": license_info.get("expires_at")
                }
        
        # Usuario FREE - verificar límite diario
        usage_count = self.get_usage_count(identifier, period="daily")
        remaining = max(0, self.FREE_DAILY_LIMIT - usage_count)
        allowed = usage_count < self.FREE_DAILY_LIMIT
        
        # Calcular cuándo se resetea (medianoche)
        now = datetime.now()
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        hours_until_reset = int((tomorrow - now).total_seconds() / 3600)
        reset_str = f"{hours_until_reset} horas" if hours_until_reset > 0 else "menos de 1 hora"
        
        return {
            "allowed": allowed,
            "remaining": remaining,
            "limit": self.FREE_DAILY_LIMIT,
            "plan": "FREE",
            "reset_in": reset_str,
            "reset_date": tomorrow.strftime("%d/%m/%Y %H:%M")
        }
    
    def validate_license(self, license_key: str) -> dict:
        """
        Validar una licencia PRO.
        
        Args:
            license_key: Clave de licencia
        
        Returns:
            {
                "valid": bool,
                "plan": str,
                "expires_at": str,
                "days_left": int,
                "email": str
            }
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT plan_type, expires_at, email, is_active
                FROM pro_licenses
                WHERE license_key = ?
            """, (license_key,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return {"valid": False, "reason": "Licencia no encontrada"}
            
            plan, expires_at, email, is_active = result
            
            # Verificar si está activa
            if not is_active:
                return {"valid": False, "reason": "Licencia desactivada"}
            
            # Verificar expiración
            if expires_at:
                expiry = datetime.fromisoformat(expires_at)
                now = datetime.now()
                
                if now > expiry:
                    return {"valid": False, "reason": "Licencia expirada"}
                
                # Calcular días restantes
                days_left = (expiry - now).days
                
                return {
                    "valid": True,
                    "plan": plan,
                    "expires_at": expiry.strftime("%d/%m/%Y"),
                    "days_left": days_left,
                    "email": email
                }
            else:
                # Licencia permanente
                return {
                    "valid": True,
                    "plan": plan,
                    "expires_at": "Permanente",
                    "days_left": 999,
                    "email": email
                }
            
        except Exception as e:
            logger.error(f"❌ Error al validar licencia: {e}")
            return {"valid": False, "reason": "Error de validación"}
    
    def create_license(self, email: str, plan_type: str = "PRO", 
                      duration_days: int = 30, license_key: str = None) -> str:
        """
        Crear una nueva licencia PRO.
        
        Args:
            email: Email del usuario
            plan_type: Tipo de plan (PRO, ENTERPRISE, etc.)
            duration_days: Duración en días (default: 30)
            license_key: Clave personalizada (se genera si no se provee)
        
        Returns:
            Clave de licencia generada
        """
        import secrets
        
        # Generar clave si no se provee
        if not license_key:
            license_key = f"RVC-PRO-{secrets.token_hex(8).upper()}"
        
        # Calcular expiración (30 días por defecto)
        expires_at = (datetime.now() + timedelta(days=duration_days)).isoformat()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO pro_licenses (license_key, email, plan_type, expires_at)
                VALUES (?, ?, ?, ?)
            """, (license_key, email, plan_type, expires_at))
            
            conn.commit()
            conn.close()
            
            expiry_date = datetime.fromisoformat(expires_at)
            logger.info(f"✅ Licencia creada: {license_key} para {email} (expira: {expiry_date.strftime('%d/%m/%Y')})")
            return license_key
            
        except Exception as e:
            logger.error(f"❌ Error al crear licencia: {e}")
            raise
    
    def get_usage_stats(self, identifier: str = None) -> dict:
        """
        Obtener estadísticas de uso.
        
        Args:
            identifier: Si se provee, estadísticas de ese usuario. Si no, globales.
        
        Returns:
            Diccionario con estadísticas
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if identifier:
                # Stats de un usuario específico
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_queries,
                        COUNT(DISTINCT endpoint) as endpoints_used,
                        MIN(timestamp) as first_query,
                        MAX(timestamp) as last_query
                    FROM usage_tracking
                    WHERE identifier = ?
                """, (identifier,))
            else:
                # Stats globales
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_queries,
                        COUNT(DISTINCT identifier) as unique_users,
                        MIN(timestamp) as first_query,
                        MAX(timestamp) as last_query
                    FROM usage_tracking
                """)
            
            result = cursor.fetchone()
            conn.close()
            
            return {
                "total_queries": result[0],
                "unique_metric": result[1],
                "first_query": result[2],
                "last_query": result[3]
            }
            
        except Exception as e:
            logger.error(f"❌ Error al obtener stats: {e}")
            return {}
    
    def cleanup_old_records(self, days: int = 30):
        """Limpiar registros antiguos para mantener BD ligera."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute("""
                DELETE FROM usage_tracking
                WHERE timestamp < ?
            """, (cutoff,))
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"🧹 Limpieza: {deleted} registros eliminados (>{days} días)")
            
        except Exception as e:
            logger.error(f"❌ Error en limpieza: {e}")


# Instancia singleton
_limiter = None

def get_limiter() -> UsageLimiter:
    """Obtener instancia singleton del limiter."""
    global _limiter
    if _limiter is None:
        _limiter = UsageLimiter()
    return _limiter


if __name__ == "__main__":
    # Tests rápidos
    limiter = UsageLimiter()
    
    print("✅ Sistema de límites inicializado")
    
    # Test de tracking
    limiter.track_usage("192.168.1.100", "/analyze")
    
    # Test de límites
    check = limiter.check_limit("192.168.1.100")
    print(f"\n📊 Check límite: {check}")
    
    # Test de licencia (crear demo)
    try:
        key = limiter.create_license("demo@example.com", "PRO")
        print(f"\n🔑 Licencia demo creada: {key}")
        
        validation = limiter.validate_license(key)
        print(f"✅ Validación: {validation}")
    except:
        print("⚠️ Licencia demo ya existe")
    
    # Stats
    stats = limiter.get_usage_stats()
    print(f"\n📈 Stats globales: {stats}")

"""
Database Manager - Abstraccion para SQLite (desarrollo) y PostgreSQL (produccion)
Permite persistir el contador de visitas entre redeploys en produccion.
"""

import os
import sqlite3
import logging
from pathlib import Path
from typing import Optional, Tuple, Any
from urllib.parse import urlparse

logger = logging.getLogger("DBManager")

# Detectar si estamos en produccion (variable DATABASE_URL presente)
DATABASE_URL = os.getenv("DATABASE_URL")
IS_PRODUCTION = DATABASE_URL is not None

# Intentar importar psycopg2 solo si estamos en produccion
if IS_PRODUCTION:
    try:
        import psycopg2
        from psycopg2.extras import DictCursor
        logger.info("PostgreSQL habilitado (produccion)")
    except ImportError:
        logger.error("psycopg2 no disponible - instalar con: pip install psycopg2-binary")
        IS_PRODUCTION = False
else:
    logger.info("SQLite habilitado (desarrollo)")


class DatabaseManager:
    """
    Gestor de base de datos que soporta SQLite y PostgreSQL
    de forma transparente.
    """

    def __init__(self, sqlite_path: Optional[Path] = None):
        """
        Inicializa el gestor de base de datos.

        Args:
            sqlite_path: Ruta al archivo SQLite (solo para desarrollo)
        """
        self.is_production = IS_PRODUCTION
        self.sqlite_path = sqlite_path
        self.database_url = DATABASE_URL

        if self.is_production:
            logger.info(f"Modo: PRODUCCION (PostgreSQL)")
            # Fix para Render: reemplazar postgres:// con postgresql://
            if self.database_url and self.database_url.startswith("postgres://"):
                self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)
                logger.info("URL ajustada: postgres:// -> postgresql://")
        else:
            logger.info(f"Modo: DESARROLLO (SQLite: {self.sqlite_path})")

    def get_connection(self):
        """Retorna una conexion a la base de datos apropiada"""
        if self.is_production:
            return psycopg2.connect(self.database_url, cursor_factory=DictCursor)
        else:
            return sqlite3.connect(str(self.sqlite_path))

    def execute_query(self, query: str, params: Tuple = ()) -> Any:
        """
        Ejecuta una consulta y retorna los resultados.

        Args:
            query: Consulta SQL (con placeholders apropiados)
            params: Parametros de la consulta

        Returns:
            Lista de resultados
        """
        # Convertir placeholders de SQLite (?) a PostgreSQL (%s) si es necesario
        if self.is_production:
            query = query.replace("?", "%s")

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.commit()
            return results
        finally:
            cursor.close()
            conn.close()

    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """
        Ejecuta una consulta de actualizacion (INSERT, UPDATE, DELETE).

        Args:
            query: Consulta SQL
            params: Parametros de la consulta

        Returns:
            Numero de filas afectadas
        """
        # Convertir placeholders de SQLite (?) a PostgreSQL (%s) si es necesario
        if self.is_production:
            query = query.replace("?", "%s")

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(query, params)
            rowcount = cursor.rowcount
            conn.commit()
            return rowcount
        finally:
            cursor.close()
            conn.close()

    def init_tables(self):
        """Inicializa las tablas necesarias en la base de datos"""
        if self.is_production:
            self._init_postgres_tables()
        else:
            self._init_sqlite_tables()

    def _init_sqlite_tables(self):
        """Inicializa tablas para SQLite"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Tabla de visitas totales
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS site_visits (
                    id INTEGER PRIMARY KEY,
                    total_visits INTEGER DEFAULT 0,
                    last_updated TEXT
                )
            ''')

            # Tabla de visitas diarias
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_visits (
                    date TEXT PRIMARY KEY,
                    visits INTEGER DEFAULT 0
                )
            ''')

            # Inicializar contador si no existe
            cursor.execute('SELECT COUNT(*) FROM site_visits WHERE id = 1')
            if cursor.fetchone()[0] == 0:
                cursor.execute('INSERT INTO site_visits (id, total_visits) VALUES (1, 0)')

            conn.commit()
            logger.info("Tablas SQLite inicializadas")
        finally:
            cursor.close()
            conn.close()

    def _init_postgres_tables(self):
        """Inicializa tablas para PostgreSQL"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Tabla de visitas totales
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS site_visits (
                    id INTEGER PRIMARY KEY,
                    total_visits INTEGER DEFAULT 0,
                    last_updated TIMESTAMP
                )
            ''')

            # Tabla de visitas diarias
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_visits (
                    date DATE PRIMARY KEY,
                    visits INTEGER DEFAULT 0
                )
            ''')

            # Inicializar contador si no existe
            cursor.execute('SELECT COUNT(*) FROM site_visits WHERE id = 1')
            if cursor.fetchone()[0] == 0:
                cursor.execute('INSERT INTO site_visits (id, total_visits) VALUES (1, 0)')

            conn.commit()
            logger.info("Tablas PostgreSQL inicializadas")
        finally:
            cursor.close()
            conn.close()


# Instancia global del gestor de base de datos
_db_manager: Optional[DatabaseManager] = None


def get_db_manager(sqlite_path: Optional[Path] = None) -> DatabaseManager:
    """
    Retorna el gestor de base de datos (singleton).

    Args:
        sqlite_path: Ruta al archivo SQLite (solo primera vez)

    Returns:
        Instancia del DatabaseManager
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(sqlite_path)
        _db_manager.init_tables()
    return _db_manager

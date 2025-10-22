#!/bin/bash
# ============================================
# BACKUP SCRIPT - RVC Analyzer
# ============================================
# Script para crear backups automáticos del proyecto
# Uso: ./scripts/backup.sh [daily|weekly|monthly]

set -e  # Salir si hay errores

# Configuración
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_ROOT="${PROJECT_ROOT}/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_ONLY=$(date +%Y%m%d)

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Tipo de backup (default: daily)
BACKUP_TYPE="${1:-daily}"

# Directorios de backup según tipo
case "$BACKUP_TYPE" in
    daily)
        BACKUP_DIR="${BACKUP_ROOT}/daily"
        RETENTION_DAYS=7
        ;;
    weekly)
        BACKUP_DIR="${BACKUP_ROOT}/weekly"
        RETENTION_DAYS=30
        ;;
    monthly)
        BACKUP_DIR="${BACKUP_ROOT}/monthly"
        RETENTION_DAYS=365
        ;;
    *)
        echo -e "${RED}Error: Tipo de backup inválido. Use: daily, weekly, o monthly${NC}"
        exit 1
        ;;
esac

# Crear directorios si no existen
mkdir -p "$BACKUP_DIR"

# Nombre del archivo de backup
BACKUP_FILE="${BACKUP_DIR}/rcv_backup_${BACKUP_TYPE}_${DATE_ONLY}.tar.gz"

echo -e "${YELLOW}============================================${NC}"
echo -e "${YELLOW}RVC Analyzer - Backup ${BACKUP_TYPE}${NC}"
echo -e "${YELLOW}============================================${NC}"
echo -e "Timestamp: ${TIMESTAMP}"
echo -e "Backup file: ${BACKUP_FILE}"
echo ""

# ============================================
# VERIFICAR GIT STATUS
# ============================================
echo -e "${YELLOW}[1/5] Verificando estado de Git...${NC}"

cd "$PROJECT_ROOT"

if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo -e "${RED}⚠️  ADVERTENCIA: Hay cambios sin commitear en Git${NC}"
    echo -e "${YELLOW}Cambios detectados:${NC}"
    git status --short
    echo ""
    read -p "¿Continuar con el backup de todas formas? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Backup cancelado${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Git status verificado${NC}"
echo ""

# ============================================
# CREAR BACKUP
# ============================================
echo -e "${YELLOW}[2/5] Creando backup...${NC}"

# Archivos y directorios a incluir
tar -czf "$BACKUP_FILE" \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.venv' \
    --exclude='venv' \
    --exclude='env' \
    --exclude='.git' \
    --exclude='*.log' \
    --exclude='backups' \
    --exclude='data/cache.db' \
    --exclude='data/temp' \
    --exclude='.DS_Store' \
    --exclude='Thumbs.db' \
    --exclude='.env' \
    -C "$PROJECT_ROOT" \
    .

# Verificar que el backup se creó
if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✓ Backup creado exitosamente (${BACKUP_SIZE})${NC}"
else
    echo -e "${RED}✗ Error al crear backup${NC}"
    exit 1
fi

echo ""

# ============================================
# CREAR BACKUP DE BASE DE DATOS
# ============================================
echo -e "${YELLOW}[3/5] Backup de base de datos...${NC}"

DB_FILE="${PROJECT_ROOT}/data/cache.db"
DB_BACKUP="${BACKUP_DIR}/cache_db_${DATE_ONLY}.db"

if [ -f "$DB_FILE" ]; then
    cp "$DB_FILE" "$DB_BACKUP"
    DB_SIZE=$(du -h "$DB_BACKUP" | cut -f1)
    echo -e "${GREEN}✓ Database backup creado (${DB_SIZE})${NC}"
else
    echo -e "${YELLOW}⚠️  No se encontró base de datos en data/cache.db${NC}"
fi

echo ""

# ============================================
# LIMPIAR BACKUPS ANTIGUOS
# ============================================
echo -e "${YELLOW}[4/5] Limpiando backups antiguos...${NC}"

# Encontrar y eliminar backups más antiguos que RETENTION_DAYS
DELETED_COUNT=0

find "$BACKUP_DIR" -name "rcv_backup_${BACKUP_TYPE}_*.tar.gz" -type f -mtime +${RETENTION_DAYS} | while read file; do
    echo "  Eliminando: $(basename "$file")"
    rm "$file"
    DELETED_COUNT=$((DELETED_COUNT + 1))
done

find "$BACKUP_DIR" -name "cache_db_*.db" -type f -mtime +${RETENTION_DAYS} | while read file; do
    echo "  Eliminando: $(basename "$file")"
    rm "$file"
done

if [ $DELETED_COUNT -eq 0 ]; then
    echo -e "${GREEN}✓ No hay backups antiguos para eliminar${NC}"
else
    echo -e "${GREEN}✓ ${DELETED_COUNT} backups antiguos eliminados${NC}"
fi

echo ""

# ============================================
# RESUMEN
# ============================================
echo -e "${YELLOW}[5/5] Resumen del backup${NC}"

TOTAL_BACKUPS=$(find "$BACKUP_DIR" -name "rcv_backup_${BACKUP_TYPE}_*.tar.gz" -type f | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

echo -e "Tipo: ${BACKUP_TYPE}"
echo -e "Total backups ${BACKUP_TYPE}: ${TOTAL_BACKUPS}"
echo -e "Espacio usado: ${TOTAL_SIZE}"
echo -e "Retención: ${RETENTION_DAYS} días"
echo ""

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✓ Backup completado exitosamente${NC}"
echo -e "${GREEN}============================================${NC}"
echo -e "Archivo: ${BACKUP_FILE}"
echo -e "Timestamp: ${TIMESTAMP}"
echo ""

# ============================================
# NOTAS DE USO
# ============================================
# Para restaurar un backup:
# tar -xzf backups/daily/rcv_backup_daily_YYYYMMDD.tar.gz -C /ruta/destino
#
# Para automatizar (cron):
# 0 2 * * * /ruta/rcv_proyecto/scripts/backup.sh daily
# 0 3 * * 0 /ruta/rcv_proyecto/scripts/backup.sh weekly
# 0 4 1 * * /ruta/rcv_proyecto/scripts/backup.sh monthly

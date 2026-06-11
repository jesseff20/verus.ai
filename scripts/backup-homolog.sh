#!/bin/bash
# ========================================
# bravojus - Backup do Sandbox Homolog
# ========================================
# Faz pg_dump do container bravojus_db_homolog (banco bravojus_homolog,
# porta 5435), usado para validar migrations/features antes de aplicar
# em prod. Salva em backups/db/ com timestamp.
#
# Uso:
#   ./scripts/backup-homolog.sh
#   ./scripts/backup-homolog.sh --full  # inclui media files do backend
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/backups/db"
DATE=$(date +%Y%m%d_%H%M%S)

DB_CONTAINER="bravojus_db_homolog"
DB_USER="bravojus"
DB_NAME="bravojus_homolog"

FULL_BACKUP=false

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step()  { echo -e "${BLUE}[$1]${NC} $2"; }

while [[ $# -gt 0 ]]; do
    case $1 in
        --full) FULL_BACKUP=true; shift ;;
        -h|--help)
            echo "Uso: ./scripts/backup-homolog.sh [--full]"
            exit 0
            ;;
        *) log_error "Opção desconhecida: $1"; exit 1 ;;
    esac
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  bravojus - Backup Homolog${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verificar container rodando
if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
    log_error "Container ${DB_CONTAINER} não está rodando!"
    log_warn "Suba com: docker compose -f docker-compose.homolog.yml up -d"
    exit 1
fi

mkdir -p "$BACKUP_DIR"

if [ "$FULL_BACKUP" = true ]; then
    BACKUP_FILE="bravojus_homolog_${DATE}_FULL"
else
    BACKUP_FILE="bravojus_homolog_${DATE}"
fi

# ========================================
# STEP 1: Backup do banco
# ========================================
log_step "1/3" "Criando dump do banco ${DB_NAME}..."

docker exec "$DB_CONTAINER" pg_dump \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --clean \
    --if-exists \
    -F c > "${BACKUP_DIR}/${BACKUP_FILE}.dump"

DUMP_SIZE=$(ls -lh "${BACKUP_DIR}/${BACKUP_FILE}.dump" | awk '{print $5}')
log_info "✓ Dump criado: ${BACKUP_FILE}.dump (${DUMP_SIZE})"

# ========================================
# STEP 2: Backup de media (se --full)
# ========================================
if [ "$FULL_BACKUP" = true ]; then
    log_step "2/3" "Copiando media files..."
    MEDIA_DIR="${PROJECT_DIR}/backend/media"

    if [ -d "$MEDIA_DIR" ] && [ "$(ls -A $MEDIA_DIR 2>/dev/null)" ]; then
        tar -czf "${BACKUP_DIR}/${BACKUP_FILE}_media.tar.gz" -C "${PROJECT_DIR}/backend" media/
        MEDIA_SIZE=$(ls -lh "${BACKUP_DIR}/${BACKUP_FILE}_media.tar.gz" | awk '{print $5}')
        log_info "✓ Media files: ${BACKUP_FILE}_media.tar.gz (${MEDIA_SIZE})"
    else
        log_warn "Nenhum media file encontrado em ${MEDIA_DIR}"
        touch "${BACKUP_DIR}/${BACKUP_FILE}_media.empty"
    fi

    log_step "3/3" "Empacotando dump + media..."
    cd "$BACKUP_DIR"
    tar -czf "${BACKUP_FILE}_COMPLETE.tar.gz" \
        "${BACKUP_FILE}.dump" \
        "${BACKUP_FILE}_media"* 2>/dev/null || true
    rm -f "${BACKUP_FILE}.dump" "${BACKUP_FILE}_media.tar.gz" "${BACKUP_FILE}_media.empty"
    FINAL_FILE="${BACKUP_FILE}_COMPLETE.tar.gz"
    FINAL_SIZE=$(ls -lh "$FINAL_FILE" | awk '{print $5}')
    cd "$PROJECT_DIR"
else
    log_step "2/3" "Pulando media files (use --full para incluir)"
    log_step "3/3" "Finalizando..."
    FINAL_FILE="${BACKUP_FILE}.dump"
    FINAL_SIZE="$DUMP_SIZE"
fi

# ========================================
# Link simbólico para último backup
# ========================================
cd "$BACKUP_DIR"
rm -f "latest_homolog.dump" "latest_homolog_COMPLETE.tar.gz" 2>/dev/null || true

if [ "$FULL_BACKUP" = true ]; then
    ln -sf "$FINAL_FILE" "latest_homolog_COMPLETE.tar.gz"
else
    ln -sf "$FINAL_FILE" "latest_homolog.dump"
fi

# Manter últimos 5 backups do homolog
ls -t bravojus_homolog_*.dump 2>/dev/null | tail -n +6 | xargs -r rm -- 2>/dev/null || true
ls -t bravojus_homolog_*_COMPLETE.tar.gz 2>/dev/null | tail -n +6 | xargs -r rm -- 2>/dev/null || true

cd "$PROJECT_DIR"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}[SUCCESS]${NC} Backup do homolog concluído!"
echo -e "${BLUE}========================================${NC}"
log_info "Arquivo: ${YELLOW}${BACKUP_DIR}/${FINAL_FILE}${NC}"
log_info "Tamanho: ${YELLOW}${FINAL_SIZE}${NC}"
echo ""

#!/bin/bash
# ========================================
# bravojus - Script Unificado de Backup
# ========================================
# Uso:
#   ./scripts/backup.sh                     # Backup simples (só banco)
#   ./scripts/backup.sh --full              # Backup completo (banco + media)
#   ./scripts/backup.sh --env local         # Força ambiente local
#   ./scripts/backup.sh --env prod          # Força ambiente produção
#
# Exemplos:
#   ./scripts/backup.sh                     # Backup rápido do banco
#   ./scripts/backup.sh --full              # Backup para migração (banco + media)
#   ./scripts/backup.sh --full --env local  # Backup completo do ambiente local

set -e

# ========================================
# Configurações
# ========================================
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/backups/db"
DATE=$(date +%Y%m%d_%H%M%S)

# Defaults
FULL_BACKUP=false
FORCE_ENV=""

# ========================================
# Funções
# ========================================
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[$1]${NC} $2"; }

show_help() {
    echo "Uso: ./scripts/backup.sh [opções]"
    echo ""
    echo "Opções:"
    echo "  --full        Backup completo (banco + media files)"
    echo "  --env ENV     Força ambiente (local ou prod)"
    echo "  -h, --help    Mostra esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  ./scripts/backup.sh                    # Backup rápido do banco"
    echo "  ./scripts/backup.sh --full             # Backup para migração"
    echo "  ./scripts/backup.sh --env prod         # Backup do servidor"
}

detect_environment() {
    # Se forçado via --env, usar esse
    if [ -n "$FORCE_ENV" ]; then
        echo "$FORCE_ENV"
        return
    fi

    # Detectar automaticamente
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "verus_ai_local"; then
        echo "local"
    elif docker ps --format '{{.Names}}' 2>/dev/null | grep -q "bravodoc_db_prod"; then
        echo "prod"
    else
        echo "unknown"
    fi
}

get_db_container() {
    local env=$1
    case $env in
        local) echo "verus_ai_local" ;;
        prod)  echo "bravodoc_db_prod" ;;
        *)     echo "" ;;
    esac
}

get_compose_file() {
    local env=$1
    case $env in
        local) echo "${PROJECT_DIR}/docker-compose.local.yml" ;;
        prod)  echo "${PROJECT_DIR}/docker-compose.prod.yml" ;;
        *)     echo "" ;;
    esac
}

# ========================================
# Parse argumentos
# ========================================
while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            FULL_BACKUP=true
            shift
            ;;
        --env)
            FORCE_ENV="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Opção desconhecida: $1"
            show_help
            exit 1
            ;;
    esac
done

# ========================================
# Início
# ========================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  bravojus - Backup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Detectar ambiente
ENV=$(detect_environment)
if [ "$ENV" = "unknown" ]; then
    log_error "Não foi possível detectar o ambiente!"
    log_error "Certifique-se que o container do banco está rodando."
    log_warn "Containers esperados:"
    log_warn "  - Local: verus_ai_local"
    log_warn "  - Prod:  bravodoc_db_prod"
    exit 1
fi

DB_CONTAINER=$(get_db_container "$ENV")
COMPOSE_FILE=$(get_compose_file "$ENV")

log_info "Ambiente detectado: ${YELLOW}${ENV}${NC}"
log_info "Container: ${YELLOW}${DB_CONTAINER}${NC}"
echo ""

# Criar diretório de backup
mkdir -p "$BACKUP_DIR"

# ========================================
# STEP 1: Backup do banco
# ========================================
if [ "$FULL_BACKUP" = true ]; then
    BACKUP_FILE="bravojus_${ENV}_${DATE}_FULL"
else
    BACKUP_FILE="bravojus_${ENV}_${DATE}"
fi

log_step "1/3" "Criando backup do banco de dados..."

# Verificar se container está rodando
if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
    log_error "Container ${DB_CONTAINER} não está rodando!"
    exit 1
fi

# Fazer dump
docker exec "$DB_CONTAINER" pg_dump \
    -U bravojus \
    -d bravojus \
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

    # Criar pacote completo
    log_step "3/3" "Criando pacote completo..."

    cd "$BACKUP_DIR"
    tar -czf "${BACKUP_FILE}_COMPLETE.tar.gz" \
        "${BACKUP_FILE}.dump" \
        "${BACKUP_FILE}_media"* 2>/dev/null || true

    # Limpar arquivos intermediários
    rm -f "${BACKUP_FILE}.dump"
    rm -f "${BACKUP_FILE}_media.tar.gz"
    rm -f "${BACKUP_FILE}_media.empty"

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
# Criar link simbólico para último backup
# ========================================
cd "$BACKUP_DIR"
rm -f "latest_${ENV}.dump" "latest_${ENV}_COMPLETE.tar.gz" 2>/dev/null || true

if [ "$FULL_BACKUP" = true ]; then
    ln -sf "$FINAL_FILE" "latest_${ENV}_COMPLETE.tar.gz"
else
    ln -sf "$FINAL_FILE" "latest_${ENV}.dump"
fi

# ========================================
# Limpar backups antigos (manter últimos 5)
# ========================================
log_info "Limpando backups antigos..."
ls -t bravojus_${ENV}_*.dump 2>/dev/null | tail -n +6 | xargs -r rm -- 2>/dev/null || true
ls -t bravojus_${ENV}_*_COMPLETE.tar.gz 2>/dev/null | tail -n +6 | xargs -r rm -- 2>/dev/null || true

cd "$PROJECT_DIR"

# ========================================
# Resumo
# ========================================
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}[SUCCESS]${NC} Backup concluído!"
echo -e "${BLUE}========================================${NC}"
echo ""
log_info "Arquivo: ${YELLOW}${BACKUP_DIR}/${FINAL_FILE}${NC}"
log_info "Tamanho: ${YELLOW}${FINAL_SIZE}${NC}"
log_info "Ambiente: ${YELLOW}${ENV}${NC}"
echo ""

if [ "$FULL_BACKUP" = true ]; then
    log_info "Para restaurar em outro ambiente:"
    echo ""
    echo "  # Copiar para servidor:"
    echo "  scp ${BACKUP_DIR}/${FINAL_FILE} maelson@proderjdoc.bravonix.ia.br:~/bravodoc/backups/"
    echo ""
    echo "  # Restaurar:"
    echo "  ./scripts/restore.sh ${FINAL_FILE}"
else
    log_info "Para restaurar:"
    echo ""
    echo "  ./scripts/restore.sh ${FINAL_FILE}"
    echo ""
    log_warn "Este backup contém apenas o banco de dados."
    log_warn "Use --full para incluir media files."
fi
echo ""

#!/bin/bash
# ========================================
# bravojus - Script Unificado de Restore
# ========================================
# Uso:
#   ./scripts/restore.sh <arquivo>          # Detecta formato automaticamente
#   ./scripts/restore.sh --env local <arq>  # Força ambiente local
#   ./scripts/restore.sh --env prod <arq>   # Força ambiente produção
#   ./scripts/restore.sh --no-confirm <arq> # Pula confirmação (para automação)
#
# Formatos suportados:
#   - .dump           (pg_dump custom format)
#   - .sql            (SQL texto)
#   - .sql.gz         (SQL comprimido)
#   - .tar.gz         (pacote completo: banco + media)
#
# Exemplos:
#   ./scripts/restore.sh backups/db/verus_ai_local_20260206.dump
#   ./scripts/restore.sh backups/db/bravojus_prod_20260206_COMPLETE.tar.gz
#   ./scripts/restore.sh --env prod --no-confirm latest_prod.dump

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
TEMP_DIR="${PROJECT_DIR}/temp-restore"
DATE=$(date +%Y%m%d_%H%M%S)

# Defaults
FORCE_ENV=""
NO_CONFIRM=false
BACKUP_FILE=""

# ========================================
# Funções
# ========================================
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[$1]${NC} $2"; }

show_help() {
    echo "Uso: ./scripts/restore.sh [opções] <arquivo>"
    echo ""
    echo "Opções:"
    echo "  --env ENV       Força ambiente (local ou prod)"
    echo "  --no-confirm    Pula confirmação (para automação)"
    echo "  -h, --help      Mostra esta ajuda"
    echo ""
    echo "Formatos suportados:"
    echo "  .dump           pg_dump custom format"
    echo "  .sql            SQL texto"
    echo "  .sql.gz         SQL comprimido"
    echo "  .tar.gz         Pacote completo (banco + media)"
    echo ""
    echo "Exemplos:"
    echo "  ./scripts/restore.sh verus_ai_local_20260206.dump"
    echo "  ./scripts/restore.sh --env prod backup_COMPLETE.tar.gz"
}

detect_environment() {
    if [ -n "$FORCE_ENV" ]; then
        echo "$FORCE_ENV"
        return
    fi

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

detect_format() {
    local file=$1
    if [[ "$file" == *"_COMPLETE.tar.gz" ]] || [[ "$file" == *".tar.gz" && "$file" != *".sql.tar.gz" ]]; then
        echo "package"
    elif [[ "$file" == *.dump ]]; then
        echo "dump"
    elif [[ "$file" == *.sql.gz ]]; then
        echo "sql_gz"
    elif [[ "$file" == *.sql ]]; then
        echo "sql"
    else
        echo "unknown"
    fi
}

cleanup() {
    rm -rf "$TEMP_DIR" 2>/dev/null || true
}

trap cleanup EXIT

# ========================================
# Parse argumentos
# ========================================
while [[ $# -gt 0 ]]; do
    case $1 in
        --env)
            FORCE_ENV="$2"
            shift 2
            ;;
        --no-confirm)
            NO_CONFIRM=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        -*)
            log_error "Opção desconhecida: $1"
            show_help
            exit 1
            ;;
        *)
            BACKUP_FILE="$1"
            shift
            ;;
    esac
done

# ========================================
# Validações
# ========================================
if [ -z "$BACKUP_FILE" ]; then
    log_error "Arquivo de backup não especificado!"
    echo ""
    show_help
    echo ""
    log_info "Backups disponíveis em ${BACKUP_DIR}:"
    ls -lh "$BACKUP_DIR"/*.dump "$BACKUP_DIR"/*.tar.gz 2>/dev/null || echo "  Nenhum backup encontrado"
    exit 1
fi

# Resolver caminho do arquivo
if [[ "$BACKUP_FILE" != /* ]]; then
    # Tentar primeiro no diretório atual
    if [ -f "$BACKUP_FILE" ]; then
        BACKUP_PATH="$BACKUP_FILE"
    # Depois no diretório de backups
    elif [ -f "${BACKUP_DIR}/${BACKUP_FILE}" ]; then
        BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE}"
    else
        log_error "Arquivo não encontrado: $BACKUP_FILE"
        exit 1
    fi
else
    BACKUP_PATH="$BACKUP_FILE"
fi

if [ ! -f "$BACKUP_PATH" ]; then
    log_error "Arquivo não encontrado: $BACKUP_PATH"
    exit 1
fi

# ========================================
# Início
# ========================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  bravojus - Restore${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Detectar ambiente
ENV=$(detect_environment)
if [ "$ENV" = "unknown" ]; then
    log_error "Não foi possível detectar o ambiente!"
    log_error "Certifique-se que o container do banco está rodando."
    exit 1
fi

DB_CONTAINER=$(get_db_container "$ENV")
COMPOSE_FILE=$(get_compose_file "$ENV")
FORMAT=$(detect_format "$BACKUP_PATH")

log_info "Ambiente: ${YELLOW}${ENV}${NC}"
log_info "Container: ${YELLOW}${DB_CONTAINER}${NC}"
log_info "Arquivo: ${YELLOW}$(basename $BACKUP_PATH)${NC}"
log_info "Formato: ${YELLOW}${FORMAT}${NC}"
echo ""

if [ "$FORMAT" = "unknown" ]; then
    log_error "Formato de arquivo não reconhecido!"
    exit 1
fi

# ========================================
# Confirmação
# ========================================
if [ "$NO_CONFIRM" = false ]; then
    echo -e "${RED}ATENÇÃO: Isso irá SUBSTITUIR todos os dados no banco!${NC}"
    echo ""
    read -p "Digite 'SIM' para confirmar: " CONFIRM
    echo ""

    if [ "$CONFIRM" != "SIM" ]; then
        log_warn "Operação cancelada pelo usuário"
        exit 0
    fi
fi

# Verificar container
if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
    log_error "Container ${DB_CONTAINER} não está rodando!"
    exit 1
fi

# ========================================
# STEP 1: Backup de segurança
# ========================================
log_step "1/4" "Criando backup de segurança..."

SAFETY_BACKUP="${BACKUP_DIR}/safety_before_restore_${DATE}.dump"

docker exec "$DB_CONTAINER" pg_dump \
    -U bravojus \
    -d bravojus \
    --clean \
    --if-exists \
    -F c > "$SAFETY_BACKUP"

SAFETY_SIZE=$(ls -lh "$SAFETY_BACKUP" | awk '{print $5}')
log_info "✓ Backup de segurança: $(basename $SAFETY_BACKUP) (${SAFETY_SIZE})"

# ========================================
# STEP 2: Preparar arquivo para restore
# ========================================
log_step "2/4" "Preparando arquivo para restore..."

mkdir -p "$TEMP_DIR"

case $FORMAT in
    package)
        # Extrair pacote
        tar -xzf "$BACKUP_PATH" -C "$TEMP_DIR"

        # Encontrar arquivo de banco
        DUMP_FILE=$(find "$TEMP_DIR" -name "*.dump" 2>/dev/null | head -1)
        SQL_FILE=$(find "$TEMP_DIR" -name "*.sql" -o -name "*.sql.gz" 2>/dev/null | head -1)

        if [ -n "$DUMP_FILE" ]; then
            RESTORE_FILE="$DUMP_FILE"
            RESTORE_FORMAT="dump"
        elif [ -n "$SQL_FILE" ]; then
            if [[ "$SQL_FILE" == *.gz ]]; then
                gunzip -c "$SQL_FILE" > "${TEMP_DIR}/restore.sql"
                RESTORE_FILE="${TEMP_DIR}/restore.sql"
            else
                RESTORE_FILE="$SQL_FILE"
            fi
            RESTORE_FORMAT="sql"
        else
            log_error "Nenhum arquivo de banco encontrado no pacote!"
            exit 1
        fi

        # Verificar media files
        MEDIA_FILE=$(find "$TEMP_DIR" -name "*_media.tar.gz" 2>/dev/null | head -1)
        ;;

    dump)
        RESTORE_FILE="$BACKUP_PATH"
        RESTORE_FORMAT="dump"
        ;;

    sql_gz)
        gunzip -c "$BACKUP_PATH" > "${TEMP_DIR}/restore.sql"
        RESTORE_FILE="${TEMP_DIR}/restore.sql"
        RESTORE_FORMAT="sql"
        ;;

    sql)
        RESTORE_FILE="$BACKUP_PATH"
        RESTORE_FORMAT="sql"
        ;;
esac

log_info "✓ Arquivo preparado: $(basename $RESTORE_FILE)"

# ========================================
# STEP 3: Restaurar banco
# ========================================
log_step "3/4" "Restaurando banco de dados..."

# Encerrar conexões ativas
docker exec "$DB_CONTAINER" psql -U bravojus -d postgres -c "
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = 'bravojus' AND pid <> pg_backend_pid();
" 2>/dev/null || true

# Recriar banco
docker exec "$DB_CONTAINER" psql -U bravojus -d postgres -c "DROP DATABASE IF EXISTS bravojus;" 2>/dev/null || true
docker exec "$DB_CONTAINER" psql -U bravojus -d postgres -c "CREATE DATABASE bravojus OWNER bravojus;"

# Restaurar conforme formato
if [ "$RESTORE_FORMAT" = "dump" ]; then
    cat "$RESTORE_FILE" | docker exec -i "$DB_CONTAINER" pg_restore \
        -U bravojus \
        -d bravojus \
        --no-owner \
        --no-privileges \
        --clean \
        --if-exists 2>&1 || true
else
    cat "$RESTORE_FILE" | docker exec -i "$DB_CONTAINER" psql \
        -U bravojus \
        -d bravojus 2>&1 || true
fi

log_info "✓ Banco restaurado"

# ========================================
# STEP 4: Restaurar media (se pacote completo)
# ========================================
if [ "$FORMAT" = "package" ] && [ -n "$MEDIA_FILE" ]; then
    log_step "4/4" "Restaurando media files..."

    tar -xzf "$MEDIA_FILE" -C "$TEMP_DIR"

    if [ -d "${TEMP_DIR}/media" ]; then
        mkdir -p "${PROJECT_DIR}/backend/media"
        cp -r "${TEMP_DIR}/media/"* "${PROJECT_DIR}/backend/media/" 2>/dev/null || true
        chmod -R 755 "${PROJECT_DIR}/backend/media"
        log_info "✓ Media files restaurados"
    else
        log_warn "Nenhum media file encontrado no pacote"
    fi
else
    log_step "4/4" "Pulando media files (não incluídos no backup)"
fi

# ========================================
# Resumo
# ========================================
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}[SUCCESS]${NC} Restore concluído!"
echo -e "${BLUE}========================================${NC}"
echo ""
log_info "Banco restaurado de: ${YELLOW}$(basename $BACKUP_PATH)${NC}"
log_info "Ambiente: ${YELLOW}${ENV}${NC}"
echo ""
log_info "Backup de segurança salvo em:"
echo "  ${SAFETY_BACKUP}"
echo ""
log_warn "Se algo deu errado, restaure o backup de segurança:"
echo "  ./scripts/restore.sh $(basename $SAFETY_BACKUP)"
echo ""

if [ "$ENV" = "prod" ]; then
    log_info "Reiniciando backend..."
    docker compose -f "$COMPOSE_FILE" restart backend 2>/dev/null || true
fi

log_info "Pronto! Teste a aplicação para verificar os dados."
echo ""

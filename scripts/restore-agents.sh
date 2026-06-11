#!/bin/bash
# ========================================
# bravojus - Restaurar Configuração Estrutural
# ========================================
# Restaura agentes, KBs (metadata), blueprints e seções a partir de um JSON.
# NÃO afeta documentos gerados pelos usuários (GenerationSession, SectionGeneration, etc.)
# NÃO restaura arquivos físicos das KBs - apenas cria os registros de metadata.
#
# Uso:
#   ./scripts/restore-agents.sh <arquivo>.json                  # Detecta ambiente
#   ./scripts/restore-agents.sh <arquivo>.json --dry-run        # Preview sem alterar
#   ./scripts/restore-agents.sh <arquivo>.json --force          # Sobrescrever existentes
#   ./scripts/restore-agents.sh <arquivo>.json --only-agents    # Só agentes + KBs
#   ./scripts/restore-agents.sh --env prod <arquivo>.json       # Forçar produção

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

# Defaults
FORCE_ENV=""
EXTRA_ARGS=""
BACKUP_FILE=""

# ========================================
# Funções
# ========================================
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

show_help() {
    echo "Uso: ./scripts/restore-agents.sh [opções] <arquivo>.json"
    echo ""
    echo "Opções:"
    echo "  --env ENV         Força ambiente (local ou prod)"
    echo "  --dry-run         Mostra o que seria restaurado sem alterar nada"
    echo "  --force           Sobrescreve registros existentes"
    echo "  --only-agents     Restaura apenas agentes (sem blueprints/seções)"
    echo "  -h, --help        Mostra esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  ./scripts/restore-agents.sh backup_agents_2026-02-19.json --dry-run"
    echo "  ./scripts/restore-agents.sh backup_agents_2026-02-19.json --force"
    echo "  ./scripts/restore-agents.sh --env prod backup_agents_2026-02-19.json"
}

detect_environment() {
    if [ -n "$FORCE_ENV" ]; then
        echo "$FORCE_ENV"
        return
    fi

    if [ -d "${PROJECT_DIR}/backend/venv" ] && docker ps --format '{{.Names}}' 2>/dev/null | grep -q "verus_ai_local"; then
        echo "local"
    elif docker ps --format '{{.Names}}' 2>/dev/null | grep -q "bravodoc_backend_prod"; then
        echo "prod"
    else
        echo "unknown"
    fi
}

# ========================================
# Parse argumentos
# ========================================
while [[ $# -gt 0 ]]; do
    case $1 in
        --env)
            FORCE_ENV="$2"
            shift 2
            ;;
        --dry-run)
            EXTRA_ARGS="$EXTRA_ARGS --dry-run"
            shift
            ;;
        --force)
            EXTRA_ARGS="$EXTRA_ARGS --force"
            shift
            ;;
        --only-agents)
            EXTRA_ARGS="$EXTRA_ARGS --only-agents"
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

# Validar arquivo
if [ -z "$BACKUP_FILE" ]; then
    log_error "Arquivo de backup não especificado!"
    echo ""
    show_help
    echo ""
    log_info "Backups disponíveis:"
    {
        ls -lht "${PROJECT_DIR}/backend/backups/"backup_config_*.json 2>/dev/null
        ls -lht "${PROJECT_DIR}/backend/backups/"backup_agents_*.json 2>/dev/null
        ls -lht "${PROJECT_DIR}/backups/"backup_config_*.json 2>/dev/null
        ls -lht "${PROJECT_DIR}/backups/"backup_agents_*.json 2>/dev/null
    } 2>/dev/null | sort -r | awk '!seen[$NF]++' | awk 'NR<=10' || echo "  Nenhum backup encontrado"
    exit 1
fi

# ========================================
# Início
# ========================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  bravojus - Restaurar Configuração Estrutural${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

ENV=$(detect_environment)
log_info "Ambiente detectado: ${YELLOW}${ENV}${NC}"
log_info "Arquivo: ${YELLOW}${BACKUP_FILE}${NC}"
echo ""

case $ENV in
    local)
        # Resolver caminho absoluto do arquivo ANTES de cd
        if [[ "$BACKUP_FILE" != /* ]]; then
            # Caminho relativo - tentar encontrar
            if [ -f "${PROJECT_DIR}/${BACKUP_FILE}" ]; then
                RESOLVED_FILE="$(cd "${PROJECT_DIR}" && realpath "${BACKUP_FILE}")"
            elif [ -f "${PROJECT_DIR}/backend/backups/${BACKUP_FILE}" ]; then
                RESOLVED_FILE="${PROJECT_DIR}/backend/backups/${BACKUP_FILE}"
            elif [ -f "${PROJECT_DIR}/backups/${BACKUP_FILE}" ]; then
                RESOLVED_FILE="${PROJECT_DIR}/backups/${BACKUP_FILE}"
            else
                log_error "Arquivo não encontrado: $BACKUP_FILE"
                exit 1
            fi
        else
            RESOLVED_FILE="$BACKUP_FILE"
        fi

        log_info "Executando via venv local..."
        cd "${PROJECT_DIR}/backend"
        source venv/bin/activate
        python manage.py restore_agents "$RESOLVED_FILE" $EXTRA_ARGS
        ;;
    prod)
        CONTAINER="bravodoc_backend_prod"

        if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
            log_error "Container ${CONTAINER} não está rodando!"
            exit 1
        fi

        # Em prod, o arquivo precisa estar dentro de /app/backups/ (volume montado)
        # Se o caminho não é absoluto, assumir que está em /app/backups/
        if [[ "$BACKUP_FILE" != /* ]]; then
            CONTAINER_PATH="/app/backups/${BACKUP_FILE}"
        else
            CONTAINER_PATH="$BACKUP_FILE"
        fi

        # Verificar se o arquivo existe no container
        if ! docker exec "$CONTAINER" test -f "$CONTAINER_PATH"; then
            log_error "Arquivo não encontrado no container: $CONTAINER_PATH"
            log_warn "Certifique-se que o arquivo está em backups/ (volume montado em /app/backups/)"
            log_info "Arquivos disponíveis no container:"
            docker exec "$CONTAINER" ls -lh /app/backups/backup_agents_*.json 2>/dev/null || echo "  Nenhum"
            exit 1
        fi

        log_info "Executando dentro do container ${YELLOW}${CONTAINER}${NC}..."
        docker exec "$CONTAINER" python manage.py restore_agents "$CONTAINER_PATH" $EXTRA_ARGS
        ;;
    *)
        log_error "Não foi possível detectar o ambiente!"
        log_warn "Certifique-se que:"
        log_warn "  - Local: venv existe e container verus_ai_local está rodando"
        log_warn "  - Prod: container bravodoc_backend_prod está rodando"
        exit 1
        ;;
esac

# ========================================
# Resumo
# ========================================
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}[SUCCESS]${NC} Restauração concluída!"
echo -e "${BLUE}========================================${NC}"
echo ""

#!/bin/bash
# ========================================
# bravojus - Backup de Configuração Estrutural
# ========================================
# Exporta agentes, KBs (metadata), blueprints e seções para JSON.
# NÃO exporta documentos de usuários (GenerationSession, SectionGeneration, etc.)
# NÃO exporta arquivos físicos das KBs (apenas metadata).
#
# Uso:
#   ./scripts/backup-agents.sh                  # Detecta ambiente
#   ./scripts/backup-agents.sh --env local      # Força local
#   ./scripts/backup-agents.sh --env prod       # Força produção
#   ./scripts/backup-agents.sh --only-agents    # Só agentes + KBs (sem blueprints/seções)

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

# ========================================
# Funções
# ========================================
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

show_help() {
    echo "Uso: ./scripts/backup-agents.sh [opções]"
    echo ""
    echo "Opções:"
    echo "  --env ENV         Força ambiente (local ou prod)"
    echo "  --only-agents     Exporta apenas agentes (sem blueprints/seções)"
    echo "  -h, --help        Mostra esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  ./scripts/backup-agents.sh                  # Backup completo"
    echo "  ./scripts/backup-agents.sh --only-agents    # Só agentes"
    echo "  ./scripts/backup-agents.sh --env prod       # Em produção"
}

detect_environment() {
    if [ -n "$FORCE_ENV" ]; then
        echo "$FORCE_ENV"
        return
    fi

    # Local: backend roda fora do Docker (venv)
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
        --only-agents)
            EXTRA_ARGS="--only-agents"
            shift
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
echo -e "${BLUE}  bravojus - Backup de Agentes${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

ENV=$(detect_environment)
log_info "Ambiente detectado: ${YELLOW}${ENV}${NC}"

case $ENV in
    local)
        # Local: executa via venv direto
        log_info "Executando via venv local..."
        cd "${PROJECT_DIR}/backend"
        source venv/bin/activate
        python manage.py backup_agents $EXTRA_ARGS
        ;;
    prod)
        # Produção: executa dentro do container backend
        CONTAINER="bravodoc_backend_prod"

        if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
            log_error "Container ${CONTAINER} não está rodando!"
            exit 1
        fi

        log_info "Executando dentro do container ${YELLOW}${CONTAINER}${NC}..."
        docker exec "$CONTAINER" python manage.py backup_agents $EXTRA_ARGS
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
echo -e "${GREEN}[SUCCESS]${NC} Backup de configuração estrutural concluído!"
echo -e "${BLUE}========================================${NC}"
echo ""

# Listar últimos backups
log_info "Últimos backups de configuração:"
{
    ls -lht "${PROJECT_DIR}/backend/backups/"backup_config_*.json 2>/dev/null
    ls -lht "${PROJECT_DIR}/backend/backups/"backup_agents_*.json 2>/dev/null
    ls -lht "${PROJECT_DIR}/backups/"backup_config_*.json 2>/dev/null
    ls -lht "${PROJECT_DIR}/backups/"backup_agents_*.json 2>/dev/null
} 2>/dev/null | sort -r | awk '!seen[$NF]++' | awk 'NR<=5' || echo "  Nenhum backup encontrado"
echo ""

log_info "Para restaurar (sem afetar documentos dos usuários):"
echo "  ./scripts/restore-agents.sh <arquivo>.json --force"
echo ""

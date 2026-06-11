#!/bin/bash

# 🚀 Script de Setup Local - Verus.AI
# Execute: bash setup_local.sh

set -e  # Exit on error

echo "🚀 Verus.AI - Setup Local"
echo "========================="
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Função de log
log() {
    echo -e "${GREEN}✅ $1${NC}"
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. Verificar Python
echo "1️⃣  Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    log "Python encontrado: $PYTHON_VERSION"
else
    error "Python 3 não encontrado!"
    exit 1
fi

# 2. Criar venv
echo ""
echo "2️⃣  Criando ambiente virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    log "Venv criado"
else
    warn "Venv já existe"
fi

# 3. Ativar venv
echo ""
echo "3️⃣  Ativando venv..."
source venv/bin/activate
log "Venv ativado"

# 4. Upgrade pip
echo ""
echo "4️⃣  Atualizando pip..."
pip install --upgrade pip --quiet
log "Pip atualizado"

# 5. Instalar dependências
echo ""
echo "5️⃣  Instalando dependências..."
echo "   (isso pode demorar 2-3 minutos...)"
pip install -r requirements.txt --quiet
log "Dependências instaladas"

# 6. Verificar .env
echo ""
echo "6️⃣  Verificando arquivo .env..."
if [ ! -f ".env" ]; then
    warn ".env não encontrado! Criando template..."
    cat > .env << 'EOF'
DEBUG=True
SECRET_KEY=dev-secret-key-local-12345

# Database (EDITE COM SUAS CREDENCIAIS)
DB_NAME=bravojus
DB_USER=postgres
DB_PASSWORD=MUDE_AQUI
DB_HOST=localhost
DB_PORT=5432

# APIs (ADICIONE SUAS CHAVES)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Redis (opcional)
REDIS_URL=redis://localhost:6379/0
EOF
    warn "Arquivo .env criado! EDITE AS CREDENCIAIS ANTES DE CONTINUAR!"
    warn "Execute: nano .env"
    exit 0
else
    log ".env encontrado"
fi

# 7. Verificar Postgres
echo ""
echo "7️⃣  Verificando PostgreSQL..."
if pg_isready -U postgres &> /dev/null; then
    log "PostgreSQL está rodando"
else
    error "PostgreSQL não está rodando!"
    echo "   Inicie com: brew services start postgresql@15"
    exit 1
fi

# 8. Verificar se banco existe
echo ""
echo "8️⃣  Verificando banco de dados..."
if psql -U postgres -lqt | cut -d \| -f 1 | grep -qw bravojus; then
    log "Banco 'bravojus' já existe"
else
    warn "Banco 'bravojus' não encontrado. Criando..."
    createdb -U postgres bravojus
    log "Banco criado"
fi

# 9. Django check
echo ""
echo "9️⃣  Verificando configuração Django..."
python manage.py check
log "Configuração OK"

# 10. Migrations
echo ""
echo "🔟 Criando migrations..."
python manage.py makemigrations
log "Migrations criadas"

echo ""
echo "1️⃣1️⃣  Aplicando migrations..."
python manage.py migrate
log "Migrations aplicadas"

# 11. Collectstatic
echo ""
echo "1️⃣2️⃣  Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear
log "Static files coletados"

# 12. Criar superuser
echo ""
echo "1️⃣3️⃣  Deseja criar um superuser? (s/n)"
read -r response
if [[ "$response" =~ ^([sS][iI][mM]|[sS])$ ]]; then
    python manage.py createsuperuser
fi

# Finalização
echo ""
echo "========================================="
echo -e "${GREEN}🎉 SETUP COMPLETO!${NC}"
echo "========================================="
echo ""
echo "Para rodar o servidor:"
echo "  source venv/bin/activate"
echo "  python manage.py runserver"
echo ""
echo "Acessos:"
echo "  - Admin: http://localhost:8000/admin"
echo "  - API: http://localhost:8000/api/docs/"
echo ""

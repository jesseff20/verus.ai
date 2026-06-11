#!/bin/bash

# ========================================
# BravoDoc - Setup Nginx na VM
# ========================================
# Este script configura o Nginx que JÁ ESTÁ INSTALADO na VM
# para servir o BravoDoc junto com outros projetos

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}BravoDoc - Configuração Nginx${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR]${NC} Este script precisa rodar como root"
    echo "Use: sudo ./scripts/setup-nginx.sh"
    exit 1
fi

# Check if nginx is installed
if ! command -v nginx &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Nginx não está instalado!"
    echo "Instale: sudo apt-get install nginx"
    exit 1
fi

# Copy config file
echo -e "${GREEN}[INFO]${NC} Copiando configuração do BravoDoc..."
cp nginx/bravodoc-site.conf /etc/nginx/sites-available/bravodoc

# Create symlink
if [ -f /etc/nginx/sites-enabled/bravodoc ]; then
    echo -e "${YELLOW}[WARN]${NC} Symlink já existe, removendo antigo..."
    rm /etc/nginx/sites-enabled/bravodoc
fi

echo -e "${GREEN}[INFO]${NC} Criando symlink..."
ln -s /etc/nginx/sites-available/bravodoc /etc/nginx/sites-enabled/

# Create directories for static/media
echo -e "${GREEN}[INFO]${NC} Criando diretórios para static/media..."
mkdir -p /opt/bravodoc/staticfiles
mkdir -p /opt/bravodoc/media

# Set permissions
chown -R www-data:www-data /opt/bravodoc/staticfiles
chown -R www-data:www-data /opt/bravodoc/media

# Test nginx config
echo -e "${GREEN}[INFO]${NC} Testando configuração do Nginx..."
if nginx -t; then
    echo -e "${GREEN}[INFO]${NC} Configuração válida!"
else
    echo -e "${RED}[ERROR]${NC} Erro na configuração do Nginx!"
    exit 1
fi

# Reload nginx
echo -e "${GREEN}[INFO]${NC} Recarregando Nginx..."
systemctl reload nginx

echo ""
echo -e "${GREEN}[INFO]${NC} ========================================="
echo -e "${GREEN}[INFO]${NC} Nginx configurado com sucesso!${NC}"
echo -e "${GREEN}[INFO]${NC} ========================================="
echo ""
echo -e "${GREEN}[INFO]${NC} Próximos passos:"
echo -e "${GREEN}[INFO]${NC} 1. Subir containers Docker:"
echo -e "${GREEN}[INFO]${NC}    docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo -e "${GREEN}[INFO]${NC} 2. Configurar SSL (Let's Encrypt):"
echo -e "${GREEN}[INFO]${NC}    sudo certbot --nginx -d bravodoc.bravonix.ia.br"
echo ""
echo -e "${GREEN}[INFO]${NC} 3. Testar acesso:"
echo -e "${GREEN}[INFO]${NC}    http://bravodoc.bravonix.ia.br"
echo ""

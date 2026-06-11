# Deploy Verus.AI — Histórico de Deploys (IBM Cloud)

> **AVISO:** Este documento é um registro histórico de deploys reais.
> O projeto foi renomeado de **BravoDoc/Bravogov** para **Verus.AI**.
> O usuário Docker Hub `mqmaellson39` e o domínio `bravodoc.bravonix.ia.br`
> são do ambiente anterior. Consulte `docker-compose.dokploy.yml` para o deploy atual.

Documentação dos comandos executados para subir o servidor e containers.

---

## Contexto

- **Servidor:** IBM Cloud - 163.107.86.167
- **Domínio BravoDoc:** bravodoc.bravonix.ia.br
- **Domínio ComplianceNow:** api.compliancenow.com.br
- **Problema:** Ambos os domínios apontam para o mesmo IP, mas são serviços diferentes

### Arquitetura Final

| Serviço | Porta | Tecnologia |
| --- | --- | --- |
| ComplianceNow API | 8000 | uvicorn (FastAPI) - Supervisor |
| BravoDoc Backend | 8001 | gunicorn (Django) - Docker |
| BravoDoc Frontend | 3001 | Next.js 16.1.1 - Docker |
| Nginx Local | 80/443 | Reverse Proxy + SSL |

---

## Passo 1: Atualizar docker-compose.prod.yml

**Objetivo:** Expor as portas do backend (8001) e frontend (3001) para o host.

**Arquivo:** `~/bravodoc/docker-compose.prod.yml` na IBM

**Alteração no backend:**

```yaml
backend:
  ports:
    - "8001:8000"
```

**Alteração no frontend:**

```yaml
frontend:
  ports:
    - "3001:3000"
```

---

## Passo 2: Criar config Nginx para BravoDoc

**Objetivo:** Configurar virtual host para bravodoc.bravonix.ia.br

**Arquivo:** `/etc/nginx/sites-available/bravodoc`

---

## Passo 3: Habilitar site no Nginx

**Comando:**

```bash
sudo ln -s /etc/nginx/sites-available/bravodoc /etc/nginx/sites-enabled/bravodoc
```

---

## Passo 4: Testar e reiniciar Nginx

**Comandos:**

```bash
sudo nginx -t
sudo systemctl restart nginx
```

---

## Passo 5: Reiniciar containers Docker

**Comando:**

```bash
cd ~/bravodoc && docker compose -f docker-compose.prod.yml up -d
```

---

## Build e Deploy de Imagens Docker

### IMPORTANTE: Sempre usar `--platform linux/amd64`

O servidor IBM é Linux AMD64. Se buildar sem essa flag em um Mac (Apple Silicon), a imagem não funcionará.

### Build Frontend (local - Mac/Linux)

```bash
cd /Users/maelsonmarquesdelima/Sistemas_IA/Bravogov/frontend

docker build \
  --platform linux/amd64 \
  --build-arg NEXT_PUBLIC_API_URL=https://bravodoc.bravonix.ia.br \
  --build-arg NEXT_PUBLIC_API_BASE_PATH=/v1 \
  --build-arg NEXT_PUBLIC_APP_NAME=BravoDoc \
  --build-arg NEXT_PUBLIC_APP_VERSION=1.0.0 \
  --build-arg NEXT_PUBLIC_TINYMCE_API_KEY=uys67ncyqgy8vcltmxdftgek0g1h7q7mf5r09wjy9h3pwlvf \
  -t mqmaellson39/bravodoc-frontend:latest \
  -f Dockerfile .
```

### Build Backend (local - Mac/Linux)

```bash
cd /Users/maelsonmarquesdelima/Sistemas_IA/Bravogov/backend

docker build \
  --platform linux/amd64 \
  -t mqmaellson39/bravodoc-backend:latest \
  -f Dockerfile .
```

### Push para Docker Hub

```bash
docker push mqmaellson39/bravodoc-frontend:latest
docker push mqmaellson39/bravodoc-backend:latest
```

### Atualizar no Servidor IBM

**Pré-requisito:** Fazer login no Docker Hub no servidor (como usuário ubuntu):

```bash
ssh ubuntu@163.107.86.167
docker login -u mqmaellson39
```

**Atualizar containers:**

```bash
ssh ubuntu@163.107.86.167 "cd ~/bravodoc && sudo docker compose -f docker-compose.prod.yml pull && sudo docker compose -f docker-compose.prod.yml up -d"
```

**Atualizar apenas frontend:**

```bash
ssh ubuntu@163.107.86.167 "cd ~/bravodoc && sudo docker compose -f docker-compose.prod.yml pull frontend && sudo docker compose -f docker-compose.prod.yml up -d frontend"
```

**Atualizar apenas backend:**

```bash
ssh ubuntu@163.107.86.167 "cd ~/bravodoc && sudo docker compose -f docker-compose.prod.yml pull backend && sudo docker compose -f docker-compose.prod.yml up -d backend"
```

---

## Execução dos Comandos

### Data: 2025-12-27

---

---

## Deploy PRODERJ - proderjdoc.bravonix.ia.br

### Contexto PRODERJ

| Item | Valor |
|------|-------|
| **Servidor** | VPS com Traefik (proxy reverso) |
| **Domínio** | proderjdoc.bravonix.ia.br |
| **Usuário SSH** | maelson |
| **Senha SSH** | anVtjWNwqy |
| **Diretório** | ~/bravodoc |
| **Tag Docker** | `:proderjdoc` |

### Estrutura no Servidor

```text
~/bravodoc/
├── .env                      ← Variáveis de ambiente
├── docker-compose.prod.yml   ← Arquivo compose
└── backups/                  ← Backups do banco
    └── *.dump                ← Arquivos de backup
```

> **NOTA:** O projeto NÃO é sincronizado via Git no servidor. Apenas arquivos de configuração são enviados via SCP. As imagens Docker são baixadas do Docker Hub.

---

### Passo 1: Fazer Backup Local (antes de qualquer deploy)

```bash
# Na máquina local
cd /Users/maelsonmarquesdelima/Sistemas_IA/Bravogov

# Backup completo (banco + media)
./scripts/backup.sh --full

# Ou backup simples (só banco)
./scripts/backup.sh
```

O backup será salvo em `backups/db/` com nome tipo `bravogov_local_YYYYMMDD_HHMMSS_FULL_COMPLETE.tar.gz`

---

### Passo 2: Build e Push das Imagens Docker e controle de versionamento, precisa se atentar a isso aqui

**IMPORTANTE:** Usar `--platform linux/amd64` (servidor é Linux, não ARM)

**Backend:**

```bash
cd /Users/maelsonmarquesdelima/Sistemas_IA/Bravogov/backend

docker buildx build --platform linux/amd64 -t mqmaellson39/bravodoc-backend:proderjdoc -t mqmaellson39/bravodoc-backend:v1.3.0 -f Dockerfile.prod --push .
```

**Frontend:**

```bash
cd /Users/maelsonmarquesdelima/Sistemas_IA/Bravogov/frontend

docker buildx build --platform linux/amd64 --build-arg NEXT_PUBLIC_API_URL=https://proderjdoc.bravonix.ia.br --build-arg NEXT_PUBLIC_API_BASE_PATH=/api/v1 --build-arg NEXT_PUBLIC_APP_NAME=Verus.AI --build-arg NEXT_PUBLIC_APP_VERSION=1.3.0 --build-arg NEXT_PUBLIC_TINYMCE_API_KEY=uys67ncyqgy8vcltmxdftgek0g1h7q7mf5r09wjy9h3pwlvf -t mqmaellson39/bravodoc-frontend:proderjdoc -t mqmaellson39/bravodoc-frontend:v1.3.0 --push .
```

---

### Passo 3: Enviar Arquivos para o Servidor (via SCP)

**Enviar docker-compose.prod.yml:**

```bash
scp /Users/maelsonmarquesdelima/Sistemas_IA/Bravogov/docker-compose.prod.yml maelson@proderjdoc.bravonix.ia.br:~/bravodoc/
# Senha: anVtjWNwqy
```

**Enviar .env (template configurado):**

```bash
scp /Users/maelsonmarquesdelima/Sistemas_IA/Bravogov/.env.proderj.example maelson@proderjdoc.bravonix.ia.br:/tmp/
# Depois no servidor: mv /tmp/.env.proderj.example ~/bravodoc/.env

# Senha: anVtjWNwqy
```

**Enviar backup do banco:**

```bash
# Enviar para /tmp primeiro (evita problemas de permissão)
scp backups/db/bravogov_local_*_COMPLETE.tar.gz maelson@proderjdoc.bravonix.ia.br:/tmp/
# Senha: anVtjWNwqy
scp backups/db/bravogov_local_20260208_132319_FULL_COMPLETE.tar.gz maelson@proderjdoc.bravonix.ia.br:~/bravodoc/backups/

# Depois no servidor mover para ~/bravodoc/backups/
```

---

### Passo 4: Acessar o Servidor via SSH

```bash
ssh maelson@proderjdoc.bravonix.ia.br
# Senha: anVtjWNwqy
```

---

### Passo 5: Configurar Arquivos no Servidor

```bash
# Mover .env do /tmp para o lugar certo
mv /tmp/.env.proderj.example ~/bravodoc/.env

# Mover backup do /tmp para backups
mkdir -p ~/bravodoc/backups
mv /tmp/bravogov_local_*_COMPLETE.tar.gz ~/bravodoc/backups/

# Editar .env se necessário
nano ~/bravodoc/.env
```

**Variáveis essenciais no .env:**

```bash
# Database
DB_NAME=bravogov
DB_USER=bravogov
DB_PASSWORD=SENHA_FORTE_AQUI
REDIS_PASSWORD=SENHA_FORTE_AQUI

# API Keys
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-proj-...

# Cloudflare R2 Storage
USE_R2=True
CLOUDFLARE_R2_ACCOUNT_ID=d5987aa352e4072680028a000bced2ef
CLOUDFLARE_R2_ENDPOINT=https://d5987aa352e4072680028a000bced2ef.r2.cloudflarestorage.com
CLOUDFLARE_R2_ACCESS_KEY_ID=acacffc9e37627165322ea7e78ac0bdf
CLOUDFLARE_R2_SECRET_ACCESS_KEY=70d298fb2b3440b104c576553f6ee1ee5c87e9b75b2a47738159dc5f958bf2a7
CLOUDFLARE_R2_BUCKET_NAME=proderjdoc
CLOUDFLARE_R2_PUBLIC_URL=pub-f673c2898bae4dd59945d57cb0d41786.r2.dev
```

---

### Passo 6: Subir os Containers

```bash
cd ~/bravodoc

# Baixar novas imagens
docker-compose -f docker-compose.prod.yml pull

# Subir containers
docker-compose -f docker-compose.prod.yml up -d

# Ou com force-recreate (recomendado após atualização)
docker-compose -f docker-compose.prod.yml up -d --force-recreate
```

---

### Passo 7: Restaurar Backup do Banco

**IMPORTANTE:** Executar DEPOIS que os containers estiverem rodando.

```bash
cd ~/bravodoc/backups

# Extrair o arquivo compactado
tar -xzf bravogov_local_*_COMPLETE.tar.gz

# Listar arquivos extraídos
ls -la
# Deve ter: bravogov_local_*.dump e bravogov_local_*_media.tar.gz

# Restaurar o banco
docker exec -i bravodoc_db_prod pg_restore \
  -U bravogov \
  -d bravogov \
  --clean \
  --if-exists \
  < bravogov_local_*.dump

# Se der erro de "database in use", parar o backend primeiro:
docker-compose -f ~/bravodoc/docker-compose.prod.yml stop backend celery celery-beat
# Restaurar novamente
# Depois subir novamente:
docker-compose -f ~/bravodoc/docker-compose.prod.yml up -d
```

**Restaurar media files (se necessário):**

```bash
# Extrair media
tar -xzf bravogov_local_*_media.tar.gz

# Copiar para o volume do backend
docker cp media/. bravodoc_backend_prod:/app/media/
```

---

### Passo 8: Verificar Status

```bash
# Ver containers rodando
docker-compose -f docker-compose.prod.yml ps

# Ver logs do backend
docker-compose -f docker-compose.prod.yml logs -f backend

# Ver logs do frontend
docker-compose -f docker-compose.prod.yml logs -f frontend

# Testar se está funcionando
curl -I https://proderjdoc.bravonix.ia.br
```

---

### Comandos Úteis

```bash
# Parar todos os containers
docker-compose -f docker-compose.prod.yml down

# Reiniciar apenas backend
docker-compose -f docker-compose.prod.yml restart backend

# Acessar shell do container
docker exec -it bravodoc_backend_prod bash

# Rodar migrations
docker exec bravodoc_backend_prod python manage.py migrate

# Rodar todos os seeds (popular dados iniciais)
docker exec bravodoc_backend_prod python manage.py populate_all

# Ver variáveis de ambiente do R2
docker exec bravodoc_backend_prod env | grep R2
```

---

### Backup no Servidor (para fazer backup do banco em produção)

```bash
# Criar backup do banco de produção
docker exec bravodoc_db_prod pg_dump \
  -U bravogov \
  -d bravogov \
  -F c > ~/bravodoc/backups/backup_prod_$(date +%Y%m%d_%H%M%S).dump

# Baixar para máquina local
scp maelson@proderjdoc.bravonix.ia.br:~/bravodoc/backups/backup_prod_*.dump ./backups/db/
```


### Restaurar Backup no Servidor PRODERJ

  1. Ver onde está o backup:

  ls ~/bravodoc/backups/

  Deve ter algo como bravogov_local_XXXXXXXX_XXXXXX_FULL_COMPLETE.tar.gz

  2. Extrair o arquivo compactado:

  cd ~/bravodoc/backups
  tar -xzf bravogov_local_*_COMPLETE.tar.gz

  Isso vai gerar:
  - bravogov_local_*.dump (o banco)
  - bravogov_local_*_media.tar.gz (os arquivos de mídia)

  3. Verificar que o container do banco está rodando:

  docker ps | grep bravodoc_db_prod

  Se não estiver rodando, suba com:
  cd ~/bravodoc && docker-compose -f docker-compose.prod.yml up -d db

  4. Restaurar o dump no banco:

  cd ~/bravodoc/backups
  docker exec -i bravodoc_db_prod pg_restore -U bravogov -d bravogov --clean --if-exists
   < bravogov_local_*.dump

  - --clean = apaga as tabelas antes de restaurar
  - --if-exists = não dá erro se a tabela não existir ainda

  Se der erro "database is being accessed by other users", pare os serviços que usam o
  banco:

  cd ~/bravodoc
  docker-compose -f docker-compose.prod.yml stop backend celery celery-beat
  docker exec -i bravodoc_db_prod pg_restore -U bravogov -d bravogov --clean --if-exists
   < ~/bravodoc/backups/bravogov_local_*.dump
  docker-compose -f docker-compose.prod.yml up -d

  5. Rodar migrations (caso tenha algo novo):

  docker exec bravodoc_backend_prod python manage.py migrate

  6. Popular dados iniciais (seeds):

  docker exec bravodoc_backend_prod python manage.py populate_all

  Resumindo: o comando principal é o do passo 4. O resto é preparação e pós-restore.


  gh release create v1.1.0 \
    --title "v1.1.0 - Manutenção de produção" \                                      
    --notes "$(cat <<'EOF'
  ## Fixes                                                                           
  - URLs de histórico com tipo + phase + generation_session
  - Normalizer de subseções em preview/exports                                       
  - Fix tabela PDF com fundo preto
  - JWT single-flight no interceptor do frontend                                     
  - N+1 em tr/etp-sessions (889 → 1 query)                                           
  - N+1 em admin BlueprintSection (1400 → 18 queries)
  - Fix header OU-toggle na fase de Decisão do TR                                    
  - Remoção do texto 'Alternativa' confuso                                           
  - Sidebar lê versão de NEXT_PUBLIC_APP_VERSION
                                                                                     
  ## Deploy       
  - Docker: mqmaellson39/bravodoc-{backend,frontend}:v1.1.0                          
  EOF             
  )"
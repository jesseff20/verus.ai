#!/bin/bash
set -e

# ---- Diagnóstico de variáveis de ambiente ----
echo "============================================"
echo "  Verus.AI — Entrypoint Diagnostics"
echo "============================================"
echo "  PORT:          ${PORT:-8000}"
echo "  ENVIRONMENT:   ${ENVIRONMENT:-local}"
echo "  DATABASE_URL:  ${DATABASE_URL:+SET (hidden)}${DATABASE_URL:-NOT SET}"
echo "  DB_HOST:       ${DB_HOST:-not set}"
echo "  REDIS_URL:     ${REDIS_URL:+SET (hidden)}${REDIS_URL:-NOT SET}"
echo "============================================"

if [ -z "$DATABASE_URL" ] && [ -z "$DB_HOST" ]; then
  echo ""
  echo "ERROR: Neither DATABASE_URL nor DB_HOST is set."
  echo "  On Railway: add a PostgreSQL service and link DATABASE_URL."
  echo "  On Docker:  ensure DB_HOST is set in docker-compose environment."
  echo ""
  exit 1
fi

# Wait for database to be reachable
echo "Waiting for database..."
DB_READY=0
for i in $(seq 1 30); do
  if python -c "
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.local')
import django; django.setup()
from django.db import connection; connection.ensure_connection()
" 2>/dev/null; then
    echo "Database ready."
    DB_READY=1
    break
  fi
  echo "  DB not ready (attempt $i/30), retrying in 2s..."
  sleep 2
done

if [ "$DB_READY" = "0" ]; then
  echo ""
  echo "ERROR: Database unreachable after 60s."
  echo "  DATABASE_URL=${DATABASE_URL:+SET}${DATABASE_URL:-NOT SET}"
  echo "  DB_HOST=${DB_HOST:-not set}"
  echo "  Check your database service is running and env vars are correct."
  echo ""
  exit 1
fi

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Migrando registros anthropic → watsonx..."
python manage.py migrate_anthropic_to_watsonx || true

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Corrigindo BrandSettings e CopilotConfig (remove referências a contrata.ai)..."
python manage.py fix_brand_settings || true

echo "Corrigindo domínio de email dos usuários para @verus.ai..."
python manage.py fix_user_emails || true

echo "Migrando usuário admin → usuario_demo (se existir)..."
python manage.py migrate_admin_to_usuario_demo || true

# ===========================================================================
# Seeds CRÍTICOS — rodam ANTES do gunicorn (sistema não funciona sem eles)
# ===========================================================================
echo "Criando módulos do sistema (crítico)..."
python manage.py seed_modules || { echo "WARN: seed_modules falhou — sistema pode ter módulos faltando"; }

echo "Criando tipos de documentos jurídicos (crítico)..."
python manage.py seed_document_types || { echo "WARN: seed_document_types falhou — tipos de documento podem faltar"; }

echo "Criando ambiente demo de produção — usuários, clientes, casos (crítico)..."
python manage.py seed_production_demo || { echo "WARN: seed_production_demo falhou — dados demo podem faltar"; }

# ===========================================================================
# Seeds OPCIONAIS — executados em background para não bloquear o gunicorn.
# Todos são idempotentes (|| true garante que falhas não derrubam o container).
# ===========================================================================
SEED_LOG="/app/logs/seeds.log"
(
  echo "[seed] Iniciando seeds opcionais em background..."

  echo "[seed] Removendo tipos/blueprints legados de licitação (ETP, DFD, etc)..."
  python manage.py clean_legacy_document_types || true

  echo "[seed] Removendo sessões e documentos legados de ETP/licitação..."
  python manage.py clean_legacy_sessions || true

  # TODO(verus-ai): blueprints abaixo são de direito privado (BravoJus).
  # Manter por compatibilidade, mas criar blueprints específicos de procuradoria
  # (mandado de segurança, ação civil pública, ADI, recursos administrativos, etc.) — Fase 5.
  echo "[seed] Criando blueprints jurídicos completos (seções e estrutura)..."
  python manage.py seed_juridico_completo --force || true

  echo "[seed] Criando blueprints de Família e Sucessões..."
  python manage.py seed_familia_sucessoes --force || true

  echo "[seed] Criando blueprints de Previdenciário e Consumidor..."
  python manage.py seed_previdenciario_consumidor --force || true

  echo "[seed] Criando blueprints de Tributário e Administrativo..."
  python manage.py seed_tributario_administrativo --force || true

  echo "[seed] Criando blueprints de Procuradoria Municipal (pareceres, minutas, execução fiscal, contratos)..."
  python manage.py seed_procuradoria_municipal --force || true

  echo "[seed] Criando blueprints de Digital/LGPD e Empresarial..."
  python manage.py seed_digital_lgpd_empresarial --force || true

  echo "[seed] Criando blueprints de Ações Cíveis..."
  python manage.py seed_civel_acoes --force || true

  echo "[seed] Criando blueprints de Cível Complemento (réplica, possessória, usucapião, etc.)..."
  python manage.py seed_civel_complemento --force || true

  echo "[seed] Criando blueprints de Imobiliário e Locação..."
  python manage.py seed_imobiliario_locacao --force || true

  echo "[seed] Criando blueprints de Família - Complemento..."
  python manage.py seed_familia_complemento --force || true

  echo "[seed] Criando blueprints de Criminal - Recursos..."
  python manage.py seed_criminal_recursos --force || true

  echo "[seed] Criando blueprints de Trabalhista - Complemento..."
  python manage.py seed_trabalhista_complemento --force || true

  echo "[seed] Criando blueprints de Consumidor - Complemento..."
  python manage.py seed_consumidor_complemento --force || true

  echo "[seed] Criando blueprints de Tributário - Complemento..."
  python manage.py seed_tributario_complemento --force || true

  echo "[seed] Criando blueprints de Constitucional, Ambiental e Eleitoral..."
  python manage.py seed_constitucional_ambiental_eleitoral --force || true

  echo "[seed] Criando blueprints de Militar, Internacional, Empresarial e Previd./Tributário..."
  python manage.py seed_militar_internacional_empresarial --force || true

  echo "[seed] Criando blueprints Especializados Complementares (JEC, Agrário, Sanitário, Desportivo, etc.)..."
  python manage.py seed_especializado_complementar --force || true

  echo "[seed] Criando agentes especializados de seção (SectionAgentConfig)..."
  python manage.py criar_agentes_especializados --force || true

  echo "[seed] Migrando todos os agentes para IBM WatsonX + criando validadores..."
  python manage.py update_agents_watsonx --force || true

  echo "[seed] Vinculando agentes generator/validator a todas as BlueprintSections..."
  python manage.py ensure_blueprint_agents --force || true

  echo "[seed] Corrigindo areas M2M dos blueprints (fix_blueprint_areas)..."
  python manage.py fix_blueprint_areas || true

  echo "[seed] Configurando visibilidade de blueprints para Procuradoria Municipal..."
  python manage.py set_blueprint_visibility || true

  echo "[seed] Aplicando padrão PDF ABNT a todos os blueprints..."
  python manage.py fix_pdf_standards || true

  echo "[seed] Criando AgentPrompt jurídicos (chat) no WatsonX..."
  python manage.py seed_watsonx_agents --force || true

  echo "[seed] Criando geradores de documentos jurídicos..."
  python manage.py seed_document_generators || true

  echo "[seed] Criando ferramentas dos agentes de formulário..."
  python manage.py seed_agent_tools || true

  echo "[seed] Criando assistentes de formulários..."
  python manage.py seed_form_assistants || true

  echo "[seed] Importando legislação brasileira na base de conhecimento..."
  # seed_legislacao depende de rede externa (planalto.gov.br). Tentar até 3x com pausa.
  # Usa --no-embeddings para evitar dependência de API de embeddings no startup.
  _seed_leg_ok=0
  for attempt in 1 2 3; do
    echo "[seed] seed_legislacao tentativa $attempt/3..."
    if python manage.py seed_legislacao --no-embeddings; then
      _seed_leg_ok=1
      break
    fi
    echo "[seed] seed_legislacao falhou na tentativa $attempt. Aguardando 10s..."
    sleep 10
  done
  if [ "$_seed_leg_ok" = "0" ]; then
    echo "[seed] AVISO: seed_legislacao falhou em todas as tentativas. KB ficara vazia."
  fi

  echo "[seed] Vinculando legislação aos agentes (criando KnowledgeBase wrappers)..."
  python manage.py link_kb_agents || true

  echo "[seed] Criando tribunais e comarcas..."
  python manage.py seed_courts || true

  echo "[seed] Importando magistrados dos tribunais..."
  python manage.py seed_judges || true

  echo "[seed] Populando ministros do STF..."
  python manage.py seed_stf_ministers || true

  echo "[seed] Populando desembargadores..."
  python manage.py seed_desembargadores || true

  echo "[seed] Populando membros do TSE..."
  python manage.py seed_tse_members || true

  echo "[seed] Populando ministros do TST..."
  python manage.py seed_tst_ministers || true

  echo "[seed] Populando ministros do STM..."
  python manage.py seed_stm_ministers || true

  echo "[seed] Populando fases processuais..."
  python manage.py seed_case_phases || true

  echo "[seed] Criando fluxos judiciais de sistema (BPMN)..."
  python manage.py seed_judicial_flows --force || true

  # TODO(verus-ai): seed_clients cria "clientes" de escritório privado.
  # Procuradorias não têm clientes — têm partes processuais e órgãos assistidos.
  # Desabilitar quando o modelo de Parte/Órgão Assistido for implementado (Fase 4).
  echo "[seed] Populando clientes demo..."
  python manage.py seed_clients || true

  # TODO(verus-ai): tabela OAB de honorários não se aplica a procuradorias públicas.
  # Mantido por não causar dano; remover ou substituir por tabela de sucumbência pública na Fase 4.
  echo "[seed] Populando tabela de honorários OAB..."
  python manage.py seed_oab_fees || true

  echo "[seed] Populando padrões LGPD..."
  python manage.py seed_lgpd_defaults || true

  echo "[seed] Populando notificações e lembretes..."
  python manage.py seed_notifications || true
  python manage.py seed_reminders || true

  echo "[seed] Populando dados demo (prazos, tarefas, audiências, financeiro) nos casos..."
  python manage.py seed_case_demo_data || true

  echo "[seed] Populando dados demo de novas features (Timesheet, CRM, KPIs, NFS-e)..."
  python manage.py seed_new_features_demo || true

  echo "[seed] Criando jornada demo de workflow judicial..."
  python manage.py seed_demo_workflow_journey || true

  echo "[seed] Todos os seeds concluídos em background."
) 2>&1 | tee -a "$SEED_LOG" &

# ===========================================================================

echo "Starting Gunicorn on port ${PORT:-8000} (seeds rodando em background)..."
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --timeout 600 \
  --workers 2 \
  --threads 4 \
  --worker-class gthread

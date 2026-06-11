# Backup e Restore de Agentes

## Visão Geral

Dois tipos de backup disponíveis:

| Tipo | Script | O que salva | Formato |
|------|--------|-------------|---------|
| **Agentes** | `backup-agents.sh` | Agentes, blueprints, seções, prompts, configs | JSON (~600 KB) |
| **Banco completo** | `backup.sh` | Tudo (usuários, sessões, KBs, embeddings, etc.) | .dump (pg_dump) |

---

## Backup de Agentes (JSON)

Exporta todos os `SectionAgentConfig`, `DocumentBlueprint` e `BlueprintSection` com:
- Prompts (system_prompt, user_prompt_template)
- Configurações LLM (provider, model, temperature, max_tokens)
- Configurações RAG (use_rag, query_template, top_k, threshold)
- Knowledge Bases vinculadas (M2M por nome)
- Campos estruturados das seções (section_fields)
- Dependências entre seções (depends_on)
- Configurações de PDF do blueprint (fontes, cores, margens, capa)

### Comandos

```bash
# Local (detecta automaticamente)
./scripts/backup-agents.sh

# Produção
./scripts/backup-agents.sh --env prod

# Apenas agentes (sem blueprints/seções)
./scripts/backup-agents.sh --only-agents

# Restaurar (preview)
./scripts/restore-agents.sh backup_agents_2026-02-19_105159.json --dry-run

# Restaurar (cria novos, não toca existentes)
./scripts/restore-agents.sh backup_agents_2026-02-19_105159.json

# Restaurar (sobrescreve existentes)
./scripts/restore-agents.sh backup_agents_2026-02-19_105159.json --force

# Restaurar em produção
./scripts/restore-agents.sh --env prod backup_agents_2026-02-19_105159.json --force
```

### Onde ficam os arquivos

| Ambiente | Caminho |
|----------|---------|
| Local | `backend/backups/backup_agents_*.json` |
| Produção | `backups/backup_agents_*.json` (volume montado em `/app/backups/`) |

---

## Backup Completo (pg_dump)

```bash
# Backup do banco
./scripts/backup.sh

# Backup do banco + media
./scripts/backup.sh --full

# Restaurar
./scripts/restore.sh backups/db/bravogov_local_20260219.dump
```

### Onde ficam os arquivos

`backups/db/` - dumps do PostgreSQL

---

## Volume Docker (Produção)

O `docker-compose.prod.yml` monta `./backups` em `/app/backups/` no container backend.
Backups gerados dentro do container aparecem automaticamente no host.

```yaml
# docker-compose.prod.yml (trecho)
backend:
  volumes:
    - ./backups:/app/backups
```

---

## Fluxo de Trabalho

```
1. Desenvolve local → edita prompts no admin
2. ./scripts/backup-agents.sh          # Salva estado atual
3. ./scripts/build-and-push.sh         # Build e push Docker Hub
4. [No servidor] ./scripts/deploy.sh   # Pull e sobe containers
5. [No servidor] ./scripts/restore-agents.sh backup_agents_*.json --force
```

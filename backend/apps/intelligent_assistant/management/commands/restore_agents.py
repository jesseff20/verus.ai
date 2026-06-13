"""
Management command para restaurar configuração estrutural a partir de um backup JSON.

Restaura APENAS dados estruturais (agentes, KBs, blueprints, seções).
Preserva: documentos dos usuários (GenerationSession, SectionGeneration, etc.),
          embeddings das KBs (KnowledgeBaseEmbedding / pgvector) e arquivos físicos.

Os embeddings ficam no banco — enquanto o banco não for zerado eles sobrevivem.
Só é necessário reenviar arquivos se o banco foi completamente zerado (DROP DATABASE).

Usage:
    python manage.py restore_agents backup_config_2026-03-17.json
    python manage.py restore_agents backup_config_2026-03-17.json --dry-run
    python manage.py restore_agents backup_config_2026-03-17.json --force
    python manage.py restore_agents backup_config_2026-03-17.json --only-agents
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.intelligent_assistant.models import (
    SectionAgentConfig,
    DocumentBlueprint,
    BlueprintSection,
    KnowledgeBase,
    AgentKnowledgeBaseLink,
)
from apps.core.models import DocumentType


class Command(BaseCommand):
    help = 'Restaura configuração estrutural (agentes, KBs, blueprints, seções) de um backup JSON'

    def add_arguments(self, parser):
        parser.add_argument(
            'file',
            type=str,
            help='Caminho do arquivo JSON de backup',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra o que seria restaurado sem criar nada',
        )
        parser.add_argument(
            '--only-agents',
            action='store_true',
            help='Restaurar apenas agentes e KBs (sem blueprints e seções)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Sobrescrever registros existentes (update_or_create por nome)',
        )

    def handle(self, *args, **options):
        file_path = Path(options['file'])
        dry_run = options['dry_run']
        only_agents = options['only_agents']
        force = options['force']

        if not file_path.is_absolute():
            base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / 'backups'
            file_path = base_dir / file_path

        if not file_path.exists():
            self.stderr.write(self.style.ERROR(f'Arquivo não encontrado: {file_path}'))
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        version = data.get('version', '1.0')
        exported_at = data.get('exported_at', 'desconhecido')

        self.stdout.write(self.style.MIGRATE_HEADING(
            '=' * 70 + '\n'
            f'RESTAURAÇÃO DE CONFIGURAÇÃO ESTRUTURAL\n'
            f'Arquivo: {file_path.name}\n'
            f'Versão:  {version}\n'
            f'Exportado em: {exported_at}\n'
            '=' * 70
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] Nenhum dado será criado\n'))

        agents_data = data.get('agents', [])
        kbs_data = data.get('knowledge_bases', [])
        links_data = data.get('agent_kb_links', [])
        blueprints_data = data.get('blueprints', [])
        sections_data = data.get('sections', [])

        self.stdout.write(
            f'  Agentes no backup:        {len(agents_data)}\n'
            f'  KnowledgeBases no backup: {len(kbs_data)}\n'
            f'  Vínculos agente↔KB:       {len(links_data)}\n'
            f'  Blueprints no backup:     {len(blueprints_data)}\n'
            f'  Seções no backup:         {len(sections_data)}\n'
        )

        if dry_run:
            self._dry_run_report(agents_data, kbs_data, blueprints_data, sections_data, only_agents)
            return

        try:
            with transaction.atomic():
                # Ordem de restauração:
                # Blueprints → KBs → Agentes → KBLinks → Seções
                # (Blueprints primeiro pois KBs layer=blueprint referenciam blueprints)

                blueprint_map = {}
                if not only_agents:
                    self.stdout.write(self.style.MIGRATE_LABEL(
                        f'\n[1/5] Restaurando {len(blueprints_data)} blueprints...'
                    ))
                    blueprint_map = self._restore_blueprints(blueprints_data, force)
                else:
                    self.stdout.write(self.style.WARNING('\n[1/5] Blueprints: pulado (--only-agents)'))

                self.stdout.write(self.style.MIGRATE_LABEL(
                    f'\n[2/5] Restaurando {len(kbs_data)} knowledge bases...'
                ))
                kb_map = self._restore_knowledge_bases(kbs_data, blueprint_map, force)

                self.stdout.write(self.style.MIGRATE_LABEL(
                    f'\n[3/5] Restaurando {len(agents_data)} agentes...'
                ))
                agent_map = self._restore_agents(agents_data, kb_map, force)

                self.stdout.write(self.style.MIGRATE_LABEL(
                    f'\n[4/5] Restaurando {len(links_data)} vínculos agente↔KB...'
                ))
                self._restore_agent_kb_links(links_data, agent_map, kb_map)

                if not only_agents:
                    self.stdout.write(self.style.MIGRATE_LABEL(
                        f'\n[5/5] Restaurando {len(sections_data)} seções...'
                    ))
                    self._restore_sections(sections_data, agent_map, blueprint_map, force)
                else:
                    self.stdout.write(self.style.WARNING('\n[5/5] Seções: pulado (--only-agents)'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'\nERRO na restauração: {e}'))
            self.stderr.write('Nenhum dado foi alterado (rollback automático).')
            raise

        self.stdout.write(self.style.SUCCESS(
            '\n' + '=' * 70 + '\n'
            'Restauração concluída com sucesso!\n'
            'Preservados: documentos dos usuários, embeddings e arquivos das KBs.\n'
            '=' * 70
        ))

    # ──────────────────────────────────────────────
    # KnowledgeBases
    # ──────────────────────────────────────────────

    def _restore_knowledge_bases(self, kbs_data, blueprint_map, force):
        """Cria/atualiza KBs. Retorna mapeamento nome → instância."""
        kb_map = {}
        created = updated = skipped = 0

        for kb_data in kbs_data:
            name = kb_data['name']
            existing = KnowledgeBase.objects.filter(name=name).first()

            if existing and not force:
                kb_map[name] = existing
                skipped += 1
                continue

            # Resolver blueprint pelo nome
            blueprint = None
            bp_name = kb_data.get('blueprint_name')
            if bp_name:
                blueprint = blueprint_map.get(bp_name) or DocumentBlueprint.objects.filter(name=bp_name).first()
                if not blueprint:
                    self.stdout.write(self.style.WARNING(
                        f'    [!] Blueprint "{bp_name}" não encontrado para KB "{name}" — vínculo ignorado'
                    ))

            defaults = {
                'description': kb_data.get('description', ''),
                'kb_layer': kb_data.get('kb_layer', 'global'),
                'blueprint': blueprint,
                'is_active': kb_data.get('is_active', True),
            }

            if existing and force:
                for k, v in defaults.items():
                    setattr(existing, k, v)
                existing.save()
                kb_map[name] = existing
                updated += 1
            else:
                kb = KnowledgeBase.objects.create(name=name, **defaults)
                kb_map[name] = kb
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f'  Criadas: {created} | Atualizadas: {updated} | Puladas: {skipped}'
        ))
        if skipped:
            self.stdout.write(self.style.WARNING(
                f'  Use --force para atualizar as {skipped} KBs existentes.'
            ))
        self.stdout.write(self.style.WARNING(
            '  NOTA: embeddings e arquivos das KBs existentes no banco são preservados.\n'
            '        Só é necessário reenviar arquivos se o banco foi zerado do zero.'
        ))
        return kb_map

    # ──────────────────────────────────────────────
    # Agentes
    # ──────────────────────────────────────────────

    def _restore_agents(self, agents_data, kb_map, force):
        """Restaura agentes e retorna mapeamento nome → instância."""
        agent_map = {}
        created = updated = skipped = 0

        for agent_data in agents_data:
            name = agent_data['name']
            existing = SectionAgentConfig.objects.filter(name=name).first()

            if existing and not force:
                agent_map[name] = existing
                skipped += 1
                continue

            defaults = {
                'description': agent_data.get('description', ''),
                'agent_type': agent_data['agent_type'],
                'system_prompt': agent_data['system_prompt'],
                'user_prompt_template': agent_data['user_prompt_template'],
                'llm_provider': agent_data.get('llm_provider', 'watsonx'),
                'model_name': agent_data.get('model_name', 'mistralai/mistral-medium-2505'),
                'temperature': agent_data.get('temperature', 0.7),
                'max_tokens': agent_data.get('max_tokens', 4000),
                'use_rag': agent_data.get('use_rag', True),
                'rag_query_template': agent_data.get('rag_query_template', ''),
                'rag_top_k': agent_data.get('rag_top_k', 5),
                'rag_similarity_threshold': agent_data.get('rag_similarity_threshold', 0.7),
                'is_active': agent_data.get('is_active', True),
                'is_default': agent_data.get('is_default', False),
            }

            agent, is_new = SectionAgentConfig.objects.update_or_create(
                name=name,
                defaults=defaults,
            )

            # M2M simples (compatibilidade v1.0 e v2.0)
            kb_names = agent_data.get('knowledge_base_names', [])
            if kb_names:
                kbs = KnowledgeBase.objects.filter(name__in=kb_names)
                agent.knowledge_bases.set(kbs)
                missing = set(kb_names) - set(kbs.values_list('name', flat=True))
                if missing:
                    self.stdout.write(self.style.WARNING(
                        f'    [!] KBs não encontradas para "{name}": {missing}'
                    ))

            agent_map[name] = agent
            if is_new:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'  Criados: {created} | Atualizados: {updated} | Pulados: {skipped}'
        ))
        return agent_map

    # ──────────────────────────────────────────────
    # AgentKnowledgeBaseLinks
    # ──────────────────────────────────────────────

    def _restore_agent_kb_links(self, links_data, agent_map, kb_map):
        """Restaura vínculos ricos agente↔KB (AgentKnowledgeBaseLink)."""
        created = updated = skipped = 0

        for link_data in links_data:
            agent = agent_map.get(link_data['agent_name'])
            kb = kb_map.get(link_data['kb_name'])

            if not agent:
                self.stdout.write(self.style.WARNING(
                    f'    [!] Agente não encontrado: "{link_data["agent_name"]}" — vínculo ignorado'
                ))
                skipped += 1
                continue
            if not kb:
                self.stdout.write(self.style.WARNING(
                    f'    [!] KB não encontrada: "{link_data["kb_name"]}" — vínculo ignorado'
                ))
                skipped += 1
                continue

            _, is_new = AgentKnowledgeBaseLink.objects.update_or_create(
                agent=agent,
                knowledge_base=kb,
                defaults={
                    'priority': link_data.get('priority', 0),
                    'purpose': link_data.get('purpose', 'reference'),
                    'instruction': link_data.get('instruction', ''),
                    'top_k': link_data.get('top_k', 5),
                    'min_similarity': link_data.get('min_similarity', 0.6),
                    'include_summary': link_data.get('include_summary', False),
                    'selected_sources': link_data.get('selected_sources', []),
                    'is_active': link_data.get('is_active', True),
                },
            )
            if is_new:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'  Criados: {created} | Atualizados: {updated} | Pulados/ignorados: {skipped}'
        ))

    # ──────────────────────────────────────────────
    # Blueprints
    # ──────────────────────────────────────────────

    def _restore_blueprints(self, blueprints_data, force):
        blueprint_map = {}
        created = updated = skipped = 0

        for bp_data in blueprints_data:
            name = bp_data['name']
            existing = DocumentBlueprint.objects.filter(name=name).first()

            if existing and not force:
                blueprint_map[name] = existing
                skipped += 1
                continue

            doc_type_code = bp_data.get('document_type_code')
            doc_type = None
            if doc_type_code:
                try:
                    doc_type = DocumentType.objects.get(code=doc_type_code)
                except DocumentType.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f'    [!] DocumentType "{doc_type_code}" não encontrado para "{name}"'
                    ))
                    continue

            defaults = {
                'description': bp_data.get('description', ''),
                'version': bp_data.get('version', '1.0'),
                'legal_basis': bp_data.get('legal_basis', ''),
                'metadata': bp_data.get('metadata', {}),
                'organization_name': bp_data.get('organization_name', ''),
                'organization_acronym': bp_data.get('organization_acronym', ''),
                'header_text': bp_data.get('header_text', ''),
                'footer_text': bp_data.get('footer_text', ''),
                'primary_color': bp_data.get('primary_color', '#7030A0'),
                'secondary_color': bp_data.get('secondary_color', '#5B2EE0'),
                'custom_css': bp_data.get('custom_css', ''),
                'cover_page_enabled': bp_data.get('cover_page_enabled', True),
                'cover_title': bp_data.get('cover_title', ''),
                'cover_subtitle': bp_data.get('cover_subtitle', ''),
                'cover_organization_text': bp_data.get('cover_organization_text', ''),
                'cover_footer_text': bp_data.get('cover_footer_text', ''),
                'cover_background_color': bp_data.get('cover_background_color', '#FFFFFF'),
                'pdf_font_family': bp_data.get('pdf_font_family', 'Times New Roman'),
                'pdf_font_size': bp_data.get('pdf_font_size', '12pt'),
                'pdf_line_height': bp_data.get('pdf_line_height', '1.5'),
                'pdf_text_align': bp_data.get('pdf_text_align', 'justify'),
                'pdf_paragraph_indent': bp_data.get('pdf_paragraph_indent', '1.5cm'),
                'pdf_paragraph_spacing': bp_data.get('pdf_paragraph_spacing', '12pt'),
                'pdf_page_margin_top': bp_data.get('pdf_page_margin_top', '2.5cm'),
                'pdf_page_margin_bottom': bp_data.get('pdf_page_margin_bottom', '2.5cm'),
                'pdf_page_margin_left': bp_data.get('pdf_page_margin_left', '3cm'),
                'pdf_page_margin_right': bp_data.get('pdf_page_margin_right', '2cm'),
                'is_active': bp_data.get('is_active', True),
                'is_default': bp_data.get('is_default', False),
            }

            if existing and force:
                for k, v in defaults.items():
                    setattr(existing, k, v)
                if doc_type:
                    existing.document_type = doc_type
                existing.save()
                blueprint_map[name] = existing
                updated += 1
            else:
                if not doc_type:
                    self.stdout.write(self.style.ERROR(
                        f'    [ERRO] Não é possível criar "{name}" sem DocumentType'
                    ))
                    continue
                bp = DocumentBlueprint.objects.create(name=name, document_type=doc_type, **defaults)
                blueprint_map[name] = bp
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f'  Criados: {created} | Atualizados: {updated} | Pulados: {skipped}'
        ))
        return blueprint_map

    # ──────────────────────────────────────────────
    # Seções
    # ──────────────────────────────────────────────

    def _restore_sections(self, sections_data, agent_map, blueprint_map, force):
        created = updated = skipped = 0
        sections_with_deps = []

        for section_data in sections_data:
            bp_name = section_data['blueprint_name']
            blueprint = blueprint_map.get(bp_name)

            if not blueprint:
                self.stdout.write(self.style.WARNING(
                    f'    [!] Blueprint "{bp_name}" não encontrado, '
                    f'pulando seção {section_data["section_number"]} - {section_data["section_name"]}'
                ))
                skipped += 1
                continue

            gen_agent = agent_map.get(section_data.get('generator_agent_name'))
            val_agent = agent_map.get(section_data.get('validator_agent_name'))

            existing = BlueprintSection.objects.filter(
                blueprint=blueprint,
                section_key=section_data['section_key'],
            ).first()

            if existing and not force:
                skipped += 1
                if section_data.get('depends_on_keys'):
                    sections_with_deps.append((existing, section_data['depends_on_keys'], bp_name))
                continue

            defaults = {
                'section_number': section_data['section_number'],
                'section_name': section_data['section_name'],
                'description': section_data.get('description', ''),
                'instructions': section_data.get('instructions', ''),
                'legal_reference': section_data.get('legal_reference', ''),
                'generator_agent': gen_agent,
                'validator_agent': val_agent,
                'order': section_data.get('order', 0),
                'is_required': section_data.get('is_required', True),
                'allow_skip': section_data.get('allow_skip', True),
                'max_generation_attempts': section_data.get('max_generation_attempts', 3),
                'section_fields': section_data.get('section_fields', []),
                'is_active': section_data.get('is_active', True),
            }

            if existing and force:
                for k, v in defaults.items():
                    setattr(existing, k, v)
                existing.save()
                section = existing
                updated += 1
            else:
                section = BlueprintSection.objects.create(
                    blueprint=blueprint,
                    section_key=section_data['section_key'],
                    **defaults,
                )
                created += 1

            if section_data.get('depends_on_keys'):
                sections_with_deps.append((section, section_data['depends_on_keys'], bp_name))

            if section_data.get('generator_agent_name') and not gen_agent:
                self.stdout.write(self.style.WARNING(
                    f'    [!] Gerador não encontrado: "{section_data["generator_agent_name"]}"'
                ))
            if section_data.get('validator_agent_name') and not val_agent:
                self.stdout.write(self.style.WARNING(
                    f'    [!] Validador não encontrado: "{section_data["validator_agent_name"]}"'
                ))

        if sections_with_deps:
            self.stdout.write(self.style.MIGRATE_LABEL(
                f'\n  Resolvendo dependências de {len(sections_with_deps)} seções...'
            ))
            for section, deps_keys, bp_name in sections_with_deps:
                blueprint = blueprint_map.get(bp_name)
                if not blueprint:
                    continue
                dep_sections = BlueprintSection.objects.filter(
                    blueprint=blueprint,
                    section_key__in=deps_keys,
                )
                section.depends_on.set(dep_sections)

        self.stdout.write(self.style.SUCCESS(
            f'  Criadas: {created} | Atualizadas: {updated} | Puladas: {skipped}'
        ))

    # ──────────────────────────────────────────────
    # Dry run
    # ──────────────────────────────────────────────

    def _dry_run_report(self, agents_data, kbs_data, blueprints_data, sections_data, only_agents):
        self.stdout.write(self.style.MIGRATE_LABEL('\n── KnowledgeBases ──'))
        for kb in kbs_data:
            exists = KnowledgeBase.objects.filter(name=kb['name']).exists()
            status = 'EXISTE' if exists else 'NOVA'
            n = len(kb.get('source_files', []))
            self.stdout.write(
                f'  [{status}] [{kb["kb_layer"]}] {kb["name"]} ({n} arquivo(s))'
            )

        self.stdout.write(self.style.MIGRATE_LABEL('\n── Agentes ──'))
        for agent in agents_data:
            exists = SectionAgentConfig.objects.filter(name=agent['name']).exists()
            status = 'EXISTE' if exists else 'NOVO'
            self.stdout.write(
                f'  [{status}] [{agent["agent_type"][:3].upper()}] {agent["name"]}'
            )

        if not only_agents:
            self.stdout.write(self.style.MIGRATE_LABEL('\n── Blueprints ──'))
            for bp in blueprints_data:
                exists = DocumentBlueprint.objects.filter(name=bp['name']).exists()
                status = 'EXISTE' if exists else 'NOVO'
                self.stdout.write(f'  [{status}] {bp["name"]}')

            self.stdout.write(self.style.MIGRATE_LABEL('\n── Seções ──'))
            current_bp = None
            for section in sections_data:
                if section['blueprint_name'] != current_bp:
                    current_bp = section['blueprint_name']
                    self.stdout.write(f'\n  {current_bp}:')
                gen = '✓' if section.get('generator_agent_name') else '✗'
                val = '✓' if section.get('validator_agent_name') else '✗'
                self.stdout.write(
                    f'    {section["section_number"]:02d}. {section["section_name"][:45]}'
                    f' | Gen: {gen} | Val: {val}'
                )

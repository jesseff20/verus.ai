"""
Management command para exportar configuração estrutural do sistema para JSON.

Exporta: agentes, knowledge bases (metadata), blueprints, seções e vínculos agente↔KB.
NÃO exporta: sessões de usuários, seções geradas, documentos exportados, arquivos físicos das KBs.

Usage:
    python manage.py backup_agents
    python manage.py backup_agents --output /caminho/custom.json
    python manage.py backup_agents --only-agents   # Apenas agentes + KBs (sem blueprints/seções)
"""
import json
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from apps.intelligent_assistant.models import (
    SectionAgentConfig,
    DocumentBlueprint,
    BlueprintSection,
    KnowledgeBase,
    AgentKnowledgeBaseLink,
)


class Command(BaseCommand):
    help = 'Exporta configuração estrutural (agentes, KBs, blueprints, seções) para JSON'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output', '-o',
            type=str,
            default=None,
            help='Caminho do arquivo de saída (default: backups/backup_config_YYYY-MM-DD_HHMMSS.json)',
        )
        parser.add_argument(
            '--only-agents',
            action='store_true',
            help='Exportar apenas agentes e KBs (sem blueprints e seções)',
        )

    def handle(self, *args, **options):
        only_agents = options['only_agents']
        now = datetime.now()
        timestamp = now.strftime('%Y-%m-%d_%H%M%S')

        if options['output']:
            output_path = Path(options['output'])
        else:
            base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / 'backups'
            base_dir.mkdir(parents=True, exist_ok=True)
            output_path = base_dir / f'backup_config_{timestamp}.json'

        self.stdout.write(self.style.MIGRATE_HEADING(
            '=' * 70 + '\n'
            'BACKUP DE CONFIGURAÇÃO ESTRUTURAL\n'
            '(agentes, KBs, blueprints, seções)\n'
            '=' * 70
        ))

        data = {
            'exported_at': now.isoformat(),
            'version': '2.0',
        }

        # ── 1. Agentes ──
        agents = SectionAgentConfig.objects.prefetch_related('knowledge_bases').all().order_by('agent_type', 'name')
        agents_data = []

        for agent in agents:
            agents_data.append({
                'id': str(agent.id),
                'name': agent.name,
                'description': agent.description,
                'agent_type': agent.agent_type,
                'system_prompt': agent.system_prompt,
                'user_prompt_template': agent.user_prompt_template,
                'llm_provider': agent.llm_provider,
                'model_name': agent.model_name,
                'temperature': agent.temperature,
                'max_tokens': agent.max_tokens,
                'use_rag': agent.use_rag,
                'rag_query_template': agent.rag_query_template,
                'rag_top_k': agent.rag_top_k,
                'rag_similarity_threshold': agent.rag_similarity_threshold,
                'is_active': agent.is_active,
                'is_default': agent.is_default,
                'knowledge_base_names': list(
                    agent.knowledge_bases.values_list('name', flat=True)
                ),
            })

        data['agents'] = agents_data
        generators = sum(1 for a in agents_data if a['agent_type'] == 'generator')
        validators = sum(1 for a in agents_data if a['agent_type'] == 'validator')
        self.stdout.write(self.style.SUCCESS(
            f'  [+] {len(agents_data)} agentes '
            f'(geradores: {generators} | validadores: {validators})'
        ))

        # ── 2. KnowledgeBases (metadata apenas, sem arquivos binários) ──
        kbs = KnowledgeBase.objects.select_related(
            'blueprint', 'agent_config', 'section'
        ).prefetch_related('source_files').all()
        kbs_data = []

        for kb in kbs:
            kbs_data.append({
                'id': str(kb.id),
                'name': kb.name,
                'description': kb.description,
                'kb_layer': kb.kb_layer,
                'blueprint_name': kb.blueprint.name if kb.blueprint else None,
                'agent_config_name': kb.agent_config.name if kb.agent_config else None,
                'section_key': kb.section.section_key if kb.section else None,
                'is_active': kb.is_active,
                # Metadata dos arquivos (apenas referência — sem binários)
                'source_files': [
                    {
                        'file_name': f.file_name,
                        'file_size': f.file_size,
                        'file_type': f.file_type,
                        'category': f.category,
                        'tags': f.tags,
                        'chunk_count': f.chunk_count,
                        'status': f.status,
                    }
                    for f in kb.source_files.all()
                ],
            })

        data['knowledge_bases'] = kbs_data
        self.stdout.write(self.style.SUCCESS(
            f'  [+] {len(kbs_data)} knowledge bases'
        ))
        for kb in kbs_data:
            n = len(kb['source_files'])
            self.stdout.write(f'      [{kb["kb_layer"]}] {kb["name"]}: {n} arquivo(s)')

        # ── 3. Vínculos Agente↔KB (AgentKnowledgeBaseLink) ──
        links = AgentKnowledgeBaseLink.objects.select_related(
            'agent', 'knowledge_base'
        ).all().order_by('agent__name', 'priority')
        links_data = []

        for link in links:
            links_data.append({
                'agent_name': link.agent.name,
                'kb_name': link.knowledge_base.name,
                'priority': link.priority,
                'purpose': link.purpose,
                'instruction': link.instruction,
                'top_k': link.top_k,
                'min_similarity': link.min_similarity,
                'include_summary': link.include_summary,
                'selected_sources': link.selected_sources,
                'is_active': link.is_active,
            })

        data['agent_kb_links'] = links_data
        self.stdout.write(self.style.SUCCESS(
            f'  [+] {len(links_data)} vínculos agente↔KB'
        ))

        if not only_agents:
            # ── 4. Blueprints ──
            blueprints = DocumentBlueprint.objects.all().order_by('name')
            blueprints_data = []

            for bp in blueprints:
                blueprints_data.append({
                    'id': str(bp.id),
                    'name': bp.name,
                    'description': bp.description,
                    'document_type_code': bp.document_type.code if bp.document_type else None,
                    'version': bp.version,
                    'legal_basis': bp.legal_basis,
                    'metadata': bp.metadata,
                    'organization_name': bp.organization_name,
                    'organization_acronym': bp.organization_acronym,
                    'header_text': bp.header_text,
                    'footer_text': bp.footer_text,
                    'primary_color': bp.primary_color,
                    'secondary_color': bp.secondary_color,
                    'custom_css': bp.custom_css,
                    'cover_page_enabled': bp.cover_page_enabled,
                    'cover_title': bp.cover_title,
                    'cover_subtitle': bp.cover_subtitle,
                    'cover_organization_text': bp.cover_organization_text,
                    'cover_footer_text': bp.cover_footer_text,
                    'cover_background_color': bp.cover_background_color,
                    'pdf_font_family': bp.pdf_font_family,
                    'pdf_font_size': bp.pdf_font_size,
                    'pdf_line_height': bp.pdf_line_height,
                    'pdf_text_align': bp.pdf_text_align,
                    'pdf_paragraph_indent': bp.pdf_paragraph_indent,
                    'pdf_paragraph_spacing': bp.pdf_paragraph_spacing,
                    'pdf_page_margin_top': bp.pdf_page_margin_top,
                    'pdf_page_margin_bottom': bp.pdf_page_margin_bottom,
                    'pdf_page_margin_left': bp.pdf_page_margin_left,
                    'pdf_page_margin_right': bp.pdf_page_margin_right,
                    'is_active': bp.is_active,
                    'is_default': bp.is_default,
                })

            data['blueprints'] = blueprints_data
            self.stdout.write(self.style.SUCCESS(
                f'  [+] {len(blueprints_data)} blueprints'
            ))

            # ── 5. Seções ──
            sections = BlueprintSection.objects.select_related(
                'blueprint', 'generator_agent', 'validator_agent'
            ).prefetch_related('depends_on').all().order_by('blueprint__name', 'order', 'section_number')
            sections_data = []

            for section in sections:
                sections_data.append({
                    'id': str(section.id),
                    'blueprint_name': section.blueprint.name,
                    'section_number': section.section_number,
                    'section_name': section.section_name,
                    'section_key': section.section_key,
                    'description': section.description,
                    'instructions': section.instructions,
                    'legal_reference': section.legal_reference,
                    'generator_agent_name': section.generator_agent.name if section.generator_agent else None,
                    'validator_agent_name': section.validator_agent.name if section.validator_agent else None,
                    'depends_on_keys': list(
                        section.depends_on.values_list('section_key', flat=True)
                    ),
                    'order': section.order,
                    'is_required': section.is_required,
                    'allow_skip': section.allow_skip,
                    'max_generation_attempts': section.max_generation_attempts,
                    'section_fields': section.section_fields,
                    'is_active': section.is_active,
                })

            data['sections'] = sections_data
            self.stdout.write(self.style.SUCCESS(
                f'  [+] {len(sections_data)} seções'
            ))
            bp_counts = {}
            for s in sections_data:
                bp_counts[s['blueprint_name']] = bp_counts.get(s['blueprint_name'], 0) + 1
            for bp_name, count in bp_counts.items():
                self.stdout.write(f'      {bp_name}: {count} seções')

        # ── Salvar ──
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        size_kb = output_path.stat().st_size / 1024
        self.stdout.write(self.style.SUCCESS(
            '\n' + '=' * 70 + '\n'
            f'Backup salvo em:\n{output_path}\n'
            f'Tamanho: {size_kb:.1f} KB\n'
            '=' * 70
        ))

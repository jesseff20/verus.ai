"""
Management command para migrar agentes de formulário de AgentPrompt para FormAssistant
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.agents.models import AgentPrompt
from apps.forms.models import FormAssistant


class Command(BaseCommand):
    help = 'Migra agentes de formulário (form_assistant) de AgentPrompt para FormAssistant'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a migração sem alterar o banco de dados',
        )
        parser.add_argument(
            '--delete-old',
            action='store_true',
            help='Deleta os AgentPrompt antigos após a migração',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        delete_old = options['delete_old']

        if dry_run:
            self.stdout.write(self.style.WARNING('=== MODO DRY-RUN (simulação) ===\n'))

        # Buscar todos os form_assistant EXCETO o "Assistente de Licitações"
        old_agents = AgentPrompt.objects.filter(category='form_assistant').exclude(
            agent_type='chat_assistant'
        )

        total_count = old_agents.count()
        self.stdout.write(f'\nEncontrados {total_count} agentes form_assistant para migrar:\n')

        # Listar agentes que serão migrados
        for agent in old_agents:
            self.stdout.write(f'  - {agent.name} (tipo: {agent.agent_type})')

        if total_count == 0:
            self.stdout.write(self.style.WARNING('\nNenhum agente para migrar.'))
            return

        if not dry_run:
            confirm = input(f'\nDeseja prosseguir com a migração de {total_count} agentes? (s/N): ')
            if confirm.lower() != 's':
                self.stdout.write(self.style.ERROR('Migração cancelada.'))
                return

        self.stdout.write('\n' + '='*60)
        self.stdout.write('INICIANDO MIGRAÇÃO...\n')

        migrated_count = 0
        errors = []
        first_default = True  # Apenas o primeiro será marcado como default

        with transaction.atomic():
            for old_agent in old_agents:
                try:
                    self.stdout.write(f'\nMigrando: {old_agent.name}')

                    # Verificar se já existe
                    existing = FormAssistant.objects.filter(
                        name=old_agent.name,
                        assistant_type=old_agent.agent_type
                    ).first()

                    if existing:
                        self.stdout.write(
                            self.style.WARNING(f'  ⚠️  Já existe FormAssistant com mesmo nome/tipo. Pulando...')
                        )
                        continue

                    if not dry_run:
                        # Determinar se este será o default
                        # Apenas o primeiro migrado pode ser default com field_id vazio
                        is_default_for_new = first_default and old_agent.is_default
                        if is_default_for_new:
                            first_default = False

                        # Criar novo FormAssistant
                        new_assistant = FormAssistant.objects.create(
                            name=old_agent.name,
                            description=old_agent.description,
                            assistant_type=old_agent.agent_type,
                            field_id='',  # Vazio - será configurado no campo do formulário
                            system_prompt=old_agent.system_prompt,
                            user_prompt_template=old_agent.user_prompt_template,
                            llm_provider=old_agent.llm_provider,
                            model_name=old_agent.model_name,
                            temperature=old_agent.temperature,
                            max_tokens=old_agent.max_tokens,
                            use_rag=old_agent.use_rag,
                            rag_query_template=old_agent.rag_query_template,
                            icon=old_agent.icon,
                            color=old_agent.color,
                            display_order=old_agent.display_order,
                            is_active=old_agent.is_active,
                            is_default=is_default_for_new,  # Apenas primeiro pode ser default
                            created_by=old_agent.created_by
                        )
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Criado FormAssistant ID: {new_assistant.id}')
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ [DRY-RUN] Seria criado FormAssistant')
                        )

                    migrated_count += 1

                except Exception as e:
                    error_msg = f'Erro ao migrar {old_agent.name}: {str(e)}'
                    errors.append(error_msg)
                    self.stdout.write(self.style.ERROR(f'  ✗ {error_msg}'))

            # Deletar agentes antigos se solicitado
            if delete_old and not dry_run:
                self.stdout.write('\n' + '='*60)
                self.stdout.write('DELETANDO AGENTES ANTIGOS...\n')

                deleted_count = 0
                for old_agent in old_agents:
                    try:
                        agent_name = old_agent.name
                        old_agent.delete()
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Deletado: {agent_name}'))
                        deleted_count += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  ✗ Erro ao deletar {old_agent.name}: {str(e)}'))

                self.stdout.write(f'\nTotal deletados: {deleted_count}')

            if dry_run:
                # Rollback em dry-run
                transaction.set_rollback(True)

        # Sumário final
        self.stdout.write('\n' + '='*60)
        self.stdout.write('SUMÁRIO DA MIGRAÇÃO:\n')
        self.stdout.write(f'  Total encontrados: {total_count}')
        self.stdout.write(f'  Migrados com sucesso: {migrated_count}')
        self.stdout.write(f'  Erros: {len(errors)}')

        if errors:
            self.stdout.write('\nERROS:')
            for error in errors:
                self.stdout.write(self.style.ERROR(f'  - {error}'))

        if dry_run:
            self.stdout.write(self.style.WARNING('\n*** DRY-RUN: Nenhuma alteração foi feita no banco ***'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ Migração concluída com sucesso!'))
            self.stdout.write('\nPróximos passos:')
            self.stdout.write('  1. Acesse o Django Admin em /admin/forms/formassistant/')
            self.stdout.write('  2. Configure field_id específicos se necessário')
            if not delete_old:
                self.stdout.write('  3. Execute novamente com --delete-old para remover AgentPrompt antigos')

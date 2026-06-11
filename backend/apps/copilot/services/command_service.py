"""
CommandService - Processa comandos @ no Copilot.

Comandos disponíveis:
- @jurisprudencia - Pesquisa jurisprudência
- @documento - Opera em documentos (versões, diff)
- @argumentos - Busca argumentos na biblioteca viva
- @colaboracao - Gerencia sessões colaborativas
- @tribunal - Integração com tribunais
- @peticao - Protocola petições
- @caso - Opera em casos/processos
- @agendar - Agendar lembrete (ex: @agendar 3 dias - Revisar caso)
- @agendar_recorrente - Agendar lembrete recorrente
- @meus_casos - Ver casos ativos com prazos
- @meus_prazos - Ver prazos pendentes
- @meus_lembretes - Ver lembretes agendados
- @gerar - Gerar peça para caso (ex: @gerar reclamacao trabalhista para Costa vs TransLog)
- @blueprints_caso - Blueprints sugeridos para um caso
- @criar_sessao - Criar sessão para caso com blueprint específico
"""
import logging
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import timedelta

from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Resultado da execução de um comando @"""
    success: bool
    command: str
    data: Any
    message: str
    error: Optional[str] = None


class CommandService:
    """Serviço para processar comandos @ no Copilot"""

    # Mapeamento de comandos para descrições
    COMMANDS_INFO = {
        'jurisprudencia': 'Pesquisa jurisprudência e precedentes',
        'documento': 'Gerencia versões de documentos',
        'argumentos': 'Busca argumentos na biblioteca viva',
        'colaboracao': 'Gerencia sessões colaborativas',
        'tribunal': 'Integração com tribunais',
        'peticao': 'Protocola petições eletrônicas',
        'caso': 'Gerencia casos e processos',
        'prazo': 'Consulta prazos processuais',
        'modelo': 'Busca modelos de peças',
        'resumo': 'Gera resumo de documentos com IA',
        'traduzir': 'Traduzir textos jurídicos',
        'revisar': 'Revisar peças jurídicas',
        'citar': 'Gerar citações e referências',
        'expandir': 'Expandir tópicos em texto completo',
        'blueprint': 'Listar blueprints disponíveis por área',
        'legislacao': 'Buscar legislação oficial na internet',
        'simulacao': 'Informações sobre simulações jurídicas disponíveis',
        'agendar': 'Agendar lembrete (ex: @agendar 3 dias - Revisar caso)',
        'agendar_recorrente': 'Agendar lembrete recorrente',
        'meus_casos': 'Ver seus casos ativos com prazos',
        'meus_prazos': 'Ver todos os prazos pendentes',
        'meus_lembretes': 'Ver lembretes agendados',
        'gerar': 'Gerar peça para caso (ex: @gerar reclamacao trabalhista para Costa vs TransLog)',
        'blueprints_caso': 'Blueprints sugeridos para um caso',
        'criar_sessao': 'Criar sessão para caso com blueprint específico',
        'notificar': 'Enviar notificação via WhatsApp (ex: @notificar whatsapp +5521999998888 - Prazo vence amanhã)',
    }

    def __init__(self, user):
        self.user = user

    def parse_command(self, message: str) -> Optional[tuple]:
        """
        Extrai comando @ da mensagem.
        Retorna (command, args) ou None se não houver comando.
        """
        if '@' not in message:
            return None

        # Encontrar primeiro @
        at_index = message.index('@')
        rest = message[at_index + 1:].strip()

        if not rest:
            return None

        # Extrair nome do comando (até primeiro espaço ou fim)
        parts = rest.split(None, 1)
        command = parts[0].lower().strip()
        args = parts[1] if len(parts) > 1 else ''

        # Remover caracteres inválidos do comando
        command = ''.join(c for c in command if c.isalnum() or c == '_')

        if not command:
            return None

        return (command, args, message)

    async def execute_command(self, command: str, args: str, full_message: str) -> CommandResult:
        """
        Executa um comando @ com os argumentos fornecidos.
        """
        command_handlers = {
            'jurisprudencia': self._handle_jurisprudencia,
            'documento': self._handle_documento,
            'argumentos': self._handle_argumentos,
            'colaboracao': self._handle_colaboracao,
            'tribunal': self._handle_tribunal,
            'peticao': self._handle_peticao,
            'caso': self._handle_caso,
            'prazo': self._handle_prazo,
            'modelo': self._handle_modelo,
            'resumo': self._handle_resumo,
            'traduzir': self._handle_traduzir,
            'revisar': self._handle_revisar,
            'citar': self._handle_citar,
            'expandir': self._handle_expandir,
            'blueprint': self._handle_blueprint,
            'legislacao': self._handle_legislacao,
            'simulacao': self._handle_simulacao,
            'agendar': self._handle_agendar,
            'agendar_recorrente': self._handle_agendar_recorrente,
            'meus_casos': self._handle_meus_casos,
            'meus_prazos': self._handle_meus_prazos,
            'meus_lembretes': self._handle_meus_lembretes,
            'gerar': self._handle_gerar,
            'blueprints_caso': self._handle_blueprints_caso,
            'criar_sessao': self._handle_criar_sessao,
            'notificar': self._handle_notificar,
        }

        handler = command_handlers.get(command)
        if not handler:
            return CommandResult(
                success=False,
                command=command,
                data=None,
                message='',
                error=f'Comando @{command} não reconhecido. Comandos disponíveis: {", ".join(self.COMMANDS_INFO.keys())}'
            )

        try:
            return await handler(args, full_message)
        except Exception as e:
            logger.exception(f'[copilot] Erro ao executar comando @{command}: {e}')
            return CommandResult(
                success=False,
                command=command,
                data=None,
                message='',
                error=f'Erro ao executar @{command}: {str(e)}'
            )

    async def _handle_jurisprudencia(self, args: str, full_message: str) -> CommandResult:
        """Pesquisa jurisprudência"""
        from apps.jurisprudence.services import JurisprudenceService

        # Extrair query dos argumentos ou da mensagem
        query = args.strip() if args else full_message.split('@jurisprudencia', 1)[1].strip()

        if not query:
            return CommandResult(
                success=False,
                command='jurisprudencia',
                data=None,
                message='',
                error='Informe os termos da pesquisa. Ex: @jurisprudencia dano moral transporte público'
            )

        try:
            service = JurisprudenceService()
            results = service.search(query, limit=5)

            if not results:
                return CommandResult(
                    success=True,
                    command='jurisprudencia',
                    data=[],
                    message=f'Nenhum precedente encontrado para "{query}"'
                )

            formatted = []
            for r in results[:5]:
                formatted.append({
                    'titulo': r.get('titulo', 'Sem título'),
                    'tribunal': r.get('tribunal', 'Desconhecido'),
                    'classe': r.get('classe_juridica', ''),
                    'ementa': r.get('ementa', '')[:300],
                    'data': r.get('data_julgamento', ''),
                })

            return CommandResult(
                success=True,
                command='jurisprudencia',
                data=formatted,
                message=f'Encontrados {len(formatted)} precedentes para "{query}"'
            )

        except Exception as e:
            return CommandResult(
                success=False,
                command='jurisprudencia',
                data=None,
                message='',
                error=f'Erro na pesquisa: {str(e)}'
            )

    async def _handle_documento(self, args: str, full_message: str) -> CommandResult:
        """Opera em documentos - versões, diff, rollback"""
        from apps.documents.services.version_control_service import VersionControlService

        # Parse: @documento <doc_id> <acao> [args]
        parts = args.split(None, 2)

        if len(parts) < 2:
            return CommandResult(
                success=False,
                command='documento',
                data=None,
                message='',
                error='Uso: @documento <id> <acao>. Ações: versoes, diff, rollback'
            )

        doc_id = parts[0]
        action = parts[1].lower()

        try:
            service = VersionControlService()

            if action == 'versoes':
                # Listar versões
                versions = service.get_versions()
                return CommandResult(
                    success=True,
                    command='documento',
                    data=[{
                        'version': v.version_number,
                        'type': v.version_type,
                        'created_at': v.created_at,
                        'summary': v.change_summary,
                    } for v in versions],
                    message=f'Documento possui {len(versions)} versões'
                )

            elif action == 'diff':
                # Diff entre versões
                if len(parts) < 3:
                    return CommandResult(
                        success=False,
                        command='documento',
                        data=None,
                        message='',
                        error='Uso: @documento <id> diff <v1> <v2>'
                    )
                diff_parts = parts[2].split()
                if len(diff_parts) < 2:
                    return CommandResult(
                        success=False,
                        command='documento',
                        data=None,
                        message='',
                        error='Informe duas versões para diff. Ex: @documento abc diff 1.0.0 1.1.0'
                    )

                diff = service.get_diff(diff_parts[0], diff_parts[1])
                return CommandResult(
                    success=True,
                    command='documento',
                    data={
                        'old_version': diff.old_version,
                        'new_version': diff.new_version,
                        'changes': diff.changes,
                        'summary': diff.summary,
                    },
                    message=diff.summary
                )

            else:
                return CommandResult(
                    success=False,
                    command='documento',
                    data=None,
                    message='',
                    error=f'Ação "{action}" não reconhecida. Use: versoes, diff'
                )

        except Exception as e:
            return CommandResult(
                success=False,
                command='documento',
                data=None,
                message='',
                error=f'Erro: {str(e)}'
            )

    async def _handle_argumentos(self, args: str, full_message: str) -> CommandResult:
        """Busca argumentos na biblioteca viva"""
        from apps.legal_library.models import LegalArgument

        query = args.strip()

        if not query:
            return CommandResult(
                success=False,
                command='argumentos',
                data=None,
                message='',
                error='Informe termos da busca. Ex: @argumentos prescrição penal'
            )

        try:
            # Buscar por título ou conteúdo
            argumentos = LegalArgument.objects.filter(
                models.Q(title__icontains=query) | models.Q(content__icontains=query)
            ).order_by('-effectiveness_score')[:10]

            if not argumentos:
                return CommandResult(
                    success=True,
                    command='argumentos',
                    data=[],
                    message=f'Nenhum argumento encontrado para "{query}"'
                )

            formatted = [{
                'id': str(arg.id),
                'titulo': arg.title,
                'categoria': arg.category,
                'especialidade': arg.specialty,
                'efetividade': f'{arg.effectiveness_score:.1%}',
                'usos': arg.usage_count,
                'sucessos': arg.success_count,
            } for arg in argumentos]

            return CommandResult(
                success=True,
                command='argumentos',
                data=formatted,
                message=f'Encontrados {len(formatted)} argumentos para "{query}"'
            )

        except Exception as e:
            return CommandResult(
                success=False,
                command='argumentos',
                data=None,
                message='',
                error=f'Erro na busca: {str(e)}'
            )

    async def _handle_colaboracao(self, args: str, full_message: str) -> CommandResult:
        """Gerencia sessões colaborativas"""
        from apps.collaboration.models import CollaborationSession

        parts = args.split(None, 1)
        action = parts[0].lower() if parts else 'listar'

        try:
            if action in ['listar', 'lista', 'ls']:
                sessoes = CollaborationSession.objects.filter(
                    status='active'
                ).order_by('-created_at')[:10]

                formatted = [{
                    'id': str(s.id),
                    'documento': s.document_id,
                    'tipo': s.document_type,
                    'colaboradores': s.get_collaborator_count(),
                    'status': s.status,
                } for s in sessoes]

                return CommandResult(
                    success=True,
                    command='colaboracao',
                    data=formatted,
                    message=f'{len(formatted)} sessões ativas'
                )

            elif action in ['criar', 'novo', 'new']:
                if len(parts) < 2:
                    return CommandResult(
                        success=False,
                        command='colaboracao',
                        data=None,
                        message='',
                        error='Uso: @colaboracao criar <doc_id> [tipo]'
                    )

                doc_parts = parts[1].split()
                doc_id = doc_parts[0]
                doc_type = doc_parts[1] if len(doc_parts) > 1 else 'legal'

                sessao = CollaborationSession.objects.create(
                    document_id=doc_id,
                    document_type=doc_type,
                    created_by=self.user
                )

                return CommandResult(
                    success=True,
                    command='colaboracao',
                    data={'id': str(sessao.id), 'status': 'active'},
                    message=f'Sessão {sessao.id} criada com sucesso'
                )

            else:
                return CommandResult(
                    success=False,
                    command='colaboracao',
                    data=None,
                    message='',
                    error=f'Ação "{action}" não reconhecida. Use: listar, criar'
                )

        except Exception as e:
            return CommandResult(
                success=False,
                command='colaboracao',
                data=None,
                message='',
                error=f'Erro: {str(e)}'
            )

    async def _handle_tribunal(self, args: str, full_message: str) -> CommandResult:
        """Integração com tribunais"""
        from apps.integration.models import TribunalIntegration

        parts = args.split(None, 1)
        action = parts[0].lower() if parts else 'listar'

        try:
            if action in ['listar', 'lista', 'ls']:
                tribunais = TribunalIntegration.objects.all().order_by('name')

                formatted = [{
                    'id': str(t.id),
                    'nome': t.name,
                    'codigo': t.code,
                    'sistema': t.system_type,
                    'status': t.connection_status,
                } for t in tribunais]

                return CommandResult(
                    success=True,
                    command='tribunal',
                    data=formatted,
                    message=f'{len(formatted)} tribunais configurados'
                )

            elif action in ['sincronizar', 'sync']:
                if len(parts) < 2:
                    return CommandResult(
                        success=False,
                        command='tribunal',
                        data=None,
                        message='',
                        error='Uso: @tribunal sincronizar <num_processo>'
                    )

                process_number = parts[1].strip()

                # Import aqui para evitar circular import
                from apps.integration.services.esaj_service import get_tribunal_service

                # Pegar primeiro tribunal ativo
                tribunal = TribunalIntegration.objects.filter(is_active=True).first()
                if not tribunal:
                    return CommandResult(
                        success=False,
                        command='tribunal',
                        data=None,
                        message='',
                        error='Nenhum tribunal ativo configurado'
                    )

                service = get_tribunal_service(tribunal.system_type)
                # Nota: connect() requer certificado configurado
                result = service.consult_process(process_number)

                return CommandResult(
                    success=True,
                    command='tribunal',
                    data=result or {'processo': process_number, 'status': 'não encontrado'},
                    message=f'Processo {process_number} consultado'
                )

            else:
                return CommandResult(
                    success=False,
                    command='tribunal',
                    data=None,
                    message='',
                    error=f'Ação "{action}" não reconhecida. Use: listar, sincronizar'
                )

        except Exception as e:
            return CommandResult(
                success=False,
                command='tribunal',
                data=None,
                message='',
                error=f'Erro: {str(e)}'
            )

    async def _handle_peticao(self, args: str, full_message: str) -> CommandResult:
        """Protocola petições"""
        return CommandResult(
            success=False,
            command='peticao',
            data=None,
            message='',
            error='Funcionalidade em desenvolvimento. Use a interface de petições.'
        )

    async def _handle_caso(self, args: str, full_message: str) -> CommandResult:
        """Opera em casos/processos"""
        from apps.cases.models import LegalCase

        parts = args.split(None, 1)
        action = parts[0].lower() if parts else 'listar'

        try:
            if action in ['listar', 'lista', 'ls']:
                casos = LegalCase.objects.filter(
                    models.Q(advogado_responsavel=self.user) | models.Q(created_by=self.user)
                ).order_by('-created_at')[:10]

                formatted = [{
                    'id': str(c.id),
                    'numero': c.numero_processo or 'Sem número',
                    'titulo': c.titulo,
                    'status': c.status,
                } for c in casos]

                return CommandResult(
                    success=True,
                    command='caso',
                    data=formatted,
                    message=f'{len(formatted)} casos encontrados'
                )

            else:
                return CommandResult(
                    success=False,
                    command='caso',
                    data=None,
                    message='',
                    error=f'Ação "{action}" não reconhecida. Use: listar'
                )

        except Exception as e:
            return CommandResult(
                success=False,
                command='caso',
                data=None,
                message='',
                error=f'Erro: {str(e)}'
            )

    async def _handle_prazo(self, args: str, full_message: str) -> CommandResult:
        """Consulta prazos processuais"""
        # Implementação futura - calendário jurídico
        return CommandResult(
            success=True,
            command='prazo',
            data={'message': 'Funcionalidade em desenvolvimento'},
            message='Consulta de prazos será implementada em breve'
        )

    async def _handle_modelo(self, args: str, full_message: str) -> CommandResult:
        """Busca modelos de peças"""
        from apps.forms.models import FormTemplate

        query = args.strip()

        try:
            if query:
                modelos = FormTemplate.objects.filter(
                    models.Q(name__icontains=query) | models.Q(description__icontains=query)
                ).order_by('name')[:10]
            else:
                modelos = FormTemplate.objects.all().order_by('name')[:10]

            formatted = [{
                'id': str(m.id),
                'nome': m.name,
                'descricao': m.description or '',
                'categoria': m.category or 'geral',
            } for m in modelos]

            return CommandResult(
                success=True,
                command='modelo',
                data=formatted,
                message=f'{len(formatted)} modelos encontrados'
            )

        except Exception as e:
            return CommandResult(
                success=False,
                command='modelo',
                data=None,
                message='',
                error=f'Erro: {str(e)}'
            )

    async def _handle_resumo(self, args: str, full_message: str) -> CommandResult:
        """Gera resumo de documentos ou textos com IA"""
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        texto = args.strip() if args else ''

        if not texto:
            return CommandResult(
                success=False,
                command='resumo',
                data=None,
                message='',
                error='Forneça o texto para resumir. Ex: @resumo [cole o texto aqui]'
            )

        try:
            llm = UnifiedLLMService()
            prompt = f"Faça um resumo conciso e objetivo do texto abaixo, destacando os pontos principais:\n\n{texto}"

            # Usar LLM para gerar resumo
            result = llm.generate(
                user_prompt=prompt,
                system_prompt='Você é um assistente jurídico especializado em resumir textos de forma clara e objetiva.',
                provider='watsonx',
                model='meta-llama/llama-3-3-70b-instruct',
                temperature=0.3,
                max_tokens=500
            )

            resumo = result.get('content', '')

            return CommandResult(
                success=True,
                command='resumo',
                data={'original_length': len(texto), 'resumo': resumo, 'resumo_length': len(resumo)},
                message=f'Resumo gerado ({len(resumo)} caracteres)'
            )

        except Exception as e:
            return CommandResult(
                success=False,
                command='resumo',
                data=None,
                message='',
                error=f'Erro ao gerar resumo: {str(e)}'
            )

    async def _handle_traduzir(self, args: str, full_message: str) -> CommandResult:
        """Traduz textos jurídicos"""
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        # Parse: @traduzir [texto] para [idioma]
        texto = args.strip() if args else ''
        idioma_alvo = 'inglês'

        # Extrair idioma alvo se especificado
        if ' para ' in texto:
            partes = texto.rsplit(' para ', 1)
            texto = partes[0].strip()
            idioma_alvo = partes[1].strip().lower()

        if not texto:
            return CommandResult(
                success=False,
                command='traduzir',
                data=None,
                message='',
                error='Forneça o texto para traduzir. Ex: @traduzir [texto] para inglês'
            )

        try:
            llm = UnifiedLLMService()
            prompt = f"Traduza o texto abaixo para {idioma_alvo}, mantendo o significado jurídico e técnico:\n\n{texto}"

            result = llm.generate(
                user_prompt=prompt,
                system_prompt='Você é um tradutor jurídico especializado em terminologia legal.',
                provider='watsonx',
                model='meta-llama/llama-3-3-70b-instruct',
                temperature=0.3,
                max_tokens=1000
            )

            traducao = result.get('content', '')

            return CommandResult(
                success=True,
                command='traduzir',
                data={
                    'original': texto[:200],
                    'traducao': traducao,
                    'idioma': idioma_alvo
                },
                message=f'Tradução para {idioma_alvo} concluída'
            )

        except Exception as e:
            return CommandResult(
                success=False,
                command='traduzir',
                data=None,
                message='',
                error=f'Erro na tradução: {str(e)}'
            )

    async def _handle_revisar(self, args: str, full_message: str) -> CommandResult:
        """Revisa peças jurídicas"""
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        texto = args.strip() if args else ''

        if not texto:
            return CommandResult(
                success=False,
                command='revisar',
                data=None,
                message='',
                error='Forneça o texto para revisar. Ex: @revisar [cole o texto da petição]'
            )

        try:
            llm = UnifiedLLMService()
            prompt = f"""Revise o texto jurídico abaixo, identificando:
1. Erros gramaticais e ortográficos
2. Problemas de clareza ou ambiguidade
3. Sugestões de melhoria na argumentação
4. Citações legais que podem fortalecer o texto

Texto para revisão:
{texto}

Forneça a revisão de forma estruturada."""

            result = llm.generate(
                user_prompt=prompt,
                system_prompt='Você é um advogado sênior especializado em revisão de peças processuais.',
                provider='watsonx',
                model='meta-llama/llama-3-3-70b-instruct',
                temperature=0.3,
                max_tokens=1500
            )

            revisao = result.get('content', '')

            return CommandResult(
                success=True,
                command='revisar',
                data={'texto_original': texto[:300], 'revisao': revisao},
                message='Revisão concluída'
            )

        except Exception as e:
            return CommandResult(
                success=False,
                command='revisar',
                data=None,
                message='',
                error=f'Erro na revisão: {str(e)}'
            )

    async def _handle_citar(self, args: str, full_message: str) -> CommandResult:
        """Gera citações e referências jurídicas"""
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        tema = args.strip() if args else ''

        if not tema:
            return CommandResult(
                success=False,
                command='citar',
                data=None,
                message='',
                error='Informe o tema para citação. Ex: @citar dano moral, @citar prescrição penal'
            )

        try:
            llm = UnifiedLLMService()
            prompt = f"""Gere citações jurídicas relevantes sobre o tema "{tema}", incluindo:
1. Artigos de lei aplicáveis
2. Súmulas dos tribunais superiores (STF, STJ, TST)
3. Precedentes importantes
4. Doutrina relevante

Formate no padrão ABNT para citações jurídicas."""

            result = llm.generate(
                user_prompt=prompt,
                system_prompt='Você é um especialista em referências e citações jurídicas no padrão ABNT.',
                provider='watsonx',
                model='meta-llama/llama-3-3-70b-instruct',
                temperature=0.4,
                max_tokens=1200
            )

            citacoes = result.get('content', '')

            return CommandResult(
                success=True,
                command='citar',
                data={'tema': tema, 'citacoes': citacoes},
                message=f'Citações geradas para "{tema}"'
            )

        except Exception as e:
            return CommandResult(
                success=False,
                command='citar',
                data=None,
                message='',
                error=f'Erro ao gerar citações: {str(e)}'
            )

    async def _handle_expandir(self, args: str, full_message: str) -> CommandResult:
        """Expande tópicos em texto completo"""
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        topicos = args.strip() if args else ''

        if not topicos:
            return CommandResult(
                success=False,
                command='expandir',
                data=None,
                message='',
                error='Forneça os tópicos para expandir. Ex: @expandir 1. Introdução 2. Fundamentos 3. Pedidos'
            )

        try:
            llm = UnifiedLLMService()
            prompt = f"""Expanda os tópicos abaixo em um texto jurídico completo e bem fundamentado,
com linguagem formal e técnica adequada ao direito brasileiro:

{topicos}

Desenvolva cada tópico com parágrafos completos, citações legais e argumentação sólida."""

            result = llm.generate(
                user_prompt=prompt,
                system_prompt='Você é um advogado especialista em redação de peças processuais.',
                provider='watsonx',
                model='meta-llama/llama-3-3-70b-instruct',
                temperature=0.5,
                max_tokens=2000
            )

            texto_expandido = result.get('content', '')

            return CommandResult(
                success=True,
                command='expandir',
                data={'topicos': topicos[:200], 'texto_expandido': texto_expandido},
                message='Texto expandido com sucesso'
            )

        except Exception as e:
            return CommandResult(
                success=False,
                command='expandir',
                data=None,
                message='',
                error=f'Erro ao expandir: {str(e)}'
            )

    async def _handle_blueprint(self, args: str, full_message: str) -> CommandResult:
        """Lista blueprints disponíveis, opcionalmente filtrados por área"""
        from apps.intelligent_assistant.models.blueprint import DocumentBlueprint

        query = args.strip() if args else ''

        try:
            queryset = DocumentBlueprint.objects.filter(is_active=True).select_related('document_type__category')

            if query:
                queryset = queryset.filter(
                    models.Q(areas__code__icontains=query) |
                    models.Q(areas__name__icontains=query) |
                    models.Q(document_type__category__name__icontains=query)
                ).distinct()

            blueprints = list(queryset[:50])

            if not blueprints:
                return CommandResult(
                    success=True,
                    command='blueprint',
                    data=None,
                    message=f"Nenhum blueprint encontrado para '{query}'. Use @blueprint sem argumentos para listar todos."
                )

            # Formatar como tabela Markdown
            lines = ["## Blueprints Disponíveis\n"]
            lines.append("| Peça | Área | Ação |")
            lines.append("|------|------|------|")
            for bp in blueprints:
                areas = ', '.join(a.name for a in bp.areas.all()[:3])
                lines.append(f"| {bp.name} | {areas} | [Criar](/dashboard/intelligent-assistant) |")

            lines.append(f"\n**Total**: {len(blueprints)} blueprints disponíveis")

            return CommandResult(
                success=True,
                command='blueprint',
                data=None,
                message='\n'.join(lines)
            )

        except Exception as e:
            return CommandResult(
                success=False,
                command='blueprint',
                data=None,
                message='',
                error=f'Erro ao listar blueprints: {str(e)}'
            )

    async def _handle_simulacao(self, args: str, full_message: str) -> CommandResult:
        """Retorna informações sobre simulações jurídicas disponíveis"""
        sub = args.strip().lower() if args else ''

        if sub in ['juri', 'júri', 'jury']:
            lines = [
                "## Simulação de Júri\n",
                "Simula uma sessão completa do Tribunal do Júri (CPP art. 447+).\n",
                "**Como funciona:**",
                "- 7 jurados com perfis personalizáveis (idade, profissão, personalidade)",
                "- Fases: Promotor → Defensor → Réplica → Tréplica → Deliberação → Quesitos → Veredicto",
                "- Relatório analítico com argumentos para alterar resultado\n",
                "**Documentos recomendados para melhor resultado:**",
                "- Denúncia ou queixa-crime",
                "- Pronúncia",
                "- Alegações finais (acusação e defesa)",
                "- Provas documentais e periciais",
                "- Antecedentes do réu\n",
                "**Link:** [Acessar Simulador de Júri](/dashboard/simulations/jury)",
            ]
            return CommandResult(
                success=True,
                command='simulacao',
                data=None,
                message='\n'.join(lines)
            )

        elif sub in ['sentenca', 'sentença', 'juiz', 'judge']:
            lines = [
                "## Simulação de Sentença\n",
                "Simula a sentença de um juiz específico por comarca.\n",
                "**Como funciona:**",
                "- Análise do perfil e padrões de decisão do juiz",
                "- Relatório estratégico: o que garantiu vitória ou como reverter derrota",
                "- Checklist de providências imediatas\n",
                "**Documentos recomendados para melhor resultado:**",
                "- Petição inicial ou contestação",
                "- Provas documentais relevantes",
                "- Jurisprudência do tribunal da comarca",
                "- Informações sobre o juiz (nome, vara, comarca)\n",
                "**Link:** [Acessar Simulador de Sentença](/dashboard/simulations/judge)",
            ]
            return CommandResult(
                success=True,
                command='simulacao',
                data=None,
                message='\n'.join(lines)
            )

        else:
            lines = [
                "## Simulações Jurídicas Disponíveis\n",
                "### 1. Simulação de Júri",
                "Simula sessão completa do Tribunal do Júri com 7 jurados e todas as fases.",
                "- [Acessar Simulador de Júri](/dashboard/simulations/jury)",
                "- Uso: `@simulacao juri`\n",
                "### 2. Simulação de Sentença",
                "Simula sentença de juiz específico com análise de perfil e estratégia.",
                "- [Acessar Simulador de Sentença](/dashboard/simulations/judge)",
                "- Uso: `@simulacao sentenca`\n",
                "**Dica:** Anexe documentos do caso para obter simulações mais precisas.",
            ]
            return CommandResult(
                success=True,
                command='simulacao',
                data=None,
                message='\n'.join(lines)
            )

    async def _handle_legislacao(self, args: str, full_message: str) -> CommandResult:
        """Busca legislação oficial em fontes da internet (planalto, STF, STJ)"""
        from apps.kb.legislation_search import LegislationSearchService

        query = args.strip() if args else ''

        if not query:
            return CommandResult(
                success=False,
                command='legislacao',
                data=None,
                message='',
                error='Informe o termo de busca. Ex: @legislacao lei de drogas art 33'
            )

        try:
            result = LegislationSearchService.search_all(query)

            if not result.get('combined_text') and result.get('total_results', 0) == 0:
                return CommandResult(
                    success=True,
                    command='legislacao',
                    data=result,
                    message=f'Nenhuma legislação encontrada para "{query}". Tente termos mais específicos.'
                )

            # Formatar como Markdown
            lines = [f"## Legislação: {query}\n"]

            for fonte, dados in result.get('fontes', {}).items():
                if not dados.get('success'):
                    continue

                lines.append(f"### Fonte: {dados.get('source', fonte)}")

                for r in dados.get('results', [])[:3]:
                    titulo = r.get('title') or r.get('titulo', 'Sem título')
                    url = r.get('url', '')
                    snippet = r.get('snippet') or r.get('enunciado', '')
                    if url:
                        lines.append(f"- [{titulo}]({url})")
                    else:
                        lines.append(f"- {titulo}")
                    if snippet:
                        lines.append(f"  > {snippet[:200]}")

                lines.append('')

            if result.get('combined_text'):
                lines.append("### Texto Extraído (trecho)\n")
                lines.append(result['combined_text'][:2000])

            lines.append(f"\n**Total**: {result['total_results']} resultados encontrados")

            return CommandResult(
                success=True,
                command='legislacao',
                data=result,
                message='\n'.join(lines)
            )

        except Exception as e:
            return CommandResult(
                success=False,
                command='legislacao',
                data=None,
                message='',
                error=f'Erro ao buscar legislação: {str(e)}'
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Autonomy commands: @agendar, @agendar_recorrente, @meus_casos,
    #                    @meus_prazos, @meus_lembretes
    # ─────────────────────────────────────────────────────────────────────────

    async def _handle_agendar(self, args: str, full_message: str) -> CommandResult:
        """
        Cria lembrete pontual.
        Formato: @agendar <número> <período> - <descrição>
        Exemplos: @agendar 3 dias - Revisar prazo do caso Costa vs TransLog
                  @agendar 2 horas - Ligar para cliente
                  @agendar 1 semana - Verificar andamento processual
        """
        from apps.accounts.models import UserReminder

        args_text = args.strip()
        if not args_text:
            return CommandResult(
                success=False,
                command='agendar',
                data=None,
                message='',
                error=(
                    'Formato: @agendar <numero> <periodo> - <descricao>\n'
                    'Exemplo: @agendar 3 dias - Revisar caso\n'
                    'Periodos: minutos, horas, dias, semanas, meses'
                ),
            )

        match = re.match(
            r'(\d+)\s*(minutos?|horas?|dias?|semanas?|meses?)\s*[-\u2013]\s*(.+)',
            args_text,
            re.IGNORECASE,
        )
        if not match:
            return CommandResult(
                success=False,
                command='agendar',
                data=None,
                message='',
                error=(
                    'Formato: @agendar <numero> <periodo> - <descricao>\n'
                    'Exemplo: @agendar 3 dias - Revisar caso'
                ),
            )

        amount = int(match.group(1))
        unit = match.group(2).lower().rstrip('s')
        description = match.group(3).strip()

        unit_map = {
            'minuto': 'minutes',
            'hora': 'hours',
            'dia': 'days',
            'semana': 'weeks',
        }
        if unit in ('mes', 'mese'):
            delta = timedelta(days=amount * 30)
        else:
            delta = timedelta(**{unit_map.get(unit, 'days'): amount})

        scheduled = timezone.now() + delta

        try:
            reminder = UserReminder.objects.create(
                user=self.user,
                title=description,
                scheduled_date=scheduled,
                frequency='once',
                copilot_prompt=(
                    f'O usuario pediu para lembrar sobre: {description}. '
                    f'Analise o contexto e sugira acoes.'
                ),
                priority='medium',
                status='active',
            )

            return CommandResult(
                success=True,
                command='agendar',
                data={
                    'reminder_id': reminder.id,
                    'scheduled_date': scheduled.isoformat(),
                },
                message=(
                    f"Lembrete agendado para "
                    f"{scheduled.strftime('%d/%m/%Y as %H:%M')}:\n"
                    f"**{description}**\n\n"
                    f"Voce sera notificado e o Copilot analisara o contexto automaticamente."
                ),
            )
        except Exception as e:
            return CommandResult(
                success=False,
                command='agendar',
                data=None,
                message='',
                error=f'Erro ao criar lembrete: {str(e)}',
            )

    async def _handle_agendar_recorrente(self, args: str, full_message: str) -> CommandResult:
        """
        Cria lembrete recorrente.
        Formato: @agendar_recorrente <frequencia> - <descrição>
        Exemplos: @agendar_recorrente semanal - Revisar andamentos
                  @agendar_recorrente diario - Verificar prazos
                  @agendar_recorrente mensal - Relatorio de casos
        """
        from apps.accounts.models import UserReminder

        args_text = args.strip()
        if not args_text:
            return CommandResult(
                success=False,
                command='agendar_recorrente',
                data=None,
                message='',
                error=(
                    'Formato: @agendar_recorrente <frequencia> - <descricao>\n'
                    'Frequencias: diario, semanal, quinzenal, mensal, trimestral, anual\n'
                    'Exemplo: @agendar_recorrente semanal - Revisar andamentos'
                ),
            )

        freq_map = {
            'diario': 'daily',
            'diaria': 'daily',
            'semanal': 'weekly',
            'quinzenal': 'biweekly',
            'mensal': 'monthly',
            'trimestral': 'quarterly',
            'anual': 'yearly',
        }

        match = re.match(
            r'(diario|diaria|semanal|quinzenal|mensal|trimestral|anual)\s*[-\u2013]\s*(.+)',
            args_text,
            re.IGNORECASE,
        )
        if not match:
            return CommandResult(
                success=False,
                command='agendar_recorrente',
                data=None,
                message='',
                error=(
                    'Formato: @agendar_recorrente <frequencia> - <descricao>\n'
                    'Frequencias: diario, semanal, quinzenal, mensal, trimestral, anual'
                ),
            )

        freq_label = match.group(1).lower()
        frequency = freq_map.get(freq_label, 'weekly')
        description = match.group(2).strip()

        # First occurrence based on frequency
        first_delta_map = {
            'daily': timedelta(days=1),
            'weekly': timedelta(weeks=1),
            'biweekly': timedelta(weeks=2),
            'monthly': timedelta(days=30),
            'quarterly': timedelta(days=90),
            'yearly': timedelta(days=365),
        }
        scheduled = timezone.now() + first_delta_map.get(frequency, timedelta(weeks=1))

        try:
            reminder = UserReminder.objects.create(
                user=self.user,
                title=description,
                scheduled_date=scheduled,
                frequency=frequency,
                copilot_prompt=(
                    f'Lembrete recorrente ({freq_label}): {description}. '
                    f'Analise o contexto atual e sugira acoes.'
                ),
                priority='medium',
                status='active',
            )

            return CommandResult(
                success=True,
                command='agendar_recorrente',
                data={
                    'reminder_id': reminder.id,
                    'frequency': frequency,
                    'scheduled_date': scheduled.isoformat(),
                },
                message=(
                    f"Lembrete recorrente ({freq_label}) criado:\n"
                    f"**{description}**\n\n"
                    f"Proximo disparo: {scheduled.strftime('%d/%m/%Y as %H:%M')}\n"
                    f"O Copilot analisara o contexto a cada disparo."
                ),
            )
        except Exception as e:
            return CommandResult(
                success=False,
                command='agendar_recorrente',
                data=None,
                message='',
                error=f'Erro ao criar lembrete recorrente: {str(e)}',
            )

    async def _handle_meus_casos(self, args: str, full_message: str) -> CommandResult:
        """Retorna resumo dos casos ativos do usuario com prazos proximos."""
        from apps.cases.models import LegalCase

        try:
            cases = LegalCase.objects.filter(
                models.Q(advogado_responsavel=self.user) | models.Q(created_by=self.user),
            ).order_by('-updated_at')[:10]

            if not cases:
                return CommandResult(
                    success=True,
                    command='meus_casos',
                    data=[],
                    message='Voce nao tem casos cadastrados.',
                )

            lines = ["**Seus casos ativos:**\n"]
            for c in cases:
                status = c.get_status_display() if hasattr(c, 'get_status_display') else c.status
                esp = c.get_especialidade_display() if hasattr(c, 'get_especialidade_display') else (c.especialidade or 'Geral')
                lines.append(f"- **{c.titulo}** ({status}) - {esp}")
                if c.cliente_nome:
                    lines.append(f"  Cliente: {c.cliente_nome}")
                # Prazos proximos
                prazos = c.prazos.filter(
                    status__in=['pendente', 'em_andamento'],
                ).order_by('data_prazo')[:2]
                for p in prazos:
                    lines.append(
                        f"  Prazo: {p.titulo} ({p.data_prazo.strftime('%d/%m')})"
                    )

            return CommandResult(
                success=True,
                command='meus_casos',
                data=None,
                message='\n'.join(lines),
            )
        except Exception as e:
            return CommandResult(
                success=False,
                command='meus_casos',
                data=None,
                message='',
                error=f'Erro ao buscar casos: {str(e)}',
            )

    async def _handle_meus_prazos(self, args: str, full_message: str) -> CommandResult:
        """Retorna prazos pendentes do usuario ordenados por data."""
        from apps.cases.models import LegalDeadline

        try:
            deadlines = LegalDeadline.objects.filter(
                models.Q(responsavel=self.user) | models.Q(caso__advogado_responsavel=self.user),
                status__in=['pendente', 'em_andamento'],
                caso__deleted_at__isnull=True,
            ).select_related('caso').order_by('data_prazo')[:15]

            if not deadlines:
                return CommandResult(
                    success=True,
                    command='meus_prazos',
                    data=[],
                    message='Nenhum prazo pendente encontrado.',
                )

            lines = ["**Seus prazos pendentes:**\n"]
            today = timezone.now().date()
            for d in deadlines:
                days_left = (d.data_prazo - today).days if d.data_prazo else None
                if days_left is not None and days_left <= 2:
                    urgency = '[URGENTE]'
                elif days_left is not None and days_left <= 5:
                    urgency = '[ATENCAO]'
                else:
                    urgency = '[OK]'
                case_name = d.caso.titulo if d.caso else 'Sem caso'
                date_str = d.data_prazo.strftime('%d/%m/%Y') if d.data_prazo else 'Sem data'
                lines.append(f"{urgency} **{d.titulo}** - {date_str}")
                if days_left is not None:
                    lines.append(f"   Caso: {case_name} | Faltam: {days_left} dias")
                else:
                    lines.append(f"   Caso: {case_name}")

            return CommandResult(
                success=True,
                command='meus_prazos',
                data=None,
                message='\n'.join(lines),
            )
        except Exception as e:
            return CommandResult(
                success=False,
                command='meus_prazos',
                data=None,
                message='',
                error=f'Erro ao buscar prazos: {str(e)}',
            )

    async def _handle_meus_lembretes(self, args: str, full_message: str) -> CommandResult:
        """Retorna lembretes ativos do usuario."""
        from apps.accounts.models import UserReminder

        try:
            reminders = UserReminder.objects.filter(
                user=self.user,
                status='active',
            ).order_by('scheduled_date')[:15]

            if not reminders:
                return CommandResult(
                    success=True,
                    command='meus_lembretes',
                    data=[],
                    message=(
                        'Nenhum lembrete ativo.\n'
                        'Use @agendar para criar um. Ex: @agendar 3 dias - Revisar caso'
                    ),
                )

            lines = ["**Seus lembretes ativos:**\n"]
            for r in reminders:
                freq = r.get_frequency_display()
                date_str = r.scheduled_date.strftime('%d/%m/%Y %H:%M')
                lines.append(f"- **{r.title}** ({freq})")
                lines.append(f"  Proximo disparo: {date_str}")

            return CommandResult(
                success=True,
                command='meus_lembretes',
                data=None,
                message='\n'.join(lines),
            )
        except Exception as e:
            return CommandResult(
                success=False,
                command='meus_lembretes',
                data=None,
                message='',
                error=f'Erro ao buscar lembretes: {str(e)}',
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Action commands: @gerar, @blueprints_caso, @criar_sessao
    # ─────────────────────────────────────────────────────────────────────────

    async def _handle_gerar(self, args: str, full_message: str) -> CommandResult:
        """
        Gera peça jurídica para um caso.
        Formato: @gerar <tipo_documento> para <caso>
        Exemplo: @gerar reclamacao trabalhista para Costa vs TransLog
        """
        from .action_service import ActionService

        svc = ActionService(self.user)
        args_text = args.strip()

        if not args_text:
            return CommandResult(
                success=False,
                command='gerar',
                data=None,
                message='',
                error=(
                    'Formato: @gerar <tipo_documento> para <caso>\n'
                    'Exemplo: @gerar reclamacao trabalhista para Costa vs TransLog\n'
                    'Use @blueprint para listar tipos de documentos disponíveis.'
                ),
            )

        # Parse: "@gerar reclamacao trabalhista para Costa vs TransLog"
        parts = args_text.lower().split(' para ')
        doc_query = parts[0].strip() if parts else args_text
        case_query = parts[1].strip() if len(parts) > 1 else ''

        # Find blueprints
        try:
            blueprints = list(svc.find_blueprints(query=doc_query))
        except Exception as e:
            return CommandResult(
                success=False,
                command='gerar',
                data=None,
                message='',
                error=f'Erro ao buscar blueprints: {str(e)}',
            )

        if not blueprints:
            return CommandResult(
                success=True,
                command='gerar',
                data=None,
                message=(
                    f"Nenhum blueprint encontrado para '{doc_query}'.\n"
                    f"Use @blueprint para listar todos os tipos de documentos disponíveis."
                ),
            )

        bp = blueprints[0]

        # Find case
        if not case_query:
            return CommandResult(
                success=True,
                command='gerar',
                data=None,
                message=(
                    f"Blueprint encontrado: **{bp.name}**\n"
                    f"Especifique o caso: @gerar {doc_query} para [nome do caso]"
                ),
            )

        try:
            cases = list(svc.find_cases(case_query))
        except Exception as e:
            return CommandResult(
                success=False,
                command='gerar',
                data=None,
                message='',
                error=f'Erro ao buscar casos: {str(e)}',
            )

        if not cases:
            return CommandResult(
                success=True,
                command='gerar',
                data=None,
                message=(
                    f"Nenhum caso encontrado para '{case_query}'.\n"
                    f"Use @meus_casos para listar seus casos."
                ),
            )

        case = cases[0]

        # Create session and map fields
        try:
            session = svc.create_session_for_case(case, bp)
            field_data = svc.map_case_to_fields(case, bp)
        except Exception as e:
            return CommandResult(
                success=False,
                command='gerar',
                data=None,
                message='',
                error=f'Erro ao criar sessão: {str(e)}',
            )

        # Build response with link
        link = f"/dashboard/intelligent-assistant/gerador?session={session.id}&phase=generation"

        lines = [
            f"**Sessão criada com sucesso!**\n",
            f"**Documento**: {bp.name}",
            f"**Caso**: {case.titulo}",
            f"**Cliente**: {case.cliente_nome}",
            f"**Tribunal**: {case.tribunal or 'Não definido'}",
            f"\n**Campos preenchidos automaticamente** do caso:",
        ]

        filled = 0
        for sec_num, fields in field_data.items():
            for fname, fval in fields.items():
                if fval:
                    lines.append(f"  - {fname}: {fval}")
                    filled += 1

        if filled == 0:
            lines.append("  (nenhum campo preenchido automaticamente)")

        lines.append(f"\n[Abrir no Gerador de Pecas]({link})")
        lines.append(
            f"\nVoce pode revisar e editar os campos, depois clicar em **Gerar Completo**."
        )

        return CommandResult(
            success=True,
            command='gerar',
            data={'session_id': str(session.id), 'field_data': field_data},
            message='\n'.join(lines),
        )

    async def _handle_blueprints_caso(self, args: str, full_message: str) -> CommandResult:
        """
        Sugere blueprints adequados para um caso.
        Formato: @blueprints_caso <nome ou titulo do caso>
        """
        from .action_service import ActionService

        svc = ActionService(self.user)
        query = args.strip()

        if not query:
            return CommandResult(
                success=False,
                command='blueprints_caso',
                data=None,
                message='',
                error=(
                    'Formato: @blueprints_caso <nome do caso>\n'
                    'Exemplo: @blueprints_caso Costa vs TransLog'
                ),
            )

        try:
            cases = list(svc.find_cases(query))
        except Exception as e:
            return CommandResult(
                success=False,
                command='blueprints_caso',
                data=None,
                message='',
                error=f'Erro ao buscar casos: {str(e)}',
            )

        if not cases:
            return CommandResult(
                success=True,
                command='blueprints_caso',
                data=None,
                message=(
                    f"Nenhum caso encontrado para '{query}'.\n"
                    f"Use @meus_casos para listar seus casos."
                ),
            )

        case = cases[0]

        try:
            blueprints = list(svc.blueprints_for_case(case))
        except Exception as e:
            return CommandResult(
                success=False,
                command='blueprints_caso',
                data=None,
                message='',
                error=f'Erro ao buscar blueprints: {str(e)}',
            )

        esp_display = (
            case.get_especialidade_display()
            if hasattr(case, 'get_especialidade_display')
            else case.especialidade
        )

        lines = [
            f"## Blueprints sugeridos para: {case.titulo}\n",
            f"**Especialidade**: {esp_display}",
            f"**Cliente**: {case.cliente_nome}\n",
        ]

        if not blueprints:
            lines.append(
                "Nenhum blueprint especifico encontrado para esta especialidade.\n"
                "Use @blueprint para ver todos os disponiveis."
            )
        else:
            lines.append("| Peca | Acao |")
            lines.append("|------|------|")
            for bp in blueprints:
                lines.append(
                    f"| {bp.name} | `@gerar {bp.name.lower()[:30]} para {case.titulo[:30]}` |"
                )

        return CommandResult(
            success=True,
            command='blueprints_caso',
            data=None,
            message='\n'.join(lines),
        )

    async def _handle_criar_sessao(self, args: str, full_message: str) -> CommandResult:
        """
        Cria sessão de geração vinculada a caso e blueprint.
        Formato: @criar_sessao <caso> com <blueprint>
        Exemplo: @criar_sessao Costa vs TransLog com Reclamação Trabalhista
        """
        from .action_service import ActionService

        svc = ActionService(self.user)
        args_text = args.strip()

        if not args_text:
            return CommandResult(
                success=False,
                command='criar_sessao',
                data=None,
                message='',
                error=(
                    'Formato: @criar_sessao <caso> com <blueprint>\n'
                    'Exemplo: @criar_sessao Costa vs TransLog com Reclamação Trabalhista'
                ),
            )

        # Parse: "Costa vs TransLog com Reclamação Trabalhista"
        parts = args_text.lower().split(' com ')
        case_query = parts[0].strip() if parts else args_text
        bp_query = parts[1].strip() if len(parts) > 1 else ''

        if not bp_query:
            return CommandResult(
                success=False,
                command='criar_sessao',
                data=None,
                message='',
                error=(
                    'Especifique o blueprint.\n'
                    'Formato: @criar_sessao <caso> com <blueprint>\n'
                    'Use @blueprints_caso <caso> para ver sugestões.'
                ),
            )

        # Find case
        try:
            cases = list(svc.find_cases(case_query))
        except Exception as e:
            return CommandResult(
                success=False,
                command='criar_sessao',
                data=None,
                message='',
                error=f'Erro ao buscar casos: {str(e)}',
            )

        if not cases:
            return CommandResult(
                success=True,
                command='criar_sessao',
                data=None,
                message=f"Nenhum caso encontrado para '{case_query}'. Use @meus_casos para listar.",
            )

        case = cases[0]

        # Find blueprint
        try:
            blueprints = list(svc.find_blueprints(query=bp_query))
        except Exception as e:
            return CommandResult(
                success=False,
                command='criar_sessao',
                data=None,
                message='',
                error=f'Erro ao buscar blueprints: {str(e)}',
            )

        if not blueprints:
            return CommandResult(
                success=True,
                command='criar_sessao',
                data=None,
                message=(
                    f"Nenhum blueprint encontrado para '{bp_query}'.\n"
                    f"Use @blueprint para listar todos."
                ),
            )

        bp = blueprints[0]

        # Create session
        try:
            session = svc.create_session_for_case(case, bp)
            field_data = svc.map_case_to_fields(case, bp)
        except Exception as e:
            return CommandResult(
                success=False,
                command='criar_sessao',
                data=None,
                message='',
                error=f'Erro ao criar sessão: {str(e)}',
            )

        link = f"/dashboard/intelligent-assistant/gerador?session={session.id}&phase=generation"

        lines = [
            f"**Sessão criada!**\n",
            f"**Documento**: {bp.name}",
            f"**Caso**: {case.titulo}",
            f"**Cliente**: {case.cliente_nome}",
        ]

        filled = sum(1 for fields in field_data.values() for v in fields.values() if v)
        if filled:
            lines.append(f"\n{filled} campo(s) preenchidos automaticamente do caso.")

        lines.append(f"\n[Abrir no Gerador de Pecas]({link})")

        return CommandResult(
            success=True,
            command='criar_sessao',
            data={'session_id': str(session.id)},
            message='\n'.join(lines),
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Communication command: @notificar
    # ─────────────────────────────────────────────────────────────────────────

    async def _handle_notificar(self, args: str, full_message: str) -> CommandResult:
        """
        Envia notificacao via WhatsApp ou Email com mensagem gerada por IA.
        Formato: @notificar whatsapp <numero> - <mensagem>
                 @notificar email <email> - <mensagem>
        Exemplo: @notificar whatsapp +5521999998888 - Prazo vence amanha no caso Costa
        """
        from .communication_service import CommunicationService

        args_text = args.strip()
        if not args_text:
            return CommandResult(
                success=False,
                command='notificar',
                data=None,
                message='',
                error=(
                    'Formato: @notificar whatsapp <numero> - <mensagem>\n'
                    'Exemplo: @notificar whatsapp +5521999998888 - Prazo vence amanha no caso Costa\n'
                    'Ou: @notificar email user@email.com - Documento pronto para revisao'
                ),
            )

        # Parse channel type
        parts = args_text.split(None, 1)
        channel_type = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ''

        if channel_type not in ('whatsapp', 'email'):
            return CommandResult(
                success=False,
                command='notificar',
                data=None,
                message='',
                error=(
                    f'Canal "{channel_type}" nao reconhecido.\n'
                    'Use: whatsapp ou email\n'
                    'Exemplo: @notificar whatsapp +5521999998888 - Mensagem aqui'
                ),
            )

        # Parse destination and message
        match = re.match(r'(\S+)\s*[-\u2013]\s*(.+)', rest, re.DOTALL)
        if not match:
            return CommandResult(
                success=False,
                command='notificar',
                data=None,
                message='',
                error=(
                    'Formato: @notificar <canal> <destino> - <mensagem>\n'
                    'Exemplo: @notificar whatsapp +5521999998888 - Prazo vence amanha'
                ),
            )

        destination = match.group(1).strip()
        message_context = match.group(2).strip()

        svc = CommunicationService()

        try:
            if channel_type == 'whatsapp':
                # Generate AI-powered message
                ai_message = svc.generate_notification_text(
                    'custom',
                    {'title': message_context, 'message': message_context},
                )
                link = svc.generate_whatsapp_link(destination, ai_message)

                return CommandResult(
                    success=True,
                    command='notificar',
                    data={
                        'channel': 'whatsapp',
                        'destination': destination,
                        'message': ai_message,
                        'whatsapp_link': link,
                    },
                    message=(
                        f'**Mensagem WhatsApp gerada:**\n\n'
                        f'{ai_message}\n\n'
                        f'[Abrir no WhatsApp]({link})'
                    ),
                )

            elif channel_type == 'email':
                subject, body = svc.generate_email_content(
                    'custom',
                    {'title': message_context, 'message': message_context},
                )

                # Try to send email
                from django.core.mail import send_mail
                try:
                    send_mail(
                        subject=subject,
                        message='',
                        html_message=body,
                        from_email='noreply@verus.ai',
                        recipient_list=[destination],
                        fail_silently=True,
                    )
                    status = 'enviado'
                except Exception:
                    logger.warning("Failed to send notification email to %s", destination, exc_info=True)
                    status = 'erro no envio'

                return CommandResult(
                    success=True,
                    command='notificar',
                    data={
                        'channel': 'email',
                        'destination': destination,
                        'subject': subject,
                        'status': status,
                    },
                    message=(
                        f'**E-mail {status}:**\n\n'
                        f'**Para:** {destination}\n'
                        f'**Assunto:** {subject}\n\n'
                        f'{body[:500]}'
                    ),
                )

        except Exception as e:
            return CommandResult(
                success=False,
                command='notificar',
                data=None,
                message='',
                error=f'Erro ao enviar notificacao: {str(e)}',
            )

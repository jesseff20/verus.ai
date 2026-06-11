"""
Serviço de geração de petição por IA baseada em dados do caso específico.
Usa o UnifiedLLMService existente para gerar petição completa.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class PetitionAIService:
    """Gera petição completa baseada nos dados do caso, não apenas blueprint genérico."""

    PETITION_TYPES = {
        'inicial': {
            'name': 'Petição Inicial',
            'sections': ['qualificacao', 'fatos', 'direito', 'pedidos', 'valor_causa', 'provas', 'encerramento'],
        },
        'contestacao': {
            'name': 'Contestação',
            'sections': ['preliminares', 'merito', 'pedidos', 'provas', 'encerramento'],
        },
        'recurso_apelacao': {
            'name': 'Recurso de Apelação',
            'sections': ['cabimento', 'tempestividade', 'razoes', 'pedido_reforma', 'encerramento'],
        },
        'agravo_instrumento': {
            'name': 'Agravo de Instrumento',
            'sections': ['cabimento', 'urgencia', 'merito', 'pedidos', 'encerramento'],
        },
        'embargos_declaracao': {
            'name': 'Embargos de Declaração',
            'sections': ['obscuridade_omissao', 'fundamentacao', 'pedidos', 'encerramento'],
        },
        'mandado_seguranca': {
            'name': 'Mandado de Segurança',
            'sections': ['autoridade_coatora', 'direito_liquido_certo', 'ilegalidade', 'pedido_liminar', 'pedidos', 'encerramento'],
        },
        'habeas_corpus': {
            'name': 'Habeas Corpus',
            'sections': ['paciente_coator', 'constrangimento_ilegal', 'fundamentos', 'pedido_liminar', 'pedidos'],
        },
    }

    @classmethod
    def generate_petition(cls, case_id, petition_type: str, extra_instructions: str = '', user=None) -> dict:
        """
        Gera petição completa baseada nos dados do caso.
        """
        from apps.cases.models import LegalCase, CaseDocument
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        if petition_type not in cls.PETITION_TYPES:
            return {
                'success': False,
                'error': f'Tipo de petição não suportado: {petition_type}',
                'available_types': list(cls.PETITION_TYPES.keys()),
            }

        try:
            case = LegalCase.objects.select_related('client', 'advogado_responsavel').get(id=case_id)
        except LegalCase.DoesNotExist:
            return {'success': False, 'error': 'Caso não encontrado'}

        petition_config = cls.PETITION_TYPES[petition_type]

        # Build context from case data
        case_context = cls._build_case_context(case)

        # Build the prompt
        system_prompt = f"""Você é um advogado brasileiro especialista em {case.get_especialidade_display()}.
Gere uma {petition_config['name']} completa, profissional e fundamentada juridicamente.

REGRAS:
1. Use linguagem jurídica formal brasileira
2. Cite artigos de lei relevantes (CPC, CC, CF, CLT, etc.)
3. Fundamente com doutrina e jurisprudência quando possível
4. Estruture com cabeçalho, qualificação das partes, fatos, direito, pedidos e encerramento
5. Use os dados reais do caso fornecidos abaixo
6. Não invente fatos — use apenas as informações disponíveis
7. Quando informação estiver ausente, indique [PREENCHER: descrição do dado necessário]
"""

        user_prompt = f"""DADOS DO CASO:
{case_context}

TIPO DE PETIÇÃO: {petition_config['name']}
SEÇÕES OBRIGATÓRIAS: {', '.join(petition_config['sections'])}

{f'INSTRUÇÕES ADICIONAIS DO ADVOGADO: {extra_instructions}' if extra_instructions else ''}

Gere a petição completa agora:"""

        try:
            llm_service = UnifiedLLMService()
            response = llm_service.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=8000,
                temperature=0.3,
                user=user,
                usage_type='document_gen',
                description=f'Geracao de peticao: {petition_config["name"]}',
            )

            return {
                'success': True,
                'petition_type': petition_type,
                'petition_name': petition_config['name'],
                'case_id': str(case.id),
                'case_titulo': case.titulo,
                'content': response.get('content', ''),
                'tokens_used': response.get('total_tokens', 0),
                'sections': petition_config['sections'],
            }
        except Exception as e:
            logger.error(f"Error generating petition: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    @classmethod
    def _build_case_context(cls, case) -> str:
        """Constrói contexto textual do caso para o prompt."""
        lines = []
        lines.append(f"Título: {case.titulo}")
        lines.append(f"Número do Processo: {case.numero_processo or '[Não distribuído]'}")
        lines.append(f"Especialidade: {case.get_especialidade_display()}")
        lines.append(f"Status: {case.get_status_display()}")
        lines.append(f"Fase: {case.get_fase_display()}")

        if case.client:
            c = case.client
            lines.append(f"\nCLIENTE:")
            lines.append(f"  Nome: {c.name}")
            lines.append(f"  Tipo: {c.get_client_type_display()}")
            lines.append(f"  CPF/CNPJ: {c.cpf_cnpj or '[Não informado]'}")
            lines.append(f"  Endereço: {c.address}, {c.city}/{c.state} — CEP {c.zipcode}" if c.address else "  Endereço: [Não informado]")
        else:
            lines.append(f"\nCLIENTE: {case.cliente_nome}")
            lines.append(f"  CPF/CNPJ: {case.cliente_cpf_cnpj or '[Não informado]'}")

        lines.append(f"\nPARTE CONTRÁRIA: {case.parte_contraria or '[Não informado]'}")
        lines.append(f"  CPF/CNPJ: {case.parte_contraria_cpf_cnpj or '[Não informado]'}")

        lines.append(f"\nTRIBUNAL: {case.tribunal or '[Não informado]'}")
        lines.append(f"VARA/JUÍZO: {case.vara_juizo or '[Não informado]'}")
        lines.append(f"COMARCA: {case.comarca or '[Não informado]'}")

        if case.valor_causa:
            lines.append(f"\nVALOR DA CAUSA: R$ {case.valor_causa}")

        if case.descricao:
            lines.append(f"\nDESCRIÇÃO/FATOS:\n{case.descricao}")

        if case.observacoes:
            lines.append(f"\nOBSERVAÇÕES:\n{case.observacoes}")

        if case.advogado_responsavel:
            adv = case.advogado_responsavel
            lines.append(f"\nADVOGADO: {adv.get_full_name()}")
            oab = getattr(adv, 'oab_number', '') or ''
            if oab:
                lines.append(f"  OAB: {oab}")

        return '\n'.join(lines)

    @classmethod
    def list_petition_types(cls) -> list:
        """Lista todos os tipos de petição disponíveis."""
        return [
            {'id': k, 'name': v['name'], 'sections': v['sections']}
            for k, v in cls.PETITION_TYPES.items()
        ]

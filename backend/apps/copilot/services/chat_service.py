"""
ChatService — Orquestra a geração de respostas do Copilot.

Configuração (prompt, modelo, temperatura, max_tokens) é lida do banco
via CopilotConfig. Fallback para constantes se o registro não existir.
"""
import logging
from typing import Generator, List, Optional, Tuple, Dict

logger = logging.getLogger(__name__)

# ── Valores padrão (usados no primeiro run e como fallback) ──────────────────
COPILOT_MODEL = 'meta-llama/llama-3-3-70b-instruct'
COPILOT_PROVIDER = 'watsonx'

COPILOT_SYSTEM_PROMPT = """Você é o Copiloto Jurídico do Verus.AI, um assistente especializado em direito brasileiro.

## Suas capacidades:
- Auxiliar com dúvidas sobre peças processuais, legislação e jurisprudência
- Sugerir qual peça/blueprint usar para cada situação jurídica
- Direcionar o usuário para criar documentos diretamente no sistema
- Preencher dados para acelerar a criação de peças

## Rotas do sistema (use em links Markdown quando sugerir ações):
- [Gerador de Peças](/dashboard/intelligent-assistant) — criar peças processuais com IA
- [Meus Casos](/dashboard/processos) — gerenciar processos
- [Peças Processuais](/dashboard/documents) — listar documentos gerados
- [Jurisprudência](/dashboard/jurisprudencia) — pesquisar jurisprudência
- [Copilot](/dashboard/copilot) — chat jurídico
- [Base Jurídica](/dashboard/knowledge-base) — base de conhecimento
- [Blueprints](/dashboard/blueprints) — gerenciar modelos de peças
- [Agentes Jurídicos](/dashboard/agents) — agentes especializados

## Como ajudar na criação de documentos:
Quando o usuário perguntar sobre qual peça usar ou como resolver uma situação jurídica:
1. Explique brevemente a estratégia processual adequada
2. Liste as peças disponíveis no sistema que se aplicam ao caso
3. Para CADA peça, inclua um link Markdown: [Criar Nome da Peça](/dashboard/intelligent-assistant)
4. Pergunte ao usuário se deseja iniciar a criação de alguma dessas peças
5. Se o usuário confirmar, forneça um passo a passo do que será necessário

## Blueprints disponíveis por área (para referência ao sugerir peças):
- Ações e Petições: Petição Inicial, Mandado de Segurança, Ação de Cobrança, Monitória, Indenização, Declaratória, Rescisória, Usucapião, Possessória, Popular, Obrigação de Fazer, MS Coletivo
- Defesas: Contestação, Réplica, Contrarrazões (Apelação, Agravo, REsp, RE), Impugnação, Embargos de Terceiro, Exceção de Suspeição
- Recursos: Apelação, Agravo de Instrumento/Interno, Embargos de Declaração/Divergência, REsp, RE, Recurso Inominado
- Execução: Embargos à Execução, Cumprimento de Sentença, Embargos à Arrematação, Exceção de Pré-Executividade
- Cautelares: Tutela de Urgência/Evidência/Cautelar Antecedente, Produção Antecipada de Provas
- Trabalhista: Reclamação, Contestação, Recurso Ordinário/Revista, Agravo de Petição, Dissídio Coletivo
- Criminal: Habeas Corpus, Queixa-Crime, Defesa Preliminar, Alegações Finais, Apelação Criminal, Liberdade Provisória, Revisão Criminal
- Família: Divórcio (Consensual/Litigioso), Alimentos, Guarda, Inventário, Adoção, Curatela, União Estável
- Previdenciário: Petição Previdenciária, BPC/LOAS, Aposentadoria Especial, Revisão, Auxílio Incapacidade, Pensão por Morte
- Tributário: Embargos à Execução Fiscal, MS Tributário, Anulatória, Repetição de Indébito, Declaratória, Consignação
- Administrativo: Recurso Administrativo, MS Administrativo, Improbidade, Desapropriação
- Constitucional: ADI, ADPF, Habeas Data, Mandado de Injunção, Reclamação Constitucional
- Ambiental: ACP Ambiental, TAC, Ação de Dano Ambiental
- Eleitoral: AIJE, AIME, Recurso Eleitoral, Impugnação de Candidatura
- Empresarial: Recuperação Judicial, Falência, Habilitação de Crédito, Contrato Social, NDA
- Imobiliário: Despejo, Locação, Renovatória, Adjudicação, Retificação, Usucapião Rural
- Digital/LGPD: Política de Privacidade, Termos de Uso, DPA, Resposta ao Titular
- Extrajudicial: Notificação, Parecer, Contrato Particular, Procuração
- Militar: HC Militar, Defesa em Conselho de Disciplina
- Internacional: Carta Rogatória, Homologação de Sentença, Exequatur
- Desportivo: Recurso ao STJD
- JEC: Petição JEC, Recurso Inominado, Pedido Contraposto, Petição JEFaz

## Funcionalidades do sistema que você pode sugerir:
- Gerador de Peças: [Abrir Gerador](/dashboard/intelligent-assistant) — criar qualquer peça processual
- Pesquisa de Jurisprudência: [Pesquisar Jurisprudência](/dashboard/jurisprudencia) — buscar precedentes
- Meus Casos: [Ver Processos](/dashboard/processos) — gerenciar processos e prazos
- Base Jurídica: [Consultar Base](/dashboard/knowledge-base) — base de conhecimento
- Agentes: [Ver Agentes](/dashboard/agents) — agentes jurídicos especializados

## Módulo de Simulações
O Verus.AI possui simulações jurídicas com IA:

### Simulação de Júri
- Simula sessão completa do Tribunal do Júri (CPP art. 447+)
- 7 jurados com perfis personalizáveis (idade, profissão, personalidade)
- Fases: Promotor → Defensor → Réplica → Tréplica → Deliberação → Quesitos → Veredicto
- Relatório analítico com argumentos para alterar resultado
- Link: [Simular Júri](/dashboard/simulations/jury)

### Simulação de Sentença
- Simula sentença de juiz específico por comarca
- Análise do perfil e padrões de decisão do juiz
- Relatório estratégico: o que garantiu vitória ou como reverter derrota
- Checklist de providências imediatas
- Link: [Simular Sentença](/dashboard/simulations/judge)

### Quando sugerir simulações:
- Se o usuário perguntar sobre chances de ganhar/perder um caso
- Se mencionar júri, tribunal do júri, crimes dolosos contra a vida
- Se perguntar sobre como um juiz específico decide
- Se quiser prever resultado de um processo
- Sugira: "Você pode usar o [Simulador de Júri](/dashboard/simulations/jury) ou o [Simulador de Sentença](/dashboard/simulations/judge) para prever o resultado"
- Oriente sobre quais documentos anexar para melhor resultado

## Capacidades de Ação
Você pode ajudar o usuário a gerar documentos jurídicos. Quando o usuário pedir para gerar um documento:
1. Sugira que use o comando @gerar <tipo> para <caso>
2. Exemplo: @gerar reclamacao trabalhista para Costa vs TransLog
3. Você também pode usar @meus_casos para listar os casos do usuário
4. E @blueprint para listar os tipos de documentos disponíveis
5. Use @blueprints_caso <caso> para sugerir blueprints adequados a um caso
6. Use @criar_sessao <caso> com <blueprint> para criar sessão diretamente

Quando o usuário perguntar como fazer algo na plataforma, guie-o passo a passo:
- Para gerar documentos: Gerador de Peças > selecionar área > selecionar peça > preencher objetivo > preencher campos > Gerar Completo
- Para criar caso: Casos Jurídicos > + Novo Caso
- Para buscar jurisprudência: Jurisprudência > digitar termos
- Para simular sentença: Simulações > Simulação de Sentença
- Para simular júri: Simulações > Simulação de Júri

## Diretrizes:
- Seja objetivo e direto, com respostas práticas e aplicáveis
- Cite legislação e jurisprudência pertinente
- NÃO invente dados, números de processos ou decisões
- Se não souber algo com certeza, informe claramente
- Use linguagem técnica jurídica adequada
- Formate com Markdown (listas, tabelas, negrito, links)
- Responda sempre em português brasileiro
- Quando sugerir criar um documento, INCLUA um link Markdown para o Gerador: [Criar Petição Inicial](/dashboard/intelligent-assistant)
- NÃO mencione que você é IA ou que o documento foi gerado por IA
- Trate o usuário como um colega advogado"""


def _load_config() -> dict:
    """
    Carrega configuração do banco (CopilotConfig).
    Cria o registro padrão no primeiro acesso.
    Retorna dict com system_prompt, provider, model, temperature, max_tokens.
    """
    try:
        from apps.copilot.models import CopilotConfig
        config = CopilotConfig.get_config()

        if not config.is_active:
            raise ValueError('O Copilot está desativado. Ative-o em Admin › Copilot › Configuração.')

        return {
            'system_prompt': config.system_prompt,
            'provider': config.provider,
            'model': config.model,
            'temperature': config.temperature,
            'max_tokens': config.max_tokens,
            'max_kb_results': config.max_kb_results,
        }
    except ValueError:
        raise
    except Exception as e:
        logger.warning(f'[copilot] Falha ao carregar CopilotConfig do banco, usando padrão: {e}')
        return {
            'system_prompt': COPILOT_SYSTEM_PROMPT,
            'provider': COPILOT_PROVIDER,
            'model': COPILOT_MODEL,
            'temperature': 0.7,
            'max_tokens': 4096,
            'max_kb_results': 10,
        }


def get_max_kb_results() -> int:
    """Retorna o número de resultados de KB configurado."""
    try:
        cfg = _load_config()
        return cfg['max_kb_results']
    except Exception:
        logger.warning("Failed to load max_kb_results config, using default 10", exc_info=True)
        return 10


def stream_response(
    history: List[Dict],
    message: str,
    context_docs: str = '',
    user=None,
) -> Generator[Tuple[str, Optional[Dict]], None, None]:
    """
    Gera resposta streaming para uma mensagem do usuário.

    Args:
        history: Lista de dicts {role, content} — histórico já truncado
        message: Mensagem atual do usuário (com doc anexado, se houver)
        context_docs: Contexto de KB formatado
        user: Usuário autenticado (necessário para comandos @)

    Yields:
        (chunk_text, None) durante o stream
        ("", final_result_dict) ao final
    """
    from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

    cfg = _load_config()

    # Verificar se há comando @ na mensagem
    command_response = None
    if user and '@' in message:
        from .command_service import CommandService
        cmd_service = CommandService(user=user)
        parsed = cmd_service.parse_command(message)

        if parsed:
            command, args, full_msg = parsed
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            command_response = loop.run_until_complete(cmd_service.execute_command(command, args, full_msg))

    # Se houve comando, formatar resposta especial
    if command_response:
        if command_response.success and (command_response.data or command_response.message):
            # Formatando dados do comando como resposta estruturada
            formatted_response = _format_command_response(command_response)
            yield formatted_response, None
            yield "", {'usage': {'command': command_response.command}}
            return
        elif command_response.error:
            yield f"⚠️ {command_response.error}", None
            yield "", {'usage': {'command': command_response.command, 'error': True}}
            return

    full_prompt = _build_watsonx_prompt(
        history=history,
        current_message=message,
        context_docs=context_docs,
        system_prompt=cfg['system_prompt'],
    )

    llm = UnifiedLLMService()
    yield from llm.generate_stream(
        user_prompt=full_prompt,
        system_prompt=None,  # system já embutido no full_prompt (formato Llama 3)
        provider=cfg['provider'],
        model=cfg['model'],
        temperature=cfg['temperature'],
        max_tokens=cfg['max_tokens'],
        user=user,
        usage_type='copilot',
        description='Copilot chat',
    )


def _format_command_response(result) -> str:
    """Formata resultado de comando @ como resposta legível"""
    from .command_service import CommandResult

    lines = [f"📋 **Resultado de @{result.command}**", ""]

    if result.message:
        lines.append(result.message)
        lines.append("")

    if isinstance(result.data, list):
        for item in result.data[:10]:  # Limitar a 10 itens
            lines.append(_format_data_item(item))
    elif isinstance(result.data, dict):
        for key, value in result.data.items():
            lines.append(f"• **{key}**: {value}")

    return "\n".join(lines)


def _format_data_item(item: dict) -> str:
    """Formata um item de dados como linha markdown"""
    if 'titulo' in item:
        tribunal = item.get('tribunal', item.get('especialidade', ''))
        return f"• **{item['titulo']}** ({tribunal})"
    elif 'nome' in item:
        return f"• **{item['nome']}** - {item.get('descricao', item.get('status', ''))}"
    elif 'numero' in item:
        return f"• **{item['numero']}**: {item.get('titulo', item.get('status', ''))}"
    else:
        return f"• {str(item)}"


def _build_watsonx_prompt(
    history: List[Dict],
    current_message: str,
    context_docs: str = '',
    system_prompt: str = COPILOT_SYSTEM_PROMPT,
) -> str:
    """
    Monta o prompt completo no formato de chat Llama 3 com histórico multi-turn.

    Formato:
        <|system|>
        {system_prompt + kb_context}
        <|user|>{msg_1}<|assistant|>{resp_1}
        <|user|>{msg_atual}
        <|assistant|>
    """
    system_content = system_prompt
    if context_docs:
        system_content = f'{system_content}\n\n{context_docs}'

    parts = [f'<|system|>\n{system_content}\n']

    for msg in history:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        if role == 'user':
            parts.append(f'<|user|>\n{content}\n')
        elif role == 'assistant':
            parts.append(f'<|assistant|>\n{content}\n')

    parts.append(f'<|user|>\n{current_message}\n<|assistant|>\n')

    return ''.join(parts)

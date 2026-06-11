"""
Serviço de IA para análise de Clientes.
Integração com Copilot para:
- Preenchimento automático via upload de documentos
- Análise de conflito de interesses
- Sugestão de faixa de honorários
- Busca de dados públicos (Receita Federal)
"""
import logging
from typing import Optional, Dict, Any, List
from django.db.models import Q

logger = logging.getLogger(__name__)


class ClientAIService:
    """Serviço de IA para análise de clientes."""

    @staticmethod
    async def extract_data_from_document(
        file_content: bytes,
        filename: str,
        document_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extrai dados de documento uploadado (CPF/CNPJ, RG, Contrato Social).

        Args:
            file_content: Conteúdo binário do arquivo
            filename: Nome do arquivo
            document_type: Tipo do documento (cpf, cnpj, rg, contrato_social)

        Returns:
            Dict com dados extraídos:
            - name, cpf_cnpj, rg, email, phone, address, etc.
            - confidence: 0-100
            - raw_text: texto extraído
        """
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService
        import base64

        # Codificar arquivo em base64 para envio à IA
        file_base64 = base64.b64encode(file_content).decode('utf-8')

        # Determinar tipo de documento
        doc_type_hints = {
            'cpf': 'CPF ou documento pessoal',
            'cnpj': 'CNPJ ou contrato social',
            'rg': 'RG ou identidade',
            'contrato_social': 'Contrato social completo',
        }
        hint = doc_type_hints.get(document_type, 'documento') if document_type else 'documento'

        prompt = f"""
Extraia todos os dados estruturados deste {hint} em formato JSON.

**Dados para extrair (se disponíveis no documento):**
- Nome completo / Razão social
- CPF / CNPJ
- RG (se pessoa física)
- Endereço completo (logradouro, número, complemento, bairro, cidade, UF, CEP)
- Telefone(s)
- E-mail
- Nome de sócios (se empresa)
- Capital social (se empresa)
- Data de nascimento/fundação
- Estado civil / Regime de bens (se aplicável)
- Profissão / Atividade econômica

**Formato de resposta (JSON puro):**
{{
    "name": "nome extraído",
    "cpf_cnpj": "000.000.000-00 ou 00.000.000/0000-00",
    "rg": "RG se houver",
    "email": "email se houver",
    "phone": "telefone se houver",
    "address": "endereço completo",
    "city": "cidade",
    "state": "UF",
    "zipcode": "CEP",
    "company_name": "razão social (se PJ)",
    "contact_person": "nome do contato (se PJ)",
    "confidence": 85,
    "raw_text": "texto completo extraído"
}}
"""

        try:
            llm = UnifiedLLMService.get_service()

            # Usar capacidade de visão/OCR se disponível
            response = await llm.generate_with_attachment_async(
                prompt=prompt,
                file_base64=file_base64,
                filename=filename,
                temperature=0.1,  # Baixa temperatura para extração precisa
            )

            import json
            import re

            # Extrair JSON da resposta
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    'data': result,
                    'confidence': result.get('confidence', 70),
                    'raw_text': result.get('raw_text', ''),
                }
            else:
                return {
                    'data': {},
                    'confidence': 0,
                    'raw_text': response,
                }

        except Exception as e:
            logger.error(f'Erro na extração de documento: {e}')
            return {
                'data': {},
                'confidence': 0,
                'error': str(e),
            }

    @staticmethod
    async def check_conflict_of_interest(
        client_name: str,
        cpf_cnpj: Optional[str] = None,
        company_name: Optional[str] = None,
        case_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Verifica conflito de interesses com clientes/casos existentes.

        Args:
            client_name: Nome do potencial cliente
            cpf_cnpj: CPF ou CNPJ
            company_name: Nome da empresa (se PJ)
            case_description: Descrição do caso

        Returns:
            Dict com:
            - has_conflict: bool
            - conflicts: lista de conflitos encontrados
            - risk_level: 'low' | 'medium' | 'high'
            - recommendation: texto com recomendação
        """
        from apps.cases.models import Client, LegalCase
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        # Busca inicial no banco por similaridade
        conflicts_found = []

        # Buscar por nome similar
        similar_clients = Client.objects.filter(
            Q(name__icontains=client_name) |
            Q(company_name__icontains=client_name) |
            Q(name__icontains=company_name) if company_name else Q()
        )[:10]

        for client in similar_clients:
            conflicts_found.append({
                'type': 'cliente_existente',
                'name': client.name,
                'cpf_cnpj': client.cpf_cnpj,
                'is_active': client.is_active,
            })

        # Buscar por CPF/CNPJ
        if cpf_cnpj:
            cpf_match = Client.objects.filter(cpf_cnpj=cpf_cnpj).first()
            if cpf_match and cpf_match.name != client_name:
                conflicts_found.append({
                    'type': 'cpf_cnpj_duplicado',
                    'name': cpf_match.name,
                    'cpf_cnpj': cpf_match.cpf_cnpj,
                })

        # Se encontrou conflitos diretos, retornar
        if conflicts_found:
            return {
                'has_conflict': True,
                'conflicts': conflicts_found,
                'risk_level': 'high' if len(conflicts_found) > 2 else 'medium',
                'recommendation': f'Foram encontrados {len(conflicts_found)} conflito(s) em potencial. Revise antes de prosseguir.',
                'requires_review': True,
            }

        # Analisar descrição do caso com IA para conflitos indiretos
        if case_description:
            # Buscar clientes ativos e casos
            active_clients = Client.objects.filter(is_active=True).values('name', 'company_name')[:50]
            active_cases = LegalCase.objects.filter(
                status__in=['ativo', 'aguardando', 'suspenso']
            ).values('titulo', 'cliente_nome', 'parte_contraria')[:50]

            prompt = f"""
Analise se há conflito de interesses entre o potencial novo cliente e clientes/casos ativos.

**Novo Cliente:**
- Nome: {client_name}
- CPF/CNPJ: {cpf_cnpj or 'Não informado'}
- Descrição do caso: {case_description[:500]}

**Clientes Ativos (parcial):**
{[c['name'] or c['company_name'] for c in active_clients][:20]}

**Casos Ativos (parcial):**
{[f"{c['titulo']} ({c['cliente_nome']} vs {c['parte_contraria']})" for c in active_cases][:20]}

**Tarefa:**
1. Identifique possíveis conflitos (parte contrária em caso ativo, cliente existente, etc.)
2. Classifique o risco (low/medium/high)
3. Dê uma recomendação clara

**Formato (JSON):**
{{
    "has_conflict": true/false,
    "conflicts": [{{"type": "...", "description": "..."}}],
    "risk_level": "low|medium|high",
    "recommendation": "texto",
    "analysis": "explicação detalhada"
}}
"""

            try:
                llm = UnifiedLLMService.get_service()
                response = await llm.generate_async(prompt, temperature=0.3)

                import json
                import re

                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    result = json.loads(json_match.group())
                    return {
                        'has_conflict': result.get('has_conflict', False),
                        'conflicts': result.get('conflicts', []),
                        'risk_level': result.get('risk_level', 'low'),
                        'recommendation': result.get('recommendation', ''),
                        'analysis': result.get('analysis', ''),
                        'requires_review': result.get('has_conflict', False),
                    }
            except Exception as e:
                logger.warning(f'Erro na análise de conflito: {e}')

        # Sem conflitos encontrados
        return {
            'has_conflict': False,
            'conflicts': [],
            'risk_level': 'low',
            'recommendation': 'Nenhum conflito de interesses identificado. Pode prosseguir.',
            'requires_review': False,
        }

    @staticmethod
    async def suggest_fee_range(
        client_data: Dict[str, Any],
        case_data: Optional[Dict[str, Any]] = None,
        local_oab_table: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Sugere faixa de honorários baseada no perfil do cliente e caso.

        Args:
            client_data: Dados do cliente (nome, cpf_cnpj, etc.)
            case_data: Dados do caso (especialidade, valor_causa, complexidade)
            local_oab_table: Tabela OAB local (opcional)

        Returns:
            Dict com:
            - min_value, max_value: faixa sugerida
            - suggested_value: valor recomendado
            - factors: fatores considerados
            - oab_reference: valor de referência da OAB
        """
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        # Tabela OAB de referência (valores base 2024)
        oab_base = local_oab_table or {
            'consulta': 500,
            'peticao_inicial': 2000,
            'contestacao': 2500,
            'acao_simples': 3000,
            'acao_complexa': 5000,
            'recursos': 2000,
        }

        specialty_multipliers = {
            'civel': 1.0,
            'criminal': 1.3,
            'trabalhista': 1.1,
            'tributario': 1.5,
            'familia': 1.2,
            'empresarial': 1.4,
            'previdenciario': 1.0,
            'administrativo': 1.1,
        }

        prompt = f"""
Sugira uma faixa de honorários advocatícios justa e competitiva.

**Dados do Cliente:**
- Nome: {client_data.get('name', 'N/A')}
- Tipo: {client_data.get('client_type', 'pessoa_fisica')}
- CPF/CNPJ: {client_data.get('cpf_cnpj', 'N/A')}

**Dados do Caso:**
- Especialidade: {case_data.get('specialty', 'N/A') if case_data else 'Não informado'}
- Valor da causa: R$ {case_data.get('valor_causa', 0) if case_data else 0}
- Complexidade: {case_data.get('complexity', 'N/A') if case_data else 'Não informada'}
- Fase: {case_data.get('fase', 'N/A') if case_data else 'Não informada'}

**Tabela OAB Referência:**
- Consulta: R$ {oab_base['consulta']}
- Petição inicial: R$ {oab_base['peticao_inicial']}
- Ação simples: R$ {oab_base['acao_simples']}
- Ação complexa: R$ {oab_base['acao_complexa']}

**Tarefa:**
1. Calcule faixa de honorários considerando:
   - Tabela OAB como mínimo
   - Complexidade do caso
   - Valor da causa (se informado)
   - Perfil financeiro do cliente
2. Justifique a recomendação

**Formato (JSON):**
{{
    "min_value": 0000,
    "max_value": 0000,
    "suggested_value": 0000,
    "fee_type": "fixed|hourly|success|mixed",
    "factors": ["fator 1", "fator 2"],
    "oab_reference": 0000,
    "justification": "texto"
}}
"""

        try:
            llm = UnifiedLLMService.get_service()
            response = await llm.generate_async(prompt, temperature=0.3)

            import json
            import re

            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    'min_value': result.get('min_value', 0),
                    'max_value': result.get('max_value', 0),
                    'suggested_value': result.get('suggested_value', 0),
                    'fee_type': result.get('fee_type', 'fixed'),
                    'factors': result.get('factors', []),
                    'oab_reference': result.get('oab_reference', 0),
                    'justification': result.get('justification', ''),
                }
        except Exception as e:
            logger.warning(f'Erro na sugestão de honorários: {e}')

        # Fallback heurístico
        base = oab_base['acao_simples']
        multiplier = specialty_multipliers.get(
            case_data.get('specialty', 'civel') if case_data else 'civel', 1.0
        )

        return {
            'min_value': base * multiplier * 0.8,
            'max_value': base * multiplier * 1.5,
            'suggested_value': base * multiplier,
            'fee_type': 'fixed',
            'factors': ['Cálculo baseado na tabela OAB e especialidade'],
            'oab_reference': base,
            'justification': 'Valor calculado heuristicamente baseado na tabela OAB.',
        }

    @staticmethod
    def search_public_data(cpf_cnpj: str) -> Dict[str, Any]:
        """
        Busca dados públicos em APIs externas (Receita Federal, etc.).

        Nota: Implementação placeholder para integração futura.

        Args:
            cpf_cnpj: CPF ou CNPJ

        Returns:
            Dict com dados encontrados ou status da busca
        """
        # TODO: Implementar integração com:
        # - Receita Federal (CNPJ)
        # - SINTegra/SENDF (inscrição estadual)
        # - APIs de CPF (quando disponíveis legalmente)
        # - Datajud/Receitaws para consultas públicas

        logger.info(f'Busca de dados públicos para {cpf_cnpj} - não implementado')

        return {
            'status': 'not_implemented',
            'message': 'Integração com APIs públicas pendente de configuração.',
            'suggestion': 'Preencha os dados manualmente ou faça upload de documento.',
        }

    @staticmethod
    def extract_data_from_document_sync(
        file_content: bytes,
        filename: str,
        document_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Versão síncrona fallback para extração de documento."""
        # Fallback: retorna estrutura vazia
        return {
            'data': {},
            'confidence': 0,
            'error': 'Extração por IA não disponível (async)',
            'raw_text': f'Arquivo: {filename}',
        }

    @staticmethod
    def check_conflict_of_interest_sync(
        client_name: str,
        cpf_cnpj: Optional[str] = None,
        company_name: Optional[str] = None,
        case_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Versão síncrona fallback para verificação de conflito."""
        from apps.cases.models import Client, LegalCase

        # Busca direta no banco (sem IA)
        conflicts_found = []

        if cpf_cnpj:
            cpf_match = Client.objects.filter(cpf_cnpj=cpf_cnpj).first()
            if cpf_match:
                conflicts_found.append({
                    'type': 'cpf_cnpj_duplicado',
                    'name': cpf_match.name,
                    'cpf_cnpj': cpf_match.cpf_cnpj,
                })

        if client_name:
            similar = Client.objects.filter(
                Q(name__icontains=client_name) |
                Q(company_name__icontains=client_name)
            )[:5]
            for client in similar:
                if client.cpf_cnpj != cpf_cnpj:
                    conflicts_found.append({
                        'type': 'nome_similar',
                        'name': client.name,
                        'cpf_cnpj': client.cpf_cnpj,
                    })

        if conflicts_found:
            return {
                'has_conflict': True,
                'conflicts': conflicts_found,
                'risk_level': 'medium',
                'recommendation': 'Conflitos encontrados. Revise antes de prosseguir.',
                'requires_review': True,
            }

        return {
            'has_conflict': False,
            'conflicts': [],
            'risk_level': 'low',
            'recommendation': 'Nenhum conflito identificado.',
            'requires_review': False,
        }

    @staticmethod
    def suggest_fee_range_sync(
        client_data: Dict[str, Any],
        case_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Versão síncrona fallback para sugestão de honorários."""
        oab_base = {
            'consulta': 500,
            'peticao_inicial': 2000,
            'contestacao': 2500,
            'acao_simples': 3000,
            'acao_complexa': 5000,
            'recursos': 2000,
        }

        specialty_multipliers = {
            'civel': 1.0,
            'criminal': 1.3,
            'trabalhista': 1.1,
            'tributario': 1.5,
            'familia': 1.2,
            'empresarial': 1.4,
            'previdenciario': 1.0,
            'administrativo': 1.1,
        }

        base = oab_base['acao_simples']
        multiplier = specialty_multipliers.get(
            case_data.get('specialty', 'civel') if case_data else 'civel', 1.0
        )

        complexity = case_data.get('complexity', 'media') if case_data else 'media'
        if complexity == 'alta':
            base *= 1.5
        elif complexity == 'baixa':
            base *= 0.8

        min_val = base * multiplier * 0.8
        max_val = base * multiplier * 1.5

        return {
            'min_value': min_val,
            'max_value': max_val,
            'suggested_value': (min_val + max_val) / 2,
            'fee_type': 'fixed',
            'factors': ['Tabela OAB', 'Especialidade', 'Complexidade'],
            'oab_reference': oab_base['acao_simples'],
            'justification': f'Cálculo baseado na tabela OAB ({oab_base["acao_simples"]}) com multiplicadores de especialidade.',
        }

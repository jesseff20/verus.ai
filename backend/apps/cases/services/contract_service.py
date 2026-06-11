"""
Serviço para gerenciamento de contratos jurídicos.
Honorários, Procuração e Substabelecimento.
"""
import logging
import re
from datetime import datetime
from decimal import Decimal
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.core.files.base import ContentFile

from apps.cases.models import (
    LegalContract,
    HonorariosDetail,
    ProcuracaoDetail,
    SubstabelecimentoDetail,
    Client,
    LegalCase,
)

logger = logging.getLogger(__name__)


class ContractService:
    """Serviço centralizado para operações com contratos jurídicos."""

    # ── Geração de Honorários ────────────────────────────────────────────────

    @staticmethod
    def generate_honorarios(client, case, fee_details, user):
        """
        Gera contrato de honorários com IA.

        Args:
            client: instância de Client
            case: instância de LegalCase (ou None)
            fee_details: dict com fee_type, fixed_amount, hourly_rate, etc.
            user: usuário criador
        Returns:
            LegalContract com HonorariosDetail associado
        """
        # Montar prompt
        fee_type_labels = {
            'fixed': 'Valor Fixo',
            'hourly': 'Por Hora',
            'success': 'Êxito',
            'mixed': 'Misto',
        }
        fee_type = fee_details.get('fee_type', 'fixed')
        fee_label = fee_type_labels.get(fee_type, fee_type)

        prompt_parts = [
            f"Gere um contrato de honorários advocatícios completo e profissional.",
            f"Cliente: {client.name} ({client.get_client_type_display()})",
            f"CPF/CNPJ: {client.cpf_cnpj or 'Não informado'}",
            f"Endereço: {client.address or 'Não informado'}, {client.city or ''} - {client.state or ''}",
            f"Tipo de honorário: {fee_label}",
        ]

        if case:
            prompt_parts.append(f"Caso: {case.titulo}")
            prompt_parts.append(f"Número do processo: {case.numero_processo or 'Não ajuizado'}")
            prompt_parts.append(f"Especialidade: {case.get_especialidade_display()}")
            if case.valor_causa:
                prompt_parts.append(f"Valor da causa: R$ {case.valor_causa}")

        if fee_details.get('fixed_amount'):
            prompt_parts.append(f"Valor fixo: R$ {fee_details['fixed_amount']}")
        if fee_details.get('hourly_rate'):
            prompt_parts.append(f"Valor por hora: R$ {fee_details['hourly_rate']}")
        if fee_details.get('success_percentage'):
            prompt_parts.append(f"Percentual de êxito: {fee_details['success_percentage']}%")
        if fee_details.get('estimated_hours'):
            prompt_parts.append(f"Horas estimadas: {fee_details['estimated_hours']}")
        if fee_details.get('installments'):
            prompt_parts.append(f"Parcelas: {fee_details['installments']}")
        if fee_details.get('payment_terms'):
            prompt_parts.append(f"Condições de pagamento: {fee_details['payment_terms']}")
        if fee_details.get('includes_expenses'):
            prompt_parts.append("O contrato inclui despesas processuais.")

        prompt_parts.append(
            "\nGere o contrato em HTML formatado, com cláusulas numeradas, "
            "incluindo: objeto, obrigações das partes, honorários, forma de pagamento, "
            "prazo, rescisão, foro. Use linguagem jurídica formal brasileira. "
            "NÃO use markdown, retorne apenas HTML puro."
        )

        user_prompt = '\n'.join(prompt_parts)
        content_html = ContractService._generate_with_ai(user_prompt)

        # Criar contrato
        contract = LegalContract.objects.create(
            case=case,
            client=client,
            contract_type='honorarios',
            title=f"Contrato de Honorários — {client.name}",
            status='draft',
            content_html=content_html,
            created_by=user,
        )

        # Criar detalhe
        HonorariosDetail.objects.create(
            contract=contract,
            fee_type=fee_type,
            fixed_amount=fee_details.get('fixed_amount'),
            hourly_rate=fee_details.get('hourly_rate'),
            success_percentage=fee_details.get('success_percentage'),
            estimated_hours=fee_details.get('estimated_hours'),
            payment_terms=fee_details.get('payment_terms', ''),
            installments=fee_details.get('installments', 1),
            includes_expenses=fee_details.get('includes_expenses', False),
        )

        return contract

    # ── Geração de Procuração ────────────────────────────────────────────────

    @staticmethod
    def generate_procuracao(client, case, powers_detail, user):
        """
        Gera procuração com IA.

        Args:
            client: instância de Client
            case: instância de LegalCase (ou None)
            powers_detail: dict com powers_type, special_powers, etc.
            user: usuário criador
        Returns:
            LegalContract com ProcuracaoDetail associado
        """
        powers_labels = {
            'general': 'Poderes Gerais',
            'special': 'Poderes Especiais',
            'ad_judicia': 'Ad Judicia',
            'ad_judicia_extra': 'Ad Judicia et Extra',
        }
        powers_type = powers_detail.get('powers_type', 'ad_judicia')
        powers_label = powers_labels.get(powers_type, powers_type)

        prompt_parts = [
            f"Gere uma procuração jurídica completa e profissional no formato brasileiro.",
            f"Outorgante: {client.name} ({client.get_client_type_display()})",
            f"CPF/CNPJ: {client.cpf_cnpj or 'Não informado'}",
            f"RG: {client.rg or 'Não informado'}",
            f"Endereço: {client.address or 'Não informado'}, {client.city or ''} - {client.state or ''}",
            f"Tipo de poderes: {powers_label}",
        ]

        if case:
            prompt_parts.append(f"Caso: {case.titulo}")
            prompt_parts.append(f"Número do processo: {case.numero_processo or 'Não ajuizado'}")
            prompt_parts.append(f"Tribunal: {case.tribunal or 'Não informado'}")
            prompt_parts.append(f"Vara/Juízo: {case.vara_juizo or 'Não informado'}")

        if powers_detail.get('special_powers'):
            prompt_parts.append(f"Poderes especiais: {powers_detail['special_powers']}")
        if powers_detail.get('court_scope'):
            prompt_parts.append(f"Abrangência: {powers_detail['court_scope']}")
        if powers_detail.get('is_irrevocable'):
            prompt_parts.append("A procuração é IRREVOGÁVEL.")
        if powers_detail.get('valid_until'):
            prompt_parts.append(f"Válida até: {powers_detail['valid_until']}")

        prompt_parts.append(
            "\nGere a procuração em HTML formatado, com linguagem jurídica formal "
            "brasileira, incluindo qualificação completa do outorgante, "
            "cláusula de poderes, abrangência, local e data. "
            "NÃO use markdown, retorne apenas HTML puro."
        )

        user_prompt = '\n'.join(prompt_parts)
        content_html = ContractService._generate_with_ai(user_prompt)

        contract = LegalContract.objects.create(
            case=case,
            client=client,
            contract_type='procuracao',
            title=f"Procuração — {client.name}",
            status='draft',
            content_html=content_html,
            created_by=user,
        )

        ProcuracaoDetail.objects.create(
            contract=contract,
            powers_type=powers_type,
            special_powers=powers_detail.get('special_powers', ''),
            court_scope=powers_detail.get('court_scope', 'Todos os foros e instâncias'),
            valid_until=powers_detail.get('valid_until'),
            is_irrevocable=powers_detail.get('is_irrevocable', False),
        )

        return contract

    # ── Geração de Substabelecimento ─────────────────────────────────────────

    @staticmethod
    def generate_substabelecimento(client, original_procuracao, substabelecido_info, user):
        """
        Gera substabelecimento com IA.

        Args:
            client: instância de Client
            original_procuracao: instância de LegalContract (procuração original, ou None)
            substabelecido_info: dict com substabelecido_name, oab, etc.
            user: usuário criador
        Returns:
            LegalContract com SubstabelecimentoDetail associado
        """
        with_reserve = substabelecido_info.get('with_reserve', True)
        reserve_text = 'COM reserva de poderes' if with_reserve else 'SEM reserva de poderes'

        prompt_parts = [
            f"Gere um substabelecimento jurídico completo e profissional no formato brasileiro.",
            f"Substabelecente/Outorgante: {client.name}",
            f"Substabelecido: {substabelecido_info.get('substabelecido_name', '')}",
            f"OAB: {substabelecido_info.get('substabelecido_oab', '')} / {substabelecido_info.get('substabelecido_oab_state', '')}",
            f"Modalidade: {reserve_text}",
        ]

        if original_procuracao:
            prompt_parts.append(f"Procuração original: {original_procuracao.title}")
            if original_procuracao.created_at:
                prompt_parts.append(f"Data da procuração original: {original_procuracao.created_at.strftime('%d/%m/%Y')}")

        if substabelecido_info.get('powers_transferred'):
            prompt_parts.append(f"Poderes transferidos: {substabelecido_info['powers_transferred']}")
        if substabelecido_info.get('reason'):
            prompt_parts.append(f"Motivo: {substabelecido_info['reason']}")

        prompt_parts.append(
            "\nGere o substabelecimento em HTML formatado, com linguagem jurídica formal "
            "brasileira. Inclua referência à procuração original, qualificação do "
            "substabelecido, poderes transferidos, modalidade e local/data. "
            "NÃO use markdown, retorne apenas HTML puro."
        )

        user_prompt = '\n'.join(prompt_parts)
        content_html = ContractService._generate_with_ai(user_prompt)

        case = original_procuracao.case if original_procuracao else None

        contract = LegalContract.objects.create(
            case=case,
            client=client,
            contract_type='substabelecimento',
            title=f"Substabelecimento — {substabelecido_info.get('substabelecido_name', '')}",
            status='draft',
            content_html=content_html,
            created_by=user,
        )

        SubstabelecimentoDetail.objects.create(
            contract=contract,
            original_procuracao=original_procuracao,
            substabelecido_name=substabelecido_info.get('substabelecido_name', ''),
            substabelecido_oab=substabelecido_info.get('substabelecido_oab', ''),
            substabelecido_oab_state=substabelecido_info.get('substabelecido_oab_state', ''),
            with_reserve=with_reserve,
            powers_transferred=substabelecido_info.get('powers_transferred', ''),
            reason=substabelecido_info.get('reason', ''),
        )

        return contract

    # ── Geração de PDF ───────────────────────────────────────────────────────

    @staticmethod
    def generate_contract_pdf(contract_id):
        """
        Gera PDF a partir do HTML do contrato usando WeasyPrint.

        Returns:
            LegalContract com generated_pdf atualizado
        """
        contract = LegalContract.objects.get(id=contract_id)

        if not contract.content_html:
            raise ValueError("Contrato não possui conteúdo HTML para gerar PDF.")

        try:
            from weasyprint import HTML
            from django.core.files.base import ContentFile

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: 'Times New Roman', serif; font-size: 12pt; line-height: 1.6; margin: 2cm; }}
                    h1 {{ text-align: center; font-size: 16pt; }}
                    h2 {{ font-size: 14pt; }}
                    p {{ text-align: justify; }}
                </style>
            </head>
            <body>{contract.content_html}</body>
            </html>
            """

            pdf_bytes = HTML(string=html_content).write_pdf()
            filename = f"contrato_{contract.id}.pdf"
            contract.generated_pdf.save(filename, ContentFile(pdf_bytes))
            contract.save(update_fields=['generated_pdf'])

        except ImportError:
            logger.warning("[ContractService] WeasyPrint não instalado. PDF não gerado.")
            raise ValueError("WeasyPrint não está instalado no servidor.")
        except Exception as exc:
            logger.error(f"[ContractService] Erro ao gerar PDF: {exc}", exc_info=True)
            raise

        return contract

    # ── Marcar como assinado ─────────────────────────────────────────────────

    @staticmethod
    def mark_signed(contract_id):
        """Marca contrato como assinado."""
        contract = LegalContract.objects.get(id=contract_id)
        contract.status = 'signed'
        contract.signed_at = timezone.now()
        contract.save(update_fields=['status', 'signed_at', 'updated_at'])
        return contract

    # ── Estatísticas ─────────────────────────────────────────────────────────

    @staticmethod
    def get_contract_statistics(user):
        """Retorna estatísticas de contratos."""
        is_admin = user.is_staff or user.is_superuser or getattr(user, 'role', '') in ('superadmin', 'admin')

        if is_admin:
            qs = LegalContract.objects.all()
        else:
            qs = LegalContract.objects.filter(created_by=user)

        total = qs.count()
        by_type = dict(
            qs.values('contract_type')
            .annotate(n=Count('id'))
            .values_list('contract_type', 'n')
        )
        by_status = dict(
            qs.values('status')
            .annotate(n=Count('id'))
            .values_list('status', 'n')
        )

        # Valor total de honorários
        valor_total = (
            HonorariosDetail.objects
            .filter(contract__in=qs, contract__contract_type='honorarios')
            .aggregate(total=Sum('fixed_amount'))['total']
        ) or Decimal('0')

        return {
            'total': total,
            'by_type': by_type,
            'by_status': by_status,
            'signed': by_status.get('signed', 0),
            'pending': by_status.get('pending_signature', 0),
            'draft': by_status.get('draft', 0),
            'valor_total_honorarios': str(valor_total),
        }

    # ── Helper: geração com IA ───────────────────────────────────────────────

    # ── Upload e Análise com IA ──────────────────────────────────────────────

    @staticmethod
    def upload_and_analyze_contract(uploaded_file, user, contract_type=None):
        """
        Faz upload de um contrato e usa IA para analisar e extrair dados.

        Args:
            uploaded_file: arquivo Django (request.FILES)
            user: usuário que fez upload
            contract_type: tipo de contrato (opcional, IA tentará detectar)
        Returns:
            LegalContract com dados preenchidos automaticamente
        """
        # Salvar arquivo temporariamente
        temp_contract = LegalContract.objects.create(
            status='draft',
            title=f'Análise de {uploaded_file.name}',
            created_by=user,
        )
        temp_contract.uploaded_file.save(
            uploaded_file.name,
            uploaded_file,
            save=True
        )

        # Extrair texto do arquivo
        file_text = ContractService._extract_text_from_file(temp_contract.uploaded_file)

        # Analisar com IA
        analysis = ContractService._analyze_contract_with_ai(file_text, contract_type)

        # Extrair dados estruturados
        extracted_data = ContractService._parse_ai_analysis(analysis)

        # Buscar cliente existente ou criar
        client = ContractService._find_or_create_client(extracted_data, user)

        # Atualizar contrato com dados extraídos
        temp_contract.client = client
        temp_contract.contract_type = extracted_data.get('contract_type', contract_type or 'prestacao_servicos')
        temp_contract.title = extracted_data.get('title', f"Contrato — {client.name}")
        temp_contract.content_html = ContractService._convert_to_html(analysis)
        temp_contract.metadata = {
            'analysis': analysis,
            'extracted_data': extracted_data,
            'auto_filled': True,
        }
        temp_contract.save()

        return temp_contract, extracted_data

    @staticmethod
    def _extract_text_from_file(file_field):
        """Extrai texto de PDF ou DOCX."""
        try:
            file_path = file_field.path
            if file_path.lower().endswith('.pdf'):
                # Tentar pypdf
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(file_path)
                    return '\n'.join(page.extract_text() for page in reader.pages if page.extract_text())
                except ImportError:
                    logger.warning("pypdf não instalado. Usando fallback.")
            elif file_path.lower().endswith('.docx'):
                try:
                    from docx import Document
                    doc = Document(file_path)
                    return '\n'.join(p.text for p in doc.paragraphs)
                except ImportError:
                    logger.warning("python-docx não instalado.")
        except Exception as exc:
            logger.error(f"[ContractService] Erro ao extrair texto: {exc}")

        # Fallback: retornar nome do arquivo
        return f"Arquivo: {file_field.name}"

    @staticmethod
    def _analyze_contract_with_ai(file_text, contract_type=None):
        """Analisa contrato com IA e retorna dados estruturados."""
        try:
            from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService
            llm = UnifiedLLMService()

            type_hint = f" (provavelmente {contract_type})" if contract_type else ""
            prompt = f"""Você é um assistente jurídico especializado em análise de contratos brasileiros.

Analise o seguinte contrato{type_hint} e extraia TODAS as informações abaixo em formato JSON válido.
Retorne APENAS o JSON, sem markdown ou explicações.

Extraia:
1. contract_type: tipo do contrato (honorarios, procuracao, prestacao_servicos, etc.)
2. title: título sugerido
3. client_name: nome do cliente/contratante
4. client_type: pessoa_fisica ou pessoa_juridica
5. cpf_cnpj: CPF ou CNPJ do cliente
6. email: e-mail do cliente
7. phone: telefone do cliente
8. address: endereço completo
9. city: cidade
10. state: UF
11. contract_value: valor do contrato (se houver)
12. payment_terms: condições de pagamento
13. key_clauses: principais cláusulas (lista)
14. parties: partes envolvidas (nome, qualificação)
15. obligations: obrigações de cada parte
16. term: prazo/vigência do contrato
17. termination: condições de rescisão
18. forum: foro eleito

CONTRATO:
{file_text[:15000]}  # Limitar para não exceder token limit

Retorne JSON válido."""

            result = llm.generate(
                user_prompt=prompt,
                system_prompt='Você é um assistente jurídico especializado em análise de contratos brasileiros. Retorne APENAS JSON válido, sem markdown.',
                provider='watsonx',
                model='mistralai/mistral-medium-2505',
                max_tokens=4000,
                temperature=0.1,
            )
            content = result.get('content', '').strip()
            # Limpar markdown se houver
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            return content.strip()
        except Exception as exc:
            logger.error(f"[ContractService._analyze_contract_with_ai] Erro: {exc}", exc_info=True)
            return '{"error": "Erro na análise com IA"}'

    @staticmethod
    def _parse_ai_analysis(analysis_json):
        """Parse do JSON retornado pela IA."""
        import json
        try:
            data = json.loads(analysis_json)
            # Normalizar campos
            return {
                'contract_type': data.get('contract_type', 'prestacao_servicos'),
                'title': data.get('title', 'Contrato Analisado'),
                'client_name': data.get('client_name', ''),
                'client_type': data.get('client_type', 'pessoa_fisica'),
                'cpf_cnpj': data.get('cpf_cnpj', ''),
                'email': data.get('email', ''),
                'phone': data.get('phone', ''),
                'address': data.get('address', ''),
                'city': data.get('city', ''),
                'state': data.get('state', ''),
                'contract_value': data.get('contract_value'),
                'payment_terms': data.get('payment_terms', ''),
                'key_clauses': data.get('key_clauses', []),
                'parties': data.get('parties', []),
                'obligations': data.get('obligations', {}),
                'term': data.get('term', ''),
                'termination': data.get('termination', ''),
                'forum': data.get('forum', ''),
            }
        except (json.JSONDecodeError, Exception) as exc:
            logger.error(f"[ContractService._parse_ai_analysis] Erro: {exc}")
            return {'contract_type': 'prestacao_servicos', 'title': 'Contrato Analisado'}

    @staticmethod
    def _find_or_create_client(extracted_data, user):
        """Busca cliente existente pelo CPF/CNPJ ou nome, ou cria novo."""
        cpf_cnpj = extracted_data.get('cpf_cnpj', '')
        client_name = extracted_data.get('client_name', '')

        # Tentar buscar por CPF/CNPJ
        if cpf_cnpj:
            client = Client.objects.filter(cpf_cnpj=cpf_cnpj).first()
            if client:
                return client

        # Tentar buscar por nome (fuzzy)
        if client_name:
            client = Client.objects.filter(name__icontains=client_name[:50]).first()
            if client:
                return client

        # Criar novo cliente
        return Client.objects.create(
            name=client_name or 'Cliente não identificado',
            client_type=extracted_data.get('client_type', 'pessoa_fisica'),
            cpf_cnpj=cpf_cnpj,
            email=extracted_data.get('email', ''),
            phone=extracted_data.get('phone', ''),
            address=extracted_data.get('address', ''),
            city=extracted_data.get('city', ''),
            state=extracted_data.get('state', ''),
            company_name=client_name if extracted_data.get('client_type') == 'pessoa_juridica' else '',
            created_by=user,
        )

    @staticmethod
    def _convert_to_html(analysis_json):
        """Converte análise JSON em HTML formatado."""
        import json
        try:
            data = json.loads(analysis_json)
        except:
            data = {}

        parties_html = ''
        if data.get('parties'):
            for party in data['parties']:
                parties_html += f"<p><strong>Parte:</strong> {party}</p>"

        clauses_html = ''
        if data.get('key_clauses'):
            clauses_html = '<h3>Cláusulas Principais</h3><ul>'
            for clause in data['key_clauses']:
                clauses_html += f'<li>{clause}</li>'
            clauses_html += '</ul>'

        return f"""
<h1>Contrato Analisado</h1>
<h2>Dados do Cliente</h2>
<p><strong>Nome:</strong> {data.get('client_name', 'N/A')}</p>
<p><strong>CPF/CNPJ:</strong> {data.get('cpf_cnpj', 'N/A')}</p>
<p><strong>E-mail:</strong> {data.get('email', 'N/A')}</p>
<p><strong>Telefone:</strong> {data.get('phone', 'N/A')}</p>
<p><strong>Endereço:</strong> {data.get('address', 'N/A')} - {data.get('city', '')} {data.get('state', '')}</p>
{parties_html}
{clauses_html}
<h3>Condições de Pagamento</h3>
<p>{data.get('payment_terms', 'Não especificado')}</p>
<h3>Vigência</h3>
<p>{data.get('term', 'Não especificado')}</p>
<h3>Rescisão</h3>
<p>{data.get('termination', 'Não especificado')}</p>
<h3>Foro</h3>
<p>{data.get('forum', 'Não especificado')}</p>
"""

    # ── Helper: geração com IA ───────────────────────────────────────────────

    @staticmethod
    def _generate_with_ai(user_prompt):
        """Gera conteúdo HTML usando o serviço de LLM."""
        try:
            from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService
            llm = UnifiedLLMService()
            result = llm.generate(
                user_prompt=user_prompt,
                system_prompt=(
                    'Você é um assistente jurídico especializado em contratos e documentos '
                    'jurídicos brasileiros. Gere documentos em HTML puro (sem markdown), '
                    'com formatação profissional e linguagem jurídica formal. '
                    'Use tags HTML como <h1>, <h2>, <p>, <ol>, <li>, <strong>, <em>. '
                    'Não inclua tags <html>, <head> ou <body>.'
                ),
                provider='watsonx',
                model='mistralai/mistral-medium-2505',
                max_tokens=3000,
                temperature=0.3,
            )
            content = result.get('content', '').strip()
            # Remove markdown wrappers if any
            if '```html' in content:
                content = content.split('```html')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            return content.strip()
        except Exception as exc:
            logger.error(f"[ContractService._generate_with_ai] Erro: {exc}", exc_info=True)
            return '<p><em>Erro ao gerar conteúdo com IA. Edite manualmente.</em></p>'

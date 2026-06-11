"""
ClientCopilotService - AI assistant for law firm clients.
Limited to client's own cases. Always recommends consulting the lawyer.
"""
import json
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

CLIENT_SYSTEM_PROMPT = """Você é o assistente virtual do Verus.AI, um escritório de advocacia.
Você está conversando com um CLIENTE do escritório, NÃO com um advogado.

REGRAS FUNDAMENTAIS:
1. NUNCA dê conselhos jurídicos. Você explica termos e status, mas SEMPRE recomende que o cliente converse com seu advogado responsável para decisões.
2. Só acesse informações dos casos DESTE cliente. Nunca mencione outros clientes.
3. Use linguagem simples e acessível. Evite jargão jurídico sem explicação.
4. Seja empático e profissional.
5. Quando o cliente perguntar algo que requer decisão jurídica, diga: "Recomendo que converse com seu advogado sobre isso. Posso ajudá-lo a enviar uma mensagem?"
6. Você pode explicar termos jurídicos, mostrar status de processos, listar prazos e documentos.
7. Encerre respostas complexas com: "Para orientação jurídica específica, converse com Dr./Dra. [nome do advogado]."

CONTEXTO DO CLIENTE:
{client_context}

CASOS DO CLIENTE:
{cases_context}
"""


class ClientCopilotService:
    """AI assistant for clients - limited scope, always recommends lawyer."""

    @staticmethod
    def build_client_context(client):
        """Build context string about the client."""
        return f"""
Nome: {client.name}
Tipo: {client.get_client_type_display()}
E-mail: {client.email or 'não informado'}
"""

    @staticmethod
    def build_cases_context(client):
        """Build context about client's cases."""
        from apps.cases.models import LegalCase, LegalDeadline, CasePhase, Audiencia

        cases = LegalCase.objects.filter(client=client).select_related('advogado_responsavel')
        if not cases.exists():
            return "O cliente não possui casos ativos no momento."

        context_parts = []
        for case in cases[:5]:  # Max 5 cases for context
            lawyer_name = ''
            if case.advogado_responsavel:
                lawyer_name = case.advogado_responsavel.get_full_name() or case.advogado_responsavel.username

            # Get current phase
            current_phase = CasePhase.objects.filter(caso=case).order_by('-created_at').first()

            # Get upcoming deadlines
            deadlines = LegalDeadline.objects.filter(
                caso=case, status='pendente', data_prazo__gte=timezone.now().date()
            ).order_by('data_prazo')[:3]

            # Get upcoming hearings
            hearings = Audiencia.objects.filter(
                caso=case, data_hora__gte=timezone.now()
            ).order_by('data_hora')[:2]

            part = f"""
--- Caso: {case.titulo} ---
Número: {case.numero_processo or 'não informado'}
Status: {case.get_status_display()}
Fase Atual: {current_phase.name if current_phase else 'não definida'}
Advogado Responsável: {lawyer_name or 'não atribuído'}
Tribunal: {case.tribunal or 'não informado'}
Vara: {case.vara_juizo or 'não informado'}
"""
            if deadlines:
                part += "Próximos Prazos:\n"
                for d in deadlines:
                    part += f"  - {d.titulo}: {d.data_prazo.strftime('%d/%m/%Y')} ({d.get_prioridade_display()})\n"

            if hearings:
                part += "Próximas Audiências:\n"
                for h in hearings:
                    part += f"  - {h.get_tipo_display()}: {h.data_hora.strftime('%d/%m/%Y %H:%M')} em {h.local or 'local a definir'}\n"

            context_parts.append(part)

        return "\n".join(context_parts)

    @staticmethod
    def process_command(client, message):
        """Process @commands from client messages."""
        msg = message.strip().lower()

        from apps.cases.models import LegalCase, LegalDeadline, Audiencia, CaseDocument
        from apps.accounts.models import ClientMessage

        # @status or "status do meu processo"
        if '@status' in msg or ('status' in msg and 'processo' in msg):
            cases = LegalCase.objects.filter(client=client).select_related('advogado_responsavel')
            if not cases.exists():
                return "Você não possui processos registrados no momento. Se acredita que há um erro, entre em contato com o escritório."
            result = "📋 **Status dos seus processos:**\n\n"
            for c in cases:
                lawyer = c.advogado_responsavel
                lawyer_name = lawyer.get_full_name() if lawyer else 'não atribuído'
                result += f"**{c.titulo}**\n"
                result += f"- Número: {c.numero_processo or 'não informado'}\n"
                result += f"- Status: {c.get_status_display()}\n"
                result += f"- Advogado: {lawyer_name}\n\n"
            result += "\n💡 *Para detalhes, clique em \"Meus Casos\" no menu lateral.*"
            return result

        # @prazos
        if '@prazos' in msg or 'prazo' in msg:
            deadlines = LegalDeadline.objects.filter(
                caso__client=client, status='pendente', data_prazo__gte=timezone.now().date()
            ).select_related('caso').order_by('data_prazo')[:10]
            if not deadlines:
                return "✅ Você não possui prazos pendentes no momento."
            result = "📅 **Seus próximos prazos:**\n\n"
            for d in deadlines:
                days_left = (d.data_prazo - timezone.now().date()).days
                urgency = "🔴" if days_left <= 3 else "🟡" if days_left <= 7 else "🟢"
                result += f"{urgency} **{d.titulo}** - {d.data_prazo.strftime('%d/%m/%Y')} ({days_left} dias)\n"
                result += f"   Caso: {d.caso.titulo}\n\n"
            result += "\n⚠️ *Se tiver dúvidas sobre algum prazo, converse com seu advogado.*"
            return result

        # @audiencias
        if '@audiencia' in msg or 'audiência' in msg or 'audiencia' in msg:
            hearings = Audiencia.objects.filter(
                caso__client=client, data_hora__gte=timezone.now()
            ).select_related('caso').order_by('data_hora')[:5]
            if not hearings:
                return "📅 Você não possui audiências agendadas no momento."
            result = "🏛️ **Suas próximas audiências:**\n\n"
            for h in hearings:
                result += f"**{h.get_tipo_display()}** - {h.data_hora.strftime('%d/%m/%Y às %H:%M')}\n"
                result += f"- Caso: {h.caso.titulo}\n"
                result += f"- Local: {h.local or 'a definir'}\n"
                if h.observacoes:
                    result += f"- Observações: {h.observacoes}\n"
                result += "\n"
            result += "💡 *Chegue com antecedência e leve os documentos solicitados pelo seu advogado.*"
            return result

        # @documentos
        if '@documento' in msg or ('documento' in msg and ('preciso' in msg or 'enviar' in msg or 'pendente' in msg)):
            result = "📄 **Sobre seus documentos:**\n\n"
            result += "Você pode:\n"
            result += "- 📥 **Enviar documentos**: Acesse \"Documentos\" no menu e clique em \"Enviar Documento\"\n"
            result += "- 📋 **Ver documentos**: Acesse a página de cada caso para ver os documentos disponíveis\n\n"
            result += "💡 *Se não sabe quais documentos enviar, pergunte ao seu advogado.*"
            return result

        # @financeiro or "quanto devo"
        if '@financeiro' in msg or 'financeiro' in msg or 'devo' in msg or 'pagamento' in msg or 'valor' in msg:
            result = "💰 **Informações financeiras:**\n\n"
            result += "Acesse a seção \"Financeiro\" no menu lateral para ver:\n"
            result += "- Valores devidos e pagos\n"
            result += "- Próximos vencimentos\n"
            result += "- Histórico de pagamentos\n\n"
            result += "⚠️ *Para dúvidas sobre valores ou negociação, entre em contato com seu advogado.*"
            return result

        # @advogado or "falar com advogado"
        if '@advogado' in msg or ('advogado' in msg and ('falar' in msg or 'contato' in msg or 'mensagem' in msg)):
            result = "💬 **Contato com seu advogado:**\n\n"
            result += "Você pode enviar uma mensagem diretamente pela seção \"Mensagens\" no menu lateral.\n\n"
            cases = LegalCase.objects.filter(client=client).select_related('advogado_responsavel')
            for c in cases:
                if c.advogado_responsavel:
                    name = c.advogado_responsavel.get_full_name()
                    result += f"- **{c.titulo}**: {name}\n"
            result += "\n💡 *Seu advogado receberá uma notificação quando você enviar a mensagem.*"
            return result

        return None  # No command matched, use LLM

    @staticmethod
    def generate_response(client, message):
        """Generate AI response for client query."""
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        # Check commands first
        command_result = ClientCopilotService.process_command(client, message)
        if command_result:
            return command_result

        # Build context and use LLM
        client_ctx = ClientCopilotService.build_client_context(client)
        cases_ctx = ClientCopilotService.build_cases_context(client)

        system_prompt = CLIENT_SYSTEM_PROMPT.format(
            client_context=client_ctx,
            cases_context=cases_ctx,
        )

        try:
            llm = UnifiedLLMService()
            result = llm.generate(
                user_prompt=message,
                system_prompt=system_prompt,
                provider='watsonx',
                model='mistralai/mistral-medium-2505',
                max_tokens=800,
                temperature=0.4,
            )
            response = result.get('content', '') or result.get('text', '')
            if response:
                return response.strip()
        except Exception as e:
            logger.exception('Client copilot LLM error')

        return (
            "Desculpe, não consegui processar sua pergunta no momento. "
            "Tente novamente ou entre em contato com seu advogado diretamente "
            "pela seção \"Mensagens\"."
        )

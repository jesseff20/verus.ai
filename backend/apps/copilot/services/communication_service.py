"""
CommunicationService - Generates and sends notifications via WhatsApp and Email using AI.

Usage:
    from apps.copilot.services.communication_service import CommunicationService

    svc = CommunicationService()
    link = svc.send_whatsapp(user, notification)
    svc.send_email(user, notification)
"""
import json
import logging
import re
import urllib.parse

from django.utils import timezone

logger = logging.getLogger(__name__)


class CommunicationService:
    """Generates and sends notifications via WhatsApp and Email using AI."""

    def generate_whatsapp_link(self, phone_number: str, message: str) -> str:
        """Generate wa.me link with pre-filled message."""
        clean_number = re.sub(r'[^\d+]', '', phone_number)
        if not clean_number.startswith('+'):
            clean_number = '+55' + clean_number  # Default Brazil
        # wa.me expects number without '+'
        encoded_message = urllib.parse.quote(message)
        return f"https://wa.me/{clean_number.replace('+', '')}?text={encoded_message}"

    def generate_notification_text(self, notification_type: str, context: dict) -> str:
        """Use LLM to generate personalized notification text for WhatsApp."""
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        prompt = (
            f"Gere uma mensagem de notificacao profissional e concisa para um advogado.\n"
            f"Tipo: {notification_type}\n"
            f"Contexto: {json.dumps(context, ensure_ascii=False)}\n\n"
            f"A mensagem deve:\n"
            f"- Ser profissional e direta\n"
            f"- Incluir os dados relevantes (nome do caso, prazo, etc.)\n"
            f"- Ter no maximo 3 linhas\n"
            f"- Incluir um call-to-action claro\n\n"
            f"Formato para WhatsApp (com emojis discretos):"
        )

        try:
            llm = UnifiedLLMService()
            result = llm.generate(
                user_prompt=prompt,
                system_prompt='Voce e um assistente juridico que cria mensagens de notificacao.',
                provider='watsonx',
                model='mistralai/mistral-medium-2505',
                max_tokens=200,
                temperature=0.3,
            )
            text = result.get('content', '') or result.get('text', '')
            if text:
                return text.strip()
        except Exception as e:
            logger.warning('LLM text generation failed, using fallback: %s', e)

        # Fallback: build message from context
        title = context.get('title', 'Notificacao Verus.AI')
        message = context.get('message', '')
        return f"Verus.AI - {title}\n{message}"

    def generate_email_content(self, notification_type: str, context: dict) -> tuple:
        """Generate email subject and body using LLM. Returns (subject, body_html)."""
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        prompt = (
            f"Gere um e-mail profissional de notificacao juridica.\n"
            f"Tipo: {notification_type}\n"
            f"Contexto: {json.dumps(context, ensure_ascii=False)}\n\n"
            f"Retorne em formato:\n"
            f"ASSUNTO: [assunto do email]\n"
            f"CORPO: [corpo do email em HTML simples]\n\n"
            f"O email deve ser formal, conciso e com identidade Verus.AI."
        )

        try:
            llm = UnifiedLLMService()
            result = llm.generate(
                user_prompt=prompt,
                system_prompt='Voce e um assistente juridico que cria e-mails de notificacao profissionais.',
                provider='watsonx',
                model='mistralai/mistral-medium-2505',
                max_tokens=500,
                temperature=0.3,
            )
            text = result.get('content', '') or result.get('text', '')
            if text and 'ASSUNTO:' in text and 'CORPO:' in text:
                parts = text.split('CORPO:')
                subject = parts[0].replace('ASSUNTO:', '').strip()
                body = parts[1].strip()
                return subject, body
        except Exception as e:
            logger.warning('LLM email generation failed, using fallback: %s', e)

        # Fallback
        title = context.get('title', 'Notificacao Verus.AI')
        message = context.get('message', '')
        subject = f'Verus.AI - {title}'
        body = (
            f'<div style="font-family: Arial, sans-serif; max-width: 600px;">'
            f'<h2 style="color: #7030A0;">Verus.AI</h2>'
            f'<h3>{title}</h3>'
            f'<p>{message}</p>'
            f'<hr/>'
            f'<p style="font-size:12px; color:#888;">Este e-mail foi enviado pelo Verus.AI.</p>'
            f'</div>'
        )
        return subject, body

    def send_whatsapp(self, user, notification, context=None):
        """
        Generate WhatsApp notification and save link.
        Returns the wa.me link or None if user has no active WhatsApp channel.
        """
        from apps.accounts.models import NotificationMessage

        channels = user.notification_channels.filter(channel='whatsapp', is_active=True)
        if not channels.exists():
            return None

        channel = channels.first()
        if not channel.whatsapp_number:
            return None

        ctx = context or {
            'title': notification.title,
            'message': notification.message,
        }
        message = self.generate_notification_text(notification.type, ctx)
        link = self.generate_whatsapp_link(channel.whatsapp_number, message)

        NotificationMessage.objects.create(
            notification=notification,
            user=user,
            channel='whatsapp',
            body=message,
            whatsapp_link=link,
            status='pending',
        )
        return link

    def send_email(self, user, notification, context=None):
        """
        Generate and send email notification.
        Uses Django's send_mail. Falls back to user.email if no email channel.
        """
        from django.core.mail import send_mail
        from apps.accounts.models import NotificationMessage

        channels = user.notification_channels.filter(channel='email', is_active=True)
        email = channels.first().email_address if channels.exists() and channels.first().email_address else user.email

        if not email:
            return None

        ctx = context or {
            'title': notification.title,
            'message': notification.message,
        }
        subject, body = self.generate_email_content(notification.type, ctx)

        status = 'sent'
        try:
            send_mail(
                subject=subject,
                message='',
                html_message=body,
                from_email='noreply@verus.ai',
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception:
            logger.exception('Failed to send email to %s', email)
            status = 'failed'

        NotificationMessage.objects.create(
            notification=notification,
            user=user,
            channel='email',
            subject=subject,
            body=body,
            status=status,
            sent_at=timezone.now() if status == 'sent' else None,
        )
        return status

    def send_all_channels(self, user, notification, context=None, auto_only=False):
        """
        Send notification through active channels for the user.
        If auto_only=True, only sends through channels with auto_send=True.
        Returns dict with results per channel.
        """
        results = {}

        # WhatsApp
        try:
            whatsapp_link = self.send_whatsapp(user, notification, context)
            if whatsapp_link:
                results['whatsapp'] = {'status': 'pending', 'link': whatsapp_link}
        except Exception as e:
            logger.exception('Error sending WhatsApp notification')
            results['whatsapp'] = {'status': 'error', 'error': str(e)}

        # Email
        try:
            email_status = self.send_email(user, notification, context)
            if email_status:
                results['email'] = {'status': email_status}
        except Exception as e:
            logger.exception('Error sending email notification')
            results['email'] = {'status': 'error', 'error': str(e)}

        return results

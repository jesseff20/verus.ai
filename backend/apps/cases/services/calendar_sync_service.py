"""
Serviço de sincronização com Google Calendar e Microsoft Outlook.
Preparado para integração — requer credenciais OAuth2.
"""
import logging
from datetime import datetime, timedelta
from django.conf import settings

logger = logging.getLogger(__name__)


class CalendarSyncService:
    """Sincroniza audiências e prazos com calendários externos."""

    PROVIDERS = {
        'google': {
            'name': 'Google Calendar',
            'auth_url': 'https://accounts.google.com/o/oauth2/v2/auth',
            'token_url': 'https://oauth2.googleapis.com/token',
            'scopes': ['https://www.googleapis.com/auth/calendar'],
            'api_base': 'https://www.googleapis.com/calendar/v3',
        },
        'outlook': {
            'name': 'Microsoft Outlook',
            'auth_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
            'token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
            'scopes': ['Calendars.ReadWrite'],
            'api_base': 'https://graph.microsoft.com/v1.0',
        },
    }

    @classmethod
    def get_auth_url(cls, provider: str, user_id, redirect_uri: str) -> dict:
        """Gera URL de autorização OAuth2."""
        if provider not in cls.PROVIDERS:
            return {'error': f'Provider não suportado: {provider}'}

        config = cls.PROVIDERS[provider]

        if provider == 'google':
            client_id = getattr(settings, 'GOOGLE_CALENDAR_CLIENT_ID', '')
            if not client_id:
                return {
                    'error': 'GOOGLE_CALENDAR_CLIENT_ID não configurado',
                    'setup_required': True,
                    'env_vars': ['GOOGLE_CALENDAR_CLIENT_ID', 'GOOGLE_CALENDAR_CLIENT_SECRET'],
                }

            import urllib.parse
            params = {
                'client_id': client_id,
                'redirect_uri': redirect_uri,
                'response_type': 'code',
                'scope': ' '.join(config['scopes']),
                'access_type': 'offline',
                'state': str(user_id),
            }
            auth_url = f"{config['auth_url']}?{urllib.parse.urlencode(params)}"
            return {'auth_url': auth_url, 'provider': provider}

        elif provider == 'outlook':
            client_id = getattr(settings, 'OUTLOOK_CLIENT_ID', '')
            if not client_id:
                return {
                    'error': 'OUTLOOK_CLIENT_ID não configurado',
                    'setup_required': True,
                    'env_vars': ['OUTLOOK_CLIENT_ID', 'OUTLOOK_CLIENT_SECRET', 'OUTLOOK_TENANT_ID'],
                }

            import urllib.parse
            params = {
                'client_id': client_id,
                'redirect_uri': redirect_uri,
                'response_type': 'code',
                'scope': ' '.join(config['scopes']),
                'state': str(user_id),
            }
            auth_url = f"{config['auth_url']}?{urllib.parse.urlencode(params)}"
            return {'auth_url': auth_url, 'provider': provider}

    @classmethod
    def sync_events(cls, user, provider: str, access_token: str) -> dict:
        """
        Sincroniza audiências e prazos do usuário com o calendário externo.
        Cria eventos no calendário para cada audiência e prazo.
        """
        from apps.cases.models import Audiencia, LegalDeadline

        events_synced = 0
        errors = []

        # Get audiências
        audiencias = Audiencia.objects.filter(
            caso__advogado_responsavel=user,
            status='agendada',
        ).select_related('caso')

        # Get prazos pendentes
        prazos = LegalDeadline.objects.filter(
            responsavel=user,
            status__in=['pendente', 'em_andamento'],
        ).select_related('caso')

        events_to_sync = []

        for aud in audiencias:
            events_to_sync.append({
                'summary': f'[Audiência] {aud.get_tipo_display()} — {aud.caso.titulo}',
                'description': f'Caso: {aud.caso.numero_processo or aud.caso.titulo}\nLocal: {aud.local}\nJuiz: {aud.juiz}\n\n{aud.observacoes}',
                'start': aud.data_hora.isoformat(),
                'end': (aud.data_hora + timedelta(hours=2)).isoformat(),
                'location': aud.local,
                'color': '11',  # Red for hearings
                'source_type': 'audiencia',
                'source_id': str(aud.id),
            })

        for prazo in prazos:
            events_to_sync.append({
                'summary': f'[Prazo] {prazo.titulo} — {prazo.caso.titulo}',
                'description': f'Caso: {prazo.caso.numero_processo or prazo.caso.titulo}\nTipo: {prazo.get_tipo_display()}\nPrioridade: {prazo.get_prioridade_display()}\n\n{prazo.descricao}',
                'start': f'{prazo.data_prazo}T09:00:00',
                'end': f'{prazo.data_prazo}T09:30:00',
                'color': '6' if prazo.prioridade in ('alta', 'urgente') else '9',
                'source_type': 'prazo',
                'source_id': str(prazo.id),
            })

        if provider == 'google':
            for event_data in events_to_sync:
                result = cls._create_google_event(access_token, event_data)
                if result.get('success'):
                    events_synced += 1
                else:
                    errors.append(result.get('error', 'Unknown error'))

        elif provider == 'outlook':
            for event_data in events_to_sync:
                result = cls._create_outlook_event(access_token, event_data)
                if result.get('success'):
                    events_synced += 1
                else:
                    errors.append(result.get('error', 'Unknown error'))

        return {
            'provider': provider,
            'total_events': len(events_to_sync),
            'events_synced': events_synced,
            'errors': errors,
        }

    @staticmethod
    def _create_google_event(access_token: str, event_data: dict) -> dict:
        """Cria evento no Google Calendar."""
        import requests

        calendar_event = {
            'summary': event_data['summary'],
            'description': event_data['description'],
            'start': {'dateTime': event_data['start'], 'timeZone': 'America/Sao_Paulo'},
            'end': {'dateTime': event_data['end'], 'timeZone': 'America/Sao_Paulo'},
            'colorId': event_data.get('color', '1'),
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 60},
                    {'method': 'email', 'minutes': 1440},
                ],
            },
        }

        if event_data.get('location'):
            calendar_event['location'] = event_data['location']

        try:
            response = requests.post(
                'https://www.googleapis.com/calendar/v3/calendars/primary/events',
                json=calendar_event,
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10,
            )

            if response.status_code in (200, 201):
                return {'success': True, 'event_id': response.json().get('id')}
            else:
                return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _create_outlook_event(access_token: str, event_data: dict) -> dict:
        """Cria evento no Microsoft Outlook/365."""
        import requests

        outlook_event = {
            'subject': event_data['summary'],
            'body': {'contentType': 'text', 'content': event_data['description']},
            'start': {'dateTime': event_data['start'], 'timeZone': 'E. South America Standard Time'},
            'end': {'dateTime': event_data['end'], 'timeZone': 'E. South America Standard Time'},
            'isReminderOn': True,
            'reminderMinutesBeforeStart': 60,
        }

        if event_data.get('location'):
            outlook_event['location'] = {'displayName': event_data['location']}

        try:
            response = requests.post(
                'https://graph.microsoft.com/v1.0/me/events',
                json=outlook_event,
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json',
                },
                timeout=10,
            )

            if response.status_code in (200, 201):
                return {'success': True, 'event_id': response.json().get('id')}
            else:
                return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

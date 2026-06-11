"""
share_views - Endpoints para compartilhamento de sessões do Copilot.
"""
import json
import logging

from django.http import JsonResponse
from rest_framework.views import APIView

from apps.intelligent_assistant.views._helpers import _authenticate_request
from ..services import share_service

logger = logging.getLogger(__name__)


class CreateShareView(APIView):
    """
    POST /api/v1/copilot/share/create/
    Cria compartilhamento de sessão.

    Body:
        session_id: UUID
        shared_with_emails: string[] (opcional)
        is_public: bool (opcional, default false)
        expires_days: int (opcional)
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        user, error = _authenticate_request(request)
        if error:
            return error

        try:
            body = json.loads(request.body) if request.body else {}
        except (json.JSONDecodeError, Exception):
            body = {}

        session_id = body.get('session_id')
        shared_with_emails = body.get('shared_with_emails', [])
        is_public = body.get('is_public', False)
        expires_days = body.get('expires_days')

        if not session_id:
            return JsonResponse({'error': 'session_id é obrigatório'}, status=400)

        try:
            share_code = share_service.create_share(
                user_id=user.id,
                session_id=str(session_id),
                shared_with_emails=shared_with_emails,
                is_public=is_public,
                expires_days=expires_days,
            )

            # Gerar link de compartilhamento
            share_url = f'/copilot/shared/{share_code}'

            return JsonResponse({
                'share_code': share_code,
                'share_url': share_url,
                'is_public': is_public,
                'expires_days': expires_days,
            })

        except Exception as e:
            logger.exception(f'[copilot] Erro ao criar compartilhamento: {e}')
            return JsonResponse({'error': f'Erro ao criar compartilhamento: {str(e)}'}, status=500)


class GetShareView(APIView):
    """
    GET /api/v1/copilot/share/<share_code>/
    Obtém informações de um compartilhamento.
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request, share_code):
        user, error = _authenticate_request(request)
        if error:
            return error

        requesting_email = user.email

        share_data = share_service.get_share(share_code, requesting_email)

        if not share_data:
            return JsonResponse(
                {'error': 'Compartilhamento não encontrado ou acesso não permitido'},
                status=404
            )

        return JsonResponse(share_data)


class DeleteShareView(APIView):
    """
    POST /api/v1/copilot/share/<share_code>/delete/
    Exclui um compartilhamento.
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request, share_code):
        user, error = _authenticate_request(request)
        if error:
            return error

        deleted = share_service.delete_share(share_code, user.id)

        if not deleted:
            return JsonResponse(
                {'error': 'Compartilhamento não encontrado ou você não tem permissão'},
                status=404
            )

        return JsonResponse({'status': 'deleted'})


class ListSharesView(APIView):
    """
    GET /api/v1/copilot/share/list/
    Lista compartilhamentos do usuário.
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user, error = _authenticate_request(request)
        if error:
            return error

        shares = share_service.list_user_shares(user.id)

        return JsonResponse({'shares': shares})


class RevokeShareView(APIView):
    """
    POST /api/v1/copilot/share/<share_code>/revoke/
    Revoga acesso de um email específico.

    Body:
        email: string
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request, share_code):
        user, error = _authenticate_request(request)
        if error:
            return error

        try:
            body = json.loads(request.body) if request.body else {}
        except (json.JSONDecodeError, Exception):
            body = {}

        email = body.get('email')

        if not email:
            return JsonResponse({'error': 'email é obrigatório'}, status=400)

        revoked = share_service.revoke_share(share_code, email, user.id)

        if not revoked:
            return JsonResponse(
                {'error': 'Não foi possível revogar o acesso'},
                status=400
            )

        return JsonResponse({'status': 'revoked'})

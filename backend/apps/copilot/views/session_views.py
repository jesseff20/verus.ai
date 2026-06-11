import json
import logging

from django.http import JsonResponse
from rest_framework.views import APIView

from apps.intelligent_assistant.views._helpers import _authenticate_request
from ..services import session_service

logger = logging.getLogger(__name__)


class SyncSessionView(APIView):
    """
    POST /api/v1/copilot/session/sync/
    Sobrescreve o histórico Redis com a lista de mensagens enviada.
    Usado pelo frontend após edição de mensagem (edit & regenerate).

    Body: { session_id: "uuid", messages: [{role, content, timestamp?}] }
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

        session_id = body.get('session_id') or request.POST.get('session_id')
        messages = body.get('messages', [])

        if not session_id:
            return JsonResponse({'error': 'session_id é obrigatório'}, status=400)

        if not isinstance(messages, list):
            return JsonResponse({'error': 'messages deve ser uma lista'}, status=400)

        synced = session_service.set_history(user.id, str(session_id), messages)
        if not synced:
            return JsonResponse({'error': 'Sessão não encontrada ou expirada'}, status=404)

        return JsonResponse({'status': 'synced', 'count': len(messages)})


class SessionView(APIView):
    """
    GET /api/v1/copilot/session/
    Cria uma nova sessão e retorna o session_id.
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user, error = _authenticate_request(request)
        if error:
            return error

        session_id = session_service.create_session(user.id)
        return JsonResponse({'session_id': session_id})


class ClearSessionView(APIView):
    """
    POST /api/v1/copilot/session/clear/
    Limpa o histórico de uma sessão existente.

    Body: { session_id: "uuid" }
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        user, error = _authenticate_request(request)
        if error:
            return error

        try:
            import json
            body = json.loads(request.body) if request.body else {}
        except (json.JSONDecodeError, Exception):
            body = {}
        session_id = body.get('session_id') or request.POST.get('session_id')

        if not session_id:
            return JsonResponse({'error': 'session_id é obrigatório'}, status=400)

        cleared = session_service.clear_session(user.id, str(session_id))
        if not cleared:
            return JsonResponse({'error': 'Sessão não encontrada ou expirada'}, status=404)

        return JsonResponse({'status': 'cleared'})


class SessionsListView(APIView):
    """
    GET /api/v1/copilot/sessions/
    Lista todas as sessões do usuário com preview.
    Query params: limit, search (opcional)
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user, error = _authenticate_request(request)
        if error:
            return error

        limit = int(request.GET.get('limit', 20))
        search_query = request.GET.get('search', '')

        sessions = session_service.list_sessions(user.id, limit=limit, search_query=search_query)

        return JsonResponse({'sessions': sessions})


class SessionDetailView(APIView):
    """
    GET /api/v1/copilot/session/{session_id}/ - carrega histórico
    DELETE /api/v1/copilot/session/{session_id}/ - exclui sessão
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request, session_id):
        user, error = _authenticate_request(request)
        if error:
            return error

        history = session_service.get_history(user.id, str(session_id))
        if history is None:
            return JsonResponse({'error': 'Sessão não encontrada ou expirada'}, status=404)

        return JsonResponse({'session_id': session_id, 'messages': history})

    def delete(self, request, session_id):
        user, error = _authenticate_request(request)
        if error:
            return error

        deleted = session_service.delete_session(user.id, str(session_id))
        if not deleted:
            return JsonResponse({'error': 'Sessão não encontrada ou expirada'}, status=404)

        return JsonResponse({'status': 'deleted'})

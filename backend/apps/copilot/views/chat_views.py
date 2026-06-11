"""
chat_views - Endpoint SSE de streaming do Copilot.

Aceita multipart/form-data (quando há arquivo) ou application/json.
Emite eventos SSE: started, token, completed, error.

Tokens are buffered and flushed every FLUSH_INTERVAL seconds or every
FLUSH_TOKEN_COUNT tokens so the frontend receives larger chunks instead of
character-by-character updates.
"""
import json
import logging
import os
import time

from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.intelligent_assistant.views._helpers import _authenticate_request, _format_sse_event
from ..services import session_service
from ..services.context_builder import build_kb_context, truncate_history_for_context
from ..services.document_context_service import extract_from_upload, format_for_prompt
from ..services.chat_service import stream_response
from ..services.case_context_service import build_case_context
from ..services.user_kb_context import get_user_context

logger = logging.getLogger(__name__)

# ── Upload validation ────────────────────────────────────────────────────────
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.xlsx', '.xls'}
ALLOWED_MIMES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'text/plain',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
}


@csrf_exempt
@require_http_methods(['POST'])
def chat_stream(request):
    """
    POST /api/v1/copilot/chat/stream/

    Body (multipart ou JSON):
        session_id: UUID
        message: string
        file: (opcional) arquivo para análise inline
    """
    user, error = _authenticate_request(request)
    if error:
        return error

    # Parse de campos - suporta multipart e JSON
    content_type = request.content_type or ''
    if 'multipart' in content_type:
        session_id = request.POST.get('session_id', '')
        message = request.POST.get('message', '')
        uploaded_file = request.FILES.get('file')
    else:
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, Exception):
            body = {}
        session_id = str(body.get('session_id', ''))
        message = body.get('message', '')
        uploaded_file = None

    if not session_id:
        return _json_error('session_id é obrigatório', 400)

    if not message and not uploaded_file:
        return _json_error('message ou file é obrigatório', 400)

    # Validate uploaded file type (extension + MIME)
    if uploaded_file:
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        mime = getattr(uploaded_file, 'content_type', '') or ''
        if ext not in ALLOWED_EXTENSIONS:
            return _json_error(f'Tipo de arquivo não permitido: {ext}', 400)
        if mime and mime not in ALLOWED_MIMES:
            return _json_error(f'Tipo de conteúdo não permitido: {mime}', 400)

    # Validar sessão
    history = session_service.get_history(user.id, session_id)
    if history is None:
        return _json_error('Sessão não encontrada ou expirada', 404)

    def event_stream():
        full_text = ''
        usage = {}

        try:
            yield _format_sse_event('started', {'message': 'Iniciando resposta...'})

            # Processar arquivo anexado
            doc_context = ''
            has_attachment = False
            if uploaded_file:
                try:
                    result = extract_from_upload(uploaded_file)
                    doc_context = format_for_prompt(result)
                    has_attachment = True
                except ValueError as e:
                    yield _format_sse_event('error', {'message': str(e)})
                    return

            # Montar mensagem completa (texto + doc)
            full_user_message = message
            if doc_context:
                full_user_message = f'{message}\n{doc_context}' if message else doc_context.strip()

            # Truncar histórico para caber no contexto
            trimmed_history = truncate_history_for_context(history)

            # Buscar contexto de KB
            kb_context = build_kb_context(message or uploaded_file.name if uploaded_file else '')

            # Injetar contexto dos casos do usuario
            case_context = build_case_context(user)
            if case_context:
                kb_context = f'{kb_context}\n\n{case_context}' if kb_context else case_context

            # Injetar contexto da base de conhecimento pessoal do usuario
            user_kb = get_user_context(user, message or '')
            if user_kb:
                kb_context = f'{kb_context}\n\n{user_kb}' if kb_context else user_kb

            # Salvar mensagem do usuário no histórico
            session_service.append_message(
                user.id, session_id, 'user', full_user_message, has_attachment=has_attachment
            )

            # Streaming da resposta — buffer tokens for chunked delivery
            FLUSH_INTERVAL = 0.15   # seconds between flushes
            FLUSH_TOKEN_COUNT = 20  # max tokens before forced flush
            token_buffer: list[str] = []
            last_flush = time.time()

            for chunk, final_result in stream_response(trimmed_history, full_user_message, kb_context, user=user):
                if final_result is not None:
                    usage = final_result.get('usage', {})
                elif chunk:
                    full_text += chunk
                    token_buffer.append(chunk)
                    now = time.time()
                    if now - last_flush >= FLUSH_INTERVAL or len(token_buffer) >= FLUSH_TOKEN_COUNT:
                        buffered = ''.join(token_buffer)
                        yield _format_sse_event('token', {'text': buffered})
                        token_buffer = []
                        last_flush = now

            # Flush remaining buffered tokens
            if token_buffer:
                buffered = ''.join(token_buffer)
                yield _format_sse_event('token', {'text': buffered})

            # Salvar resposta no histórico
            session_service.append_message(user.id, session_id, 'assistant', full_text)

            yield _format_sse_event('completed', {
                'full_text': full_text,
                'usage': usage,
            })

        except Exception as e:
            logger.exception(f'[copilot] Erro no stream: {e}')
            yield _format_sse_event('error', {'message': f'Erro interno: {str(e)}'})

    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


def _json_error(message: str, status: int):
    from django.http import JsonResponse
    return JsonResponse({'error': message}, status=status)

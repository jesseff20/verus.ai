"""
Custom exception handlers para API
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Handler customizado de exceções DRF
    """
    response = exception_handler(exc, context)

    if response is not None:
        custom_response = {
            'status': 'error',
            'message': str(exc),
            'errors': response.data if isinstance(response.data, dict) else {'detail': response.data}
        }
        response.data = custom_response

    return response


class TenantNotFoundError(Exception):
    """Exceção quando tenant não é encontrado"""
    pass


class LLMProviderError(Exception):
    """Exceção quando há erro com provedor LLM"""
    pass


class RAGProcessingError(Exception):
    """Exceção durante processamento RAG"""
    pass

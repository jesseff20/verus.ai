"""
Fixtures globais para testes do app financeiro.
"""
import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Retorna um cliente DRF para testes de API."""
    return APIClient()

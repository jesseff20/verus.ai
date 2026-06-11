"""
App config para Integração com Tribunais.
"""

from django.apps import AppConfig


class IntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.integration'
    verbose_name = 'Integração com Tribunais'

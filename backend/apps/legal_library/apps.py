"""
App config para Biblioteca Viva de Argumentos.
"""

from django.apps import AppConfig


class LegalLibraryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.legal_library'
    verbose_name = 'Biblioteca Viva de Argumentos'

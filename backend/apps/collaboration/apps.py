"""
App config para Colaboração em Tempo Real.
"""

from django.apps import AppConfig


class CollaborationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.collaboration'
    verbose_name = 'Colaboração em Tempo Real'

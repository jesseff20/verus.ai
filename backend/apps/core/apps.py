from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core'

    def ready(self):
        # Importar signals de autenticacao
        from apps.core import signals  # noqa

        # Registrar auditoria para models principais
        from apps.core.signals import register_audit_signals

        # Intelligent Assistant
        from apps.intelligent_assistant.models import (
            DocumentBlueprint,
            BlueprintSection,
            IntelligentSession,
            GeneratedDocument,
        )
        register_audit_signals(DocumentBlueprint)
        register_audit_signals(BlueprintSection)
        register_audit_signals(IntelligentSession)
        register_audit_signals(GeneratedDocument)

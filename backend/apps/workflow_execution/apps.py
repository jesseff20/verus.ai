from django.apps import AppConfig


class WorkflowExecutionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.workflow_execution'
    verbose_name = 'Execução de Fluxos'

    def ready(self):
        import apps.workflow_execution.signals  # noqa: F401

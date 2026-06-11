from django.apps import AppConfig


class CasesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cases'
    verbose_name = 'Casos Jurídicos'

    def ready(self):
        import apps.cases.signals  # noqa: F401 — registers signal handlers

"""
Django settings para testes unitários (sem dependência de banco externo).
"""
from .local import *  # noqa: F403

# Usar SQLite para testes (mais rápido, sem dependência Docker)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Desabilitar migrations para testes mais rápidos
class DisableMigrations:
    def __contains__(self, item):
        return True
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Desabilitar throttling em testes
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {}

# Debug sempre True para testes
DEBUG = True

"""
Django settings para ambiente de desenvolvimento.

IMPORTANTE: Este arquivo importa as configurações base do local.py
(que funciona como "base" multi-ambiente) e sobrescreve apenas
o que é específico do ambiente de desenvolvimento.
"""
from .local import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# CORS mais permissivo em dev
CORS_ALLOW_ALL_ORIGINS = True

# Django Debug Toolbar
INSTALLED_APPS += [
    'debug_toolbar',
]

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Configurações avançadas do Debug Toolbar
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
    'SHOW_TEMPLATE_CONTEXT': True,
    'ENABLE_STACKTRACES': True,
    # Destacar queries duplicadas (N+1)
    'RESULTS_CACHE_SIZE': 100,
    # Mostrar SQL completo
    'SQL_WARNING_THRESHOLD': 100,  # ms - avisar se query > 100ms
}

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.history.HistoryPanel',
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',  # Painel SQL - MAIS IMPORTANTE
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
]

# Logging mais verboso em dev
LOGGING['root']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'DEBUG'

# Email backend para console em dev
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Celery eager mode (síncrono) para debug
CELERY_TASK_ALWAYS_EAGER = env.bool('CELERY_EAGER', default=False)
CELERY_TASK_EAGER_PROPAGATES = True

# ========================================
# CLOUDFLARE R2 STORAGE
# ========================================
USE_R2 = env.bool('USE_R2', default=False)

if USE_R2:
    # Storage backend para Media files
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

    # Configurações Cloudflare R2 (compatível S3)
    AWS_ACCESS_KEY_ID = env('CLOUDFLARE_R2_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env('CLOUDFLARE_R2_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = env('CLOUDFLARE_R2_BUCKET_NAME')
    AWS_S3_ENDPOINT_URL = env('CLOUDFLARE_R2_ENDPOINT')
    AWS_S3_REGION_NAME = 'auto'
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False  # URLs públicas sem assinatura
    AWS_S3_FILE_OVERWRITE = False  # Não sobrescrever arquivos com mesmo nome

    # URL pública para acessar os arquivos
    AWS_S3_CUSTOM_DOMAIN = env('CLOUDFLARE_R2_PUBLIC_URL', default=None)
    if AWS_S3_CUSTOM_DOMAIN:
        MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
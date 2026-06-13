"""
Django settings para desenvolvimento LOCAL (sem docker, sem multi-tenancy)
"""
from datetime import timedelta
from pathlib import Path
import os
import environ

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Environment
env = environ.Env(DEBUG=(bool, True))
environ.Env.read_env(os.path.join(BASE_DIR.parent, '.env'))  # ← CORRIGIDO: raiz/.env

# ========================================
# AMBIENTE: local | homolog | production
# ========================================
ENVIRONMENT = env('ENVIRONMENT', default='local')

# Helper function para ler variáveis com prefixo baseado no ambiente
def get_env_var(var_name, default=None, cast=str):
    """
    Lê variável de ambiente com prefixo baseado em ENVIRONMENT.

    Exemplos:
    - ENVIRONMENT=local      -> LOCAL_DB_NAME
    - ENVIRONMENT=homolog    -> HOMOLOG_DB_NAME
    - ENVIRONMENT=production -> DB_NAME
    """
    if ENVIRONMENT == 'local':
        prefixed_var = f'LOCAL_{var_name}'
    elif ENVIRONMENT == 'homolog':
        prefixed_var = f'HOMOLOG_{var_name}'
    else:  # production
        prefixed_var = var_name

    if cast == bool:
        return env.bool(prefixed_var, default=default)
    elif cast == list:
        return env.list(prefixed_var, default=default or [])
    else:
        return env(prefixed_var, default=default)

# SECURITY
# Em produção (ENVIRONMENT != local), a SECRET_KEY DEVE estar no .env — sem fallback.
if ENVIRONMENT == 'local':
    SECRET_KEY = env('SECRET_KEY', default='django-insecure-local-dev-key-12345')
else:
    SECRET_KEY = env('SECRET_KEY')  # ValueError se não definida em produção
DEBUG = get_env_var('DEBUG', default=True, cast=bool)
# Em produção, inclui o domínio público E o hostname interno do container.
# O hostname interno (verus-backend) é necessário para aceitar requests
# vindas do proxy do Next.js na rede Docker.
if ENVIRONMENT == 'local':
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'verus-backend', '*']
else:
    ALLOWED_HOSTS = get_env_var(
        'ALLOWED_HOSTS',
        default=['verus-backend'],
        cast=list,
    )
# Sempre inclui o hostname interno do Docker — necessário para requests
# vindas do Route Handler do Next.js que proxy via rede Docker.
if 'verus-backend' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('verus-backend')

# APPS (SEM django-tenants)
INSTALLED_APPS = [
    # Local apps FIRST (accounts must be before admin)
    'apps.accounts',

    # Django built-in
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    'storages',

    # Other local apps
    'apps.core',
    'apps.forms',
    'apps.documents',
    'apps.agents',
    'apps.rag',
    'apps.kb',
    'apps.templates',
    'apps.intelligent_assistant',
    'apps.copilot',
    'apps.jurisprudence',
    'apps.cases',
    'apps.integration',
    'apps.legal_library',
    'apps.collaboration',
    'apps.simulations',
    'apps.organization',
    'apps.workflow_definition',
    'apps.workflow_execution',
    'apps.signature',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.AuditMiddleware',
]

APPEND_SLASH = False  # Evita ERR_TOO_MANY_REDIRECTS em chamadas de API

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database - PostgreSQL
# Se DATABASE_URL estiver definida (Railway, Render, etc.), ela tem prioridade.
# Caso contrário, usa variáveis individuais DB_* (docker-compose).
if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': env.db('DATABASE_URL')
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': get_env_var('DB_NAME', default='verus_ai'),
            'USER': get_env_var('DB_USER', default='verus_ai'),
            'PASSWORD': get_env_var('DB_PASSWORD', default='verus_ai123'),
            'HOST': get_env_var('DB_HOST', default='localhost'),
            'PORT': get_env_var('DB_PORT', default='5433'),
        }
    }

# Custom User
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ========================================
# CLOUDFLARE R2 STORAGE
# ========================================
USE_R2 = get_env_var('USE_R2', default=False, cast=bool)

if USE_R2:
    # Storage backend para Media files (Django 5.2+ usa STORAGES dict)
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

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

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS (baseado em ENVIRONMENT)
# Com o proxy Route Handler do Next.js, as requests do browser NUNCA chegam
# diretamente ao Django — elas passam pelo Next.js (same-origin para o browser).
# O CORS só é relevante para desenvolvimento direto (sem Next.js) ou testes.
# Em produção, o domínio público deve estar incluso para o caso de acesso direto.
_domain = env('DOMAIN', default='')
_cors_defaults = [
    'http://localhost:3000', 'http://127.0.0.1:3000',
    'http://localhost:3001', 'http://127.0.0.1:3001',
]
if _domain:
    _cors_defaults.append(f'https://{_domain}')
    _cors_defaults.append(f'http://{_domain}')

CORS_ALLOWED_ORIGINS = get_env_var(
    'CORS_ALLOWED_ORIGINS',
    default=_cors_defaults,
    cast=list,
)
CORS_ALLOW_CREDENTIALS = True

# Segurança SSL (baseado em ENVIRONMENT)
# NOTA: SECURE_SSL_REDIRECT deve ser False quando usando proxy reverso (Traefik/Nginx)
# pois o proxy já faz o redirect HTTP->HTTPS
SECURE_SSL_REDIRECT = False  # Proxy (Traefik) já faz o redirect
SESSION_COOKIE_SECURE = get_env_var('SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = get_env_var('CSRF_COOKIE_SECURE', default=False, cast=bool)

# CSRF Trusted Origins (necessário para POST requests via proxy)
CSRF_TRUSTED_ORIGINS = get_env_var(
    'CSRF_TRUSTED_ORIGINS',
    default=['http://localhost:3000', 'http://localhost:8000', 'http://verus-backend:8000',
             'https://verus.ai'],
    cast=list,
)

# SSL Proxy Header (habilita em produção para funcionar com Nginx/HTTPS)
if ENVIRONMENT == 'production':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
else:
    SECURE_PROXY_SSL_HEADER = None

# DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'config.authentication.CsrfExemptSessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/day',
        'ai_generation': '30/hour',
        'ocr_upload': '20/hour',
        'nfse_emit': '10/hour',
        'conflict_check': '60/hour',
        'login': '10/minute',
        'data_export': '5/hour',
        'protocol_submit': '20/hour',
        'digital_signature': '15/hour',
        'jurisprudence_search': '60/min',
    },
}

# JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

# Spectacular (Swagger)
SPECTACULAR_SETTINGS = {
    'TITLE': 'Verus.AI API',
    'DESCRIPTION': 'API da plataforma Verus.AI — gestão de processos, fluxos BPMN e IA para procuradorias',
    'VERSION': '1.0.0',
}

# ========================================
# SEGURANÇA AVANÇADA (Auth)
# ========================================
EMAIL_TOKEN_SECRET = env('EMAIL_TOKEN_SECRET', default='fallback-dev-email-secret')
PASSWORD_RESET_SECRET = env('PASSWORD_RESET_SECRET', default='fallback-dev-password-secret')
TOKEN_EXPIRATION_CONFIRM = env('TOKEN_EXPIRATION_CONFIRM', default='30d')
TOKEN_EXPIRATION_RESET = env('TOKEN_EXPIRATION_RESET', default='1h')
RATE_LIMIT_MAX = env.int('RATE_LIMIT_MAX', default=5)
RATE_LIMIT_WINDOW = env.int('RATE_LIMIT_WINDOW', default=60000)
EMAIL_PROVIDER_API_KEY = env('EMAIL_PROVIDER_API_KEY', default='')
RESEND_API_KEY = env('RESEND_API_KEY', default='')
EMAIL_FROM = env('EMAIL_FROM', default='noreply@verus.ai')
EMAIL_FROM_NAME = env('EMAIL_FROM_NAME', default='Verus.AI')
HASH_COST = env.int('HASH_COST', default=12)

# ========================================
# EMAIL — Resend via SMTP (Django send_mail)
# Em development.py isso é sobrescrito para console backend.
# ========================================
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='smtp.resend.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=465)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=True)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=False)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='resend')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('EMAIL_FROM', default='noreply@verus.ai')

# Cache — tenta Redis via REDIS_URL, depois via CELERY_BROKER_URL, senão LocMem
_redis_url = env('REDIS_URL', default='') or env('CELERY_BROKER_URL', default='')
if _redis_url and _redis_url.startswith('redis'):
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': _redis_url,
            'OPTIONS': {'db': '1'},
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'verus-cache',
        }
    }

# Celery (baseado em ENVIRONMENT)
CELERY_BROKER_URL = get_env_var('CELERY_BROKER_URL',
                                default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = get_env_var('CELERY_RESULT_BACKEND',
                                    default='redis://localhost:6379/0')

# Celery Beat — periodic tasks for Copilot autonomous notifications
from celery.schedules import crontab  # noqa: E402

CELERY_BEAT_SCHEDULE = {
    'check-upcoming-deadlines': {
        'task': 'apps.copilot.tasks.check_upcoming_deadlines',
        'schedule': crontab(minute=0),  # Every hour
    },
    'analyze-idle-cases': {
        'task': 'apps.copilot.tasks.analyze_idle_cases',
        'schedule': crontab(hour=8, minute=0),  # Daily at 8am
    },
    'check-pending-documents': {
        'task': 'apps.copilot.tasks.check_pending_documents',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9am
    },
    'process-user-reminders': {
        'task': 'apps.copilot.tasks.process_user_reminders',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'nightly-case-analysis': {
        'task': 'apps.copilot.tasks.nightly_case_analysis',
        'schedule': crontab(hour=0, minute=0),  # Midnight
    },
    'sync-user-knowledge-bases': {
        'task': 'apps.copilot.tasks.sync_user_knowledge_bases',
        'schedule': crontab(hour=2, minute=0),  # 2am nightly
    },
}

# LLM
OPENAI_API_KEY = env('OPENAI_API_KEY', default='')
ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY', default='')
WATSONX_API_KEY = env('WATSONX_API_KEY', default='')
WATSONX_PROJECT_ID = env('WATSONX_PROJECT_ID', default='')
WATSONX_URL = env('WATSONX_URL', default='https://us-south.ml.cloud.ibm.com')
DEFAULT_LLM_PROVIDER = env('DEFAULT_LLM_PROVIDER', default='openai')

# Tavily API (busca de jurisprudência)
TAVILY_API_KEY = env('TAVILY_API_KEY', default='')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# ========================================
# ENVIRONMENT INFO (para debug)
# ========================================
try:
    print(f"""
+==================================================+
|  Verus.AI - Django Settings (local.py)           |
+==================================================+
|  Environment: {ENVIRONMENT:<35} |
|  Debug:       {DEBUG!s:<35} |
|  DB Host:     {DATABASES['default']['HOST']:<35} |
|  DB Port:     {DATABASES['default']['PORT']:<35} |
|  DB Name:     {DATABASES['default']['NAME']:<35} |
|  DB User:     {DATABASES['default']['USER']:<35} |
|  Celery:      {CELERY_BROKER_URL:<35} |
|  SSL Redirect:{SECURE_SSL_REDIRECT!s:<35} |
|  Cookie Secure:{SESSION_COOKIE_SECURE!s:<35} |
|  R2 Storage:  {USE_R2!s:<35} |
+==================================================+
""")
except Exception:
    pass

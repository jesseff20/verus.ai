"""
WSGI config for Verus.AI project.
"""
import os
from django.core.wsgi import get_wsgi_application

# A configuracao padrao usa local.py (settings multi-ambiente que se adapta
# via variavel ENVIRONMENT). Em Docker/producao, o docker-compose sobrescreve
# DJANGO_SETTINGS_MODULE conforme necessario.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

application = get_wsgi_application()
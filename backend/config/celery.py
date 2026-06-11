"""Celery app — descoberta automática de tasks via Django apps."""
import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

app = Celery('verus_ai')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

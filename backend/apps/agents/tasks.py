"""
Celery tasks para o app de Agents
"""
from celery import shared_task
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(name='agents.calculate_assistant_analytics')
def calculate_assistant_analytics():
    """
    Task agendada para calcular analytics do assistente
    Roda diariamente para calcular os dados do dia anterior
    """
    # Calcular para ontem (dia completo)
    yesterday = (timezone.now() - timedelta(days=1)).date()
    date_str = yesterday.strftime('%Y-%m-%d')

    logger.info(f"📊 Iniciando cálculo de analytics para {date_str}")

    try:
        call_command('calculate_assistant_analytics', date=date_str, force=True, verbosity=1)
        logger.info(f"✅ Analytics calculados com sucesso para {date_str}")
        return f"Analytics calculados para {date_str}"
    except Exception as e:
        logger.error(f"❌ Erro ao calcular analytics para {date_str}: {str(e)}")
        raise

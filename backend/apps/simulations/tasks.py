"""
Simulations — Celery periodic tasks.

Provides automatic cleanup of simulations that crash while in 'running'
status, preventing them from staying stuck forever and blocking re-execution.
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name='apps.simulations.tasks.cleanup_stuck_simulations')
def cleanup_stuck_simulations():
    """Mark simulations stuck in 'running' for 2+ hours as 'failed'.

    Simulations that crash mid-execution (e.g. SSE stream drops, worker
    killed, LLM timeout) stay in 'running' status with no way to recover.
    This task periodically sweeps those and marks them as 'failed' so
    users can re-run them.
    """
    from apps.simulations.models import Simulation

    threshold = timezone.now() - timedelta(hours=2)
    stuck = Simulation.objects.filter(
        status='running',
        updated_at__lt=threshold,
    )
    count = stuck.update(status='failed')
    if count:
        logger.warning(
            'cleanup_stuck_simulations: %d stuck simulations marked as failed',
            count,
        )
    return {'cleaned': count}

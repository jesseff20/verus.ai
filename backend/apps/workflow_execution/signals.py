"""
Signals para workflow_execution.

Notifica o usuário assignado quando uma TaskInstance é criada.
Usa o model Notification se existir, senão faz log.
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import TaskInstance, FlowInstance

logger = logging.getLogger(__name__)


@receiver(post_save, sender=FlowInstance)
def sync_case_flow_status(sender, instance: FlowInstance, created: bool, **kwargs):
    """
    Quando um FlowInstance é concluído ou cancelado, limpa o active_flow do LegalCase vinculado.
    """
    if created:
        return
    if instance.status not in ('completed', 'cancelled'):
        return
    try:
        from apps.cases.models import LegalCase
        LegalCase.objects.filter(active_flow=instance).update(active_flow=None)
    except Exception as exc:
        logger.info('sync_case_flow_status: %s', exc)


@receiver(post_save, sender=TaskInstance)
def notify_task_assigned(sender, instance: TaskInstance, created: bool, **kwargs):
    """
    Ao criar uma TaskInstance com assigned_to preenchido,
    envia notificação ao usuário.
    """
    if not created:
        return
    if not instance.assigned_to:
        return

    try:
        from apps.accounts.models import Notification
        Notification.objects.create(
            user=instance.assigned_to,
            title='Nova tarefa atribuída',
            message=(
                f'Você recebeu a tarefa "{instance.label}" no fluxo '
                f'"{instance.instance.template_name_snapshot}".'
            ),
            type='task',
            link=f'/dashboard/execucoes/{instance.instance_id}',
            metadata={'task_id': str(instance.id)},
        )
    except Exception:
        # Notification model pode não existir ou ter schema diferente
        logger.info(
            'TaskInstance %s criada para usuário %s (notificação não enviada)',
            instance.id, instance.assigned_to_id,
        )

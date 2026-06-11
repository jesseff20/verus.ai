"""
Signals do app Cases.

Registra auditoria de soft delete de LegalCase via AuditLog (apps.core).
"""
import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import LegalCase

logger = logging.getLogger('cases.audit')


@receiver(pre_save, sender=LegalCase)
def log_soft_delete(sender, instance, **kwargs):
    """
    Detecta a transição deleted_at: None -> <timestamp> e cria um AuditLog.

    Executa apenas quando:
    - O registro já existe no banco (instance.pk não é None)
    - O valor anterior de deleted_at era None
    - O novo valor de deleted_at é não-None (soft delete em curso)
    """
    if not instance.pk:
        return

    try:
        old = LegalCase.all_objects.get(pk=instance.pk)
    except LegalCase.DoesNotExist:
        return

    if old.deleted_at is None and instance.deleted_at is not None:
        # Soft delete happening — record in AuditLog
        try:
            from apps.core.models import AuditLog

            AuditLog.objects.create(
                action='delete',
                severity='warning',
                entity_type='LegalCase',
                entity_id=str(instance.pk),
                entity_name=instance.numero_processo or instance.titulo,
                description=(
                    f'Soft delete de LegalCase: '
                    f'id={instance.pk}, '
                    f'numero_processo="{instance.numero_processo}", '
                    f'titulo="{instance.titulo}"'
                ),
                old_values={'deleted_at': None},
                new_values={'deleted_at': instance.deleted_at.isoformat()},
                metadata={
                    'case_id': str(instance.pk),
                    'numero_processo': instance.numero_processo,
                    'especialidade': instance.especialidade,
                    'status': instance.status,
                },
            )
            logger.warning(
                'LegalCase soft-deleted: id=%s, numero_processo=%s',
                instance.pk,
                instance.numero_processo,
            )
        except Exception as exc:
            # Never let audit logging break the actual delete operation
            logger.error(
                'Erro ao registrar AuditLog de soft delete para LegalCase %s: %s',
                instance.pk,
                exc,
                exc_info=True,
            )

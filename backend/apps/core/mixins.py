"""
Mixins de auditoria para ViewSets.

Fornece controle granular sobre acoes auditadas em APIs REST.
"""
from apps.core.services import AuditService


class AuditCreateMixin:
    """Audita criacao de registros."""

    audit_create_message = None  # Customizavel

    def perform_create(self, serializer):
        instance = serializer.save()
        entity_name = self._get_audit_entity_name(instance)

        AuditService.log(
            request=self.request,
            action='create',
            entity=instance,
            description=self.audit_create_message or f'{entity_name} criado'
        )
        return instance

    def _get_audit_entity_name(self, instance):
        return instance.__class__.__name__


class AuditUpdateMixin:
    """Audita atualizacao de registros com diff de valores."""

    audit_update_message = None

    def perform_update(self, serializer):
        # Capturar valores anteriores
        instance = self.get_object()
        old_values = self._capture_old_values(instance)

        # Salvar
        updated_instance = serializer.save()

        # Calcular diff
        new_values = self._calculate_diff(old_values, updated_instance)

        entity_name = self._get_audit_entity_name(updated_instance)

        AuditService.log(
            request=self.request,
            action='update',
            entity=updated_instance,
            description=self.audit_update_message or f'{entity_name} atualizado',
            old_values=old_values if new_values else None,
            new_values=new_values
        )
        return updated_instance

    def _capture_old_values(self, instance):
        """Captura valores antes da atualizacao."""
        from uuid import UUID
        from datetime import datetime, date
        from decimal import Decimal
        from django.db.models.fields.files import FieldFile

        values = {}
        for field in instance._meta.fields:
            if field.name.startswith('_') or field.name in ('created_at', 'updated_at', 'password'):
                continue

            val = getattr(instance, field.name)

            # Converter tipos não-serializáveis para JSON
            if isinstance(val, UUID):
                val = str(val)
            elif isinstance(val, (datetime, date)):
                val = val.isoformat() if val else None
            elif isinstance(val, Decimal):
                val = float(val)
            elif isinstance(val, FieldFile):  # FileField/ImageField
                val = val.name if val else None
            elif hasattr(val, 'pk'):  # ForeignKey - pegar apenas o ID
                val = str(val.pk) if val.pk else None

            values[field.name] = val

        return values

    def _calculate_diff(self, old_values, instance):
        """Calcula diferencas entre valores antigos e novos."""
        from uuid import UUID
        from datetime import datetime, date
        from decimal import Decimal
        from django.db.models.fields.files import FieldFile

        new_values = {}
        for field_name, old_val in old_values.items():
            new_val = getattr(instance, field_name, None)

            # Converter tipos não-serializáveis para JSON
            if isinstance(new_val, UUID):
                new_val = str(new_val)
            elif isinstance(new_val, (datetime, date)):
                new_val = new_val.isoformat() if new_val else None
            elif isinstance(new_val, Decimal):
                new_val = float(new_val)
            elif isinstance(new_val, FieldFile):  # FileField/ImageField
                new_val = new_val.name if new_val else None
            elif hasattr(new_val, 'pk'):  # ForeignKey
                new_val = str(new_val.pk) if new_val.pk else None

            if str(old_val) != str(new_val):
                new_values[field_name] = new_val

        return new_values if new_values else None

    def _get_audit_entity_name(self, instance):
        return instance.__class__.__name__


class AuditDestroyMixin:
    """Audita exclusao de registros."""

    audit_delete_message = None

    def perform_destroy(self, instance):
        entity_name = self._get_audit_entity_name(instance)
        entity_repr = self._get_entity_repr(instance)

        # Registrar ANTES de deletar
        AuditService.log(
            request=self.request,
            action='delete',
            entity=instance,
            description=self.audit_delete_message or f'{entity_name} "{entity_repr}" excluido',
            severity='warning'
        )

        instance.delete()

    def _get_audit_entity_name(self, instance):
        return instance.__class__.__name__

    def _get_entity_repr(self, instance):
        for attr in ['title', 'name', 'nome', 'numero', 'email']:
            if hasattr(instance, attr):
                val = getattr(instance, attr)
                if val:
                    return str(val)[:50]
        return str(instance.pk)


class AuditModelMixin(AuditCreateMixin, AuditUpdateMixin, AuditDestroyMixin):
    """Mixin completo para CRUD com auditoria."""
    pass


class AuditActionMixin:
    """
    Mixin para auditar acoes customizadas (actions do DRF).

    Uso:
        class MyViewSet(AuditActionMixin, viewsets.ModelViewSet):

            @action(detail=True, methods=['post'])
            def approve(self, request, pk=None):
                instance = self.get_object()
                instance.status = 'approved'
                instance.save()

                self.audit_action(
                    action='approve',
                    entity=instance,
                    description=f'Documento aprovado'
                )
                return Response({'status': 'approved'})
    """

    def audit_action(
        self,
        action: str,
        entity,
        description: str,
        severity: str = 'info',
        old_values: dict = None,
        new_values: dict = None,
        metadata: dict = None
    ):
        """Registra uma acao customizada."""
        AuditService.log(
            request=self.request,
            action=action,
            entity=entity,
            description=description,
            severity=severity,
            old_values=old_values,
            new_values=new_values,
            metadata=metadata
        )


class AuditDownloadMixin:
    """Mixin para auditar downloads de arquivos."""

    def audit_download(self, entity, filename: str = None):
        """Registra download de arquivo."""
        entity_name = entity.__class__.__name__
        entity_repr = str(entity)[:50]

        AuditService.log(
            request=self.request,
            action='download',
            entity=entity,
            description=f'Download de {entity_name} "{entity_repr}"',
            metadata={'filename': filename} if filename else None
        )

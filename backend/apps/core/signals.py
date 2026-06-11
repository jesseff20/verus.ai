"""
Signals de auditoria automatica para models.

Captura automaticamente create/update/delete em models registrados.
"""
import logging
import uuid
from django.db.models.signals import post_save, post_delete, pre_save

logger = logging.getLogger(__name__)
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed

from apps.core.services import AuditService
from apps.core.middleware import get_audit_context

User = get_user_model()


def _sanitize_for_json(obj):
    """Converte valores não serializáveis para JSON (UUIDs, etc)."""
    if obj is None:
        return None
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(v) for v in obj]
    # Para outros tipos não serializáveis, converte para string
    try:
        import json
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


# ========================================
# AUTENTICACAO
# ========================================

@receiver(user_logged_in)
def audit_user_login(sender, request, user, **kwargs):
    """Registra login do usuario."""
    AuditService.log(
        request=request,
        action='login',
        entity=user,
        description=f'Usuario {user.email} fez login'
    )


@receiver(user_logged_out)
def audit_user_logout(sender, request, user, **kwargs):
    """Registra logout do usuario."""
    if user:
        AuditService.log(
            request=request,
            action='logout',
            entity=user,
            description=f'Usuario {user.email} fez logout'
        )


@receiver(user_login_failed)
def audit_login_failed(sender, credentials, request, **kwargs):
    """Registra tentativa de login falha."""
    username = credentials.get('username', 'desconhecido')
    AuditService.log_action(
        action='login_failed',
        entity_type='User',
        entity_id='0',
        entity_name=username,
        description=f'Tentativa de login falhou para {username}',
        severity='warning'
    )


# ========================================
# USUARIO
# ========================================

@receiver(post_save, sender=User)
def audit_user_save(sender, instance, created, **kwargs):
    """Registra criacao/atualizacao de usuario."""
    if created:
        AuditService.log_action(
            action='create',
            entity_type='User',
            entity_id=str(instance.id),
            entity_name=instance.email,
            description=f'Usuario {instance.email} criado'
        )


# ========================================
# FUNCAO GENERICA PARA REGISTRAR MODELS
# ========================================

# Cache para armazenar valores anteriores (pre_save)
_pre_save_cache = {}


def register_audit_signals(model_class, entity_name=None):
    """
    Registra signals de auditoria para um model.

    Uso:
        from apps.core.signals import register_audit_signals
        from apps.documents.models import Document

        register_audit_signals(Document)
    """
    entity_name = entity_name or model_class.__name__

    def pre_save_handler(sender, instance, **kwargs):
        """Captura valores anteriores antes de salvar."""
        if instance.pk:
            try:
                old_instance = sender.objects.get(pk=instance.pk)
                _pre_save_cache[f'{sender.__name__}_{instance.pk}'] = {
                    field.name: _sanitize_for_json(getattr(old_instance, field.name))
                    for field in sender._meta.fields
                    if not field.name.startswith('_')
                }
            except sender.DoesNotExist:
                pass

    def post_save_handler(sender, instance, created, **kwargs):
        """Registra criacao ou atualizacao."""
        cache_key = f'{sender.__name__}_{instance.pk}'
        old_values = _pre_save_cache.pop(cache_key, None)

        # Pegar nome da entidade
        name = _get_entity_display_name(instance)

        # Pegar contexto
        context = get_audit_context()
        user = context.get('user')
        if user and not getattr(user, 'is_authenticated', False):
            user = None

        # Fallback: se não tem user no contexto, tentar pegar do model
        if user is None and hasattr(instance, 'user_id') and instance.user_id:
            try:
                user = User.objects.get(pk=instance.user_id)
            except User.DoesNotExist:
                pass

        if created:
            AuditService.log_action(
                action='create',
                entity_type=entity_name,
                entity_id=str(instance.pk),
                entity_name=name,
                description=f'{entity_name} "{name}" criado',
                user=user
            )
        else:
            # Calcular mudancas
            new_values = None
            if old_values:
                new_values = {}
                for field_name, old_val in old_values.items():
                    new_val = getattr(instance, field_name, None)
                    if old_val != new_val:
                        new_values[field_name] = _sanitize_for_json(new_val)
                        old_values[field_name] = _sanitize_for_json(old_val)

                # Se nao houve mudancas reais, nao registra
                if not new_values:
                    return

            AuditService.log_action(
                action='update',
                entity_type=entity_name,
                entity_id=str(instance.pk),
                entity_name=name,
                description=f'{entity_name} "{name}" atualizado',
                old_values=_sanitize_for_json(old_values),
                new_values=_sanitize_for_json(new_values),
                user=user
            )

    def post_delete_handler(sender, instance, **kwargs):
        """Registra exclusao."""
        name = _get_entity_display_name(instance)

        context = get_audit_context()
        user = context.get('user')
        if user and not getattr(user, 'is_authenticated', False):
            user = None

        # Fallback: se não tem user no contexto, tentar pegar do model
        if user is None and hasattr(instance, 'user_id') and instance.user_id:
            try:
                user = User.objects.get(pk=instance.user_id)
            except User.DoesNotExist:
                pass

        AuditService.log_action(
            action='delete',
            entity_type=entity_name,
            entity_id=str(instance.pk),
            entity_name=name,
            description=f'{entity_name} "{name}" excluido',
            severity='warning',
            user=user
        )

    # Conectar signals
    pre_save.connect(pre_save_handler, sender=model_class, weak=False)
    post_save.connect(post_save_handler, sender=model_class, weak=False)
    post_delete.connect(post_delete_handler, sender=model_class, weak=False)


def _get_entity_display_name(instance):
    """Extrai nome de exibicao da entidade."""
    for attr in ['title', 'name', 'nome', 'numero', 'email']:
        if hasattr(instance, attr):
            val = getattr(instance, attr)
            if val:
                return str(val)[:100]
    # Usar __str__ do modelo antes de cair no UUID
    try:
        display = str(instance)
        if display and display != str(instance.pk):
            return display[:100]
    except Exception:
        logger.warning("Failed to get display name for audit log entry", exc_info=True)
    return str(instance.pk)

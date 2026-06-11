"""
Migration: Reestruturação dos perfis de usuário

- Remove role 'admin' (era idêntico a superadmin)
- Adiciona roles 'reviewer' (Revisor) e 'viewer' (Visualizador)
- Converte usuários com role='admin' para role='superadmin'
- Resultado: 5 perfis (superadmin, manager, analyst, reviewer, viewer)
"""
from django.db import migrations, models


def migrate_admin_to_superadmin(apps, schema_editor):
    """Converte todos os usuários com role='admin' para 'superadmin'."""
    User = apps.get_model('accounts', 'User')
    updated = User.objects.filter(role='admin').update(role='superadmin')
    if updated:
        print(f'\n  -> {updated} usuário(s) migrado(s) de admin → superadmin')


def reverse_superadmin_to_admin(apps, schema_editor):
    """Reversão: não faz nada (não há como saber quem era admin antes)."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_alter_user_role"),
        ("accounts", "0005_notification"),
    ]

    operations = [
        # 1. Primeiro: data migration (converter admin → superadmin enquanto 'admin' ainda é válido)
        migrations.RunPython(
            migrate_admin_to_superadmin,
            reverse_superadmin_to_admin,
        ),
        # 2. Depois: alterar choices para os novos 5 perfis
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("superadmin", "Super Administrador"),
                    ("manager", "Gestor"),
                    ("analyst", "Analista"),
                    ("reviewer", "Revisor"),
                    ("viewer", "Visualizador"),
                ],
                default="analyst",
                max_length=20,
                verbose_name="Perfil",
            ),
        ),
    ]

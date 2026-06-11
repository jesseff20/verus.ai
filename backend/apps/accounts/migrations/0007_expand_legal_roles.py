"""
Migration: Expansão dos perfis para roles jurídicos

- Adiciona novos roles para escritórios de advocacia e órgãos públicos
- Converte roles antigos para os novos equivalentes:
  - manager → gestor
  - reviewer → revisor
  - analyst → analista
  - viewer → visualizador
- Aumenta max_length do campo role para 20 (compatível com novos valores)
"""
from django.db import migrations, models


def migrate_old_roles(apps, schema_editor):
    """Converte roles antigos para os novos equivalentes."""
    User = apps.get_model('accounts', 'User')

    migrations_map = {
        'manager': 'gestor',
        'reviewer': 'revisor',
        'analyst': 'analista',
        'viewer': 'visualizador',
    }

    for old_role, new_role in migrations_map.items():
        updated = User.objects.filter(role=old_role).update(role=new_role)
        if updated:
            print(f'\n  -> {updated} usuario(s) migrado(s) de {old_role} -> {new_role}')


def reverse_new_roles(apps, schema_editor):
    """Reversão: converte roles novos de volta para os antigos."""
    User = apps.get_model('accounts', 'User')

    reverse_map = {
        'gestor': 'manager',
        'revisor': 'reviewer',
        'analista': 'analyst',
        'visualizador': 'viewer',
        # Roles que não existiam antes — mapear para o mais próximo
        'admin': 'superadmin',
        'socio': 'superadmin',
        'advogado_senior': 'analyst',
        'advogado_pleno': 'analyst',
        'advogado_junior': 'analyst',
        'estagiario': 'viewer',
        'coordenador': 'manager',
        'supervisor': 'manager',
        'assistente': 'analyst',
        'paralegal': 'analyst',
        'secretaria': 'viewer',
        'procurador': 'superadmin',
        'defensor': 'analyst',
        'promotor': 'analyst',
        'assessor': 'analyst',
        'servidor': 'viewer',
        'auditor': 'reviewer',
        'cliente': 'viewer',
    }

    for new_role, old_role in reverse_map.items():
        updated = User.objects.filter(role=new_role).update(role=old_role)
        if updated:
            print(f'\n  -> {updated} usuario(s) revertido(s) de {new_role} -> {old_role}')


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_update_roles_add_reviewer_viewer"),
    ]

    operations = [
        # 1. Primeiro: data migration (converter roles antigos enquanto ainda são válidos)
        migrations.RunPython(
            migrate_old_roles,
            reverse_new_roles,
        ),
        # 2. Depois: alterar choices para os novos perfis jurídicos
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("superadmin", "Super Administrador"),
                    ("admin", "Administrador"),
                    ("socio", "Sócio / Partner"),
                    ("advogado_senior", "Advogado Sênior"),
                    ("advogado_pleno", "Advogado Pleno"),
                    ("advogado_junior", "Advogado Júnior"),
                    ("estagiario", "Estagiário de Direito"),
                    ("gestor", "Gestor / Manager"),
                    ("coordenador", "Coordenador Jurídico"),
                    ("supervisor", "Supervisor"),
                    ("analista", "Analista Jurídico"),
                    ("assistente", "Assistente Jurídico"),
                    ("paralegal", "Paralegal / Técnico Jurídico"),
                    ("secretaria", "Secretária Jurídica"),
                    ("procurador", "Procurador"),
                    ("defensor", "Defensor Público"),
                    ("promotor", "Promotor de Justiça"),
                    ("assessor", "Assessor Jurídico"),
                    ("servidor", "Servidor Público"),
                    ("revisor", "Revisor"),
                    ("auditor", "Auditor Jurídico"),
                    ("cliente", "Cliente"),
                    ("visualizador", "Visualizador"),
                ],
                default="analista",
                max_length=20,
                verbose_name="Perfil",
            ),
        ),
    ]

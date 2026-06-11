"""
Migra os roles de advocacia privada para roles de procuradoria.
Aplica ROLE_ALIASES: roles legados são convertidos para os novos roles.
"""
from django.db import migrations, models


ROLE_ALIASES = {
    'socio': 'procurador_geral',
    'advogado_senior': 'procurador',
    'advogado_pleno': 'procurador',
    'advogado_junior': 'procurador',
    'gestor': 'gerente',
    'coordenador': 'gerente',
    'assessor': 'assessor_gerencial',
    'analista': 'servidor',
    'assistente': 'servidor',
    'paralegal': 'servidor',
    'secretaria': 'distribuidor',
    'revisor': 'servidor',
    'auditor': 'servidor',
    'estagiario': 'visualizador',
    'cliente': 'visualizador',
    'defensor': 'procurador',
    'promotor': 'procurador',
    'supervisor': 'gerente',
}


def migrate_roles_forward(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    for old_role, new_role in ROLE_ALIASES.items():
        User.objects.filter(role=old_role).update(role=new_role)


def migrate_roles_backward(apps, schema_editor):
    # Retrocesso: converte roles de procuradoria de volta para os mais genéricos
    User = apps.get_model('accounts', 'User')
    reverse = {
        'procurador_geral': 'socio',
        'subprocurador_geral': 'socio',
        'gerente': 'gestor',
        'assessor_gerencial': 'assessor',
        'assessor_gabinete': 'assessor',
        'distribuidor': 'secretaria',
    }
    for new_role, old_role in reverse.items():
        User.objects.filter(role=new_role).update(role=old_role)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0020_user_organ_unit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('superadmin', 'Super Administrador'),
                    ('admin', 'Administrador'),
                    ('procurador_geral', 'Procurador(a)-Geral'),
                    ('subprocurador_geral', 'Subprocurador(a)-Geral'),
                    ('gerente', 'Gerente'),
                    ('procurador', 'Procurador(a)'),
                    ('assessor_gerencial', 'Assessor(a) Gerencial'),
                    ('assessor_gabinete', 'Assessor(a) de Gabinete'),
                    ('distribuidor', 'Distribuidor(a)'),
                    ('servidor', 'Servidor(a) Público(a)'),
                    ('visualizador', 'Visualizador'),
                ],
                default='servidor',
                max_length=25,
                verbose_name='Perfil',
            ),
        ),
        migrations.RunPython(migrate_roles_forward, migrate_roles_backward),
    ]

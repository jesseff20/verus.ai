"""
Corrige a senha do usuario_demo que foi gravada errada na migration 0019.

A migration 0019 usou NEW_PASSWORD='Demons...26@@' (valor truncado/errado).
A senha correta é 'Demonstração@@2026@@'.

Idempotente: pode ser executada múltiplas vezes sem efeitos colaterais.
"""
from django.db import migrations
from django.contrib.auth.hashers import make_password


CORRECT_PASSWORD = 'Demonstração@@2026@@'


def fix_demo_password(apps, schema_editor):
    User = apps.get_model('accounts', 'User')

    demo = User.objects.filter(username='usuario_demo').first()
    if demo:
        demo.password = make_password(CORRECT_PASSWORD)
        # Garantir também que é superadmin com email correto
        demo.is_superuser = True
        demo.is_staff = True
        demo.role = 'superadmin'
        demo.is_active = True
        if not demo.email or '@bravonix' not in demo.email:
            demo.email = 'usuario_demo@bravonix.anon'
        demo.save()
        print(f'  ✓ senha de usuario_demo corrigida (ID: {demo.pk})')
    else:
        # Nenhum usuario_demo encontrado — criar do zero
        User.objects.create(
            username='usuario_demo',
            email='usuario_demo@bravonix.anon',
            first_name='Usuário',
            last_name='Demonstração',
            password=make_password(CORRECT_PASSWORD),
            is_superuser=True,
            is_staff=True,
            role='superadmin',
            is_active=True,
        )
        print('  ✓ usuario_demo criado com senha correta')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0021_user_role_procuradoria'),
    ]

    operations = [
        migrations.RunPython(fix_demo_password, migrations.RunPython.noop),
    ]

"""
Data migration: cria/atualiza o usuário superadmin de demonstração.

Fluxo:
1. Se existir usuário com username='admin' → renomeia para 'usuario_demo' e atualiza senha
2. Se existir usuário com username='usuario_demo' → apenas atualiza senha e permissões
3. Se nenhum existir → cria usuario_demo como superadmin

Preserva ID, relacionamentos e dados históricos.
Idempotente: pode ser executado múltiplas vezes sem efeitos colaterais.
"""
from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_or_update_demo_user(apps, schema_editor):
    User = apps.get_model('accounts', 'User')

    NEW_USERNAME = 'usuario_demo'
    NEW_EMAIL = 'usuario_demo@bravonix.anon'
    NEW_PASSWORD='Demons...26@@'

    # 1. Tenta encontrar o admin antigo
    admin_user = User.objects.filter(username='admin').first()

    # 2. Tenta encontrar usuario_demo existente
    demo_user = User.objects.filter(username=NEW_USERNAME).first()

    if admin_user and not demo_user:
        # Caso 1: admin existe, usuario_demo não → renomear admin
        admin_user.username = NEW_USERNAME
        admin_user.email = NEW_EMAIL
        admin_user.first_name = 'Usuário'
        admin_user.last_name = 'Demonstração'
        admin_user.password = make_password(NEW_PASSWORD)
        admin_user.is_superuser = True
        admin_user.is_staff = True
        admin_user.role = 'superadmin'
        admin_user.is_active = True
        admin_user.save()
        print(f'  ✓ admin renomeado para usuario_demo (ID: {admin_user.pk})')

    elif demo_user:
        # Caso 2: usuario_demo já existe → atualizar senha e permissões
        demo_user.password = make_password(NEW_PASSWORD)
        demo_user.is_superuser = True
        demo_user.is_staff = True
        demo_user.role = 'superadmin'
        demo_user.is_active = True
        if not demo_user.email or demo_user.email == 'test_check@test.com':
            demo_user.email = NEW_EMAIL
        demo_user.save()
        print(f'  ✓ usuario_demo atualizado (ID: {demo_user.pk})')

        # Se admin ainda existir, remover duplicidade
        if admin_user and admin_user.pk != demo_user.pk:
            print(f'  ⊘ admin antigo (ID: {admin_user.pk}) removido')
            admin_user.delete()

    else:
        # Caso 3: nenhum existe → criar novo
        user = User.objects.create(
            username=NEW_USERNAME,
            email=NEW_EMAIL,
            first_name='Usuário',
            last_name='Demonstração',
            password=make_password(NEW_PASSWORD),
            is_superuser=True,
            is_staff=True,
            role='superadmin',
            is_active=True,
        )
        print(f'  ✓ usuario_demo criado (ID: {user.pk})')


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0018_notification_action_type_max_length'),
    ]

    operations = [
        migrations.RunPython(create_or_update_demo_user, migrations.RunPython.noop),
    ]

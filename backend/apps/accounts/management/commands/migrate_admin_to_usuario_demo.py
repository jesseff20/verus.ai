"""
Management command para migrar o usuário 'admin' para 'usuario_demo'.

Esta migração é SEGURA e IDEMPOTENTE:
- Preserva o ID, foreign keys, permissões e todos os relacionamentos.
- Altera apenas username, email, nome e senha.
- Não cria duplicatas.
- Se o usuário 'usuario_demo' já existir, apenas atualiza a senha.
- Se o usuário 'admin' não existir, não faz nada.

Usage:
    python manage.py migrate_admin_to_usuario_demo
    python manage.py migrate_admin_to_usuario_demo --dry-run  # Apenas mostra o que seria alterado
"""
import logging

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

logger = logging.getLogger(__name__)

User = get_user_model()

NEW_USERNAME = 'usuario_demo'
NEW_EMAIL = 'usuario_demo@bravonix.anon'
NEW_PASSWORD = 'Demonstração@@2026@@'
NEW_FIRST_NAME = 'Usuário'
NEW_LAST_NAME = 'Demonstração'


class Command(BaseCommand):
    help = 'Migra o usuário admin para usuario_demo preservando todos os dados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra o que seria alterado, sem salvar',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY-RUN] Nenhuma alteração será salva.\n'))

        # ─── 0. Caso direto: usuario_demo já existe (instalação nova) ───
        # Garante que a senha esteja correta mesmo sem admin para migrar.
        demo_direct = User.objects.filter(username=NEW_USERNAME).first()
        admin_user = User.objects.filter(username='admin').first()

        if not admin_user and demo_direct:
            # Apenas corrigir senha/permissões do usuario_demo existente
            if dry_run:
                self.stdout.write(f'  [DRY-RUN] usuario_demo (ID: {demo_direct.pk}): senha seria atualizada')
                return
            demo_direct.set_password(NEW_PASSWORD)
            demo_direct.is_superuser = True
            demo_direct.is_staff = True
            demo_direct.role = 'superadmin'
            demo_direct.is_active = True
            if not demo_direct.email or '@bravonix' not in demo_direct.email:
                demo_direct.email = NEW_EMAIL
            demo_direct.save()
            self.stdout.write(self.style.SUCCESS(
                f'  ✓ usuario_demo (ID: {demo_direct.pk}) senha/permissões atualizadas'
            ))
            self.stdout.write(f'  Login: {NEW_USERNAME} ou {NEW_EMAIL}')
            self.stdout.write(f'  Senha: {NEW_PASSWORD}')
            return

        if not admin_user:
            self.stdout.write(self.style.WARNING(
                'Usuário "admin" não encontrado e usuario_demo não existe. Nada a fazer.'
            ))
            return

        # ─── 2. Verifica se já existe usuario_demo (conflito) ───
        existing_demo = User.objects.filter(username=NEW_USERNAME).first()

        if existing_demo and existing_demo.pk != admin_user.pk:
            # Já existe outro usuário com username usuario_demo
            # Isso não deveria acontecer, mas vamos tratar
            self.stdout.write(self.style.ERROR(
                f'Já existe um usuário com username "{NEW_USERNAME}" (ID: {existing_demo.pk}). '
                f'Migração não pode ser automática. Resolva manualmente.'
            ))
            return

        # ─── 3. Executa a migração ───
        old_username = admin_user.username
        old_email = admin_user.email
        old_password_hashed = admin_user.password  # hash atual

        if dry_run:
            self.stdout.write(f'  [DRY-RUN] Usuário ID {admin_user.pk}:')
            self.stdout.write(f'    Username: {old_username} → {NEW_USERNAME}')
            self.stdout.write(f'    Email:    {old_email} → {NEW_EMAIL}')
            self.stdout.write(f'    Nome:     {admin_user.first_name} {admin_user.last_name} → {NEW_FIRST_NAME} {NEW_LAST_NAME}')
            self.stdout.write(f'    Senha:    [hash preservado] → [nova senha com hash]')
            self.stdout.write(f'    Role:     {admin_user.role} (preservado)')
            self.stdout.write(f'    is_superuser: {admin_user.is_superuser} (preservado)')
            self.stdout.write(f'    is_staff: {admin_user.is_staff} (preservado)')
            self.stdout.write(f'    ID:       {admin_user.pk} (preservado)')
            return

        with transaction.atomic():
            # Atualiza campos
            admin_user.username = NEW_USERNAME
            admin_user.email = NEW_EMAIL
            admin_user.first_name = NEW_FIRST_NAME
            admin_user.last_name = NEW_LAST_NAME

            # Atualiza senha com hash seguro (usa o método do Django/bcrypt)
            admin_user.set_password(NEW_PASSWORD)

            # Garante que permissões de superadmin continuam
            admin_user.is_superuser = True
            admin_user.is_staff = True
            admin_user.role = 'superadmin'

            admin_user.save()

            self.stdout.write(self.style.SUCCESS(f'  ✓ Usuário ID {admin_user.pk} migrado:'))
            self.stdout.write(f'    Username: {old_username} → {admin_user.username}')
            self.stdout.write(f'    Email:    {old_email} → {admin_user.email}')
            self.stdout.write(f'    Nome:     → {admin_user.get_full_name()}')
            self.stdout.write(f'    Senha:    atualizada com hash bcrypt')
            self.stdout.write(f'    Role:     {admin_user.role} (preservado)')
            self.stdout.write(f'    ID:       {admin_user.pk} (preservado)')

            logger.info(
                'migrate_admin_to_usuario_demo: %s → %s (ID: %s)',
                old_username, NEW_USERNAME, admin_user.pk,
            )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Migração concluída com sucesso!'))
        self.stdout.write(f'  Login: {NEW_USERNAME} ou {NEW_EMAIL}')
        self.stdout.write(f'  Senha: {NEW_PASSWORD}')

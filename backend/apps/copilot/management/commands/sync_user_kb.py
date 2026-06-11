"""
Management command to manually sync user knowledge bases.

Usage:
    python manage.py sync_user_kb              # Sync all active users
    python manage.py sync_user_kb --user=admin # Sync specific user by username
    python manage.py sync_user_kb --user=5     # Sync specific user by ID
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Sync user knowledge bases for the Copilot. Runs the same logic as the nightly Celery task.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            default=None,
            help='Username or user ID to sync. If omitted, syncs all active users.',
        )

    def handle(self, *args, **options):
        from apps.copilot.tasks import sync_single_user_knowledge

        User = get_user_model()
        username_or_id = options['user']

        if username_or_id:
            # Try by ID first, then by username
            user = None
            try:
                user = User.objects.get(pk=int(username_or_id))
            except (ValueError, User.DoesNotExist):
                try:
                    user = User.objects.get(username=username_or_id)
                except User.DoesNotExist:
                    raise CommandError(f'User "{username_or_id}" not found.')

            self.stdout.write(f'Syncing knowledge base for user: {user.username} (ID: {user.id})')
            result = sync_single_user_knowledge(user.id)
            self.stdout.write(self.style.SUCCESS(
                f'Done: created={result["created"]}, updated={result["updated"]}, '
                f'unchanged={result["unchanged"]}, errors={result["errors"]}'
            ))
        else:
            users = User.objects.filter(is_active=True)
            self.stdout.write(f'Syncing knowledge base for {users.count()} active users...')

            total_results = {'created': 0, 'updated': 0, 'unchanged': 0, 'errors': 0}
            for user in users:
                self.stdout.write(f'  Syncing: {user.username} (ID: {user.id})')
                result = sync_single_user_knowledge(user.id)
                for key in total_results:
                    total_results[key] += result.get(key, 0)

            self.stdout.write(self.style.SUCCESS(
                f'All done: created={total_results["created"]}, '
                f'updated={total_results["updated"]}, '
                f'unchanged={total_results["unchanged"]}, '
                f'errors={total_results["errors"]}'
            ))

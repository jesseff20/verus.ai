"""
Merge migration — resolve conflicting leaf nodes.
Branch 1: 0005_notification (standalone)
Branch 2: 0010_userreminder (via 0005_alter_user_role → ... → 0010)
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_notification'),
        ('accounts', '0010_userreminder'),
    ]

    operations = [
    ]

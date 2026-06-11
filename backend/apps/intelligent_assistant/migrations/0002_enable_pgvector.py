"""
Migration para habilitar a extensão pgvector no PostgreSQL.

Esta migration deve rodar ANTES das migrations que criam campos VectorField.
"""
from django.db import migrations


class Migration(migrations.Migration):
    """Habilita a extensão pgvector no PostgreSQL."""

    dependencies = [
        ('intelligent_assistant', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS vector;",
            reverse_sql="DROP EXTENSION IF EXISTS vector;"
        ),
    ]

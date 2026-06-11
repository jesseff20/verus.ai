"""
Migration: Alterar dimensão do embedding de 1536 (OpenAI) para 1024 (watsonx E5-Large).

IMPORTANTE: Executar esta migration SOMENTE após limpar os embeddings existentes
(DELETE FROM kb_documentchunk WHERE embedding IS NOT NULL), pois ALTER COLUMN
de vector(1536) para vector(1024) falha se houver dados com dimensão diferente.
"""
from django.db import migrations
import pgvector.django


class Migration(migrations.Migration):

    dependencies = [
        ('kb', '0004_add_uploading_ready_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentchunk',
            name='embedding',
            field=pgvector.django.VectorField(
                blank=True,
                dimensions=1024,
                null=True,
            ),
        ),
    ]

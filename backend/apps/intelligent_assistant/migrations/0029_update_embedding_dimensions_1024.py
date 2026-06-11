"""
Migration: Alterar dimensão dos embeddings de 1536 (OpenAI) para 1024 (watsonx E5-Large).

Afeta:
- DocumentEmbedding.embedding: vector(1536) → vector(1024)
- DocumentEmbedding.embedding_model: default 'text-embedding-3-small' → 'intfloat/multilingual-e5-large'
- KnowledgeBaseEmbedding.embedding: vector(1536) → vector(1024)
- KnowledgeBaseEmbedding.embedding_model: default 'text-embedding-3-small' → 'intfloat/multilingual-e5-large'

IMPORTANTE: Executar SOMENTE após limpar os embeddings existentes no banco.
"""
from django.db import migrations, models
import pgvector.django


class Migration(migrations.Migration):

    dependencies = [
        ('intelligent_assistant', '0028_agentknowledgebaselink_selected_sources'),
    ]

    operations = [
        # DocumentEmbedding — dimensão
        migrations.AlterField(
            model_name='documentembedding',
            name='embedding',
            field=pgvector.django.VectorField(
                dimensions=1024,
                help_text='Vetor de embedding do chunk (1024 dimensões)',
                verbose_name='Embedding Vector',
            ),
        ),
        # DocumentEmbedding — default do modelo
        migrations.AlterField(
            model_name='documentembedding',
            name='embedding_model',
            field=models.CharField(
                default='intfloat/multilingual-e5-large',
                help_text='Modelo usado para gerar o embedding',
                max_length=100,
                verbose_name='Modelo de Embedding',
            ),
        ),
        # KnowledgeBaseEmbedding — dimensão
        migrations.AlterField(
            model_name='knowledgebaseembedding',
            name='embedding',
            field=pgvector.django.VectorField(
                dimensions=1024,
                verbose_name='Embedding Vector',
            ),
        ),
        # KnowledgeBaseEmbedding — default do modelo
        migrations.AlterField(
            model_name='knowledgebaseembedding',
            name='embedding_model',
            field=models.CharField(
                default='intfloat/multilingual-e5-large',
                max_length=100,
                verbose_name='Modelo de Embedding',
            ),
        ),
    ]

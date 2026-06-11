"""
Migration: FK source_file em KnowledgeBaseEmbedding + category choices em KBSourceFile.

Permite rastrear qual arquivo-fonte gerou cada embedding e categorizar documentos.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('intelligent_assistant', '0029_update_embedding_dimensions_1024'),
    ]

    operations = [
        # 1. Adicionar FK source_file em KnowledgeBaseEmbedding
        migrations.AddField(
            model_name='knowledgebaseembedding',
            name='source_file',
            field=models.ForeignKey(
                blank=True,
                help_text='Arquivo-fonte que gerou este embedding (rastreabilidade)',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='embeddings',
                to='intelligent_assistant.kbsourcefile',
                verbose_name='Arquivo Fonte',
            ),
        ),
        # 2. Atualizar category em KBSourceFile com choices
        migrations.AlterField(
            model_name='kbsourcefile',
            name='category',
            field=models.CharField(
                blank=True,
                choices=[
                    ('lei', 'Lei / Norma'),
                    ('decreto', 'Decreto'),
                    ('manual', 'Manual / Guia'),
                    ('referencia', 'Referência Técnica'),
                    ('exemplo', 'Exemplo'),
                    ('outros', 'Outros'),
                ],
                default='',
                help_text='Classificação do documento para organização',
                max_length=50,
                verbose_name='Categoria',
            ),
        ),
    ]

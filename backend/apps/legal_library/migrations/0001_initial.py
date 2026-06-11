# Generated migration for LegalLibrary models

from django.conf import settings
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LegalArgument',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=500, verbose_name='Título')),
                ('content', models.TextField(verbose_name='Conteúdo do Argumento')),
                ('summary', models.TextField(blank=True, help_text='Síntese do argumento em 1-2 frases', verbose_name='Resumo')),
                ('category', models.CharField(choices=[('preliminar', 'Preliminar'), ('merito', 'Mérito'), ('pedido', 'Pedido'), ('fundamentacao', 'Fundamentação'), ('recurso', 'Recurso'), ('contrarrazoes', 'Contrarrazões')], default='merito', max_length=100, verbose_name='Categoria')),
                ('specialty', models.CharField(choices=[('CIV', 'Cível'), ('PEN', 'Criminal'), ('TRB', 'Trabalhista'), ('FAM', 'Família'), ('PRE', 'Previdenciário'), ('ADM', 'Administrativo'), ('TRI', 'Tributário'), ('EMP', 'Empresarial')], default='CIV', max_length=50, verbose_name='Especialidade')),
                ('subcategories', models.JSONField(default=list, help_text='Lista de tags para classificação fina', verbose_name='Subcategorias')),
                ('tribunal', models.CharField(blank=True, help_text='Ex: STF, STJ, TJSP, TRT-2', max_length=100, verbose_name='Tribunal')),
                ('effectiveness_score', models.FloatField(default=0.0, help_text='Nota 0-1 baseada em resultados', verbose_name='Score de Eficácia')),
                ('usage_count', models.IntegerField(default=0, verbose_name='Número de Usos')),
                ('success_count', models.IntegerField(default=0, verbose_name='Casos de Sucesso')),
                ('related_precedents', models.JSONField(default=list, help_text='IDs de jurisprudências que apoiam este argumento', verbose_name='Precedentes Relacionados')),
                ('status', models.CharField(choices=[('draft', 'Rascunho'), ('review', 'Em Revisão'), ('approved', 'Aprovado'), ('archived', 'Arquivado')], default='draft', max_length=20, verbose_name='Status')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('last_used_at', models.DateTimeField(blank=True, null=True, verbose_name='Usado pela última vez em')),
                ('created_by', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='legal_arguments', to=settings.AUTH_USER_MODEL, verbose_name='Criado por')),
            ],
            options={
                'verbose_name': 'Argumento Jurídico',
                'verbose_name_plural': 'Argumentos Jurídicos',
                'ordering': ['-effectiveness_score', '-usage_count'],
            },
        ),
        migrations.CreateModel(
            name='ArgumentCollection',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=500, verbose_name='Nome')),
                ('description', models.TextField(blank=True, verbose_name='Descrição')),
                ('is_public', models.BooleanField(default=False, help_text='Se true, visível para todos os usuários', verbose_name='Pública')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('created_by', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='argument_collections', to=settings.AUTH_USER_MODEL, verbose_name='Criado por')),
                ('arguments', models.ManyToManyField(blank=True, related_name='collections', to='legal_library.legalargument', verbose_name='Argumentos')),
            ],
            options={
                'verbose_name': 'Coleção de Argumentos',
                'verbose_name_plural': 'Coleções de Argumentos',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ArgumentUsage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('document_id', models.UUIDField(blank=True, help_text='ID do documento onde foi usado', null=True, verbose_name='ID do Documento')),
                ('case_id', models.UUIDField(blank=True, help_text='ID do caso onde foi usado', null=True, verbose_name='ID do Caso')),
                ('section_title', models.CharField(blank=True, help_text='Título da seção onde foi inserido', max_length=200, verbose_name='Seção')),
                ('outcome', models.CharField(choices=[('favorable', 'Favorável'), ('unfavorable', 'Desfavorável'), ('mixed', 'Misto'), ('pending', 'Pendente')], default='pending', max_length=50, verbose_name='Resultado')),
                ('used_at', models.DateTimeField(auto_now_add=True, verbose_name='Usado em')),
                ('outcome_recorded_at', models.DateTimeField(blank=True, null=True, verbose_name='Resultado registrado em')),
                ('argument', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='usages', to='legal_library.legalargument', verbose_name='Argumento')),
            ],
            options={
                'verbose_name': 'Uso de Argumento',
                'verbose_name_plural': 'Usos de Argumentos',
                'ordering': ['-used_at'],
            },
        ),
        migrations.AddIndex(
            model_name='legalargument',
            index=models.Index(fields=['specialty', 'category'], name='legal_libr_specialt_a1b2c3_idx'),
        ),
        migrations.AddIndex(
            model_name='legalargument',
            index=models.Index(fields=['tribunal'], name='legal_libr_tribunal_d4e5f6_idx'),
        ),
        migrations.AddIndex(
            model_name='legalargument',
            index=models.Index(fields=['status'], name='legal_libr_status_g7h8i9_idx'),
        ),
        migrations.AddIndex(
            model_name='argumentusage',
            index=models.Index(fields=['argument', '-used_at'], name='legal_libr_argumen_j0k1l2_idx'),
        ),
    ]

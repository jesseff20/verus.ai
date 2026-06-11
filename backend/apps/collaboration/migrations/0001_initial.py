# Generated migration for Collaboration models

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
            name='CollaborationSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('document_id', models.UUIDField(help_text='ID do documento sendo editado', verbose_name='ID do Documento')),
                ('document_type', models.CharField(choices=[('legal', 'Documento Jurídico'), ('contract', 'Contrato'), ('petition', 'Petição'), ('brief', 'Memorando')], default='legal', max_length=50, verbose_name='Tipo de Documento')),
                ('status', models.CharField(choices=[('active', 'Ativa'), ('paused', 'Pausada'), ('completed', 'Completa'), ('abandoned', 'Abandonada')], default='active', max_length=20, verbose_name='Status')),
                ('allow_comments', models.BooleanField(default=True, verbose_name='Permitir Comentários')),
                ('allow_suggestions', models.BooleanField(default=True, verbose_name='Permitir Sugestões')),
                ('max_collaborators', models.IntegerField(default=10, help_text='Limite de usuários simultâneos', verbose_name='Máximo de Colaboradores')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('last_activity_at', models.DateTimeField(blank=True, null=True, verbose_name='Última atividade em')),
                ('expires_at', models.DateTimeField(blank=True, null=True, verbose_name='Expira em')),
                ('created_by', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='collaboration_sessions', to=settings.AUTH_USER_MODEL, verbose_name='Criado por')),
            ],
            options={
                'verbose_name': 'Sessão de Colaboração',
                'verbose_name_plural': 'Sessões de Colaboração',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CollaboratorPresence',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('editing', 'Editando'), ('viewing', 'Visualizando'), ('commenting', 'Comentando'), ('away', 'Ausente')], default='viewing', max_length=20, verbose_name='Status')),
                ('cursor_position', models.IntegerField(default=0, help_text='Posição atual do cursor no documento', verbose_name='Posição do Cursor')),
                ('selected_section', models.CharField(blank=True, help_text='ID da seção que o usuário está visualizando/editando', max_length=100, verbose_name='Seção Selecionada')),
                ('last_heartbeat', models.DateTimeField(auto_now=True, verbose_name='Último heartbeat')),
                ('joined_at', models.DateTimeField(auto_now_add=True, verbose_name='Entrou em')),
                ('left_at', models.DateTimeField(blank=True, null=True, verbose_name='Saiu em')),
                ('session', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='presences', to='collaboration.collaborationsession', verbose_name='Sessão')),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='collaboration_presences', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Presença de Colaborador',
                'verbose_name_plural': 'Presenças de Colaboradores',
                'ordering': ['-joined_at'],
            },
        ),
        migrations.CreateModel(
            name='OperationLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('operation_type', models.CharField(choices=[('insert', 'Inserir'), ('delete', 'Deletar'), ('replace', 'Substituir'), ('format', 'Formatar'), ('move', 'Mover')], default='insert', max_length=20, verbose_name='Tipo de Operação')),
                ('section_id', models.CharField(blank=True, help_text='Seção onde a operação ocorreu', max_length=100, verbose_name='ID da Seção')),
                ('position', models.IntegerField(default=0, help_text='Posição onde a operação ocorreu', verbose_name='Posição')),
                ('length', models.IntegerField(default=0, help_text='Tamanho do texto afetado', verbose_name='Tamanho')),
                ('content', models.TextField(blank=True, help_text='Conteúdo inserido/substituído', verbose_name='Conteúdo')),
                ('version', models.IntegerField(default=1, help_text='Versão do documento após esta operação', verbose_name='Versão')),
                ('parent_version', models.IntegerField(default=0, help_text='Versão do documento antes desta operação', verbose_name='Versão Pai')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('session', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='operations', to='collaboration.collaborationsession', verbose_name='Sessão')),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='collaboration_operations', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Log de Operação',
                'verbose_name_plural': 'Logs de Operações',
                'ordering': ['version'],
            },
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('section_id', models.CharField(blank=True, help_text='Seção onde o comentário foi feito', max_length=100, verbose_name='ID da Seção')),
                ('position_start', models.IntegerField(default=0, help_text='Posição inicial do texto comentado', verbose_name='Posição Inicial')),
                ('position_end', models.IntegerField(default=0, help_text='Posição final do texto comentado', verbose_name='Posição Final')),
                ('quoted_text', models.TextField(blank=True, help_text='Trecho do documento sendo comentado', verbose_name='Texto Citado')),
                ('content', models.TextField(verbose_name='Conteúdo')),
                ('is_resolved', models.BooleanField(default=False, verbose_name='Resolvido')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('resolved_at', models.DateTimeField(blank=True, null=True, verbose_name='Resolvido em')),
                ('session', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='comments', to='collaboration.collaborationsession', verbose_name='Sessão')),
                ('author', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='collaboration_comments', to=settings.AUTH_USER_MODEL, verbose_name='Autor')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name='replies', to='collaboration.comment', verbose_name='Comentário Pai')),
                ('resolved_by', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='resolved_comments', to=settings.AUTH_USER_MODEL, verbose_name='Resolvido por')),
            ],
            options={
                'verbose_name': 'Comentário',
                'verbose_name_plural': 'Comentários',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='Suggestion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('section_id', models.CharField(blank=True, max_length=100, verbose_name='ID da Seção')),
                ('original_text', models.TextField(verbose_name='Texto Original')),
                ('suggested_text', models.TextField(verbose_name='Texto Sugerido')),
                ('status', models.CharField(choices=[('pending', 'Pendente'), ('accepted', 'Aceita'), ('rejected', 'Rejeitada'), ('modified', 'Modificada')], default='pending', max_length=20, verbose_name='Status')),
                ('comment', models.TextField(blank=True, verbose_name='Comentário/Justificativa')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('reviewed_at', models.DateTimeField(blank=True, null=True, verbose_name='Revisado em')),
                ('session', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='suggestions', to='collaboration.collaborationsession', verbose_name='Sessão')),
                ('author', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='collaboration_suggestions', to=settings.AUTH_USER_MODEL, verbose_name='Autor')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='reviewed_suggestions', to=settings.AUTH_USER_MODEL, verbose_name='Revisado por')),
            ],
            options={
                'verbose_name': 'Sugestão',
                'verbose_name_plural': 'Sugestões',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='collaborationsession',
            index=models.Index(fields=['document_id', 'status'], name='collaborat_documen_a1b2c3_idx'),
        ),
        migrations.AddIndex(
            model_name='collaborationsession',
            index=models.Index(fields=['-last_activity_at'], name='collaborat_last_a_d4e5f6_idx'),
        ),
        migrations.AddIndex(
            model_name='collaboratorpresence',
            index=models.Index(fields=['session', 'status'], name='collaborat_session_b7g8h9_idx'),
        ),
        migrations.AddIndex(
            model_name='collaboratorpresence',
            index=models.Index(fields=['last_heartbeat'], name='collaborat_last_h_i0j1k2_idx'),
        ),
        migrations.AddIndex(
            model_name='operationlog',
            index=models.Index(fields=['session', 'version'], name='collaborat_session_l3m4n5_idx'),
        ),
        migrations.AddIndex(
            model_name='operationlog',
            index=models.Index(fields=['session', '-created_at'], name='collaborat_session_o6p7q8_idx'),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['session', 'is_resolved'], name='collaborat_session_r9s0t1_idx'),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['parent', '-created_at'], name='collaborat_parent_u2v3w4_idx'),
        ),
        migrations.AddIndex(
            model_name='suggestion',
            index=models.Index(fields=['session', 'status'], name='collaborat_session_x5y6z7_idx'),
        ),
        migrations.AddConstraint(
            model_name='collaboratorpresence',
            constraint=models.UniqueConstraint(fields=('session', 'user'), name='unique_session_user'),
        ),
    ]

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Court',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('court_type', models.CharField(choices=[('STF', 'Supremo Tribunal Federal'), ('STJ', 'Superior Tribunal de Justiça'), ('TST', 'Tribunal Superior do Trabalho'), ('TJ', 'Tribunal de Justiça'), ('TRF', 'Tribunal Regional Federal'), ('TRT', 'Tribunal Regional do Trabalho'), ('JF', 'Justiça Federal'), ('JE', 'Justiça Estadual')], max_length=5)),
                ('state', models.CharField(max_length=2)),
                ('comarcas', models.JSONField(default=list)),
                ('website', models.URLField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Tribunal',
                'verbose_name_plural': 'Tribunais',
                'ordering': ['state', 'name'],
            },
        ),
        migrations.CreateModel(
            name='JudgeProfile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('state', models.CharField(max_length=2)),
                ('court', models.CharField(max_length=200)),
                ('comarca', models.CharField(max_length=200)),
                ('vara', models.CharField(blank=True, max_length=200)),
                ('specialization', models.CharField(blank=True, max_length=100)),
                ('profile_data', models.JSONField(default=dict)),
                ('decision_patterns', models.JSONField(default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Perfil de Juiz',
                'verbose_name_plural': 'Perfis de Juízes',
                'ordering': ['state', 'comarca', 'name'],
                'unique_together': {('name', 'court', 'comarca')},
            },
        ),
        migrations.CreateModel(
            name='Simulation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('simulation_type', models.CharField(choices=[('jury', 'Simulação de Júri'), ('judge', 'Simulação de Sentença')], max_length=20)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('draft', 'Rascunho'), ('configuring', 'Configurando'), ('running', 'Em Execução'), ('deliberating', 'Deliberando'), ('completed', 'Concluído')], default='draft', max_length=20)),
                ('config', models.JSONField(blank=True, default=dict)),
                ('result', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Simulação',
                'verbose_name_plural': 'Simulações',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='JuryMember',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('age', models.IntegerField()),
                ('gender', models.CharField(choices=[('masculino', 'Masculino'), ('feminino', 'Feminino'), ('outro', 'Outro')], max_length=20)),
                ('profession', models.CharField(max_length=100)),
                ('education', models.CharField(choices=[('fundamental', 'Ensino Fundamental'), ('medio', 'Ensino Médio'), ('superior', 'Ensino Superior'), ('pos_graduacao', 'Pós-Graduação')], max_length=50)),
                ('personality_traits', models.JSONField(default=list)),
                ('background', models.TextField(blank=True)),
                ('vote', models.CharField(blank=True, choices=[('absolvicao', 'Absolvição'), ('condenacao', 'Condenação'), ('desclassificacao', 'Desclassificação'), ('pendente', 'Pendente')], default='pendente', max_length=20)),
                ('reasoning', models.TextField(blank=True)),
                ('simulation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='jury_members', to='simulations.simulation')),
            ],
            options={
                'verbose_name': 'Jurado',
                'verbose_name_plural': 'Jurados',
            },
        ),
        migrations.CreateModel(
            name='JuryDebateMessage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('role', models.CharField(choices=[('jurado', 'Jurado'), ('promotor', 'Promotor'), ('defensor', 'Defensor'), ('juiz', 'Juiz Presidente'), ('sistema', 'Sistema')], max_length=20)),
                ('content', models.TextField()),
                ('phase', models.CharField(choices=[('abertura', 'Abertura'), ('acusacao', 'Sustentação da Acusação'), ('defesa', 'Sustentação da Defesa'), ('replicas', 'Réplicas'), ('treplicas', 'Tréplicas'), ('deliberacao', 'Deliberação do Conselho'), ('quesitos', 'Votação dos Quesitos'), ('veredicto', 'Veredicto')], max_length=30)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('jury_member', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='simulations.jurymember')),
                ('simulation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='debate_messages', to='simulations.simulation')),
            ],
            options={
                'verbose_name': 'Mensagem de Debate',
                'verbose_name_plural': 'Mensagens de Debate',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='SimulationDocument',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('file', models.FileField(upload_to='simulations/documents/')),
                ('extracted_text', models.TextField(blank=True)),
                ('document_type', models.CharField(choices=[('denuncia', 'Denúncia'), ('defesa', 'Defesa/Contestação'), ('prova', 'Prova Documental'), ('pericia', 'Laudo Pericial'), ('testemunho', 'Depoimento/Testemunho'), ('sentenca', 'Sentença de 1ª Instância'), ('recurso', 'Recurso'), ('outros', 'Outros')], default='outros', max_length=50)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('simulation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='simulations.simulation')),
            ],
            options={
                'verbose_name': 'Documento da Simulação',
                'verbose_name_plural': 'Documentos da Simulação',
            },
        ),
    ]

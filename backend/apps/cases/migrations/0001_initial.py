"""
Migration inicial do app cases.
"""
import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LegalCase',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('numero_processo', models.CharField(blank=True, max_length=30, verbose_name='Número do Processo')),
                ('titulo', models.CharField(max_length=255, verbose_name='Título / Assunto')),
                ('especialidade', models.CharField(
                    choices=[
                        ('civel', 'Cível'), ('criminal', 'Criminal'), ('trabalhista', 'Trabalhista'),
                        ('tributario', 'Tributário'), ('administrativo', 'Administrativo'),
                        ('previdenciario', 'Previdenciário'), ('familia', 'Família e Sucessões'),
                        ('empresarial', 'Empresarial'), ('ambiental', 'Ambiental'),
                        ('consumidor', 'Direito do Consumidor'), ('imobiliario', 'Imobiliário'),
                        ('outros', 'Outros'),
                    ],
                    default='civel', max_length=20, verbose_name='Especialidade Jurídica'
                )),
                ('status', models.CharField(
                    choices=[
                        ('ativo', 'Ativo'), ('aguardando', 'Aguardando'), ('suspenso', 'Suspenso'),
                        ('encerrado', 'Encerrado'), ('arquivado', 'Arquivado'),
                        ('ganho', 'Ganho'), ('perdido', 'Perdido'), ('acordo', 'Acordo'),
                    ],
                    default='ativo', max_length=20, verbose_name='Status'
                )),
                ('fase', models.CharField(
                    choices=[
                        ('inicial', 'Fase Inicial'), ('instrucao', 'Instrução'), ('julgamento', 'Julgamento'),
                        ('recursal', 'Recursal'), ('execucao', 'Execução'),
                        ('transitado', 'Transitado em Julgado'), ('extrajudicial', 'Extrajudicial'),
                    ],
                    default='inicial', max_length=20, verbose_name='Fase Processual'
                )),
                ('cliente_nome', models.CharField(max_length=255, verbose_name='Cliente / Parte Representada')),
                ('cliente_cpf_cnpj', models.CharField(blank=True, max_length=20, verbose_name='CPF/CNPJ do Cliente')),
                ('parte_contraria', models.CharField(blank=True, max_length=255, verbose_name='Parte Contrária')),
                ('parte_contraria_cpf_cnpj', models.CharField(blank=True, max_length=20, verbose_name='CPF/CNPJ da Parte Contrária')),
                ('tribunal', models.CharField(blank=True, max_length=100, verbose_name='Tribunal')),
                ('vara_juizo', models.CharField(blank=True, max_length=200, verbose_name='Vara / Juízo')),
                ('comarca', models.CharField(blank=True, max_length=100, verbose_name='Comarca / Seção Judiciária')),
                ('valor_causa', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name='Valor da Causa (R$)')),
                ('honorarios_combinados', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name='Honorários Combinados (R$)')),
                ('data_distribuicao', models.DateField(blank=True, null=True, verbose_name='Data de Distribuição / Ajuizamento')),
                ('data_encerramento', models.DateField(blank=True, null=True, verbose_name='Data de Encerramento')),
                ('descricao', models.TextField(blank=True, verbose_name='Descrição do Caso')),
                ('observacoes', models.TextField(blank=True, verbose_name='Observações Internas')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('advogado_responsavel', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='casos_responsavel',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Advogado Responsável',
                )),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='casos_criados',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Criado por',
                )),
            ],
            options={'verbose_name': 'Caso Jurídico', 'verbose_name_plural': 'Casos Jurídicos', 'ordering': ['-created_at']},
        ),
        migrations.AddIndex(
            model_name='legalcase',
            index=models.Index(fields=['status'], name='cases_legal_status_idx'),
        ),
        migrations.AddIndex(
            model_name='legalcase',
            index=models.Index(fields=['especialidade'], name='cases_legal_especialidade_idx'),
        ),
        migrations.AddIndex(
            model_name='legalcase',
            index=models.Index(fields=['advogado_responsavel'], name='cases_legal_advogado_idx'),
        ),
        migrations.AddIndex(
            model_name='legalcase',
            index=models.Index(fields=['created_by'], name='cases_legal_created_by_idx'),
        ),
        migrations.CreateModel(
            name='LegalDeadline',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('titulo', models.CharField(max_length=255, verbose_name='Título do Prazo')),
                ('descricao', models.TextField(blank=True, verbose_name='Descrição')),
                ('tipo', models.CharField(
                    choices=[
                        ('processual', 'Processual'), ('recursal', 'Recursal'),
                        ('extrajudicial', 'Extrajudicial'), ('contratual', 'Contratual'),
                        ('administrativo', 'Administrativo'), ('prescricional', 'Prescricional'),
                        ('decadencial', 'Decadencial'), ('outro', 'Outro'),
                    ],
                    default='processual', max_length=20, verbose_name='Tipo'
                )),
                ('prioridade', models.CharField(
                    choices=[('baixa', 'Baixa'), ('media', 'Média'), ('alta', 'Alta'), ('urgente', 'Urgente')],
                    default='media', max_length=10, verbose_name='Prioridade'
                )),
                ('status', models.CharField(
                    choices=[
                        ('pendente', 'Pendente'), ('em_andamento', 'Em Andamento'),
                        ('concluido', 'Concluído'), ('atrasado', 'Atrasado'), ('cancelado', 'Cancelado'),
                    ],
                    default='pendente', max_length=20, verbose_name='Status'
                )),
                ('data_prazo', models.DateField(verbose_name='Data do Prazo')),
                ('data_conclusao', models.DateField(blank=True, null=True, verbose_name='Data de Conclusão')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('caso', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='prazos',
                    to='cases.legalcase',
                    verbose_name='Caso',
                )),
                ('responsavel', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='prazos_responsavel',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Responsável',
                )),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='prazos_criados',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Criado por',
                )),
            ],
            options={'verbose_name': 'Prazo Processual', 'verbose_name_plural': 'Prazos Processuais', 'ordering': ['data_prazo', 'prioridade']},
        ),
        migrations.AddIndex(
            model_name='legaldeadline',
            index=models.Index(fields=['caso', 'status'], name='cases_deadline_caso_status_idx'),
        ),
        migrations.AddIndex(
            model_name='legaldeadline',
            index=models.Index(fields=['data_prazo'], name='cases_deadline_data_idx'),
        ),
        migrations.AddIndex(
            model_name='legaldeadline',
            index=models.Index(fields=['responsavel'], name='cases_deadline_responsavel_idx'),
        ),
        migrations.CreateModel(
            name='CaseTask',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('titulo', models.CharField(max_length=255, verbose_name='Título da Tarefa')),
                ('descricao', models.TextField(blank=True, verbose_name='Descrição')),
                ('status', models.CharField(
                    choices=[
                        ('pendente', 'Pendente'), ('em_andamento', 'Em Andamento'),
                        ('concluida', 'Concluída'), ('cancelada', 'Cancelada'),
                    ],
                    default='pendente', max_length=20, verbose_name='Status'
                )),
                ('prioridade', models.CharField(
                    choices=[('baixa', 'Baixa'), ('media', 'Média'), ('alta', 'Alta'), ('urgente', 'Urgente')],
                    default='media', max_length=10, verbose_name='Prioridade'
                )),
                ('data_limite', models.DateField(blank=True, null=True, verbose_name='Data Limite')),
                ('data_conclusao', models.DateField(blank=True, null=True, verbose_name='Data de Conclusão')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('caso', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='tarefas',
                    to='cases.legalcase',
                    verbose_name='Caso',
                )),
                ('responsavel', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='tarefas_responsavel',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Responsável',
                )),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='tarefas_criadas',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Criado por',
                )),
            ],
            options={'verbose_name': 'Tarefa do Caso', 'verbose_name_plural': 'Tarefas do Caso', 'ordering': ['data_limite', 'prioridade', '-created_at']},
        ),
        migrations.AddIndex(
            model_name='casetask',
            index=models.Index(fields=['caso', 'status'], name='cases_task_caso_status_idx'),
        ),
        migrations.AddIndex(
            model_name='casetask',
            index=models.Index(fields=['responsavel'], name='cases_task_responsavel_idx'),
        ),
        migrations.AddIndex(
            model_name='casetask',
            index=models.Index(fields=['data_limite'], name='cases_task_data_limite_idx'),
        ),
        migrations.CreateModel(
            name='CaseDocument',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('titulo', models.CharField(max_length=255, verbose_name='Título')),
                ('tipo', models.CharField(
                    choices=[
                        ('peticao', 'Petição'), ('decisao', 'Decisão / Sentença'),
                        ('intimacao', 'Intimação'), ('contrato', 'Contrato'),
                        ('procuracao', 'Procuração'), ('prova', 'Prova'),
                        ('parecer', 'Parecer'), ('outros', 'Outros'),
                    ],
                    default='outros', max_length=20, verbose_name='Tipo'
                )),
                ('descricao', models.TextField(blank=True, verbose_name='Descrição')),
                ('data_documento', models.DateField(blank=True, null=True, verbose_name='Data do Documento')),
                ('generated_document_id', models.UUIDField(blank=True, null=True, verbose_name='ID do Documento Gerado')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('caso', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='documentos_caso',
                    to='cases.legalcase',
                    verbose_name='Caso',
                )),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='case_docs_criados',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'verbose_name': 'Documento do Caso', 'verbose_name_plural': 'Documentos do Caso', 'ordering': ['-data_documento', '-created_at']},
        ),
    ]

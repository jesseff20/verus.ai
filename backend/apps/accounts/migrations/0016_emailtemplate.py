"""
Migration for EmailTemplate model (#19).
"""
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_team_teamassignment'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200, verbose_name='Nome')),
                ('subject', models.CharField(max_length=300, verbose_name='Assunto')),
                ('body_html', models.TextField(verbose_name='Corpo HTML')),
                ('category', models.CharField(
                    choices=[
                        ('notification', 'Notificação'), ('deadline', 'Prazo'),
                        ('client', 'Cliente'), ('billing', 'Cobrança'),
                        ('general', 'Geral'),
                    ],
                    default='general', max_length=50, verbose_name='Categoria',
                )),
                ('variables', models.JSONField(default=list, help_text='Lista de variáveis disponíveis: [{name, description}]')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('created_by', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='email_templates', to=settings.AUTH_USER_MODEL,
                    verbose_name='Criado por',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
            ],
            options={
                'verbose_name': 'Template de E-mail',
                'verbose_name_plural': 'Templates de E-mail',
                'ordering': ['category', 'name'],
            },
        ),
    ]

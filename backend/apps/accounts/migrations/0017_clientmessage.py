"""
Migration for ClientMessage model (Portal do Cliente).
"""
import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0016_emailtemplate'),
        ('cases', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientMessage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('sender_type', models.CharField(
                    choices=[('client', 'Cliente'), ('lawyer', 'Advogado')],
                    max_length=10, verbose_name='Tipo de Remetente',
                )),
                ('sender_name', models.CharField(max_length=200, verbose_name='Nome do Remetente')),
                ('content', models.TextField(verbose_name='Conteudo')),
                ('is_read', models.BooleanField(default=False, verbose_name='Lida')),
                ('attachment', models.FileField(
                    blank=True, null=True, upload_to='client_messages/', verbose_name='Anexo',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('client', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='messages', to='cases.client',
                    verbose_name='Cliente',
                )),
                ('case', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='client_messages', to='cases.legalcase',
                    verbose_name='Caso',
                )),
            ],
            options={
                'verbose_name': 'Mensagem do Cliente',
                'verbose_name_plural': 'Mensagens do Cliente',
                'ordering': ['created_at'],
            },
        ),
    ]

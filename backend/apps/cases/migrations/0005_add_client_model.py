# Generated manually — adiciona Client e FK client em LegalCase

import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0004_add_audiencia_movimentacaofinanceira'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Criar tabela Client
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=300, verbose_name='Nome')),
                ('client_type', models.CharField(
                    choices=[('pessoa_fisica', 'Pessoa Física'), ('pessoa_juridica', 'Pessoa Jurídica')],
                    default='pessoa_fisica', max_length=20, verbose_name='Tipo',
                )),
                ('cpf_cnpj', models.CharField(blank=True, db_index=True, max_length=20, verbose_name='CPF/CNPJ')),
                ('rg', models.CharField(blank=True, max_length=20, verbose_name='RG')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='E-mail')),
                ('phone', models.CharField(blank=True, max_length=20, verbose_name='Telefone')),
                ('phone_secondary', models.CharField(blank=True, max_length=20, verbose_name='Telefone Secundário')),
                ('address', models.CharField(blank=True, max_length=500, verbose_name='Endereço')),
                ('city', models.CharField(blank=True, max_length=100, verbose_name='Cidade')),
                ('state', models.CharField(blank=True, max_length=2, verbose_name='UF')),
                ('zipcode', models.CharField(blank=True, max_length=10, verbose_name='CEP')),
                ('company_name', models.CharField(blank=True, max_length=300, verbose_name='Razão Social')),
                ('contact_person', models.CharField(blank=True, max_length=200, verbose_name='Pessoa de Contato')),
                ('notes', models.TextField(blank=True, verbose_name='Observações')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('responsible_lawyer', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='clients', to=settings.AUTH_USER_MODEL,
                    verbose_name='Advogado Responsável',
                )),
                ('created_by', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_clients', to=settings.AUTH_USER_MODEL,
                    verbose_name='Criado por',
                )),
            ],
            options={
                'verbose_name': 'Cliente',
                'verbose_name_plural': 'Clientes',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='client',
            index=models.Index(fields=['client_type'], name='cases_clien_client__b2e5e7_idx'),
        ),
        migrations.AddIndex(
            model_name='client',
            index=models.Index(fields=['is_active'], name='cases_clien_is_acti_a1c3d4_idx'),
        ),
        migrations.AddIndex(
            model_name='client',
            index=models.Index(fields=['responsible_lawyer'], name='cases_clien_respons_f5e6a7_idx'),
        ),

        # 2. Adicionar FK client em LegalCase
        migrations.AddField(
            model_name='legalcase',
            name='client',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='cases', to='cases.client', verbose_name='Cliente',
            ),
        ),
    ]

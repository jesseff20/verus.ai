"""
Add LegalNotification model for Brazilian legal notifications (citações, intimações, notificações).
"""
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cases', '0008_add_overdue_reopen_fields_to_casephase'),
    ]

    operations = [
        migrations.CreateModel(
            name='LegalNotification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tipo', models.CharField(choices=[
                    ('citacao_pessoal', 'Citação Pessoal'),
                    ('citacao_hora_certa', 'Citação por Hora Certa'),
                    ('citacao_edital', 'Citação por Edital'),
                    ('citacao_eletronica', 'Citação Eletrônica'),
                    ('intimacao_pessoal', 'Intimação Pessoal'),
                    ('intimacao_dje', 'Intimação via DJe'),
                    ('intimacao_eletronica', 'Intimação Eletrônica'),
                    ('intimacao_publicacao', 'Intimação por Publicação'),
                    ('notificacao_extrajudicial', 'Notificação Extrajudicial'),
                    ('notificacao_judicial', 'Notificação Judicial'),
                    ('carta_precatoria', 'Carta Precatória'),
                    ('carta_rogatoria', 'Carta Rogatória'),
                    ('mandado_citacao', 'Mandado de Citação'),
                    ('mandado_intimacao', 'Mandado de Intimação'),
                ], max_length=30)),
                ('direcao', models.CharField(choices=[
                    ('recebida', 'Recebida'),
                    ('enviada', 'Enviada'),
                ], default='recebida', max_length=10)),
                ('status', models.CharField(choices=[
                    ('pendente', 'Pendente'),
                    ('efetivada', 'Efetivada'),
                    ('frustrada', 'Frustrada'),
                    ('cancelada', 'Cancelada'),
                ], default='pendente', max_length=20)),
                ('meio', models.CharField(blank=True, choices=[
                    ('oficial_justica', 'Oficial de Justiça'),
                    ('correio_ar', 'Correio (AR)'),
                    ('dje', 'Diário de Justiça Eletrônico'),
                    ('pje', 'PJe'),
                    ('esaj', 'e-SAJ'),
                    ('whatsapp', 'WhatsApp'),
                    ('email', 'E-mail'),
                    ('cartorio', 'Cartório de Títulos'),
                    ('edital', 'Edital'),
                ], max_length=20)),
                ('destinatario_nome', models.CharField(blank=True, max_length=300)),
                ('remetente', models.CharField(blank=True, max_length=300)),
                ('data_expedicao', models.DateField(blank=True, null=True)),
                ('data_ciencia', models.DateField(blank=True, null=True)),
                ('data_publicacao_dje', models.DateField(blank=True, null=True)),
                ('prazo_dias', models.IntegerField(blank=True, null=True)),
                ('prazo_tipo', models.CharField(choices=[
                    ('uteis', 'Úteis'),
                    ('corridos', 'Corridos'),
                ], default='uteis', max_length=10)),
                ('prazo_vencimento', models.DateField(blank=True, null=True)),
                ('base_legal', models.CharField(blank=True, max_length=200)),
                ('conteudo_resumo', models.TextField(blank=True)),
                ('observacoes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('caso', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notificacoes',
                    to='cases.legalcase',
                )),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                )),
                ('deadline_created', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='notification_source',
                    to='cases.legaldeadline',
                )),
            ],
            options={
                'verbose_name': 'Notificação Jurídica',
                'verbose_name_plural': 'Notificações Jurídicas',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='legalnotification',
            index=models.Index(fields=['caso', 'status'], name='cases_legal_caso_id_notif_status_idx'),
        ),
        migrations.AddIndex(
            model_name='legalnotification',
            index=models.Index(fields=['tipo'], name='cases_legal_tipo_notif_idx'),
        ),
        migrations.AddIndex(
            model_name='legalnotification',
            index=models.Index(fields=['prazo_vencimento'], name='cases_legal_prazo_venc_idx'),
        ),
    ]

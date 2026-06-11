"""
Add NotificationChannel and NotificationMessage models for
multi-channel notification system (WhatsApp, Email, App).
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_merge_all_branches'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationChannel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel', models.CharField(choices=[('email', 'E-mail'), ('whatsapp', 'WhatsApp'), ('app', 'Aplicação')], max_length=20, verbose_name='Canal')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('whatsapp_number', models.CharField(blank=True, help_text='Formato: +5521999998888', max_length=20, verbose_name='Número WhatsApp')),
                ('whatsapp_verified', models.BooleanField(default=False, verbose_name='WhatsApp Verificado')),
                ('email_address', models.EmailField(blank=True, help_text='Pode diferir do e-mail principal do usuário', max_length=254, verbose_name='E-mail de Notificação')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_channels', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Canal de Notificação',
                'verbose_name_plural': 'Canais de Notificação',
                'unique_together': {('user', 'channel')},
            },
        ),
        migrations.CreateModel(
            name='NotificationMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel', models.CharField(max_length=20, verbose_name='Canal')),
                ('subject', models.CharField(blank=True, max_length=500, verbose_name='Assunto')),
                ('body', models.TextField(verbose_name='Corpo da mensagem')),
                ('whatsapp_link', models.URLField(blank=True, verbose_name='Link WhatsApp')),
                ('status', models.CharField(choices=[('pending', 'Pendente'), ('sent', 'Enviado'), ('failed', 'Falhou'), ('clicked', 'Clicado')], default='pending', max_length=20, verbose_name='Status')),
                ('sent_at', models.DateTimeField(blank=True, null=True, verbose_name='Enviado em')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('notification', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='accounts.notification', verbose_name='Notificação')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_messages', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Mensagem de Notificação',
                'verbose_name_plural': 'Mensagens de Notificação',
                'ordering': ['-created_at'],
            },
        ),
    ]

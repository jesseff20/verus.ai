"""
Adiciona o campo private_key_salt à tabela SignerKey.

O salt de 16 bytes é gerado aleatoriamente por registro e usado na derivação
PBKDF2-HMAC-SHA256 da chave Fernet que protege a chave privada RSA do usuário.

Registros existentes ficam com private_key_salt=NULL (derivação legada).
Novos registros sempre recebem um salt.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signature', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='signerkey',
            name='private_key_salt',
            field=models.BinaryField(
                blank=True,
                help_text='Salt aleatório de 16 bytes usado na derivação PBKDF2 da chave Fernet.',
                null=True,
                verbose_name='Salt KDF (PBKDF2)',
            ),
        ),
    ]

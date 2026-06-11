# Generated manually — adds UniqueConstraint for cpf_cnpj on Client model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0019_expand_contract_type_choices'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='client',
            constraint=models.UniqueConstraint(
                condition=models.Q(('cpf_cnpj__gt', '')),
                fields=('cpf_cnpj',),
                name='unique_cpf_cnpj_when_set',
            ),
        ),
    ]

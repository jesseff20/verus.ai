import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0019_create_demo_superadmin'),
        ('organization', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='organ',
            field=models.ForeignKey(
                blank=True,
                help_text='Órgão/Procuradoria ao qual o usuário pertence',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='users',
                to='organization.organ',
                verbose_name='Órgão',
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='unit',
            field=models.ForeignKey(
                blank=True,
                help_text='Unidade interna (ex: Gerência Judicial 1º Grau)',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='users',
                to='organization.unit',
                verbose_name='Unidade/Gerência',
            ),
        ),
    ]

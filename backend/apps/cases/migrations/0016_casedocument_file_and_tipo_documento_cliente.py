"""
Add file field and documento_cliente tipo to CaseDocument.
Make DigitalSignature.user nullable for client portal signatures.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0015_workflow_models'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='casedocument',
            name='file',
            field=models.FileField(
                blank=True, null=True, upload_to='case_documents/',
                verbose_name='Arquivo',
            ),
        ),
        migrations.AlterField(
            model_name='casedocument',
            name='tipo',
            field=models.CharField(
                choices=[
                    ('peticao', 'Petição'),
                    ('peca', 'Peça Processual'),
                    ('decisao', 'Decisão / Sentença'),
                    ('intimacao', 'Intimação'),
                    ('contrato', 'Contrato'),
                    ('procuracao', 'Procuração'),
                    ('prova', 'Prova'),
                    ('parecer', 'Parecer'),
                    ('simulacao', 'Simulação'),
                    ('copilot', 'Análise do Copilot'),
                    ('documento_cliente', 'Documento do Cliente'),
                    ('outros', 'Outros'),
                ],
                default='outros', max_length=20, verbose_name='Tipo',
            ),
        ),
        migrations.AlterField(
            model_name='digitalsignature',
            name='user',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='digital_signatures',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Usuário',
            ),
        ),
    ]

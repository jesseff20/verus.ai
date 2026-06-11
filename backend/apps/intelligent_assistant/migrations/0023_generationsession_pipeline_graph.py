from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('intelligent_assistant', '0022_add_pipeline_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='generationsession',
            name='pipeline_graph',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Estado final do grafo de execução {nodes, edges, log} para visualização',
                verbose_name='Pipeline Graph',
            ),
        ),
    ]

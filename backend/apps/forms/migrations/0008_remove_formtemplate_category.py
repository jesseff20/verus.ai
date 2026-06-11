from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0007_remove_documentgenerator_add_blueprint"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="formtemplate",
            name="category",
        ),
    ]

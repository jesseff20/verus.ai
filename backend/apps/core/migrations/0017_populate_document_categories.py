"""
Data migration: popula a tabela DocumentCategory com os 7 valores que
estavam em CATEGORY_CHOICES do model DocumentType.

Os `code` precisam casar 1:1 com os valores antigos para que a migration
0018 consiga fazer o lookup correto ao converter o campo `category` para
ForeignKey.
"""
from django.db import migrations


CATEGORIES = [
    # (code, name, display_order)
    ('fase_preparatoria', 'Fase Preparatória', 10),
    ('fase_externa', 'Fase Externa', 20),
    ('fase_contratacao', 'Fase de Contratação', 30),
    ('impugnacoes_recursos', 'Impugnações e Recursos', 40),
    ('pareceres', 'Pareceres', 50),
    ('pos_contratacao', 'Pós-Contratação', 60),
    ('outros', 'Outros', 70),
]


def forwards(apps, schema_editor):
    DocumentCategory = apps.get_model('core', 'DocumentCategory')
    for code, name, order in CATEGORIES:
        DocumentCategory.objects.update_or_create(
            code=code,
            defaults={
                'name': name,
                'display_order': order,
                'is_active': True,
            },
        )


def backwards(apps, schema_editor):
    DocumentCategory = apps.get_model('core', 'DocumentCategory')
    DocumentCategory.objects.filter(code__in=[c[0] for c in CATEGORIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_documentcategory'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]

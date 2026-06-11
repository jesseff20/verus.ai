"""
Converte DocumentType.category de CharField (com choices hardcoded) para
ForeignKey(DocumentCategory).

Estratégia em 5 etapas atômicas para preservar dados:

1. AddField `category_new` (FK nullable)
2. RunPython: para cada DocumentType, faz lookup de DocumentCategory pelo
   `code` antigo (que estava no CharField) e seta `category_new`.
3. RemoveField `category` (CharField velho)
4. RenameField `category_new` -> `category`
5. AlterField: torna a FK NOT NULL com related_name correto.

Roll-back: `python manage.py migrate core 0017` desfaz tudo (RunPython.backwards
copia os codes de volta — mas como remove_field destrói os dados, o backwards
do RunPython só registra que rodou, sem recuperação possível).
"""
from django.db import migrations, models
import django.db.models.deletion


def copy_category_to_fk(apps, schema_editor):
    """
    Para cada DocumentType, lookup da DocumentCategory pelo code antigo
    (que estava em DocumentType.category como string).
    """
    DocumentType = apps.get_model('core', 'DocumentType')
    DocumentCategory = apps.get_model('core', 'DocumentCategory')

    # Mapa code -> DocumentCategory
    category_by_code = {c.code: c for c in DocumentCategory.objects.all()}

    for dt in DocumentType.objects.all():
        cat = category_by_code.get(dt.category)
        if cat is None:
            raise ValueError(
                f"DocumentType '{dt.code}' tem category='{dt.category}' que não "
                f"existe em DocumentCategory. Migrations 0016/0017 não rodaram "
                f"ou o banco tem dado fora dos 7 valores oficiais."
            )
        dt.category_new = cat
        dt.save(update_fields=['category_new'])


def noop_backwards(apps, schema_editor):
    # Sem como recuperar o CharField antigo após o RemoveField. Mantemos noop
    # — quem precisar de roll-back vai resetar pra 0017 antes do RemoveField.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_populate_document_categories'),
    ]

    operations = [
        # 1. Adiciona campo novo como FK nullable
        migrations.AddField(
            model_name='documenttype',
            name='category_new',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='core.documentcategory',
            ),
        ),
        # 2. Copia valores: lookup pelo code antigo
        migrations.RunPython(copy_category_to_fk, noop_backwards),
        # 3. Remove campo antigo (CharField)
        migrations.RemoveField(
            model_name='documenttype',
            name='category',
        ),
        # 4. Renomeia category_new -> category
        migrations.RenameField(
            model_name='documenttype',
            old_name='category_new',
            new_name='category',
        ),
        # 5. Torna NOT NULL + related_name definitivo
        migrations.AlterField(
            model_name='documenttype',
            name='category',
            field=models.ForeignKey(
                help_text='Fase do processo licitatório',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='document_types',
                to='core.documentcategory',
                verbose_name='Categoria',
            ),
        ),
    ]

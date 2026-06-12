"""
Migration para converter document_type de CharField para ForeignKey.

Usa a tabela centralizada DocumentType como fonte única da verdade.
"""
from django.db import migrations, models
import django.db.models.deletion


def migrate_document_type_to_fk(apps, schema_editor):
    """
    Migra os dados de document_type (código string) para ForeignKey.
    """
    DocumentBlueprint = apps.get_model('intelligent_assistant', 'DocumentBlueprint')
    DocumentType = apps.get_model('core', 'DocumentType')

    # Cache de tipos de documento
    doc_types = {dt.code: dt for dt in DocumentType.objects.all()}

    for blueprint in DocumentBlueprint.objects.all():
        old_code = blueprint.document_type_old
        if old_code and old_code in doc_types:
            blueprint.document_type = doc_types[old_code]
            blueprint.save(update_fields=['document_type'])
        else:
            # Se não encontrar, tenta criar ou usar 'custom'
            if 'custom' in doc_types:
                blueprint.document_type = doc_types['custom']
                blueprint.save(update_fields=['document_type'])
                print(f"[AVISO] Blueprint '{blueprint.name}' com tipo '{old_code}' migrado para 'custom'")


def reverse_migration(apps, schema_editor):
    """
    Reverte a migração - copia o código do DocumentType de volta para o campo string.
    """
    DocumentBlueprint = apps.get_model('intelligent_assistant', 'DocumentBlueprint')

    for blueprint in DocumentBlueprint.objects.all():
        if blueprint.document_type:
            blueprint.document_type_old = blueprint.document_type.code
            blueprint.save(update_fields=['document_type_old'])


class Migration(migrations.Migration):

    dependencies = [
        ('intelligent_assistant', '0012_add_cover_page_and_typography'),
        ('core', '0002_add_document_type'),  # Garante que DocumentType existe
    ]

    operations = [
        # 1. Renomear o campo antigo
        migrations.RenameField(
            model_name='documentblueprint',
            old_name='document_type',
            new_name='document_type_old',
        ),

        # 2. Adicionar novo campo ForeignKey (nullable inicialmente)
        migrations.AddField(
            model_name='documentblueprint',
            name='document_type',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='blueprints',
                to='core.documenttype',
                verbose_name='Tipo de Documento',
                help_text='Tipo de documento conforme tabela centralizada',
            ),
        ),

        # 3. Migrar dados
        migrations.RunPython(migrate_document_type_to_fk, reverse_migration),

        # 4. Remover o campo antigo
        migrations.RemoveField(
            model_name='documentblueprint',
            name='document_type_old',
        ),

        # 5. Campo permanece nullable (DocumentType pode não existir em banco limpo;
        #    os seeds populam os tipos após o migrate).
        migrations.AlterField(
            model_name='documentblueprint',
            name='document_type',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='blueprints',
                to='core.documenttype',
                verbose_name='Tipo de Documento',
                help_text='Tipo de documento conforme tabela centralizada',
            ),
        ),
    ]

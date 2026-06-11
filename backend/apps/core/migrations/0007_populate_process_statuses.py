# Generated manually - Popula ProcessStatus

from django.db import migrations


def populate_statuses(apps, schema_editor):
    """Popula a tabela ProcessStatus com os status padrão."""
    ProcessStatus = apps.get_model('core', 'ProcessStatus')

    statuses = [
        {
            'code': 'planejamento',
            'name': 'Em Planejamento',
            'description': 'Processo em fase inicial de planejamento',
            'category': 'inicial',
            'icon': 'Clock',
            'color': 'bg-blue-100 text-blue-800',
            'display_order': 1,
            'is_default': True,
            'is_final': False,
        },
        {
            'code': 'documentacao',
            'name': 'Documentacao Tecnica',
            'description': 'Elaboracao dos documentos tecnicos (ETP, TR, etc)',
            'category': 'andamento',
            'icon': 'FileText',
            'color': 'bg-cyan-100 text-cyan-800',
            'display_order': 2,
            'is_default': False,
            'is_final': False,
        },
        {
            'code': 'licitacao',
            'name': 'Em Licitacao',
            'description': 'Processo em fase de licitacao (publicado)',
            'category': 'andamento',
            'icon': 'Gavel',
            'color': 'bg-yellow-100 text-yellow-800',
            'display_order': 3,
            'is_default': False,
            'is_final': False,
        },
        {
            'code': 'analise',
            'name': 'Em Analise',
            'description': 'Analise de propostas e documentacao',
            'category': 'andamento',
            'icon': 'Search',
            'color': 'bg-purple-100 text-purple-800',
            'display_order': 4,
            'is_default': False,
            'is_final': False,
        },
        {
            'code': 'contratacao',
            'name': 'Em Contratacao',
            'description': 'Fase de formalizacao do contrato',
            'category': 'andamento',
            'icon': 'FileSignature',
            'color': 'bg-indigo-100 text-indigo-800',
            'display_order': 5,
            'is_default': False,
            'is_final': False,
        },
        {
            'code': 'execucao',
            'name': 'Em Execucao',
            'description': 'Contrato em execucao',
            'category': 'andamento',
            'icon': 'Play',
            'color': 'bg-teal-100 text-teal-800',
            'display_order': 6,
            'is_default': False,
            'is_final': False,
        },
        {
            'code': 'concluido',
            'name': 'Concluido',
            'description': 'Processo finalizado com sucesso',
            'category': 'finalizado',
            'icon': 'CheckCircle2',
            'color': 'bg-green-100 text-green-800',
            'display_order': 7,
            'is_default': False,
            'is_final': True,
        },
        {
            'code': 'cancelado',
            'name': 'Cancelado',
            'description': 'Processo cancelado',
            'category': 'suspenso',
            'icon': 'XCircle',
            'color': 'bg-red-100 text-red-800',
            'display_order': 8,
            'is_default': False,
            'is_final': True,
        },
        {
            'code': 'suspenso',
            'name': 'Suspenso',
            'description': 'Processo temporariamente suspenso',
            'category': 'suspenso',
            'icon': 'PauseCircle',
            'color': 'bg-orange-100 text-orange-800',
            'display_order': 9,
            'is_default': False,
            'is_final': False,
        },
    ]

    for status_data in statuses:
        ProcessStatus.objects.get_or_create(
            code=status_data['code'],
            defaults=status_data
        )


def reverse_populate(apps, schema_editor):
    """Remove os status populados."""
    ProcessStatus = apps.get_model('core', 'ProcessStatus')
    codes = [
        'planejamento', 'documentacao', 'licitacao', 'analise',
        'contratacao', 'execucao', 'concluido', 'cancelado', 'suspenso'
    ]
    ProcessStatus.objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_add_process_status"),
    ]

    operations = [
        migrations.RunPython(populate_statuses, reverse_populate),
    ]

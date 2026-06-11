"""
Popula tabela ProcessType com tipos de processo padrao.
"""
from django.db import migrations


def populate_process_types(apps, schema_editor):
    ProcessType = apps.get_model('core', 'ProcessType')

    types = [
        # Pregao
        {
            'code': 'pregao_eletronico',
            'name': 'Pregao Eletronico',
            'short_name': 'PE',
            'description': 'Modalidade de licitacao para aquisicao de bens e servicos comuns, realizada em sessao publica por meio eletronico.',
            'category': 'pregao',
            'legal_basis': 'Lei 14.133/2021, Art. 6, XLI',
            'icon': 'Gavel',
            'color': 'blue',
            'display_order': 1,
        },
        {
            'code': 'pregao_presencial',
            'name': 'Pregao Presencial',
            'short_name': 'PP',
            'description': 'Modalidade de licitacao para aquisicao de bens e servicos comuns, realizada em sessao publica presencial.',
            'category': 'pregao',
            'legal_basis': 'Lei 14.133/2021, Art. 6, XLI',
            'icon': 'Users',
            'color': 'blue',
            'display_order': 2,
        },

        # Concorrencia
        {
            'code': 'concorrencia',
            'name': 'Concorrencia',
            'short_name': 'CC',
            'description': 'Modalidade de licitacao para contratacao de bens e servicos especiais e obras e servicos comuns e especiais de engenharia.',
            'category': 'concorrencia',
            'legal_basis': 'Lei 14.133/2021, Art. 6, XXXVIII',
            'icon': 'Scale',
            'color': 'green',
            'display_order': 3,
        },
        {
            'code': 'concorrencia_internacional',
            'name': 'Concorrencia Internacional',
            'short_name': 'CI',
            'description': 'Concorrencia com participacao de empresas estrangeiras.',
            'category': 'concorrencia',
            'legal_basis': 'Lei 14.133/2021, Art. 52',
            'icon': 'Globe',
            'color': 'green',
            'display_order': 4,
        },

        # Dispensa
        {
            'code': 'dispensa',
            'name': 'Dispensa de Licitacao',
            'short_name': 'DL',
            'description': 'Contratacao direta nos casos em que a licitacao e dispensavel.',
            'category': 'dispensa',
            'legal_basis': 'Lei 14.133/2021, Art. 75',
            'icon': 'FileX',
            'color': 'amber',
            'display_order': 5,
        },
        {
            'code': 'dispensa_valor',
            'name': 'Dispensa por Valor',
            'short_name': 'DV',
            'description': 'Dispensa de licitacao em razao do valor da contratacao.',
            'category': 'dispensa',
            'legal_basis': 'Lei 14.133/2021, Art. 75, I e II',
            'icon': 'DollarSign',
            'color': 'amber',
            'display_order': 6,
        },
        {
            'code': 'dispensa_emergencial',
            'name': 'Dispensa Emergencial',
            'short_name': 'DE',
            'description': 'Dispensa em casos de emergencia ou calamidade publica.',
            'category': 'dispensa',
            'legal_basis': 'Lei 14.133/2021, Art. 75, VIII',
            'icon': 'AlertTriangle',
            'color': 'red',
            'display_order': 7,
        },

        # Inexigibilidade
        {
            'code': 'inexigibilidade',
            'name': 'Inexigibilidade',
            'short_name': 'IN',
            'description': 'Contratacao direta quando a competicao e inviavel.',
            'category': 'inexigibilidade',
            'legal_basis': 'Lei 14.133/2021, Art. 74',
            'icon': 'CheckSquare',
            'color': 'cyan',
            'display_order': 8,
        },
        {
            'code': 'inexigibilidade_exclusivo',
            'name': 'Inexigibilidade - Fornecedor Exclusivo',
            'short_name': 'IE',
            'description': 'Inexigibilidade por exclusividade de fornecedor.',
            'category': 'inexigibilidade',
            'legal_basis': 'Lei 14.133/2021, Art. 74, I',
            'icon': 'Award',
            'color': 'cyan',
            'display_order': 9,
        },

        # Chamamento Publico
        {
            'code': 'chamamento_publico',
            'name': 'Chamamento Publico',
            'short_name': 'CP',
            'description': 'Procedimento para selecao de organizacoes da sociedade civil.',
            'category': 'chamamento',
            'legal_basis': 'Lei 13.019/2014',
            'icon': 'Megaphone',
            'color': 'violet',
            'display_order': 10,
        },

        # Concurso
        {
            'code': 'concurso',
            'name': 'Concurso',
            'short_name': 'CONC',
            'description': 'Modalidade para escolha de trabalho tecnico, cientifico ou artistico.',
            'category': 'concurso',
            'legal_basis': 'Lei 14.133/2021, Art. 6, XXXIX',
            'icon': 'Trophy',
            'color': 'orange',
            'display_order': 11,
        },

        # SRP
        {
            'code': 'ata_registro_preco',
            'name': 'Ata de Registro de Precos',
            'short_name': 'ARP',
            'description': 'Sistema de Registro de Precos para contratacoes futuras.',
            'category': 'srp',
            'legal_basis': 'Lei 14.133/2021, Art. 82 a 86',
            'icon': 'FileSpreadsheet',
            'color': 'teal',
            'display_order': 12,
        },
        {
            'code': 'adesao_arp',
            'name': 'Adesao a ARP (Carona)',
            'short_name': 'AARP',
            'description': 'Adesao a ata de registro de precos de outro orgao.',
            'category': 'srp',
            'legal_basis': 'Lei 14.133/2021, Art. 86',
            'icon': 'Link',
            'color': 'teal',
            'display_order': 13,
        },

        # Outros
        {
            'code': 'leilao',
            'name': 'Leilao',
            'short_name': 'LEI',
            'description': 'Modalidade para alienacao de bens a quem oferecer o maior lance.',
            'category': 'outros',
            'legal_basis': 'Lei 14.133/2021, Art. 6, XL',
            'icon': 'Hammer',
            'color': 'gray',
            'display_order': 14,
        },
        {
            'code': 'dialogo_competitivo',
            'name': 'Dialogo Competitivo',
            'short_name': 'DC',
            'description': 'Modalidade para contratacoes que necessitem de inovacao tecnologica ou tecnica.',
            'category': 'outros',
            'legal_basis': 'Lei 14.133/2021, Art. 6, XLII',
            'icon': 'MessageCircle',
            'color': 'gray',
            'display_order': 15,
        },
        {
            'code': 'custom',
            'name': 'Customizado',
            'short_name': 'CUST',
            'description': 'Tipo de processo customizado.',
            'category': 'outros',
            'legal_basis': '',
            'icon': 'Settings',
            'color': 'gray',
            'display_order': 99,
        },
    ]

    for t in types:
        ProcessType.objects.get_or_create(code=t['code'], defaults=t)


def reverse_populate(apps, schema_editor):
    ProcessType = apps.get_model('core', 'ProcessType')
    ProcessType.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_add_process_type'),
    ]

    operations = [
        migrations.RunPython(populate_process_types, reverse_populate),
    ]

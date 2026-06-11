# Generated manually - Data migration to populate DocumentType table

from django.db import migrations


def populate_document_types(apps, schema_editor):
    """Popula a tabela DocumentType com os 26 tipos existentes."""
    DocumentType = apps.get_model('core', 'DocumentType')

    document_types = [
        # === FASE PREPARATÓRIA (Art. 18, Lei 14.133/2021) ===
        {
            'code': 'dfd',
            'name': 'Documento de Formalização de Demanda',
            'short_name': 'DFD',
            'description': 'Documento que expressa a necessidade de contratação',
            'category': 'fase_preparatoria',
            'icon': 'FileText',
            'legal_basis': 'Lei 14.133/2021, Art. 18, I',
            'display_order': 1,
        },
        {
            'code': 'etp',
            'name': 'Estudo Técnico Preliminar',
            'short_name': 'ETP',
            'description': 'Documento base para planejamento de contratações',
            'category': 'fase_preparatoria',
            'icon': 'FileSearch',
            'legal_basis': 'Lei 14.133/2021, Art. 18, §1º',
            'display_order': 2,
        },
        {
            'code': 'termo_referencia',
            'name': 'Termo de Referência',
            'short_name': 'TR',
            'description': 'Especificações técnicas e condições da contratação',
            'category': 'fase_preparatoria',
            'icon': 'ClipboardList',
            'legal_basis': 'Lei 14.133/2021, Art. 6º, XXIII',
            'display_order': 3,
        },
        {
            'code': 'projeto_basico',
            'name': 'Projeto Básico',
            'short_name': 'PB',
            'description': 'Elementos necessários para caracterização da obra ou serviço',
            'category': 'fase_preparatoria',
            'icon': 'Settings',
            'legal_basis': 'Lei 14.133/2021, Art. 6º, XXV',
            'display_order': 4,
        },
        {
            'code': 'projeto_executivo',
            'name': 'Projeto Executivo',
            'short_name': 'PE',
            'description': 'Elementos necessários à execução completa da obra',
            'category': 'fase_preparatoria',
            'icon': 'Wrench',
            'legal_basis': 'Lei 14.133/2021, Art. 6º, XXVI',
            'display_order': 5,
        },
        {
            'code': 'mapa_riscos',
            'name': 'Mapa de Riscos',
            'short_name': 'MR',
            'description': 'Identificação e análise dos riscos da contratação',
            'category': 'fase_preparatoria',
            'icon': 'AlertTriangle',
            'legal_basis': 'Lei 14.133/2021, Art. 18, X',
            'display_order': 6,
        },
        {
            'code': 'pesquisa_precos',
            'name': 'Pesquisa de Preços',
            'short_name': 'PP',
            'description': 'Orçamento estimado com base em pesquisa de mercado',
            'category': 'fase_preparatoria',
            'icon': 'DollarSign',
            'legal_basis': 'Lei 14.133/2021, Art. 23',
            'display_order': 7,
        },
        {
            'code': 'edital',
            'name': 'Edital de Licitação',
            'short_name': 'Edital',
            'description': 'Documento oficial para processos licitatórios',
            'category': 'fase_preparatoria',
            'icon': 'ScrollText',
            'legal_basis': 'Lei 14.133/2021, Art. 25',
            'display_order': 8,
        },
        {
            'code': 'contrato',
            'name': 'Contrato',
            'short_name': 'Contrato',
            'description': 'Instrumento contratual formal',
            'category': 'fase_preparatoria',
            'icon': 'Briefcase',
            'legal_basis': 'Lei 14.133/2021, Art. 89',
            'display_order': 9,
        },

        # === FASE EXTERNA ===
        {
            'code': 'ata_sessao',
            'name': 'Ata de Sessão Pública',
            'short_name': 'Ata',
            'description': 'Registro da sessão pública de abertura e julgamento',
            'category': 'fase_externa',
            'icon': 'FileText',
            'legal_basis': 'Lei 14.133/2021',
            'display_order': 10,
        },
        {
            'code': 'parecer_julgamento',
            'name': 'Parecer de Julgamento',
            'short_name': 'PJ',
            'description': 'Análise e classificação das propostas',
            'category': 'fase_externa',
            'icon': 'CheckSquare',
            'legal_basis': 'Lei 14.133/2021',
            'display_order': 11,
        },
        {
            'code': 'parecer_habilitacao',
            'name': 'Parecer de Habilitação',
            'short_name': 'PH',
            'description': 'Análise da documentação de habilitação',
            'category': 'fase_externa',
            'icon': 'UserCheck',
            'legal_basis': 'Lei 14.133/2021, Art. 62 a 70',
            'display_order': 12,
        },
        {
            'code': 'termo_adjudicacao',
            'name': 'Termo de Adjudicação',
            'short_name': 'TA',
            'description': 'Atribuição do objeto ao vencedor',
            'category': 'fase_externa',
            'icon': 'Award',
            'legal_basis': 'Lei 14.133/2021, Art. 71',
            'display_order': 13,
        },
        {
            'code': 'termo_homologacao',
            'name': 'Termo de Homologação',
            'short_name': 'TH',
            'description': 'Ratificação do procedimento licitatório',
            'category': 'fase_externa',
            'icon': 'CheckCircle',
            'legal_basis': 'Lei 14.133/2021, Art. 71',
            'display_order': 14,
        },

        # === IMPUGNAÇÕES E RECURSOS ===
        {
            'code': 'impugnacao',
            'name': 'Impugnação ao Edital',
            'short_name': 'Impugnação',
            'description': 'Questionamento ao instrumento convocatório',
            'category': 'impugnacoes_recursos',
            'icon': 'AlertCircle',
            'legal_basis': 'Lei 14.133/2021, Art. 164',
            'display_order': 15,
        },
        {
            'code': 'resposta_impugnacao',
            'name': 'Resposta à Impugnação',
            'short_name': 'Resposta',
            'description': 'Resposta da Administração à impugnação',
            'category': 'impugnacoes_recursos',
            'icon': 'MessageCircle',
            'legal_basis': 'Lei 14.133/2021, Art. 164',
            'display_order': 16,
        },
        {
            'code': 'recurso',
            'name': 'Recurso Administrativo',
            'short_name': 'Recurso',
            'description': 'Recurso contra decisão em processo licitatório',
            'category': 'impugnacoes_recursos',
            'icon': 'ArrowUpCircle',
            'legal_basis': 'Lei 14.133/2021, Art. 165',
            'display_order': 17,
        },
        {
            'code': 'contrarrazoes',
            'name': 'Contrarrazões de Recurso',
            'short_name': 'Contrarrazões',
            'description': 'Resposta ao recurso interposto',
            'category': 'impugnacoes_recursos',
            'icon': 'ArrowDownCircle',
            'legal_basis': 'Lei 14.133/2021, Art. 165',
            'display_order': 18,
        },
        {
            'code': 'decisao_recurso',
            'name': 'Decisão de Recurso',
            'short_name': 'Decisão',
            'description': 'Decisão da autoridade sobre o recurso',
            'category': 'impugnacoes_recursos',
            'icon': 'Gavel',
            'legal_basis': 'Lei 14.133/2021, Art. 165',
            'display_order': 19,
        },

        # === PARECERES ===
        {
            'code': 'parecer',
            'name': 'Parecer Técnico',
            'short_name': 'PT',
            'description': 'Análise técnica especializada',
            'category': 'pareceres',
            'icon': 'FileText',
            'legal_basis': 'Lei 14.133/2021',
            'display_order': 20,
        },
        {
            'code': 'parecer_juridico',
            'name': 'Parecer Jurídico',
            'short_name': 'PJur',
            'description': 'Análise jurídica e legal',
            'category': 'pareceres',
            'icon': 'Scale',
            'legal_basis': 'Lei 14.133/2021, Art. 53',
            'display_order': 21,
        },

        # === PÓS-CONTRATAÇÃO ===
        {
            'code': 'ordem_servico',
            'name': 'Ordem de Serviço/Fornecimento',
            'short_name': 'OS',
            'description': 'Autorização para início da execução',
            'category': 'pos_contratacao',
            'icon': 'Play',
            'legal_basis': 'Lei 14.133/2021',
            'display_order': 22,
        },
        {
            'code': 'termo_recebimento_provisorio',
            'name': 'Termo de Recebimento Provisório',
            'short_name': 'TRP',
            'description': 'Recebimento provisório do objeto',
            'category': 'pos_contratacao',
            'icon': 'Clock',
            'legal_basis': 'Lei 14.133/2021, Art. 140, I',
            'display_order': 23,
        },
        {
            'code': 'termo_recebimento_definitivo',
            'name': 'Termo de Recebimento Definitivo',
            'short_name': 'TRD',
            'description': 'Recebimento definitivo do objeto',
            'category': 'pos_contratacao',
            'icon': 'CheckCircle2',
            'legal_basis': 'Lei 14.133/2021, Art. 140, II',
            'display_order': 24,
        },
        {
            'code': 'aditivo_contratual',
            'name': 'Aditivo Contratual',
            'short_name': 'Aditivo',
            'description': 'Alteração contratual',
            'category': 'pos_contratacao',
            'icon': 'FilePlus',
            'legal_basis': 'Lei 14.133/2021, Art. 124 a 136',
            'display_order': 25,
        },

        # === OUTROS ===
        {
            'code': 'custom',
            'name': 'Customizado',
            'short_name': 'Custom',
            'description': 'Documento de tipo personalizado',
            'category': 'outros',
            'icon': 'File',
            'legal_basis': '',
            'display_order': 99,
        },
    ]

    for dt_data in document_types:
        DocumentType.objects.get_or_create(
            code=dt_data['code'],
            defaults=dt_data
        )


def reverse_populate(apps, schema_editor):
    """Remove os tipos de documento criados."""
    DocumentType = apps.get_model('core', 'DocumentType')
    DocumentType.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_add_document_type'),
    ]

    operations = [
        migrations.RunPython(populate_document_types, reverse_populate),
    ]

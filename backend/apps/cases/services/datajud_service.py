"""
Serviço de integração com CNJ DataJud (simulado).

Como não é possível conectar diretamente à API do DataJud,
este serviço gera respostas simuladas realistas para desenvolvimento e testes.
"""
import random
import uuid
from datetime import datetime, timedelta
from django.utils import timezone


class DataJudService:
    """Simula integração com a API DataJud do CNJ."""

    # Dados realistas para simulação
    TRIBUNAIS = [
        'TJSP', 'TJRJ', 'TJMG', 'TJRS', 'TJPR', 'TJBA',
        'TJPE', 'TJCE', 'TJSC', 'TJGO', 'TJDF',
        'TRF1', 'TRF2', 'TRF3', 'TRF4', 'TRF5',
        'TRT-1', 'TRT-2', 'TRT-3', 'TRT-4', 'TRT-15',
    ]

    VARAS = [
        '1ª Vara Cível',
        '2ª Vara Cível',
        '3ª Vara de Família e Sucessões',
        '5ª Vara do Trabalho',
        '1ª Vara Criminal',
        '2ª Vara Federal',
        '4ª Vara da Fazenda Pública',
        '1ª Vara Empresarial',
        '3ª Vara de Execução Fiscal',
        'Juizado Especial Cível',
    ]

    CLASSES = [
        'Ação Civil Pública',
        'Ação de Cobrança',
        'Ação de Indenização',
        'Ação Trabalhista',
        'Mandado de Segurança',
        'Habeas Corpus',
        'Execução de Título Extrajudicial',
        'Reclamação Trabalhista',
        'Ação de Alimentos',
        'Ação de Divórcio',
        'Ação de Despejo',
        'Ação Monitória',
    ]

    ASSUNTOS = [
        'Indenização por Dano Moral',
        'Rescisão do Contrato de Trabalho',
        'Obrigação de Fazer / Não Fazer',
        'Responsabilidade Civil',
        'Direito do Consumidor',
        'Cobrança de Dívida',
        'Revisão Contratual',
        'Despejo por Falta de Pagamento',
        'Alimentos',
        'Guarda de Menores',
        'Execução Fiscal',
        'Mandado de Segurança',
    ]

    MOVIMENTACOES_TIPOS = [
        ('Distribuição', 'Processo distribuído por sorteio'),
        ('Citação', 'Expedida carta de citação ao réu'),
        ('Contestação', 'Apresentação de contestação pela parte ré'),
        ('Decisão Interlocutória', 'Proferida decisão saneadora do feito'),
        ('Audiência Designada', 'Designada audiência de conciliação'),
        ('Audiência Realizada', 'Realizada audiência de instrução e julgamento'),
        ('Despacho', 'Proferido despacho de expediente'),
        ('Sentença', 'Proferida sentença nos autos'),
        ('Intimação', 'Intimação das partes via DJe'),
        ('Recurso', 'Interposto recurso de apelação'),
        ('Juntada de Petição', 'Juntada de petição intermediária'),
        ('Perícia', 'Nomeado perito judicial'),
        ('Publicação', 'Publicação de sentença no DJe'),
        ('Trânsito em Julgado', 'Certificado o trânsito em julgado'),
        ('Cumprimento de Sentença', 'Iniciado cumprimento de sentença'),
        ('Penhora', 'Determinada penhora de bens'),
        ('Baixa Definitiva', 'Autos baixados definitivamente'),
    ]

    STATUS_OPCOES = [
        'Em andamento',
        'Suspenso',
        'Arquivado',
        'Baixado',
        'Em grau de recurso',
    ]

    NOMES_PARTES = [
        'Maria da Silva Santos',
        'João Carlos de Oliveira',
        'Empresa ABC Ltda.',
        'Construtora Beta S.A.',
        'Carlos Eduardo Pereira',
        'Ana Beatriz Souza',
        'Tech Solutions Ltda.',
        'Banco Nacional S.A.',
        'Município de São Paulo',
        'Estado do Rio de Janeiro',
        'Instituto Nacional do Seguro Social - INSS',
        'União Federal',
    ]

    def search_process(self, numero_processo: str) -> dict:
        """
        Busca dados de um processo pelo número.
        Retorna dados simulados no formato DataJud.
        """
        random.seed(hash(numero_processo))

        tribunal = random.choice(self.TRIBUNAIS)
        vara = random.choice(self.VARAS)
        classe = random.choice(self.CLASSES)
        num_assuntos = random.randint(1, 3)
        assuntos = random.sample(self.ASSUNTOS, min(num_assuntos, len(self.ASSUNTOS)))
        status_proc = random.choice(self.STATUS_OPCOES)

        # Partes
        autor = random.choice(self.NOMES_PARTES)
        reu_choices = [n for n in self.NOMES_PARTES if n != autor]
        reu = random.choice(reu_choices)

        # Valor da causa
        valor_causa = round(random.uniform(5000, 500000), 2)

        # Data de distribuição
        days_ago = random.randint(30, 1500)
        data_distribuicao = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')

        # Movimentações
        movimentacoes = self._generate_movimentacoes(numero_processo, days_ago)

        return {
            'numero': numero_processo,
            'tribunal': tribunal,
            'vara': vara,
            'classe': classe,
            'assuntos': assuntos,
            'partes': {
                'autor': {
                    'nome': autor,
                    'tipo': 'Autor',
                    'advogados': [f'Dr. {random.choice(self.NOMES_PARTES).split()[0]} {random.choice(["Ferreira", "Costa", "Lima", "Almeida"])} (OAB/{random.choice(["SP", "RJ", "MG"])} {random.randint(100000, 400000)})'],
                },
                'reu': {
                    'nome': reu,
                    'tipo': 'Réu',
                    'advogados': [f'Dr. {random.choice(self.NOMES_PARTES).split()[0]} {random.choice(["Mendes", "Ribeiro", "Gomes", "Martins"])} (OAB/{random.choice(["SP", "RJ", "MG"])} {random.randint(100000, 400000)})'],
                },
            },
            'valor_causa': valor_causa,
            'data_distribuicao': data_distribuicao,
            'movimentacoes': movimentacoes,
            'status': status_proc,
        }

    def _generate_movimentacoes(self, numero_processo: str, days_range: int, limit: int = 20) -> list:
        """Gera movimentações processuais simuladas."""
        random.seed(hash(numero_processo) + 42)
        num_movs = random.randint(5, min(limit, 15))

        movs = []
        for i in range(num_movs):
            tipo, descricao = random.choice(self.MOVIMENTACOES_TIPOS)
            days_ago = random.randint(1, max(days_range, 2))
            data = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%dT%H:%M:%S')
            movs.append({
                'id': str(uuid.uuid4()),
                'data': data,
                'tipo': tipo,
                'descricao': descricao,
                'complemento': f'Referente ao processo {numero_processo}',
            })

        movs.sort(key=lambda x: x['data'], reverse=True)
        return movs[:limit]

    def get_movimentacoes(self, numero_processo: str, limit: int = 20) -> list:
        """Retorna movimentações recentes de um processo."""
        random.seed(hash(numero_processo) + 99)
        days_range = random.randint(30, 1500)
        return self._generate_movimentacoes(numero_processo, days_range, limit)

    def sync_case_data(self, case_id) -> dict:
        """
        Sincroniza dados do DataJud com um caso existente no Verus.AI.
        Atualiza status e registra movimentações recentes.
        """
        from apps.cases.models import LegalCase

        try:
            case = LegalCase.objects.get(pk=case_id)
        except LegalCase.DoesNotExist:
            return {'success': False, 'error': 'Caso não encontrado.'}

        if not case.numero_processo:
            return {'success': False, 'error': 'Caso não possui número de processo cadastrado.'}

        datajud_data = self.search_process(case.numero_processo)

        # Atualizar campos do caso com dados do DataJud
        updated_fields = []

        if datajud_data.get('tribunal') and not case.tribunal:
            case.tribunal = datajud_data['tribunal']
            updated_fields.append('tribunal')

        if datajud_data.get('vara') and not case.vara_juizo:
            case.vara_juizo = datajud_data['vara']
            updated_fields.append('vara_juizo')

        if datajud_data.get('partes', {}).get('reu', {}).get('nome') and not case.parte_contraria:
            case.parte_contraria = datajud_data['partes']['reu']['nome']
            updated_fields.append('parte_contraria')

        # Mapear status DataJud para status do modelo
        status_map = {
            'Em andamento': 'ativo',
            'Suspenso': 'suspenso',
            'Arquivado': 'arquivado',
            'Baixado': 'encerrado',
            'Em grau de recurso': 'ativo',
        }
        datajud_status = datajud_data.get('status', '')
        mapped_status = status_map.get(datajud_status)
        if mapped_status and mapped_status != case.status:
            case.status = mapped_status
            updated_fields.append('status')

        if updated_fields:
            case.save(update_fields=updated_fields + ['updated_at'])

        return {
            'success': True,
            'updated_fields': updated_fields,
            'datajud_data': datajud_data,
            'message': f'{len(updated_fields)} campo(s) atualizado(s) com dados do DataJud.',
        }

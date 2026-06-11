"""
Management command para criar clientes demo no Verus.AI.
Uso: python manage.py seed_clients
"""
from django.core.management.base import BaseCommand
from apps.cases.models import Client


DEMO_CLIENTS = [
    # 3 Pessoa Física (estados distintos)
    {
        'name': 'Maria Aparecida dos Santos',
        'client_type': 'pessoa_fisica',
        'cpf_cnpj': '123.456.789-00',
        'rg': '12.345.678-9',
        'email': 'maria.santos@verus.ai',
        'phone': '(11) 99876-5432',
        'address': 'Rua das Flores, 123, Apto 45',
        'city': 'São Paulo',
        'state': 'SP',
        'zipcode': '01234-567',
        'notes': 'Cliente desde 2023. Caso de indenização por danos morais em andamento.',
    },
    {
        'name': 'João Carlos Ferreira Lima',
        'client_type': 'pessoa_fisica',
        'cpf_cnpj': '987.654.321-00',
        'rg': '23.456.789-0',
        'email': 'joao.lima@verus.ai',
        'phone': '(21) 98765-4321',
        'phone_secondary': '(21) 3456-7890',
        'address': 'Av. Atlântica, 456, Cobertura',
        'city': 'Rio de Janeiro',
        'state': 'RJ',
        'zipcode': '22010-000',
        'notes': 'Processo trabalhista contra ex-empregador. Audiência marcada.',
    },
    {
        'name': 'Ana Carolina Ribeiro de Souza',
        'client_type': 'pessoa_fisica',
        'cpf_cnpj': '456.789.123-00',
        'rg': '34.567.890-1',
        'email': 'ana.souza@verus.ai',
        'phone': '(31) 97654-3210',
        'address': 'Rua da Bahia, 789',
        'city': 'Belo Horizonte',
        'state': 'MG',
        'zipcode': '30160-011',
        'notes': 'Divórcio consensual com partilha de bens.',
    },
    # 2 Pessoa Jurídica
    {
        'name': 'Tech Solutions Brasil Ltda',
        'client_type': 'pessoa_juridica',
        'cpf_cnpj': '12.345.678/0001-90',
        'email': 'juridico@verus.ai',
        'phone': '(11) 3456-7890',
        'phone_secondary': '(11) 3456-7891',
        'address': 'Av. Paulista, 1000, 15o andar',
        'city': 'São Paulo',
        'state': 'SP',
        'zipcode': '01310-100',
        'company_name': 'Tech Solutions Brasil Serviços de TI Ltda',
        'contact_person': 'Roberto Almeida (Diretor Jurídico)',
        'notes': 'Contrato de assessoria jurídica permanente. Foco em direito empresarial e trabalhista.',
    },
    {
        'name': 'Construtora Horizonte S.A.',
        'client_type': 'pessoa_juridica',
        'cpf_cnpj': '98.765.432/0001-10',
        'email': 'contato@verus.ai',
        'phone': '(41) 3210-9876',
        'address': 'Rua XV de Novembro, 500, Sala 301',
        'city': 'Curitiba',
        'state': 'PR',
        'zipcode': '80020-310',
        'company_name': 'Construtora Horizonte Empreendimentos Imobiliários S.A.',
        'contact_person': 'Fernanda Costa (Gerente Administrativo)',
        'notes': 'Múltiplos casos imobiliários e contratos de incorporação.',
    },
]


class Command(BaseCommand):
    help = 'Cria 5 clientes demo (3 PF + 2 PJ) para o Verus.AI'

    def handle(self, *args, **options):
        created = 0
        for data in DEMO_CLIENTS:
            cpf_cnpj = data['cpf_cnpj']
            if Client.objects.filter(cpf_cnpj=cpf_cnpj).exists():
                self.stdout.write(self.style.WARNING(f'  Pulando (já existe): {data["name"]}'))
                continue

            Client.objects.create(**data)
            created += 1
            self.stdout.write(self.style.SUCCESS(f'  Criado: {data["name"]}'))

        self.stdout.write(self.style.SUCCESS(f'\nTotal: {created} clientes demo criados.'))

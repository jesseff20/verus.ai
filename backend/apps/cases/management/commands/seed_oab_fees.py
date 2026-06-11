"""
Management command — seed_oab_fees (NO-OP para contexto de Procuradoria).

A Tabela de Honorários da OAB é específica da advocacia privada e não se
aplica a procuradorias (PGE, PGM, PGF, AGU etc.), onde os procuradores são
servidores públicos remunerados pelos cofres públicos.

Em procuradorias, os valores relevantes são as custas judiciais (tabela do
tribunal/estado) e os honorários sucumbenciais eventualmente percebidos pelo
ente público — não honorários advocatícios privados.

Se for necessário um seed de custas judiciais estaduais, crie um arquivo
específico:  seed_custas_judiciais.py

Uso: python manage.py seed_oab_fees  (não faz nada)
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        'No-op em contexto de Procuradoria. '
        'Tabela de honorários OAB não se aplica a procuradores públicos. '
        'Veja a docstring deste arquivo para mais detalhes.'
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            '\n[seed_oab_fees] IGNORADO — contexto de Procuradoria.\n'
            'A tabela de honorários OAB é específica da advocacia privada.\n'
            'Procuradores são servidores públicos; honorários sucumbenciais\n'
            'pertencem ao ente público, não ao procurador individualmente.\n'
            'Para custas judiciais estaduais, crie seed_custas_judiciais.py.\n'
        ))

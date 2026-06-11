"""
Management command — seed_clients (NO-OP para contexto de Procuradoria).

Em procuradorias (PGE, PGM, PGF etc.) não existe o conceito de "cliente" no
sentido de advocacia privada. As partes nos processos são cadastradas
diretamente em cada caso como "partes interessadas" (polo ativo, polo passivo,
terceiros interessados, entes públicos, etc.).

Por esse motivo, este seed não cria registros de Client. O modelo Client ainda
pode ser usado para cadastrar entes públicos externos, mas esse cadastro deve
ser feito via interface administrativa ou via seed específico de cada órgão.

Se precisar de dados demo de partes/entes, crie um seed separado:
    python manage.py seed_partes_demo

Uso: python manage.py seed_clients  (não faz nada)
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        'No-op em contexto de Procuradoria. '
        'Partes são gerenciadas por caso, não como clientes globais. '
        'Veja a docstring deste arquivo para mais detalhes.'
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            '\n[seed_clients] IGNORADO — contexto de Procuradoria.\n'
            'Em procuradorias, "clientes" não se aplicam: as partes são\n'
            'cadastradas diretamente em cada processo (polo ativo/passivo).\n'
            'Use seed_partes_demo para criar partes de demonstração, se necessário.\n'
        ))

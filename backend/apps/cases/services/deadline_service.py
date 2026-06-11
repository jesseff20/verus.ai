"""
Serviço para criação automática de prazos processuais.
"""
import logging
from datetime import timedelta
from django.utils import timezone

from apps.cases.models import LegalDeadline, LegalCase

logger = logging.getLogger(__name__)


class DeadlineService:
    """Calcula e cria prazos processuais automaticamente."""

    PRAZOS_PADRAO = {
        'civel': [
            {'tipo': 'processual', 'titulo': 'Contestação', 'prazo_dias': 15,
             'descricao': 'Prazo para contestar (CPC art. 335)', 'prioridade': 'alta'},
            {'tipo': 'processual', 'titulo': 'Réplica', 'prazo_dias': 15,
             'descricao': 'Prazo para réplica (CPC art. 351)', 'prioridade': 'media'},
            {'tipo': 'processual', 'titulo': 'Especificação de Provas', 'prazo_dias': 10,
             'descricao': 'Prazo para especificar provas', 'prioridade': 'media'},
        ],
        'criminal': [
            {'tipo': 'processual', 'titulo': 'Resposta à Acusação', 'prazo_dias': 10,
             'descricao': 'Prazo para resposta (CPP art. 396-A)', 'prioridade': 'urgente'},
            {'tipo': 'processual', 'titulo': 'Alegações Finais', 'prazo_dias': 5,
             'descricao': 'Prazo para alegações finais (CPP art. 403)', 'prioridade': 'alta'},
        ],
        'trabalhista': [
            {'tipo': 'processual', 'titulo': 'Defesa', 'prazo_dias': 0,
             'descricao': 'Apresentar em audiência (CLT art. 847)', 'prioridade': 'urgente'},
            {'tipo': 'recursal', 'titulo': 'Recurso Ordinário', 'prazo_dias': 8,
             'descricao': 'Prazo para RO (CLT art. 895)', 'prioridade': 'alta'},
        ],
        'tributario': [
            {'tipo': 'processual', 'titulo': 'Impugnação', 'prazo_dias': 30,
             'descricao': 'Prazo para impugnação ao auto de infração', 'prioridade': 'alta'},
            {'tipo': 'recursal', 'titulo': 'Recurso Voluntário', 'prazo_dias': 30,
             'descricao': 'Prazo para recurso voluntário ao CARF', 'prioridade': 'alta'},
        ],
        'administrativo': [
            {'tipo': 'administrativo', 'titulo': 'Defesa Administrativa', 'prazo_dias': 15,
             'descricao': 'Prazo para defesa em processo administrativo', 'prioridade': 'alta'},
            {'tipo': 'recursal', 'titulo': 'Recurso Administrativo', 'prazo_dias': 10,
             'descricao': 'Prazo para recurso administrativo', 'prioridade': 'alta'},
        ],
        'previdenciario': [
            {'tipo': 'processual', 'titulo': 'Contestação INSS', 'prazo_dias': 30,
             'descricao': 'Prazo para contestação em ações previdenciárias', 'prioridade': 'alta'},
            {'tipo': 'recursal', 'titulo': 'Recurso Inominado', 'prazo_dias': 10,
             'descricao': 'Prazo para recurso inominado (JEF)', 'prioridade': 'alta'},
        ],
        'familia': [
            {'tipo': 'processual', 'titulo': 'Contestação', 'prazo_dias': 15,
             'descricao': 'Prazo para contestar (CPC art. 335)', 'prioridade': 'alta'},
            {'tipo': 'processual', 'titulo': 'Audiência de Conciliação', 'prazo_dias': 30,
             'descricao': 'Prazo para audiência de mediação/conciliação (CPC art. 334)', 'prioridade': 'media'},
        ],
        'empresarial': [
            {'tipo': 'processual', 'titulo': 'Contestação', 'prazo_dias': 15,
             'descricao': 'Prazo para contestar (CPC art. 335)', 'prioridade': 'alta'},
            {'tipo': 'processual', 'titulo': 'Habilitação de Crédito', 'prazo_dias': 15,
             'descricao': 'Prazo para habilitação de crédito em recuperação judicial', 'prioridade': 'alta'},
        ],
        'ambiental': [
            {'tipo': 'processual', 'titulo': 'Contestação', 'prazo_dias': 15,
             'descricao': 'Prazo para contestar (CPC art. 335)', 'prioridade': 'alta'},
            {'tipo': 'administrativo', 'titulo': 'Defesa Ambiental', 'prazo_dias': 20,
             'descricao': 'Prazo para defesa em auto de infração ambiental', 'prioridade': 'urgente'},
        ],
        'consumidor': [
            {'tipo': 'processual', 'titulo': 'Contestação', 'prazo_dias': 15,
             'descricao': 'Prazo para contestar (CPC art. 335)', 'prioridade': 'alta'},
            {'tipo': 'processual', 'titulo': 'Recurso Inominado', 'prazo_dias': 10,
             'descricao': 'Prazo para recurso inominado (JEC)', 'prioridade': 'alta'},
        ],
        'imobiliario': [
            {'tipo': 'processual', 'titulo': 'Contestação', 'prazo_dias': 15,
             'descricao': 'Prazo para contestar (CPC art. 335)', 'prioridade': 'alta'},
            {'tipo': 'processual', 'titulo': 'Emenda à Inicial', 'prazo_dias': 15,
             'descricao': 'Prazo para emenda à inicial (CPC art. 321)', 'prioridade': 'media'},
        ],
        'outros': [
            {'tipo': 'processual', 'titulo': 'Contestação', 'prazo_dias': 15,
             'descricao': 'Prazo para contestar (CPC art. 335)', 'prioridade': 'alta'},
        ],
    }

    @classmethod
    def create_default_deadlines(cls, case: LegalCase, user=None, prazos_identificados=None):
        """
        Cria prazos padrão baseados na especialidade do caso ou prazos
        identificados pela IA a partir de documento.

        Args:
            case: Instância do LegalCase recém-criado.
            user: Usuário que criou o caso (para created_by nos prazos).
            prazos_identificados: Lista de prazos extraídos por IA do documento.
                Cada item: {'tipo': str, 'prazo_dias': int, 'descricao': str, 'data_inicio': str}

        Returns:
            Lista de LegalDeadline criados.
        """
        deadlines_created = []
        data_base = case.data_distribuicao or timezone.now().date()

        if prazos_identificados:
            deadlines_created = cls._create_from_ai_extraction(
                case, data_base, prazos_identificados, user
            )
        else:
            deadlines_created = cls._create_from_defaults(
                case, data_base, user
            )

        if deadlines_created:
            logger.info(
                f"[DeadlineService] Criados {len(deadlines_created)} prazos para caso {case.id}"
            )

        return deadlines_created

    @classmethod
    def _create_from_ai_extraction(cls, case, data_base, prazos_identificados, user):
        """Cria prazos a partir de dados extraídos pela IA."""
        deadlines = []
        for prazo in prazos_identificados:
            try:
                prazo_dias = int(prazo.get('prazo_dias', 15))
                data_inicio_str = prazo.get('data_inicio')

                if data_inicio_str:
                    from datetime import date as date_type
                    try:
                        parts = data_inicio_str.split('-')
                        data_inicio = date_type(int(parts[0]), int(parts[1]), int(parts[2]))
                    except (ValueError, IndexError):
                        data_inicio = data_base
                else:
                    data_inicio = data_base

                data_prazo = data_inicio + timedelta(days=prazo_dias)

                titulo = prazo.get('tipo', 'Prazo Processual')
                if titulo and titulo[0].islower():
                    titulo = titulo.capitalize()

                deadline = LegalDeadline.objects.create(
                    caso=case,
                    titulo=titulo,
                    descricao=prazo.get('descricao', ''),
                    tipo='processual',
                    prioridade='alta',
                    status='pendente',
                    data_prazo=data_prazo,
                    responsavel=case.advogado_responsavel,
                    created_by=user,
                )
                deadlines.append(deadline)
            except Exception as exc:
                logger.warning(f"[DeadlineService] Erro ao criar prazo da IA: {exc}")
                continue

        return deadlines

    @classmethod
    def _create_from_defaults(cls, case, data_base, user):
        """Cria prazos a partir dos padrões da especialidade."""
        deadlines = []
        padrao = cls.PRAZOS_PADRAO.get(case.especialidade, cls.PRAZOS_PADRAO['outros'])

        for prazo_config in padrao:
            try:
                prazo_dias = prazo_config['prazo_dias']
                data_prazo = data_base + timedelta(days=prazo_dias) if prazo_dias > 0 else data_base

                deadline = LegalDeadline.objects.create(
                    caso=case,
                    titulo=prazo_config['titulo'],
                    descricao=prazo_config['descricao'],
                    tipo=prazo_config.get('tipo', 'processual'),
                    prioridade=prazo_config.get('prioridade', 'media'),
                    status='pendente',
                    data_prazo=data_prazo,
                    responsavel=case.advogado_responsavel,
                    created_by=user,
                )
                deadlines.append(deadline)
            except Exception as exc:
                logger.warning(f"[DeadlineService] Erro ao criar prazo padrão: {exc}")
                continue

        return deadlines

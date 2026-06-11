"""
Serviço de Acompanhamento de Tribunal — Push de eventos e notificações.
"""
import logging
import random
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q

logger = logging.getLogger(__name__)

# Tipos de evento simulados
EVENT_TYPES = [
    ('movimentacao', 'Movimentação processual registrada'),
    ('intimacao', 'Intimação publicada no DJe'),
    ('publicacao', 'Publicação no Diário Oficial'),
    ('despacho', 'Despacho do juiz'),
    ('sentenca', 'Sentença proferida'),
    ('decisao', 'Decisão interlocutória'),
    ('audiencia', 'Audiência designada'),
    ('citacao', 'Citação expedida'),
    ('juntada', 'Juntada de documento'),
    ('distribuicao', 'Distribuição realizada'),
]

EVENT_DESCRIPTIONS = {
    'movimentacao': [
        'Juntada de petição do autor.',
        'Conclusos para decisão.',
        'Remetidos os autos ao contador.',
        'Expedida carta precatória.',
        'Certificado o trânsito em julgado.',
    ],
    'intimacao': [
        'Intimação para manifestação no prazo de 15 dias.',
        'Intimação da sentença proferida.',
        'Intimação para ciência do despacho.',
        'Intimação para pagamento de custas.',
        'Intimação para cumprimento de decisão.',
    ],
    'publicacao': [
        'Publicação de decisão no DJe.',
        'Publicação de edital de citação.',
        'Publicação de pauta de julgamento.',
        'Publicação de acórdão.',
    ],
    'despacho': [
        'Cite-se a parte ré para contestar em 15 dias.',
        'Defiro a tutela de urgência requerida.',
        'Designo audiência de conciliação.',
        'Indefiro o pedido de produção de prova pericial.',
        'Determino a intimação das partes.',
    ],
    'sentenca': [
        'Julgo procedente o pedido do autor.',
        'Julgo improcedente o pedido.',
        'Homologo o acordo celebrado entre as partes.',
        'Julgo parcialmente procedente.',
    ],
    'decisao': [
        'Concedo a tutela antecipada requerida.',
        'Indefiro o pedido liminar.',
        'Determino a emenda da petição inicial.',
        'Defiro a gratuidade de justiça.',
    ],
    'audiencia': [
        'Audiência de conciliação designada para 30 dias.',
        'Audiência de instrução e julgamento designada.',
        'Audiência de mediação designada.',
    ],
    'citacao': [
        'Citação por oficial de justiça expedida.',
        'Citação por edital publicada.',
        'Citação eletrônica realizada.',
    ],
    'juntada': [
        'Juntada de contestação da parte ré.',
        'Juntada de laudo pericial.',
        'Juntada de comprovante de pagamento.',
        'Juntada de substabelecimento.',
    ],
    'distribuicao': [
        'Processo distribuído para a 3ª Vara Cível.',
        'Processo redistribuído por prevenção.',
    ],
}


class TribunalPushService:
    """Gerencia acompanhamento de tribunal e eventos push."""

    @staticmethod
    def create_config(user, court_system, notification_types=None):
        """Cria configuração de acompanhamento de tribunal."""
        from apps.cases.models import TribunalPushConfig

        if notification_types is None:
            notification_types = ['movimentacao', 'intimacao', 'publicacao', 'despacho']

        config = TribunalPushConfig.objects.create(
            user=user,
            court_system=court_system,
            notification_types=notification_types,
            is_active=True,
        )
        logger.info(f"[TribunalPushService] Config criada: {config.id}")
        return config

    @staticmethod
    def check_for_updates(config):
        """Simula verificação de novas atualizações do tribunal."""
        from apps.cases.models import TribunalPushEvent, LegalCase

        # Simular 0-3 novos eventos
        num_events = random.randint(0, 3)
        events_created = []

        # Buscar casos do usuário para vincular eventos
        user_cases = list(
            LegalCase.objects.filter(
                Q(advogado_responsavel=config.user) | Q(created_by=config.user),
                status='ativo',
            ).values_list('id', flat=True)[:10]
        )

        for _ in range(num_events):
            event_type_key = random.choice(
                [et[0] for et in EVENT_TYPES if et[0] in config.notification_types]
                or [et[0] for et in EVENT_TYPES]
            )
            descriptions = EVENT_DESCRIPTIONS.get(event_type_key, ['Evento processual registrado.'])
            description = random.choice(descriptions)

            case_id = random.choice(user_cases) if user_cases else None

            event = TribunalPushEvent.objects.create(
                config=config,
                case_id=case_id,
                event_type=event_type_key,
                event_date=timezone.now() - timedelta(hours=random.randint(0, 48)),
                description=description,
                raw_data={
                    'source': config.get_court_system_display(),
                    'court_system': config.court_system,
                    'simulated': True,
                },
            )
            events_created.append(event)

        # Atualizar última verificação
        config.last_checked = timezone.now()
        config.save(update_fields=['last_checked'])

        logger.info(
            f"[TribunalPushService] Verificação concluída para config {config.id}: "
            f"{len(events_created)} eventos encontrados."
        )
        return events_created

    @staticmethod
    def process_events(config):
        """Processa eventos não processados e marca como notificados."""
        from apps.cases.models import TribunalPushEvent

        unprocessed = TribunalPushEvent.objects.filter(
            config=config,
            is_processed=False,
        )
        count = unprocessed.count()
        unprocessed.update(is_processed=True, notification_sent=True)

        logger.info(f"[TribunalPushService] {count} eventos processados para config {config.id}")
        return count

    @staticmethod
    def get_user_events(user, days=30):
        """Retorna eventos recentes do usuário."""
        from apps.cases.models import TribunalPushEvent

        cutoff = timezone.now() - timedelta(days=days)
        return TribunalPushEvent.objects.filter(
            config__user=user,
            event_date__gte=cutoff,
        ).select_related('config', 'case').order_by('-event_date')

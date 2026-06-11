"""
Integração real e-SAJ — Consulta e protocolo nos tribunais estaduais.
e-SAJ é usado por: TJSP, TJMG, TJSC, TJMS, TJAM, TJAC, TJCE, TJAL.

Documentação: APIs do e-SAJ (acesso restrito via certificado digital)
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class ESAJRealService:
    """Integração real com e-SAJ para consulta e protocolo eletrônico."""

    TRIBUNAL_ENDPOINTS = {
        'TJSP': {
            'consulta': 'https://esaj.tjsp.jus.br/cposg/search.do',
            'protocolo': 'https://esaj.tjsp.jus.br/peticionamento',
            'api': 'https://esaj.tjsp.jus.br/sajcoreext/api',
        },
        'TJMG': {
            'consulta': 'https://pje.tjmg.jus.br/pje/ConsultaPublica',
            'api': 'https://esaj.tjmg.jus.br/sajcoreext/api',
        },
        'TJSC': {
            'consulta': 'https://esaj.tjsc.jus.br/cposg/search.do',
            'api': 'https://esaj.tjsc.jus.br/sajcoreext/api',
        },
        'TJMS': {
            'consulta': 'https://esaj.tjms.jus.br/cposg/search.do',
            'api': 'https://esaj.tjms.jus.br/sajcoreext/api',
        },
    }

    def __init__(self):
        self.certificate_path = getattr(settings, 'ESAJ_CERTIFICATE_PATH', '')
        self.certificate_password = getattr(settings, 'ESAJ_CERTIFICATE_PASSWORD', '')

    @property
    def is_configured(self) -> bool:
        return bool(self.certificate_path)

    def consultar_processo(self, tribunal: str, numero_processo: str) -> dict:
        """Consulta processo no e-SAJ."""
        if tribunal not in self.TRIBUNAL_ENDPOINTS:
            return {
                'success': False,
                'error': f'Tribunal não suportado no e-SAJ: {tribunal}',
                'supported': list(self.TRIBUNAL_ENDPOINTS.keys()),
            }

        if not self.is_configured:
            return {
                'success': False,
                'error': 'e-SAJ não configurado. Configure certificado digital.',
                'setup_required': True,
                'env_vars': ['ESAJ_CERTIFICATE_PATH', 'ESAJ_CERTIFICATE_PASSWORD'],
            }

        endpoints = self.TRIBUNAL_ENDPOINTS[tribunal]

        try:
            # Use API endpoint if available
            api_url = endpoints.get('api', '')
            if api_url:
                response = requests.get(
                    f"{api_url}/processos/{numero_processo}",
                    cert=(self.certificate_path, self.certificate_password),
                    timeout=30,
                )
                if response.status_code == 200:
                    return {'success': True, 'data': response.json()}
                return {'success': False, 'error': response.text}

            return {'success': False, 'error': 'API endpoint não disponível para este tribunal'}
        except Exception as e:
            logger.error(f"e-SAJ API error: {e}")
            return {'success': False, 'error': str(e)}

    def protocolar_peticao(self, tribunal: str, numero_processo: str,
                           tipo_peticao: str, arquivo_base64: str,
                           descricao: str = '') -> dict:
        """
        Protocola petição no e-SAJ.
        Requer certificado digital ICP-Brasil.
        """
        if not self.is_configured:
            return {
                'success': False,
                'error': 'e-SAJ não configurado. Certificado digital ICP-Brasil necessário.',
                'setup_required': True,
            }

        if tribunal not in self.TRIBUNAL_ENDPOINTS:
            return {'success': False, 'error': f'Tribunal não suportado: {tribunal}'}

        endpoints = self.TRIBUNAL_ENDPOINTS[tribunal]
        protocolo_url = endpoints.get('protocolo', '')

        if not protocolo_url:
            return {'success': False, 'error': 'Endpoint de protocolo não disponível para este tribunal'}

        try:
            payload = {
                'numeroProcesso': numero_processo,
                'tipoPeticao': tipo_peticao,
                'descricao': descricao,
                'documento': {
                    'conteudo': arquivo_base64,
                    'tipo': 'application/pdf',
                },
            }

            response = requests.post(
                f"{protocolo_url}/api/v1/peticionar",
                json=payload,
                cert=(self.certificate_path, self.certificate_password),
                timeout=60,
            )

            if response.status_code in (200, 201):
                data = response.json()
                return {
                    'success': True,
                    'protocol_number': data.get('numeroProtocolo', ''),
                    'data': data,
                }
            return {'success': False, 'error': response.text}
        except Exception as e:
            logger.error(f"e-SAJ protocol error: {e}")
            return {'success': False, 'error': str(e)}

    def consultar_andamentos(self, tribunal: str, numero_processo: str) -> dict:
        """Consulta andamentos/movimentações do processo."""
        if not self.is_configured:
            return {'success': False, 'error': 'e-SAJ não configurado.', 'setup_required': True}

        endpoints = self.TRIBUNAL_ENDPOINTS.get(tribunal, {})
        api_url = endpoints.get('api', '')

        if not api_url:
            return {'success': False, 'error': 'API não disponível para este tribunal'}

        try:
            response = requests.get(
                f"{api_url}/processos/{numero_processo}/movimentacoes",
                cert=(self.certificate_path, self.certificate_password),
                timeout=30,
            )
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def list_supported_tribunals(self) -> dict:
        """Lista tribunais e-SAJ suportados."""
        return {
            'tribunals': [
                {'code': k, 'consulta': bool(v.get('consulta')), 'protocolo': bool(v.get('protocolo'))}
                for k, v in self.TRIBUNAL_ENDPOINTS.items()
            ]
        }

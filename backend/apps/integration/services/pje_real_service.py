"""
Integração real PJe — Protocolo real nos tribunais.
Usa MNI (Modelo Nacional de Interoperabilidade) via SOAP/REST.

Documentação: https://www.cnj.jus.br/programas-e-acoes/processo-judicial-eletronico-pje/
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class PJeRealService:
    """Integração real com PJe para protocolo e consulta processual."""

    # Endpoints por tribunal (exemplos — cada tribunal tem seu endpoint)
    TRIBUNAL_ENDPOINTS = {
        'TRT1': 'https://pje.trt1.jus.br/pje-consulta-api/api',
        'TRT2': 'https://pje.trt2.jus.br/pje-consulta-api/api',
        'TJRJ': 'https://pje.tjrj.jus.br/pje-consulta-api/api',
        'TJSP': 'https://pje.tjsp.jus.br/pje-consulta-api/api',
        'TJMG': 'https://pje.tjmg.jus.br/pje-consulta-api/api',
        'JFRJ': 'https://pje.jfrj.jus.br/pje-consulta-api/api',
        'JFSP': 'https://pje.jfsp.jus.br/pje-consulta-api/api',
        'STJ': 'https://pje.stj.jus.br/pje-consulta-api/api',
    }

    # MNI WSDL endpoints (Modelo Nacional de Interoperabilidade)
    MNI_ENDPOINTS = {
        'TRT1': 'https://pje.trt1.jus.br/intercomunicacao/servico/intercomunicacao-2.2.2?wsdl',
        'TRT2': 'https://pje.trt2.jus.br/intercomunicacao/servico/intercomunicacao-2.2.2?wsdl',
        'TJRJ': 'https://pje.tjrj.jus.br/intercomunicacao/servico/intercomunicacao-2.2.2?wsdl',
    }

    def __init__(self):
        self.certificate_path = getattr(settings, 'PJE_CERTIFICATE_PATH', '')
        self.certificate_password = getattr(settings, 'PJE_CERTIFICATE_PASSWORD', '')
        self.oab_number = getattr(settings, 'PJE_OAB_NUMBER', '')
        self.oab_state = getattr(settings, 'PJE_OAB_STATE', '')

    @property
    def is_configured(self) -> bool:
        return bool(self.certificate_path)

    def consultar_processo(self, tribunal: str, numero_processo: str) -> dict:
        """
        Consulta processo via API REST do PJe.
        """
        if tribunal not in self.TRIBUNAL_ENDPOINTS:
            return {
                'success': False,
                'error': f'Tribunal não suportado: {tribunal}',
                'supported': list(self.TRIBUNAL_ENDPOINTS.keys()),
            }

        if not self.is_configured:
            return {
                'success': False,
                'error': 'PJe não configurado. Configure certificado digital A1/A3.',
                'setup_required': True,
                'env_vars': ['PJE_CERTIFICATE_PATH', 'PJE_CERTIFICATE_PASSWORD', 'PJE_OAB_NUMBER', 'PJE_OAB_STATE'],
            }

        base_url = self.TRIBUNAL_ENDPOINTS[tribunal]

        try:
            response = requests.get(
                f"{base_url}/processos/{numero_processo}",
                cert=(self.certificate_path, self.certificate_password),
                timeout=30,
            )
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            return {'success': False, 'error': response.text, 'status_code': response.status_code}
        except Exception as e:
            logger.error(f"PJe API error: {e}")
            return {'success': False, 'error': str(e)}

    def consultar_movimentacoes(self, tribunal: str, numero_processo: str) -> dict:
        """Consulta movimentações/andamentos do processo."""
        if not self.is_configured:
            return {'success': False, 'error': 'PJe não configurado.', 'setup_required': True}

        base_url = self.TRIBUNAL_ENDPOINTS.get(tribunal, '')
        if not base_url:
            return {'success': False, 'error': f'Tribunal não suportado: {tribunal}'}

        try:
            response = requests.get(
                f"{base_url}/processos/{numero_processo}/movimentacoes",
                cert=(self.certificate_path, self.certificate_password),
                timeout=30,
            )
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def protocolar_peticao(self, tribunal: str, numero_processo: str,
                           tipo_documento: str, arquivo_base64: str,
                           descricao: str = '') -> dict:
        """
        Protocola petição via MNI (Modelo Nacional de Interoperabilidade).
        Requer certificado digital A1 ou A3.
        """
        if not self.is_configured:
            return {
                'success': False,
                'error': 'PJe não configurado. Certificado digital A1/A3 necessário.',
                'setup_required': True,
                'env_vars': ['PJE_CERTIFICATE_PATH', 'PJE_CERTIFICATE_PASSWORD'],
            }

        if tribunal not in self.MNI_ENDPOINTS:
            return {
                'success': False,
                'error': f'Tribunal sem endpoint MNI configurado: {tribunal}',
                'supported_mni': list(self.MNI_ENDPOINTS.keys()),
            }

        # MNI uses SOAP — requires zeep or suds library
        try:
            from zeep import Client as SoapClient
            from zeep.transports import Transport

            session = requests.Session()
            session.cert = (self.certificate_path, self.certificate_password)
            transport = Transport(session=session, timeout=60)

            client = SoapClient(self.MNI_ENDPOINTS[tribunal], transport=transport)

            # Build SOAP request
            result = client.service.entregarManifestacaoProcessual(
                idManifestante=self.oab_number,
                senhaManifestante='',
                numeroProcesso=numero_processo,
                documento={
                    'tipoDocumento': tipo_documento,
                    'descricao': descricao,
                    'conteudo': arquivo_base64,
                    'mimetype': 'application/pdf',
                }
            )

            return {
                'success': True,
                'protocol_number': str(result.get('protocoloRecebimento', '')),
                'data': str(result),
            }
        except ImportError:
            return {
                'success': False,
                'error': 'Biblioteca zeep não instalada. Execute: pip install zeep',
            }
        except Exception as e:
            logger.error(f"PJe MNI protocol error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def list_supported_tribunals(self) -> dict:
        """Lista tribunais suportados."""
        return {
            'consulta': list(self.TRIBUNAL_ENDPOINTS.keys()),
            'protocolo_mni': list(self.MNI_ENDPOINTS.keys()),
        }

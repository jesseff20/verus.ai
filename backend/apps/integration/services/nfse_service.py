"""
Integração NFS-e — Nota Fiscal de Serviço Eletrônica.
Suporta padrão ABRASF (maioria dos municípios brasileiros).

Documentação: http://www.abrasf.org.br/
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class NFSeService:
    """Integração com prefeituras para emissão de NFS-e."""

    # Principais prefeituras e seus webservices
    MUNICIPIOS = {
        'sao_paulo': {
            'name': 'São Paulo',
            'wsdl': 'https://nfe.prefeitura.sp.gov.br/ws/lotenfe.asmx?wsdl',
            'padrao': 'paulistana',
        },
        'rio_janeiro': {
            'name': 'Rio de Janeiro',
            'url': 'https://notacarioca.rio.gov.br/WSNacional/nfse.asmx',
            'padrao': 'abrasf_2.04',
        },
        'belo_horizonte': {
            'name': 'Belo Horizonte',
            'url': 'https://bhissdigital.pbh.gov.br/bhiss-ws/nfse',
            'padrao': 'abrasf_2.04',
        },
        'joao_pessoa': {
            'name': 'João Pessoa',
            'url': 'https://nfse.joaopessoa.pb.gov.br/nfse/ws',
            'padrao': 'abrasf_2.04',
        },
    }

    def __init__(self):
        self.cnpj = getattr(settings, 'NFSE_CNPJ', '')
        self.inscricao_municipal = getattr(settings, 'NFSE_INSCRICAO_MUNICIPAL', '')
        self.certificate_path = getattr(settings, 'NFSE_CERTIFICATE_PATH', '')
        self.certificate_password = getattr(settings, 'NFSE_CERTIFICATE_PASSWORD', '')
        self.municipio = getattr(settings, 'NFSE_MUNICIPIO', '')

    @property
    def is_configured(self) -> bool:
        return bool(self.cnpj and self.certificate_path and self.municipio)

    def emitir_nfse(self, dados: dict) -> dict:
        """
        Emite NFS-e.

        dados = {
            'tomador': {'cpf_cnpj': '', 'nome': '', 'email': '', 'endereco': {}},
            'servico': {'descricao': '', 'valor': Decimal, 'codigo_cnae': '6911-7/01'},
            'competencia': '2024-01',
        }
        """
        if not self.is_configured:
            return {
                'success': False,
                'error': 'NFS-e não configurado.',
                'setup_required': True,
                'env_vars': [
                    'NFSE_CNPJ', 'NFSE_INSCRICAO_MUNICIPAL',
                    'NFSE_CERTIFICATE_PATH', 'NFSE_CERTIFICATE_PASSWORD',
                    'NFSE_MUNICIPIO',
                ],
            }

        municipio_config = self.MUNICIPIOS.get(self.municipio)
        if not municipio_config:
            return {
                'success': False,
                'error': f'Município não suportado: {self.municipio}',
                'supported': list(self.MUNICIPIOS.keys()),
            }

        xml = self._build_rps_xml(dados)

        try:
            # Sign XML with certificate
            signed_xml = self._sign_xml(xml)

            # Send to prefeitura
            url = municipio_config.get('url') or municipio_config.get('wsdl')

            response = requests.post(
                url,
                data=signed_xml,
                headers={'Content-Type': 'text/xml; charset=utf-8'},
                cert=(self.certificate_path, self.certificate_password),
                timeout=60,
            )

            if response.status_code == 200:
                result = self._parse_nfse_response(response.text)
                return {'success': True, 'data': result}
            return {'success': False, 'error': response.text}
        except Exception as e:
            logger.error(f"NFS-e emission error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def consultar_nfse(self, numero_nfse: str) -> dict:
        """Consulta NFS-e emitida."""
        if not self.is_configured:
            return {'success': False, 'error': 'NFS-e não configurado.', 'setup_required': True}

        # Implementation depends on municipality
        return {'success': False, 'error': 'Implementação depende do município específico'}

    def cancelar_nfse(self, numero_nfse: str, motivo: str) -> dict:
        """Cancela NFS-e emitida."""
        if not self.is_configured:
            return {'success': False, 'error': 'NFS-e não configurado.', 'setup_required': True}

        return {'success': False, 'error': 'Implementação depende do município específico'}

    def _build_rps_xml(self, dados: dict) -> str:
        """Constrói XML do RPS (Recibo Provisório de Serviço) padrão ABRASF."""
        tomador = dados.get('tomador', {})
        servico = dados.get('servico', {})

        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<EnviarLoteRpsEnvio xmlns="http://www.abrasf.org.br/nfse.xsd">
    <LoteRps>
        <NumeroLote>1</NumeroLote>
        <Cnpj>{self.cnpj}</Cnpj>
        <InscricaoMunicipal>{self.inscricao_municipal}</InscricaoMunicipal>
        <QuantidadeRps>1</QuantidadeRps>
        <ListaRps>
            <Rps>
                <InfRps>
                    <IdentificacaoRps>
                        <Numero>1</Numero>
                        <Serie>A</Serie>
                        <Tipo>1</Tipo>
                    </IdentificacaoRps>
                    <DataEmissao>{dados.get('competencia', '')}</DataEmissao>
                    <NaturezaOperacao>1</NaturezaOperacao>
                    <OptanteSimplesNacional>2</OptanteSimplesNacional>
                    <IncentivadorCultural>2</IncentivadorCultural>
                    <Status>1</Status>
                    <Servico>
                        <Valores>
                            <ValorServicos>{servico.get('valor', 0)}</ValorServicos>
                            <IssRetido>2</IssRetido>
                            <ValorIss>0</ValorIss>
                            <Aliquota>5.00</Aliquota>
                        </Valores>
                        <ItemListaServico>{servico.get('codigo_cnae', '6911')}</ItemListaServico>
                        <Discriminacao>{servico.get('descricao', 'Serviços advocatícios')}</Discriminacao>
                        <CodigoMunicipio>2507507</CodigoMunicipio>
                    </Servico>
                    <Prestador>
                        <Cnpj>{self.cnpj}</Cnpj>
                        <InscricaoMunicipal>{self.inscricao_municipal}</InscricaoMunicipal>
                    </Prestador>
                    <Tomador>
                        <IdentificacaoTomador>
                            <CpfCnpj>
                                <Cpf>{tomador.get('cpf_cnpj', '')}</Cpf>
                            </CpfCnpj>
                        </IdentificacaoTomador>
                        <RazaoSocial>{tomador.get('nome', '')}</RazaoSocial>
                    </Tomador>
                </InfRps>
            </Rps>
        </ListaRps>
    </LoteRps>
</EnviarLoteRpsEnvio>"""
        return xml

    def _sign_xml(self, xml: str) -> str:
        """Assina XML com certificado digital A1."""
        try:
            from signxml import XMLSigner
            import lxml.etree as etree

            doc = etree.fromstring(xml.encode())
            # Sign with A1 certificate
            signer = XMLSigner()
            signed = signer.sign(doc, key=self.certificate_path)
            return etree.tostring(signed, encoding='unicode')
        except ImportError:
            logger.warning("signxml not installed. Returning unsigned XML.")
            return xml

    def _parse_nfse_response(self, xml_response: str) -> dict:
        """Parse da resposta XML da prefeitura."""
        try:
            import lxml.etree as etree
            doc = etree.fromstring(xml_response.encode())
            # Extract key fields
            ns = {'nfse': 'http://www.abrasf.org.br/nfse.xsd'}
            numero = doc.find('.//nfse:Numero', ns)
            codigo = doc.find('.//nfse:CodigoVerificacao', ns)
            return {
                'numero_nfse': numero.text if numero is not None else '',
                'codigo_verificacao': codigo.text if codigo is not None else '',
                'xml': xml_response,
            }
        except Exception:
            logger.warning("Failed to parse NFS-e XML response", exc_info=True)
            return {'xml': xml_response}

    def list_supported_municipios(self) -> dict:
        """Lista municípios suportados."""
        return {
            'municipios': [
                {'code': k, 'name': v['name'], 'padrao': v['padrao']}
                for k, v in self.MUNICIPIOS.items()
            ]
        }

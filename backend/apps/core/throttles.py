"""
Throttle classes granulares para endpoints sensíveis.
"""
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class AIGenerationThrottle(UserRateThrottle):
    """Limite para endpoints de geração IA (Petição, Blueprint, Copilot, Enhance)."""
    scope = 'ai_generation'
    rate = '30/hour'


class OCRUploadThrottle(UserRateThrottle):
    """Limite para upload/processamento OCR."""
    scope = 'ocr_upload'
    rate = '20/hour'


class NFSeEmitThrottle(UserRateThrottle):
    """Limite para emissão de NFS-e (operação fiscal crítica)."""
    scope = 'nfse_emit'
    rate = '10/hour'


class ConflictCheckThrottle(UserRateThrottle):
    """Limite para verificação de conflito de interesses."""
    scope = 'conflict_check'
    rate = '60/hour'


class LoginThrottle(AnonRateThrottle):
    """Limite para tentativas de login (prevenção brute-force)."""
    scope = 'login'
    rate = '10/minute'


class ExportThrottle(UserRateThrottle):
    """Limite para exportação de dados (operação pesada)."""
    scope = 'data_export'
    rate = '5/hour'


class ProtocolSubmitThrottle(UserRateThrottle):
    """Limite para protocolo eletrônico (operação legal crítica)."""
    scope = 'protocol_submit'
    rate = '20/hour'


class SignatureThrottle(UserRateThrottle):
    """Limite para assinatura digital."""
    scope = 'digital_signature'
    rate = '15/hour'

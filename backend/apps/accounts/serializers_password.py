"""
Serializers para o fluxo de reset de senha.

Endpoints:
- POST request-password-reset/ — Solicitação de reset (informa e-mail)
- POST reset-password/ — Execução do reset (token + nova senha)
"""
import logging

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

User = get_user_model()


class RequestResetSerializer(serializers.Serializer):
    """
    Serializer para solicitação de reset de senha.

    Recebe apenas o e-mail e valida se o usuário existe.
    Por segurança, a resposta é sempre a mesma (não revela
    se o e-mail está cadastrado ou não).
    """
    email = serializers.EmailField(
        required=True,
        help_text='E-mail cadastrado no sistema',
    )

    def validate_email(self, value):
        """
        Normaliza o e-mail (trim + lowercase).
        Não valida existência para não revelar informações.
        """
        return value.strip().lower()


class ResetPasswordSerializer(serializers.Serializer):
    """
    Serializer para execução do reset de senha.

    Recebe o token JWT e a nova senha (com confirmação).
    A validação do token (assinatura, expiração, hash) é
    feita pelo token_service, não aqui.

    A senha é hasheada com HASH_COST=12 (bcrypt) via
    set_password() do Django.
    """
    token = serializers.CharField(
        required=True,
        help_text='Token JWT recebido no link de reset',
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text='Nova senha (mín. 8 caracteres, com letras e números)',
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Confirmação da nova senha',
    )

    def validate(self, attrs):
        """
        Validações iniciais:
        1. Senhas coincidem
        2. Token tem formato básico válido
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password': 'As senhas não coincidem.',
            })

        # Remove password_confirm (não será usado depois)
        attrs.pop('password_confirm')

        # Validação básica do formato do token
        token = attrs.get('token', '')
        if not token or len(token) < 20:
            raise serializers.ValidationError({
                'token': 'Token inválido ou mal formatado.',
            })

        return attrs

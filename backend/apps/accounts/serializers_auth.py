"""
Serializers para fluxo de autenticação com confirmação de e-mail.

Inclui:
- RegisterWithConfirmSerializer: Registro com validação e envio de token
- ConfirmEmailSerializer: Validação do token de confirmação
"""
import logging

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

User = get_user_model()


class RegisterWithConfirmSerializer(serializers.ModelSerializer):
    """
    Serializer para registro de usuário com confirmação de e-mail.

    - Valida dados do formulário
    - Cria usuário em estado pendente (is_active=False)
    - Senha é hasheada com set_password() usando bcrypt (HASH_COST=12)
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone',
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
        }

    def validate(self, attrs):
        """Validações iniciais dos dados de registro."""
        # Confirma que as senhas coincidem
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password': 'As senhas não coincidem.',
            })

        # Remove password_confirm antes de criar o usuário
        attrs.pop('password_confirm')

        return attrs

    def validate_email(self, value):
        """Verifica se o e-mail já está em uso."""
        value = value.strip().lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'Este e-mail já está cadastrado no sistema.'
            )
        return value

    def validate_username(self, value):
        """Verifica se o username já está em uso."""
        value = value.strip().lower()
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                'Este nome de usuário já está em uso.'
            )
        return value

    def create(self, validated_data):
        """
        Cria o usuário em estado pendente (is_active=False).

        Usa set_password() do Django para hash da senha com bcrypt.
        O usuário só será ativado após confirmar o e-mail.
        """
        password = validated_data.pop('password')

        # Define role padrão para auto-registro
        validated_data['role'] = 'analista'

        # Cria o usuário com is_active=False (pendente)
        user = User(**validated_data)
        user.is_active = False  # Pendente — aguarda confirmação de e-mail
        user.set_password(password)  # Hash com bcrypt (HASH_COST=12)

        # Salva com username em lowercase para consistência
        user.username = user.username.strip().lower()

        try:
            user.save()
            logger.info(
                'Usuário criado em estado pendente: id=%s, email=%s',
                user.id, user.email
            )
        except Exception as e:
            logger.error('Erro ao criar usuário: %s', str(e))
            raise serializers.ValidationError(
                'Erro ao criar conta. Tente novamente mais tarde.'
            )

        return user


class ConfirmEmailSerializer(serializers.Serializer):
    """
    Serializer para validar o token de confirmação de e-mail.

    Recebe o token JWT e valida:
    - Assinatura do token
    - Expiração
    - Integridade (hash antifraude)
    """
    token = serializers.CharField(
        required=True,
        help_text='Token JWT recebido no link de confirmação',
    )

    def validate_token(self, value):
        """
        Validação básica do formato do token.
        A validação completa (assinatura, expiração, hash) é feita
        no service token_service.validar_token_confirmacao().
        """
        if not value or len(value) < 20:
            raise serializers.ValidationError('Token inválido ou mal formatado.')
        return value

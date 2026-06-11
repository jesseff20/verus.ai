"""
Serializers para autenticação e usuários
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, BrandSettings, Notification, UserReminder, NotificationChannel, NotificationMessage


class AbsoluteURLImageField(serializers.ImageField):
    """
    Campo de imagem que retorna URL absoluta sem duplicar protocolo.

    O DRF padrão usa request.build_absolute_uri() que duplica o protocolo
    quando o storage (S3/R2) já retorna URLs absolutas com https://.

    Este campo retorna a URL diretamente do storage, evitando duplicação.
    """

    def to_representation(self, value):
        if not value:
            return None
        # Retorna URL diretamente do storage, sem build_absolute_uri
        try:
            return value.url
        except AttributeError:
            return None


class UserSerializer(serializers.ModelSerializer):
    """Serializer para exibir dados do usuário"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    signature_image = AbsoluteURLImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'phone', 'department', 'position', 'avatar',
            'oab_number', 'oab_state', 'lawyer_specialties',
            'signature_image', 'signature_name',
            'preferred_llm_provider', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar novo usuário (admin only)"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'role', 'phone', 'department', 'position'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer para auto-registro (público)"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        # Usuário auto-registrado sempre começa como 'analista'
        validated_data['role'] = 'analista'
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer para login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Credenciais inválidas.')
            if not user.is_active:
                raise serializers.ValidationError('Usuário inativo.')
        else:
            raise serializers.ValidationError('Username e senha são obrigatórios.')

        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para trocar senha"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Senha atual incorreta.')
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "As senhas não coincidem."})
        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualizar perfil do usuário"""

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'department', 'position', 'avatar', 'preferred_llm_provider',
            'oab_number', 'oab_state', 'lawyer_specialties',
            'signature_image', 'signature_name',
        ]


class BrandSettingsSerializer(serializers.ModelSerializer):
    """Serializer para configurações de marca"""
    updated_by_name = serializers.CharField(
        source='updated_by.get_full_name',
        read_only=True,
        allow_null=True
    )

    # Usar AbsoluteURLImageField para evitar duplicação de protocolo com S3/R2
    logo = AbsoluteURLImageField(required=False, allow_null=True)
    logo_dark = AbsoluteURLImageField(required=False, allow_null=True)
    favicon = AbsoluteURLImageField(required=False, allow_null=True)

    class Meta:
        model = BrandSettings
        fields = [
            'id',
            'system_name',
            'system_tagline',
            'logo',
            'logo_dark',
            'favicon',
            'primary_color',
            'secondary_color',
            'accent_color',
            'created_at',
            'updated_at',
            'updated_by',
            'updated_by_name',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'updated_by_name']

    def validate_primary_color(self, value):
        """Valida formato hexadecimal da cor primária"""
        if value and not value.startswith('#'):
            raise serializers.ValidationError('Cor deve estar no formato hexadecimal (#RRGGBB)')
        if value and len(value) != 7:
            raise serializers.ValidationError('Cor deve ter 7 caracteres (#RRGGBB)')
        return value

    def validate_secondary_color(self, value):
        """Valida formato hexadecimal da cor secundária"""
        if value and not value.startswith('#'):
            raise serializers.ValidationError('Cor deve estar no formato hexadecimal (#RRGGBB)')
        if value and len(value) != 7:
            raise serializers.ValidationError('Cor deve ter 7 caracteres (#RRGGBB)')
        return value

    def validate_accent_color(self, value):
        """Valida formato hexadecimal da cor de destaque"""
        if value and not value.startswith('#'):
            raise serializers.ValidationError('Cor deve estar no formato hexadecimal (#RRGGBB)')
        if value and len(value) != 7:
            raise serializers.ValidationError('Cor deve ter 7 caracteres (#RRGGBB)')
        return value

    def update(self, instance, validated_data):
        """Atualiza e registra quem fez a alteração"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer para notificações do usuário"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'type_display', 'priority', 'priority_display',
            'title', 'message', 'link', 'is_read', 'created_at',
            'copilot_prompt', 'action_type', 'source', 'metadata',
        ]
        read_only_fields = ['id', 'created_at']


class UserReminderSerializer(serializers.ModelSerializer):
    """Serializer para lembretes do usuário"""
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    related_case_title = serializers.SerializerMethodField()

    class Meta:
        model = UserReminder
        fields = [
            'id', 'title', 'description',
            'frequency', 'frequency_display',
            'scheduled_date', 'end_date', 'custom_interval_days',
            'related_case', 'related_case_title',
            'copilot_prompt', 'link',
            'status', 'status_display',
            'last_triggered', 'trigger_count',
            'notify_before_minutes', 'priority', 'priority_display',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'last_triggered', 'trigger_count', 'created_at', 'updated_at',
        ]

    def get_related_case_title(self, obj):
        if obj.related_case:
            return str(obj.related_case)
        return None

    def validate(self, attrs):
        frequency = attrs.get('frequency', getattr(self.instance, 'frequency', 'once'))
        if frequency == 'custom' and not attrs.get('custom_interval_days'):
            raise serializers.ValidationError({
                'custom_interval_days': 'Obrigatório para frequência personalizada.',
            })
        return attrs


class NotificationChannelSerializer(serializers.ModelSerializer):
    """Serializer para canais de notificação do usuário"""
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)

    class Meta:
        model = NotificationChannel
        fields = [
            'id', 'channel', 'channel_display', 'is_active', 'auto_send',
            'whatsapp_number', 'whatsapp_verified',
            'email_address', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'whatsapp_verified']

    def validate(self, attrs):
        channel = attrs.get('channel', getattr(self.instance, 'channel', ''))
        if channel == 'whatsapp' and not attrs.get('whatsapp_number'):
            raise serializers.ValidationError({
                'whatsapp_number': 'Obrigatório para canal WhatsApp.',
            })
        if channel == 'email' and not attrs.get('email_address'):
            raise serializers.ValidationError({
                'email_address': 'Obrigatório para canal E-mail.',
            })
        return attrs


class NotificationMessageSerializer(serializers.ModelSerializer):
    """Serializer para mensagens de notificação enviadas"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = NotificationMessage
        fields = [
            'id', 'notification', 'channel', 'subject', 'body',
            'whatsapp_link', 'status', 'status_display',
            'sent_at', 'created_at',
        ]
        read_only_fields = ['id', 'sent_at', 'created_at']

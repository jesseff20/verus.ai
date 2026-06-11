"""
Views para autenticação e gerenciamento de usuários
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.utils import timezone
from datetime import timedelta
from django_filters.rest_framework import DjangoFilterBackend
from .models import User, BrandSettings, Notification, UserReminder, NotificationChannel, NotificationMessage
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    RegisterSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    BrandSettingsSerializer,
    NotificationSerializer,
    UserReminderSerializer,
    NotificationChannelSerializer,
    NotificationMessageSerializer,
)
from .permissions import (
    get_user_permissions,
    get_all_roles,
    get_permissions_matrix,
    ROLE_DESCRIPTIONS,
    PERMISSION_LABELS,
)


class LoginRateThrottle(AnonRateThrottle):
    """Throttle específico para o endpoint de login — previne brute force."""
    scope = 'login'


class IsAdminOrManager(permissions.BasePermission):
    """Permissão para admin ou manager (inclui roles jurídicos equivalentes)"""
    def has_permission(self, request, view):
        from .permissions import is_admin_or_manager
        return is_admin_or_manager(request.user)


@extend_schema_view(
    list=extend_schema(
        summary="Listar usuários",
        description="Lista todos os usuários (admin/manager) ou apenas o próprio usuário",
        tags=["Usuários"]
    ),
    retrieve=extend_schema(
        summary="Buscar usuário por ID",
        description="Retorna dados de um usuário específico",
        tags=["Usuários"]
    ),
    create=extend_schema(
        summary="Criar novo usuário",
        description="Cria um novo usuário (apenas admin/manager)",
        tags=["Usuários"],
        request=UserCreateSerializer,
        responses={201: UserSerializer}
    ),
    update=extend_schema(
        summary="Atualizar usuário",
        description="Atualiza todos os campos de um usuário",
        tags=["Usuários"],
        request=UserUpdateSerializer,
        responses={200: UserSerializer}
    ),
    partial_update=extend_schema(
        summary="Atualizar parcialmente usuário",
        description="Atualiza campos específicos de um usuário",
        tags=["Usuários"],
        request=UserUpdateSerializer,
        responses={200: UserSerializer}
    ),
    destroy=extend_schema(
        summary="Deletar usuário",
        description="Remove um usuário do sistema (apenas admin/manager)",
        tags=["Usuários"]
    ),
)
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de usuários
    - Lista/cria usuários (admin/manager only)
    - Atualiza perfil próprio (qualquer usuário autenticado)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        """Define permissões por ação"""
        if self.action in ['create', 'list', 'destroy']:
            # Apenas admin/manager pode criar, listar todos ou deletar
            permission_classes = [IsAdminOrManager]
        elif self.action in ['update', 'partial_update', 'retrieve']:
            # Usuário pode atualizar/ver apenas seu próprio perfil
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """Retorna serializer apropriado por ação"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        """Filtrar queryset por permissão"""
        user = self.request.user
        # Django superuser ou roles privilegiados vêem todos
        from .permissions import is_admin_or_manager
        if is_admin_or_manager(user):
            return User.objects.all()
        # Usuário comum vê apenas ele mesmo
        return User.objects.filter(id=user.id)

    def destroy(self, request, *args, **kwargs):
        """Desativa o usuário ao invés de deletar para preservar integridade referencial"""
        user = self.get_object()
        if user.id == request.user.id:
            return Response(
                {'detail': 'Você não pode remover sua própria conta.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.is_active = False
        user.save(update_fields=['is_active'])
        return Response(
            {'detail': 'Usuário desativado com sucesso.'},
            status=status.HTTP_200_OK
        )

    @extend_schema(
        summary="Meu perfil",
        description="Retorna ou atualiza dados do usuário autenticado",
        tags=["Usuários"],
        request=UserUpdateSerializer,
        responses={200: UserSerializer}
    )
    @action(detail=False, methods=['get', 'put', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Retorna ou atualiza dados do usuário logado"""
        if request.method == 'GET':
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        # PUT / PATCH
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=(request.method == 'PATCH'),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)

    @extend_schema(
        summary="Trocar senha",
        description="Altera a senha do usuário autenticado",
        tags=["Usuários"],
        request=ChangePasswordSerializer,
        responses={200: OpenApiResponse(description="Senha alterada com sucesso")}
    )
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        """Trocar senha do usuário logado"""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Senha alterada com sucesso.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Desativar usuário",
        description="Desativa um usuário (apenas admin/manager)",
        tags=["Usuários"],
        responses={200: OpenApiResponse(description="Usuário desativado com sucesso")}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def deactivate(self, request, pk=None):
        """Desativar usuário (admin/manager only)"""
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'detail': 'Usuário desativado com sucesso.'}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Ativar usuário",
        description="Ativa um usuário desativado (apenas admin/manager)",
        tags=["Usuários"],
        responses={200: OpenApiResponse(description="Usuário ativado com sucesso")}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def activate(self, request, pk=None):
        """Ativar usuário (admin/manager only)"""
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'detail': 'Usuário ativado com sucesso.'}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Minhas permissões",
        description="Retorna as permissões do usuário autenticado baseado na sua role",
        tags=["Usuários"],
        responses={200: OpenApiResponse(description="Permissões do usuário")}
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_permissions(self, request):
        """Retorna permissões do usuário logado"""
        user = request.user
        role_info = ROLE_DESCRIPTIONS.get(user.role, {})
        return Response({
            'role': user.role,
            'role_name': role_info.get('name', user.role),
            'role_description': role_info.get('description', ''),
            'role_color': role_info.get('color', '#6b7280'),
            'permissions': get_user_permissions(user),
        })

    @extend_schema(
        summary="Listar roles",
        description="Retorna todas as roles disponíveis no sistema",
        tags=["Usuários"],
        responses={200: OpenApiResponse(description="Lista de roles")}
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def roles(self, request):
        """Retorna todas as roles disponíveis"""
        return Response(get_all_roles())

    @extend_schema(
        summary="Matriz de permissões",
        description="Retorna a matriz completa de permissões por role",
        tags=["Usuários"],
        responses={200: OpenApiResponse(description="Matriz de permissões")}
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAdminOrManager])
    def permissions_matrix(self, request):
        """Retorna matriz de permissões (admin/manager only)"""
        return Response(get_permissions_matrix())


class AuthViewSet(viewsets.ViewSet):
    """
    ViewSet para autenticação (registro e login)
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Registrar novo usuário",
        description="Cria uma nova conta de usuário (inativa, requer aprovação do administrador)",
        tags=["Autenticação"],
        request=RegisterSerializer,
        responses={201: OpenApiResponse(description="Conta criada, aguardando aprovação")},
        examples=[
            OpenApiExample(
                name="Exemplo de registro",
                value={
                    "username": "maelson.lima",
                    "email": "maelson.lima@verus.ai",
                    "password": "qwe123",
                    "password_confirm": "qwe123",
                    "first_name": "Maelson",
                    "last_name": "Lima"
                },
                request_only=True
            )
        ]
    )
    @action(detail=False, methods=['post'], throttle_classes=[AnonRateThrottle])
    def register(self, request):
        """Registro público de novo usuário (requer aprovação do admin)"""
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_active = False  # Requer aprovação do administrador
            user.save(update_fields=['is_active'])
            return Response({
                'message': 'Conta criada com sucesso. Aguarde aprovação do administrador.',
                'user': UserSerializer(user).data,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Login",
        description="Autentica usuário e retorna tokens JWT (access e refresh)",
        tags=["Autenticação"],
        request=LoginSerializer,
        responses={200: UserSerializer},
        examples=[
            OpenApiExample(
                name="Exemplo de login",
                value={
                    "username": "maelson",
                    "password": "qwe123"
                },
                request_only=True
            )
        ]
    )
    @action(detail=False, methods=['post'], throttle_classes=[LoginRateThrottle])
    def login(self, request):
        """Login e geração de JWT tokens"""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            refresh = RefreshToken.for_user(user)

            # Obter módulos disponíveis para o usuário
            from apps.core.models import SystemModule
            available_modules = SystemModule.get_user_modules(user)

            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'available_modules': available_modules,
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Logout",
        description="Invalida o refresh token (blacklist)",
        tags=["Autenticação"],
        request={
            "type": "object",
            "properties": {
                "refresh": {"type": "string", "description": "Refresh token JWT"}
            },
            "required": ["refresh"]
        },
        responses={200: OpenApiResponse(description="Logout realizado com sucesso")}
    )
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        """Logout (blacklist do refresh token)"""
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'detail': 'Logout realizado com sucesso.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': 'Token inválido.'}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        summary="Obter configurações de marca",
        description="Retorna as configurações de identidade visual do sistema",
        tags=["Configurações"]
    ),
    retrieve=extend_schema(
        summary="Obter configurações de marca por ID",
        description="Retorna as configurações de identidade visual (sempre retorna a mesma instância singleton)",
        tags=["Configurações"]
    ),
    update=extend_schema(
        summary="Atualizar configurações de marca",
        description="Atualiza as configurações de identidade visual do sistema (apenas admin/manager)",
        tags=["Configurações"],
        request=BrandSettingsSerializer,
        responses={200: BrandSettingsSerializer}
    ),
    partial_update=extend_schema(
        summary="Atualizar parcialmente configurações de marca",
        description="Atualiza campos específicos das configurações de marca (apenas admin/manager)",
        tags=["Configurações"],
        request=BrandSettingsSerializer,
        responses={200: BrandSettingsSerializer}
    ),
)
class BrandSettingsViewSet(viewsets.ModelViewSet):
    """
    ViewSet para configurações de marca do sistema (Singleton)

    - GET: Público (AllowAny) - necessário para tela de login
    - PUT/PATCH: Apenas admin/manager pode alterar
    - DELETE: Bloqueado (não pode deletar configurações)
    """
    queryset = BrandSettings.objects.select_related('updated_by').all()
    serializer_class = BrandSettingsSerializer
    http_method_names = ['get', 'put', 'patch', 'head', 'options']  # Bloqueia DELETE e POST

    def get_permissions(self):
        """Define permissões por ação"""
        if self.action in ['update', 'partial_update']:
            # Apenas admin/manager pode atualizar
            permission_classes = [IsAdminOrManager]
        else:
            # Qualquer um pode ver (inclusive não autenticados) - necessário para tela de login
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        """Retorna a instância singleton (sempre pk=1)"""
        instance = BrandSettings.load()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Retorna a instância singleton (sempre pk=1)"""
        instance = BrandSettings.load()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(
        summary="Resetar configurações de marca",
        description="Restaura as configurações de marca para os valores padrão (apenas admin/manager)",
        tags=["Configurações"],
        responses={200: BrandSettingsSerializer}
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAdminOrManager])
    def reset(self, request):
        """Reseta configurações para valores padrão"""
        instance = BrandSettings.load()
        instance.system_name = 'Verus.AI'
        instance.system_tagline = ''
        instance.logo = None
        instance.logo_dark = None
        instance.favicon = None
        instance.primary_color = '#7030A0'
        instance.secondary_color = '#5B2EE0'
        instance.accent_color = '#8B5CF6'
        instance.updated_by = request.user
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        summary="Listar notificações",
        description="Lista as notificações do usuário autenticado (não lidas primeiro)",
        tags=["Notificações"],
    ),
)
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para notificações do usuário autenticado.

    - GET /notifications/             — listar (não lidas primeiro)
    - POST /notifications/{id}/read/  — marcar como lida
    - POST /notifications/read-all/   — marcar todas como lidas
    - GET /notifications/unread-count/ — contagem de não lidas
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by(
            'is_read', '-created_at'
        )

    @extend_schema(
        summary="Marcar notificação como lida",
        description="Marca uma notificação específica como lida",
        tags=["Notificações"],
        responses={200: NotificationSerializer},
    )
    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        """Marca uma notificação como lida"""
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @extend_schema(
        summary="Marcar todas como lidas",
        description="Marca todas as notificações do usuário como lidas",
        tags=["Notificações"],
        responses={200: OpenApiResponse(description="Todas marcadas como lidas")},
    )
    @action(detail=False, methods=['post'], url_path='read-all')
    def read_all(self, request):
        """Marca todas as notificações como lidas"""
        count = Notification.objects.filter(
            user=request.user, is_read=False
        ).update(is_read=True)
        return Response({'detail': f'{count} notificações marcadas como lidas.'})

    @extend_schema(
        summary="Contagem de não lidas",
        description="Retorna a quantidade de notificações não lidas",
        tags=["Notificações"],
        responses={200: OpenApiResponse(description="Contagem de não lidas")},
    )
    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """Retorna contagem de notificações não lidas"""
        count = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
        return Response({'count': count})

    @extend_schema(
        summary="Enviar notificação via WhatsApp",
        description="Gera mensagem com IA e retorna link wa.me para a notificação",
        tags=["Notificações"],
        responses={200: OpenApiResponse(description="Link WhatsApp gerado")},
    )
    @action(detail=True, methods=['post'], url_path='send-whatsapp')
    def send_whatsapp(self, request, pk=None):
        """Gera link WhatsApp para uma notificação específica"""
        notification = self.get_object()
        from apps.copilot.services.communication_service import CommunicationService
        svc = CommunicationService()
        link = svc.send_whatsapp(request.user, notification)
        if not link:
            return Response(
                {'detail': 'Canal WhatsApp não configurado ou sem número.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({'whatsapp_link': link})

    @extend_schema(
        summary="Enviar notificação via E-mail",
        description="Gera e-mail com IA e envia para o usuário",
        tags=["Notificações"],
        responses={200: OpenApiResponse(description="E-mail enviado")},
    )
    @action(detail=True, methods=['post'], url_path='send-email')
    def send_email(self, request, pk=None):
        """Envia e-mail para uma notificação específica"""
        notification = self.get_object()
        from apps.copilot.services.communication_service import CommunicationService
        svc = CommunicationService()
        result = svc.send_email(request.user, notification)
        if result is None:
            return Response(
                {'detail': 'Nenhum e-mail configurado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({'status': result})


@extend_schema_view(
    list=extend_schema(
        summary="Listar canais de notificação",
        description="Lista os canais de notificação do usuário autenticado",
        tags=["Canais de Notificação"],
    ),
    create=extend_schema(
        summary="Criar canal de notificação",
        description="Configura um novo canal de notificação (WhatsApp, E-mail, App)",
        tags=["Canais de Notificação"],
        request=NotificationChannelSerializer,
        responses={201: NotificationChannelSerializer},
    ),
    update=extend_schema(
        summary="Atualizar canal de notificação",
        description="Atualiza configuração de um canal",
        tags=["Canais de Notificação"],
        request=NotificationChannelSerializer,
        responses={200: NotificationChannelSerializer},
    ),
    partial_update=extend_schema(
        summary="Atualizar parcialmente canal de notificação",
        description="Atualiza campos específicos de um canal",
        tags=["Canais de Notificação"],
    ),
    destroy=extend_schema(
        summary="Remover canal de notificação",
        description="Remove um canal de notificação",
        tags=["Canais de Notificação"],
    ),
)
class NotificationChannelViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD para canais de notificação do usuário.

    - GET    /notification-channels/              — listar
    - POST   /notification-channels/              — criar
    - PUT    /notification-channels/{id}/         — atualizar
    - DELETE /notification-channels/{id}/         — remover
    - POST   /notification-channels/verify-whatsapp/ — verificar WhatsApp
    """
    serializer_class = NotificationChannelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NotificationChannel.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        summary="Verificar WhatsApp",
        description="Gera link de verificação WhatsApp para o número configurado",
        tags=["Canais de Notificação"],
        responses={200: OpenApiResponse(description="Link de verificação gerado")},
    )
    @action(detail=False, methods=['post'], url_path='verify-whatsapp')
    def verify_whatsapp(self, request):
        """Gera link de verificação para o WhatsApp do usuário"""
        channel = NotificationChannel.objects.filter(
            user=request.user, channel='whatsapp',
        ).first()
        if not channel or not channel.whatsapp_number:
            return Response(
                {'detail': 'Configure um número WhatsApp primeiro.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.copilot.services.communication_service import CommunicationService
        svc = CommunicationService()
        verification_msg = (
            f'Verus.AI - Verificacao de WhatsApp\n\n'
            f'Ola {request.user.get_full_name() or request.user.username}!\n'
            f'Seu WhatsApp foi verificado com sucesso para receber notificacoes do Verus.AI.'
        )
        link = svc.generate_whatsapp_link(channel.whatsapp_number, verification_msg)

        # Mark as verified
        channel.whatsapp_verified = True
        channel.save(update_fields=['whatsapp_verified'])

        return Response({
            'whatsapp_link': link,
            'verified': True,
        })


@extend_schema_view(
    list=extend_schema(
        summary="Listar lembretes",
        description="Lista os lembretes do usuário autenticado (filtráveis por status e frequência)",
        tags=["Lembretes"],
    ),
    create=extend_schema(
        summary="Criar lembrete",
        description="Cria um novo lembrete para o usuário autenticado",
        tags=["Lembretes"],
        request=UserReminderSerializer,
        responses={201: UserReminderSerializer},
    ),
    retrieve=extend_schema(
        summary="Buscar lembrete",
        description="Retorna um lembrete específico do usuário",
        tags=["Lembretes"],
    ),
    update=extend_schema(
        summary="Atualizar lembrete",
        description="Atualiza todos os campos de um lembrete",
        tags=["Lembretes"],
        request=UserReminderSerializer,
        responses={200: UserReminderSerializer},
    ),
    partial_update=extend_schema(
        summary="Atualizar parcialmente lembrete",
        description="Atualiza campos específicos de um lembrete",
        tags=["Lembretes"],
    ),
    destroy=extend_schema(
        summary="Excluir lembrete",
        description="Remove um lembrete do usuário",
        tags=["Lembretes"],
    ),
)
class UserReminderViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD completo para lembretes do usuário.

    - GET    /reminders/              — listar (filtros: status, frequency)
    - POST   /reminders/              — criar
    - GET    /reminders/{id}/         — detalhe
    - PUT    /reminders/{id}/         — atualizar
    - DELETE /reminders/{id}/         — excluir
    - POST   /reminders/{id}/pause/   — pausar
    - POST   /reminders/{id}/resume/  — retomar
    - GET    /reminders/upcoming/     — próximos 7 dias
    """
    serializer_class = UserReminderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'frequency', 'priority']

    def get_queryset(self):
        return UserReminder.objects.filter(
            user=self.request.user,
        ).select_related('related_case')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        summary="Pausar lembrete",
        description="Pausa um lembrete recorrente ativo",
        tags=["Lembretes"],
        responses={200: UserReminderSerializer},
    )
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pausa um lembrete ativo"""
        reminder = self.get_object()
        if reminder.status != 'active':
            return Response(
                {'detail': 'Apenas lembretes ativos podem ser pausados.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reminder.status = 'paused'
        reminder.save(update_fields=['status', 'updated_at'])
        return Response(UserReminderSerializer(reminder).data)

    @extend_schema(
        summary="Retomar lembrete",
        description="Retoma um lembrete pausado",
        tags=["Lembretes"],
        responses={200: UserReminderSerializer},
    )
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Retoma um lembrete pausado"""
        reminder = self.get_object()
        if reminder.status != 'paused':
            return Response(
                {'detail': 'Apenas lembretes pausados podem ser retomados.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reminder.status = 'active'
        reminder.save(update_fields=['status', 'updated_at'])
        return Response(UserReminderSerializer(reminder).data)

    @extend_schema(
        summary="Lembretes próximos",
        description="Retorna lembretes ativos dos próximos 7 dias (para widget do dashboard)",
        tags=["Lembretes"],
        responses={200: UserReminderSerializer(many=True)},
    )
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Retorna lembretes dos próximos 7 dias"""
        now = timezone.now()
        week_ahead = now + timedelta(days=7)
        reminders = self.get_queryset().filter(
            status='active',
            scheduled_date__gte=now,
            scheduled_date__lte=week_ahead,
        ).order_by('scheduled_date')
        serializer = self.get_serializer(reminders, many=True)
        return Response(serializer.data)

"""
Views para Biblioteca Viva de Argumentos Jurídicos.

Endpoints:
  GET/POST /api/v1/legal-library/arguments/
    - Listar/criar argumentos jurídicos

  GET/PUT/PATCH/DELETE /api/v1/legal-library/arguments/{id}/
    - Detalhes/edição/remoção de argumento

  POST /api/v1/legal-library/arguments/{id}/use/
    - Registrar uso de argumento

  POST /api/v1/legal-library/arguments/{id}/success/
    - Registrar sucesso de argumento

  GET/POST /api/v1/legal-library/collections/
    - Listar/criar coleções

  GET /api/v1/legal-library/arguments/suggest/
    - Sugerir argumentos por contexto
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse

from apps.accounts.permissions import is_admin_or_manager
from .models import LegalArgument, ArgumentCollection, ArgumentUsage
from .serializers import (
    LegalArgumentSerializer,
    LegalArgumentListSerializer,
    LegalArgumentCreateSerializer,
    LegalArgumentUpdateSerializer,
    ArgumentCollectionSerializer,
    ArgumentUsageCreateSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="Listar argumentos jurídicos",
        description="Retorna lista de argumentos jurídicos com filtros",
        tags=["LegalLibrary"],
    ),
    retrieve=extend_schema(
        summary="Buscar argumento por ID",
        description="Retorna detalhes completos de um argumento",
        tags=["LegalLibrary"],
    ),
    create=extend_schema(
        summary="Criar argumento jurídico",
        description="Cria novo argumento na biblioteca",
        tags=["LegalLibrary"],
        request=LegalArgumentCreateSerializer,
    ),
    update=extend_schema(
        summary="Atualizar argumento",
        description="Atualiza argumento existente",
        tags=["LegalLibrary"],
        request=LegalArgumentUpdateSerializer,
    ),
    destroy=extend_schema(
        summary="Remover argumento",
        description="Remove argumento da biblioteca",
        tags=["LegalLibrary"],
    ),
)
class LegalArgumentViewSet(viewsets.ModelViewSet):
    """ViewSet para Biblioteca de Argumentos Jurídicos"""
    queryset = LegalArgument.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return LegalArgumentListSerializer
        elif self.action == 'create':
            return LegalArgumentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return LegalArgumentUpdateSerializer
        return LegalArgumentSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = LegalArgument.objects.select_related('created_by')

        # Filtro por status
        if not is_admin_or_manager(user):
            # Usuários normais só vêem aprovados e públicos
            queryset = queryset.filter(
                Q(status='approved') | Q(created_by=user)
            )

        # Filtros por query params
        specialty = self.request.query_params.get('specialty')
        if specialty:
            queryset = queryset.filter(specialty=specialty)

        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        tribunal = self.request.query_params.get('tribunal')
        if tribunal:
            queryset = queryset.filter(tribunal__icontains=tribunal)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Busca por texto
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search) |
                Q(summary__icontains=search)
            )

        # Ordenação
        sort = self.request.query_params.get('sort', '-effectiveness_score')
        queryset = queryset.order_by(sort)

        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @extend_schema(
        summary="Registrar uso de argumento",
        description="Registra que um argumento foi usado em um documento/caso",
        tags=["LegalLibrary"],
        request=ArgumentUsageCreateSerializer,
        responses={200: OpenApiResponse(description="Uso registrado com sucesso")},
    )
    @action(detail=True, methods=['post'])
    def use(self, request, pk=None):
        """Registrar uso de argumento"""
        argument = self.get_object()

        serializer = ArgumentUsageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        usage = serializer.save(argument=argument)

        # Incrementar contador de uso
        argument.increment_usage()

        return Response({
            'detail': 'Uso registrado com sucesso',
            'usage_id': str(usage.id),
        })

    @extend_schema(
        summary="Registrar sucesso de argumento",
        description="Marca um uso como bem-sucedido e atualiza eficácia",
        tags=["LegalLibrary"],
        responses={200: OpenApiResponse(description="Sucesso registrado")},
    )
    @action(detail=True, methods=['post'])
    def success(self, request, pk=None):
        """Registrar sucesso"""
        argument = self.get_object()
        usage_id = request.data.get('usage_id')

        if usage_id:
            try:
                usage = ArgumentUsage.objects.get(id=usage_id)
                usage.outcome = 'favorable'
                from django.utils import timezone
                usage.outcome_recorded_at = timezone.now()
                usage.save()
            except ArgumentUsage.DoesNotExist:
                pass

        # Atualizar eficácia
        argument.record_success()

        return Response({
            'detail': 'Sucesso registrado',
            'effectiveness_score': argument.effectiveness_score,
        })

    @extend_schema(
        summary="Estatísticas de argumentos",
        description="Retorna estatísticas da biblioteca de argumentos",
        tags=["LegalLibrary"],
        responses={200: OpenApiResponse(description="Estatísticas")},
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retorna estatísticas da biblioteca"""
        queryset = self.get_queryset()

        # Contagens
        total = queryset.count()
        approved = queryset.filter(status='approved').count()
        draft = queryset.filter(status='draft').count()

        # Por especialidade
        by_specialty = queryset.values('specialty').annotate(
            count=Count('id'),
            avg_effectiveness=Avg('effectiveness_score')
        )

        # Mais usados
        top_used = queryset.order_by('-usage_count')[:5]
        top_used_data = LegalArgumentListSerializer(top_used, many=True).data

        # Mais eficazes
        top_effective = queryset.filter(
            usage_count__gte=1
        ).order_by('-effectiveness_score')[:5]
        top_effective_data = LegalArgumentListSerializer(top_effective, many=True).data

        return Response({
            'total': total,
            'approved': approved,
            'draft': draft,
            'by_specialty': list(by_specialty),
            'top_used': top_used_data,
            'top_effective': top_effective_data,
        })

    @extend_schema(
        summary="Sugerir argumentos",
        description="Sugere argumentos baseados no contexto",
        tags=["LegalLibrary"],
        parameters=[
            OpenApiParameter(name='query', description='Texto da busca'),
            OpenApiParameter(name='specialty', description='Especialidade'),
            OpenApiParameter(name='tribunal', description='Tribunal'),
        ],
        responses={200: OpenApiResponse(description="Argumentos sugeridos")},
    )
    @action(detail=False, methods=['get'])
    def suggest(self, request):
        """Sugere argumentos baseados no contexto"""
        query = request.query_params.get('query', '')
        specialty = request.query_params.get('specialty')
        tribunal = request.query_params.get('tribunal')
        limit = int(request.query_params.get('limit', 10))

        queryset = LegalArgument.objects.filter(status='approved')

        # Filtros
        if specialty:
            queryset = queryset.filter(specialty=specialty)

        if tribunal:
            queryset = queryset.filter(tribunal__icontains=tribunal)

        # Busca por similaridade (simples)
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(summary__icontains=query)
            )

        # Ordenar por eficácia e uso
        queryset = queryset.order_by('-effectiveness_score', '-usage_count')[:limit]

        serializer = LegalArgumentListSerializer(queryset, many=True)
        return Response({
            'suggestions': serializer.data,
            'count': len(serializer.data),
        })


class ArgumentCollectionViewSet(viewsets.ModelViewSet):
    """ViewSet para Coleções de Argumentos"""
    queryset = ArgumentCollection.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ArgumentCollectionSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = ArgumentCollection.objects.filter(
            Q(is_public=True) | Q(created_by=user)
        )

        # Busca
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def import_argument(request):
    """
    POST /api/v1/legal-library/import/

    Importa argumento de um documento existente.

    Request:
    {
        "document_id": "uuid",
        "section_id": "uuid",  // opcional
        "title": "Título do argumento",
        "category": "merito",
        "specialty": "CIV",
    }
    """
    from apps.documents.models import Document

    document_id = request.data.get('document_id')
    section_id = request.data.get('section_id')
    title = request.data.get('title')
    category = request.data.get('category', 'merito')
    specialty = request.data.get('specialty', 'CIV')

    if not document_id or not title:
        return Response(
            {'detail': 'document_id e title são obrigatórios'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        document = Document.objects.get(id=document_id)

        # Extrair conteúdo
        content = ''
        if section_id and document.data:
            sections = document.data.get('sections', [])
            for section in sections:
                if section.get('id') == section_id:
                    content = section.get('content', '')
                    break

        if not content:
            content = document.generated_content or document.data.get('content', '')

        # Criar argumento
        argument = LegalArgument.objects.create(
            title=title,
            content=content,
            category=category,
            specialty=specialty,
            created_by=request.user,
            status='draft',
        )

        return Response(LegalArgumentSerializer(argument).data, status=status.HTTP_201_CREATED)

    except Document.DoesNotExist:
        return Response(
            {'detail': 'Documento não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'detail': f'Erro ao importar: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

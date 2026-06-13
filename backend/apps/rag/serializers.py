"""
Serializers para RAG
"""
from rest_framework import serializers
from apps.core.constants import LLM_PROVIDER_CHOICES
from .models import RAGQuery, RAGContext


class RAGQueryListSerializer(serializers.ModelSerializer):
    """Serializer para listar queries RAG"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    etp_title = serializers.CharField(source='etp.title', read_only=True, allow_null=True)

    class Meta:
        model = RAGQuery
        fields = [
            'id', 'user_name', 'etp_title', 'query_text',
            'chunk_count', 'llm_provider', 'llm_model', 'created_at'
        ]


class RAGQueryDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalhes da query RAG"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    etp_title = serializers.CharField(source='etp.title', read_only=True, allow_null=True)

    class Meta:
        model = RAGQuery
        fields = '__all__'
        read_only_fields = [
            'id', 'user', 'query_embedding', 'retrieved_chunks',
            'chunk_count', 'search_time_ms', 'llm_time_ms',
            'total_tokens', 'created_at'
        ]


class RAGQueryExecuteSerializer(serializers.Serializer):
    """Serializer para executar query RAG"""
    query_text = serializers.CharField(
        help_text='Texto da consulta'
    )
    etp_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text='ID do ETP relacionado (opcional)'
    )
    top_k = serializers.IntegerField(
        default=5,
        min_value=1,
        max_value=20,
        help_text='Quantidade de chunks a recuperar'
    )
    similarity_threshold = serializers.FloatField(
        default=0.7,
        min_value=0.0,
        max_value=1.0,
        help_text='Threshold mínimo de similaridade'
    )
    filter_categories = serializers.ListField(
        child=serializers.CharField(),
        default=list,
        required=False,
        help_text='Categorias para filtrar documentos'
    )
    filter_tags = serializers.ListField(
        child=serializers.CharField(),
        default=list,
        required=False,
        help_text='Tags para filtrar documentos'
    )
    filter_processo = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text='Numero do processo para filtrar (ex: 2024/001)'
    )
    use_context_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text='ID do contexto RAG a usar (opcional)'
    )
    llm_provider = serializers.ChoiceField(
        choices=LLM_PROVIDER_CHOICES,
        default='openai',
        help_text='Provedor LLM para gerar resposta'
    )
    model_name = serializers.CharField(
        default='gpt-4o-mini',
        help_text='Nome do modelo LLM'
    )


class RAGContextListSerializer(serializers.ModelSerializer):
    """Serializer para listar contextos RAG"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    etp_title = serializers.CharField(source='etp.title', read_only=True, allow_null=True)
    document_count = serializers.IntegerField(source='documents.count', read_only=True)

    class Meta:
        model = RAGContext
        fields = [
            'id', 'name', 'description', 'user_name', 'etp_title',
            'document_count', 'default_top_k', 'default_threshold',
            'created_at', 'updated_at'
        ]


class RAGContextDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalhes do contexto RAG"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    etp_title = serializers.CharField(source='etp.title', read_only=True, allow_null=True)
    document_ids = serializers.PrimaryKeyRelatedField(
        source='documents',
        many=True,
        read_only=True
    )

    class Meta:
        model = RAGContext
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class RAGContextCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar contexto RAG"""
    document_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        help_text='IDs dos documentos a incluir'
    )

    class Meta:
        model = RAGContext
        fields = [
            'name', 'description', 'etp', 'document_ids',
            'default_top_k', 'default_threshold'
        ]

    def create(self, validated_data):
        document_ids = validated_data.pop('document_ids', [])
        validated_data['user'] = self.context['request'].user

        context = RAGContext.objects.create(**validated_data)

        if document_ids:
            from apps.kb.models import Document
            documents = Document.objects.filter(id__in=document_ids)
            context.documents.set(documents)

        return context


class RAGContextUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualizar contexto RAG"""
    document_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        help_text='IDs dos documentos a incluir'
    )

    class Meta:
        model = RAGContext
        fields = [
            'name', 'description', 'document_ids',
            'default_top_k', 'default_threshold'
        ]

    def update(self, instance, validated_data):
        document_ids = validated_data.pop('document_ids', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if document_ids is not None:
            from apps.kb.models import Document
            documents = Document.objects.filter(id__in=document_ids)
            instance.documents.set(documents)

        return instance

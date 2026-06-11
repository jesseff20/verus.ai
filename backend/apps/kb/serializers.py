"""
Serializers para Knowledge Base
"""
from rest_framework import serializers
from .models import Document, DocumentChunk


class DocumentChunkSerializer(serializers.ModelSerializer):
    """Serializer para chunks de documento"""
    content_preview = serializers.CharField(read_only=True)
    has_embedding = serializers.BooleanField(read_only=True)

    class Meta:
        model = DocumentChunk
        fields = [
            'id', 'chunk_index', 'content', 'content_preview',
            'has_embedding', 'metadata', 'token_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DocumentListSerializer(serializers.ModelSerializer):
    """Serializer para listar documentos (resumido)"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    file_size_mb = serializers.FloatField(read_only=True)
    chunk_count = serializers.IntegerField(read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'title', 'description', 'category', 'file_type',
            'file_size', 'file_size_mb', 'file_url', 'status', 'chunk_count',
            'tags', 'is_public', 'is_active', 'uploaded_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'file_size', 'created_at', 'updated_at']

    def get_file_url(self, obj):
        """Retorna URL do arquivo"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class DocumentDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalhes do documento (completo)"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    uploaded_by_id = serializers.IntegerField(source='uploaded_by.id', read_only=True)
    file_size_mb = serializers.FloatField(read_only=True)
    chunk_count = serializers.IntegerField(read_only=True)
    chunks = DocumentChunkSerializer(many=True, read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'title', 'description', 'category', 'file', 'file_url',
            'file_type', 'file_size', 'file_size_mb', 'extracted_text',
            'status', 'processing_error', 'processed_at', 'metadata',
            'tags', 'is_public', 'is_active', 'chunk_count', 'chunks',
            'uploaded_by_id', 'uploaded_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'file_type', 'file_size', 'file_size_mb', 'extracted_text',
            'status', 'processing_error', 'processed_at', 'created_at',
            'updated_at', 'uploaded_by_id', 'uploaded_by_name'
        ]

    def get_file_url(self, obj):
        """Retorna URL do arquivo"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer para upload de documento"""
    file = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Document
        fields = ['title', 'description', 'category', 'file', 'tags', 'is_public']

    def create(self, validated_data):
        validated_data['uploaded_by'] = self.context['request'].user
        validated_data['status'] = 'pending'
        return super().create(validated_data)


class DocumentUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualizar documento"""

    class Meta:
        model = Document
        fields = ['title', 'description', 'category', 'tags', 'is_public', 'is_active']


class DocumentSearchSerializer(serializers.Serializer):
    """Serializer para busca semântica em documentos"""
    query = serializers.CharField(
        max_length=1000,
        help_text="Texto da busca semântica"
    )
    limit = serializers.IntegerField(
        default=5,
        min_value=1,
        max_value=20,
        help_text="Quantidade de resultados (1-20)"
    )
    category = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Filtrar por categoria"
    )


class SearchResultSerializer(serializers.Serializer):
    """Serializer para resultado de busca"""
    chunk_id = serializers.UUIDField()
    document_id = serializers.UUIDField()
    document_title = serializers.CharField()
    content = serializers.CharField()
    similarity_score = serializers.FloatField()
    metadata = serializers.DictField()

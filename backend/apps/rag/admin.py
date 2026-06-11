"""
Admin para RAG
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import RAGQuery, RAGContext


@admin.register(RAGQuery)
class RAGQueryAdmin(admin.ModelAdmin):
    """Admin para RAGQuery"""
    list_display = ['query_display', 'user', 'etp', 'chunk_count', 'llm_provider', 'created_at']
    list_filter = ['llm_provider', 'created_at']
    search_fields = ['query_text', 'user__username', 'llm_response']
    readonly_fields = [
        'id', 'query_embedding', 'retrieved_chunks',
        'search_time_ms', 'llm_time_ms', 'total_tokens', 'created_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        ('Consulta', {
            'fields': ('id', 'user', 'etp', 'query_text', 'query_embedding')
        }),
        ('Parâmetros de Busca', {
            'fields': ('top_k', 'similarity_threshold', 'filter_categories', 'filter_tags')
        }),
        ('Resultados', {
            'fields': ('retrieved_chunks', 'chunk_count'),
            'classes': ('collapse',)
        }),
        ('LLM Response', {
            'fields': ('llm_response', 'llm_provider', 'llm_model')
        }),
        ('Métricas', {
            'fields': ('search_time_ms', 'llm_time_ms', 'total_tokens')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )

    def query_display(self, obj):
        return obj.query_text[:80] + '...' if len(obj.query_text) > 80 else obj.query_text
    query_display.short_description = 'Consulta'


@admin.register(RAGContext)
class RAGContextAdmin(admin.ModelAdmin):
    """Admin para RAGContext"""
    list_display = ['name', 'user', 'etp', 'document_count', 'default_top_k', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name', 'description', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    filter_horizontal = ['documents']
    ordering = ['-created_at']

    fieldsets = (
        ('Informações', {
            'fields': ('id', 'name', 'description', 'user', 'etp')
        }),
        ('Documentos', {
            'fields': ('documents',)
        }),
        ('Configurações', {
            'fields': ('default_top_k', 'default_threshold')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def document_count(self, obj):
        count = obj.documents.count()
        color = '#198754' if count > 0 else '#6c757d'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            count
        )
    document_count.short_description = 'Documentos'

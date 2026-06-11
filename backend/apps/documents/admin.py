"""
Admin para Documents
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin para ETP"""
    list_display = ['title_display', 'user', 'form_template',
                    'status_display', 'version', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at', 'form_template']
    search_fields = ['title', 'description', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at', 'completed_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Informações', {
            'fields': ('id', 'title', 'description', 'user')
        }),
        ('Templates', {
            'fields': ('form_template', 'document_template')
        }),
        ('Dados', {
            'fields': ('data',),
            'classes': ('collapse',)
        }),
        ('Conteúdo Gerado', {
            'fields': ('generated_content', 'generated_html', 'exported_file'),
            'classes': ('collapse',)
        }),
        ('Versionamento', {
            'fields': ('version', 'parent', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
    )

    def title_display(self, obj):
        if obj.title:
            return obj.title
        return format_html('<span style="color: #999;">Sem título</span>')
    title_display.short_description = 'Título'

    def status_display(self, obj):
        colors = {
            'draft': '#6c757d',
            'in_review': '#0dcaf0',
            'completed': '#198754',
            'archived': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'

"""
Admin para templates de documentos
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import DocumentTemplate


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    """Admin para DocumentTemplate"""
    list_display = [
        'name', 'blueprint', 'template_type', 'form_template',
        'version', 'is_default_display', 'is_active', 'placeholder_count_display',
        'created_by', 'created_at'
    ]
    list_filter = ['blueprint', 'template_type', 'is_active', 'is_default', 'form_template', 'created_at']
    search_fields = ['name', 'description', 'form_template__name']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'placeholder_count',
        'has_file', 'placeholders_preview', 'field_mapping_preview'
    ]
    autocomplete_fields = ['form_template', 'blueprint']
    ordering = ['-created_at']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'name', 'description', 'blueprint', 'template_type')
        }),
        ('Formulário Associado', {
            'fields': ('form_template',),
            'description': 'Selecione o formulário que fornece dados para este template'
        }),
        ('Conteúdo do Template', {
            'fields': ('content', 'file', 'custom_css'),
            'description': 'Forneça APENAS conteúdo OU arquivo, não ambos'
        }),
        ('Variáveis e Placeholders', {
            'fields': ('available_variables', 'placeholders_preview', 'field_mapping_preview')
        }),
        ('Configurações', {
            'fields': ('version', 'is_active', 'is_default')
        }),
        ('Auditoria', {
            'fields': ('created_by', 'created_at', 'updated_at', 'placeholder_count', 'has_file'),
            'classes': ('collapse',)
        }),
    )

    def is_default_display(self, obj):
        """Exibe badge para template padrão"""
        if obj.is_default:
            return format_html(
                '<span style="background-color: #ffc107; color: #000; padding: 3px 8px; border-radius: 3px; font-weight: bold;">PADRÃO</span>'
            )
        return '-'
    is_default_display.short_description = 'Padrão'

    def placeholder_count_display(self, obj):
        """Exibe quantidade de placeholders"""
        count = obj.placeholder_count
        if count > 0:
            return format_html(
                '<span style="background-color: #17a2b8; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
                count
            )
        return '-'
    placeholder_count_display.short_description = 'Placeholders'

    def placeholders_preview(self, obj):
        """Mostra preview dos placeholders extraídos"""
        placeholders = obj.extract_placeholders()
        if placeholders:
            return format_html(
                '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;"><code>{}</code></div>',
                ', '.join([f'{{{{{p}}}}}' for p in placeholders])
            )
        return 'Nenhum placeholder encontrado'
    placeholders_preview.short_description = 'Placeholders Extraídos'

    def field_mapping_preview(self, obj):
        """Mostra comparação entre placeholders do template e campos do formulário"""
        placeholders = set(obj.extract_placeholders())

        if not obj.form_template:
            return format_html(
                '<div style="background: #fff3cd; padding: 10px; border-radius: 5px; color: #856404;">'
                '⚠️ Nenhum formulário vinculado. Vincule um FormTemplate para ver a comparação.'
                '</div>'
            )

        # Extrair campos do FormTemplate
        form_fields = set()
        if obj.form_template.fields:
            for field in obj.form_template.fields:
                if isinstance(field, dict) and 'id' in field:
                    form_fields.add(field['id'])

        # Calcular diferenças
        matched = placeholders & form_fields  # Interseção
        missing_in_form = placeholders - form_fields  # No template, não no form
        missing_in_template = form_fields - placeholders  # No form, não no template

        html_parts = ['<div style="font-family: monospace; font-size: 13px;">']

        # Campos que batem
        if matched:
            html_parts.append('<div style="margin-bottom: 10px;">')
            html_parts.append('<strong style="color: #28a745;">✅ Campos OK ({}):</strong><br>'.format(len(matched)))
            for field in sorted(matched):
                html_parts.append('<span style="background: #d4edda; padding: 2px 6px; margin: 2px; display: inline-block; border-radius: 3px;">{}</span>'.format(field))
            html_parts.append('</div>')

        # Placeholders sem campo correspondente
        if missing_in_form:
            html_parts.append('<div style="margin-bottom: 10px;">')
            html_parts.append('<strong style="color: #dc3545;">❌ No template, mas NÃO no formulário ({}):</strong><br>'.format(len(missing_in_form)))
            for field in sorted(missing_in_form):
                html_parts.append('<span style="background: #f8d7da; padding: 2px 6px; margin: 2px; display: inline-block; border-radius: 3px;">{}</span>'.format(field))
            html_parts.append('<br><small style="color: #721c24;">Esses placeholders não serão preenchidos!</small>')
            html_parts.append('</div>')

        # Campos do form sem placeholder
        if missing_in_template:
            html_parts.append('<div style="margin-bottom: 10px;">')
            html_parts.append('<strong style="color: #ffc107;">⚠️ No formulário, mas NÃO no template ({}):</strong><br>'.format(len(missing_in_template)))
            for field in sorted(missing_in_template):
                html_parts.append('<span style="background: #fff3cd; padding: 2px 6px; margin: 2px; display: inline-block; border-radius: 3px;">{}</span>'.format(field))
            html_parts.append('<br><small style="color: #856404;">Esses campos estão disponíveis mas não são usados no template.</small>')
            html_parts.append('</div>')

        if not matched and not missing_in_form and not missing_in_template:
            html_parts.append('<div style="color: #6c757d;">Nenhum campo para comparar.</div>')

        html_parts.append('</div>')

        return format_html(''.join(html_parts))
    field_mapping_preview.short_description = '🔍 Comparação: Placeholders vs Campos do Formulário'

    def save_model(self, request, obj, form, change):
        """Define created_by automaticamente"""
        if not change:  # Novo objeto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    actions = ['duplicate_template', 'activate_templates', 'deactivate_templates', 'set_as_default']

    def duplicate_template(self, request, queryset):
        """Duplica templates selecionados"""
        count = 0
        for template in queryset:
            template.duplicate(request.user)
            count += 1
        self.message_user(request, f'{count} template(s) duplicado(s) com sucesso.')
    duplicate_template.short_description = 'Duplicar templates selecionados'

    def activate_templates(self, request, queryset):
        """Ativa templates"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} template(s) ativado(s).')
    activate_templates.short_description = 'Ativar templates'

    def deactivate_templates(self, request, queryset):
        """Desativa templates"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} template(s) desativado(s).')
    deactivate_templates.short_description = 'Desativar templates'

    def set_as_default(self, request, queryset):
        """Define como template padrão"""
        if queryset.count() > 1:
            self.message_user(request, 'Selecione apenas um template para definir como padrão.', level='error')
            return

        template = queryset.first()
        # Remove padrão anterior do mesmo blueprint
        DocumentTemplate.objects.filter(
            blueprint=template.blueprint,
            is_default=True
        ).update(is_default=False)

        # Define novo padrão
        template.is_default = True
        template.save()
        blueprint_name = template.blueprint.name if template.blueprint else 'sem blueprint'
        self.message_user(request, f'Template "{template.name}" definido como padrão para {blueprint_name}.')
    set_as_default.short_description = 'Definir como template padrão'

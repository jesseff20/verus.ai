from django.contrib import admin
from .models import Client, LegalCase, LegalDeadline, CaseTask, CaseDocument, CasePhase, LegalNotification


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'client_type', 'cpf_cnpj', 'email', 'phone', 'city', 'state', 'is_active', 'created_at')
    list_filter = ('client_type', 'is_active', 'state')
    search_fields = ('name', 'cpf_cnpj', 'email', 'company_name')
    readonly_fields = ('id', 'created_at', 'updated_at')


class LegalDeadlineInline(admin.TabularInline):
    model = LegalDeadline
    extra = 0
    fields = ('titulo', 'tipo', 'data_prazo', 'status', 'prioridade', 'responsavel')


class CasePhaseInline(admin.TabularInline):
    model = CasePhase
    extra = 0
    fields = ('order', 'name', 'status', 'estimated_date', 'actual_date')
    readonly_fields = ('order', 'name')
    ordering = ('order',)


class CaseTaskInline(admin.TabularInline):
    model = CaseTask
    extra = 0
    fields = ('titulo', 'status', 'prioridade', 'data_limite', 'responsavel')


class LegalNotificationInline(admin.TabularInline):
    model = LegalNotification
    extra = 0
    fields = ('tipo', 'direcao', 'status', 'meio', 'data_ciencia', 'prazo_vencimento')
    readonly_fields = ('prazo_vencimento',)


@admin.register(LegalCase)
class LegalCaseAdmin(admin.ModelAdmin):
    list_display = (
        'titulo', 'numero_processo', 'especialidade', 'status',
        'cliente_nome', 'advogado_responsavel', 'created_at',
    )
    list_filter = ('status', 'especialidade', 'fase')
    search_fields = ('titulo', 'numero_processo', 'cliente_nome', 'parte_contraria')
    inlines = [CasePhaseInline, LegalDeadlineInline, CaseTaskInline, LegalNotificationInline]
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        ('Identificação', {
            'fields': ('id', 'titulo', 'numero_processo', 'especialidade', 'status', 'fase'),
        }),
        ('Partes', {
            'fields': (
                'cliente_nome', 'cliente_cpf_cnpj',
                'parte_contraria', 'parte_contraria_cpf_cnpj',
            ),
        }),
        ('Localização Processual', {
            'fields': ('tribunal', 'vara_juizo', 'comarca'),
        }),
        ('Financeiro', {
            'fields': ('valor_causa', 'honorarios_combinados'),
        }),
        ('Responsável e Datas', {
            'fields': ('advogado_responsavel', 'data_distribuicao', 'data_encerramento'),
        }),
        ('Detalhes', {
            'fields': ('descricao', 'observacoes'),
            'classes': ('collapse',),
        }),
        ('Controle', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(LegalDeadline)
class LegalDeadlineAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'caso', 'tipo', 'data_prazo', 'status', 'prioridade', 'responsavel')
    list_filter = ('status', 'tipo', 'prioridade')
    search_fields = ('titulo', 'caso__titulo', 'caso__numero_processo')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(CaseTask)
class CaseTaskAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'caso', 'status', 'prioridade', 'data_limite', 'responsavel')
    list_filter = ('status', 'prioridade')
    search_fields = ('titulo', 'caso__titulo')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(CasePhase)
class CasePhaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'caso', 'order', 'status', 'estimated_date', 'actual_date')
    list_filter = ('status',)
    search_fields = ('name', 'caso__titulo')
    readonly_fields = ('id', 'created_at')


@admin.register(CaseDocument)
class CaseDocumentAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'caso', 'tipo', 'data_documento', 'created_at')
    list_filter = ('tipo',)
    search_fields = ('titulo', 'caso__titulo')


@admin.register(LegalNotification)
class LegalNotificationAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'caso', 'direcao', 'status', 'meio', 'data_ciencia', 'prazo_vencimento', 'created_at')
    list_filter = ('tipo', 'direcao', 'status', 'meio')
    search_fields = ('destinatario_nome', 'remetente', 'conteudo_resumo', 'caso__titulo')
    readonly_fields = ('id', 'prazo_vencimento', 'deadline_created', 'created_at', 'updated_at')

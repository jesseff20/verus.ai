from django.contrib import admin
from .models import FlowTemplate, FlowNode, FlowEdge, FlowVersion


class FlowNodeInline(admin.TabularInline):
    model = FlowNode
    extra = 0
    fields = ('node_id', 'node_type', 'label', 'role', 'order')
    readonly_fields = ('node_id',)


class FlowEdgeInline(admin.TabularInline):
    model = FlowEdge
    extra = 0
    fields = ('edge_id', 'source_node_id', 'target_node_id', 'label', 'condition')
    readonly_fields = ('edge_id',)


@admin.register(FlowTemplate)
class FlowTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'status', 'version', 'is_system_template', 'organ', 'updated_at')
    list_filter = ('status', 'category', 'is_system_template')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at', 'published_at')
    inlines = [FlowNodeInline, FlowEdgeInline]


@admin.register(FlowVersion)
class FlowVersionAdmin(admin.ModelAdmin):
    list_display = ('template', 'version_number', 'published_by', 'published_at')
    list_filter = ('template__category',)
    readonly_fields = ('id', 'published_at', 'snapshot')

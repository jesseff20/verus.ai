from rest_framework import serializers
from .models import FlowTemplate, FlowNode, FlowEdge, FlowVersion


class FlowNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlowNode
        fields = (
            'id', 'node_id', 'node_type', 'label', 'description',
            'role', 'parent_node_id', 'position', 'data', 'order',
        )


class FlowEdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlowEdge
        fields = (
            'id', 'edge_id', 'source_node_id', 'target_node_id',
            'source_handle', 'target_handle', 'label', 'condition', 'data',
        )


class FlowVersionSerializer(serializers.ModelSerializer):
    published_by_name = serializers.SerializerMethodField()

    class Meta:
        model = FlowVersion
        fields = (
            'id', 'version_number', 'published_by_name',
            'published_at', 'notes',
        )

    def get_published_by_name(self, obj):
        if obj.published_by:
            return obj.published_by.get_full_name() or obj.published_by.username
        return None


class FlowTemplateListSerializer(serializers.ModelSerializer):
    """Serializer leve para a listagem de templates."""
    node_count = serializers.ReadOnlyField()
    swimlane_count = serializers.ReadOnlyField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = FlowTemplate
        fields = (
            'id', 'name', 'description', 'category', 'status',
            'version', 'is_system_template', 'node_count', 'swimlane_count',
            'created_by_name', 'created_at', 'updated_at', 'published_at',
        )

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None


class FlowTemplateDetailSerializer(serializers.ModelSerializer):
    """Serializer completo com nós e edges — usado no editor."""
    nodes = FlowNodeSerializer(many=True, read_only=True)
    edges = FlowEdgeSerializer(many=True, read_only=True)
    versions = FlowVersionSerializer(many=True, read_only=True)

    class Meta:
        model = FlowTemplate
        fields = (
            'id', 'name', 'description', 'category', 'status',
            'version', 'is_system_template', 'organ',
            'nodes', 'edges', 'versions',
            'created_at', 'updated_at', 'published_at',
        )
        read_only_fields = ('id', 'version', 'status', 'published_at')


class FlowTemplateSaveSerializer(serializers.Serializer):
    """
    Recebe o estado completo do editor (nodes + edges) e salva tudo de uma vez.
    Substitui todos os nós e edges existentes — operação atômica.
    """
    name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True, default='')
    category = serializers.ChoiceField(
        choices=['judicial_1', 'judicial_2', 'administrative', 'other'],
        default='judicial_1',
    )
    nodes = FlowNodeSerializer(many=True)
    edges = FlowEdgeSerializer(many=True)


class FlowTemplatePublishSerializer(serializers.Serializer):
    """Dados opcionais para a ação de publicar."""
    notes = serializers.CharField(required=False, allow_blank=True, default='')

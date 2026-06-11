from rest_framework import serializers

from apps.workflow_definition.models import FlowTemplate, FlowEdge
from .models import (
    FlowInstance, TaskInstance, TaskRequest, ExecutionEvent,
    REQUEST_TYPE_CHOICES,
)


# ── ExecutionEvent ────────────────────────────────────────────────

class ExecutionEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = ExecutionEvent
        fields = [
            'id', 'event_type', 'node_id', 'node_label',
            'actor', 'actor_name', 'metadata', 'created_at',
        ]
        read_only_fields = fields

    def get_actor_name(self, obj):
        if obj.actor:
            return obj.actor.get_full_name() or obj.actor.email
        return None


# ── TaskRequest ───────────────────────────────────────────────────

class TaskRequestSerializer(serializers.ModelSerializer):
    requester_name = serializers.SerializerMethodField()
    target_user_name = serializers.SerializerMethodField()

    class Meta:
        model = TaskRequest
        fields = [
            'id', 'request_type', 'requester', 'requester_name',
            'target_user', 'target_user_name', 'justification',
            'status', 'resolution_note', 'created_at', 'resolved_at',
        ]
        read_only_fields = [
            'id', 'requester', 'requester_name', 'target_user_name',
            'status', 'resolution_note', 'created_at', 'resolved_at',
        ]

    def get_requester_name(self, obj):
        if obj.requester:
            return obj.requester.get_full_name() or obj.requester.email
        return None

    def get_target_user_name(self, obj):
        if obj.target_user:
            return obj.target_user.get_full_name() or obj.target_user.email
        return None


class CreateTaskRequestSerializer(serializers.Serializer):
    request_type = serializers.ChoiceField(choices=REQUEST_TYPE_CHOICES)
    target_user = serializers.UUIDField(required=False, allow_null=True)
    justification = serializers.CharField(min_length=10)


# ── TaskInstance ──────────────────────────────────────────────────

class TaskInstanceSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.SerializerMethodField()
    completed_by_name = serializers.SerializerMethodField()
    requests = TaskRequestSerializer(many=True, read_only=True)
    gateway_choices = serializers.SerializerMethodField()

    class Meta:
        model = TaskInstance
        fields = [
            'id', 'instance', 'node_id', 'node_type', 'label', 'role_required',
            'instructions', 'assigned_to', 'assigned_to_name',
            'status', 'gateway_choice', 'due_date', 'notes',
            'created_at', 'started_at', 'completed_at',
            'completed_by', 'completed_by_name',
            'requests', 'gateway_choices',
        ]
        read_only_fields = [
            'id', 'instance', 'node_id', 'node_type', 'label', 'role_required',
            'instructions', 'assigned_to', 'assigned_to_name', 'completed_by_name',
            'created_at', 'started_at', 'completed_at', 'completed_by',
            'requests', 'gateway_choices',
        ]

    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.get_full_name() or obj.assigned_to.email
        return None

    def get_completed_by_name(self, obj):
        if obj.completed_by:
            return obj.completed_by.get_full_name() or obj.completed_by.email
        return None

    def get_gateway_choices(self, obj):
        """Return outgoing edge options when this task is at a gateway node."""
        if 'gateway' not in (obj.node_type or ''):
            return []
        try:
            edges = FlowEdge.objects.filter(
                template=obj.instance.template,
                source_node_id=obj.node_id,
            ).values('edge_id', 'label', 'source_handle', 'condition')
            return [
                {
                    'value': e['source_handle'] or e['edge_id'],
                    'label': e['label'] or e['source_handle'] or e['edge_id'],
                    'condition': e['condition'],
                }
                for e in edges
            ]
        except Exception:
            return []


class CompleteTaskSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    gateway_choice = serializers.CharField(required=False, allow_blank=True, default='')


# ── FlowInstance ──────────────────────────────────────────────────

class FlowInstanceListSerializer(serializers.ModelSerializer):
    started_by_name = serializers.SerializerMethodField()
    pending_task_count = serializers.SerializerMethodField()

    class Meta:
        model = FlowInstance
        fields = [
            'id', 'template', 'template_name_snapshot', 'template_version_snapshot',
            'case_ref', 'case_title', 'status', 'current_node_id',
            'started_by', 'started_by_name',
            'started_at', 'completed_at', 'created_at',
            'pending_task_count',
        ]
        read_only_fields = fields

    def get_started_by_name(self, obj):
        if obj.started_by:
            return obj.started_by.get_full_name() or obj.started_by.email
        return None

    def get_pending_task_count(self, obj):
        # Use annotated value when available (avoids N+1 on list views)
        annotated = getattr(obj, 'pending_task_count_annotation', None)
        if annotated is not None:
            return annotated
        return obj.tasks.filter(status__in=('pending', 'in_progress')).count()


class FlowInstanceDetailSerializer(FlowInstanceListSerializer):
    tasks = TaskInstanceSerializer(many=True, read_only=True)
    events = ExecutionEventSerializer(many=True, read_only=True)

    class Meta(FlowInstanceListSerializer.Meta):
        fields = FlowInstanceListSerializer.Meta.fields + ['tasks', 'events']


class StartFlowSerializer(serializers.Serializer):
    template_id = serializers.UUIDField()
    case_ref = serializers.CharField(required=False, allow_blank=True, default='')
    case_title = serializers.CharField(required=False, allow_blank=True, default='')
    case_id = serializers.UUIDField(required=False, allow_null=True, default=None)

    def validate_template_id(self, value):
        try:
            template = FlowTemplate.objects.get(pk=value)
        except FlowTemplate.DoesNotExist:
            raise serializers.ValidationError('Template não encontrado.')
        if template.status != 'published':
            raise serializers.ValidationError('Apenas templates publicados podem ser instanciados.')
        return value


# ── Request resolve ───────────────────────────────────────────────

class ResolveRequestSerializer(serializers.Serializer):
    resolution_note = serializers.CharField(required=False, allow_blank=True, default='')

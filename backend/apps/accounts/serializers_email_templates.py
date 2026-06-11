"""
Serializers para Templates de E-mail (#19).
"""
from rest_framework import serializers
from .models import EmailTemplate


class EmailTemplateSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    variables_count = serializers.SerializerMethodField()

    class Meta:
        model = EmailTemplate
        fields = [
            'id', 'name', 'subject', 'body_html',
            'category', 'category_display',
            'variables', 'variables_count',
            'is_active',
            'created_by', 'created_by_name',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None

    def get_variables_count(self, obj):
        return len(obj.variables) if obj.variables else 0

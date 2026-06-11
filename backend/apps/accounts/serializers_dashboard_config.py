"""
Serializers para Dashboard Customizável — Feature #24.
"""
from rest_framework import serializers
from .models import DashboardConfig


class DashboardConfigSerializer(serializers.ModelSerializer):
    """Serializer para configuração do dashboard."""
    theme_display = serializers.CharField(source='get_theme_display', read_only=True)

    class Meta:
        model = DashboardConfig
        fields = [
            'id', 'user', 'layout', 'theme', 'theme_display',
            'auto_refresh', 'refresh_interval',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

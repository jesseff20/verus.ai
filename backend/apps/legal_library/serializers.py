"""
Serializers para Biblioteca Viva de Argumentos.
"""

from rest_framework import serializers
from .models import LegalArgument, ArgumentCollection, ArgumentUsage


class LegalArgumentSerializer(serializers.ModelSerializer):
    """Serializer para Argumento Jurídico"""
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', read_only=True)
    category_display = serializers.CharField(
        source='get_category_display', read_only=True)
    specialty_display = serializers.CharField(
        source='get_specialty_display', read_only=True)

    class Meta:
        model = LegalArgument
        fields = [
            'id', 'title', 'content', 'summary',
            'category', 'category_display', 'specialty', 'specialty_display',
            'subcategories', 'tribunal',
            'effectiveness_score', 'usage_count', 'success_count',
            'related_precedents',
            'created_by', 'created_by_name',
            'status', 'created_at', 'updated_at', 'last_used_at',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'created_by',
            'effectiveness_score', 'usage_count', 'success_count',
        ]


class LegalArgumentListSerializer(serializers.ModelSerializer):
    """Serializer para listagem de Argumentos"""
    category_display = serializers.CharField(
        source='get_category_display', read_only=True)
    specialty_display = serializers.CharField(
        source='get_specialty_display', read_only=True)

    class Meta:
        model = LegalArgument
        fields = [
            'id', 'title', 'summary',
            'category', 'category_display', 'specialty', 'specialty_display',
            'tribunal',
            'effectiveness_score', 'usage_count',
            'status', 'created_at',
        ]


class LegalArgumentCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar Argumento"""
    class Meta:
        model = LegalArgument
        fields = [
            'title', 'content', 'summary',
            'category', 'specialty', 'subcategories', 'tribunal',
            'related_precedents',
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class LegalArgumentUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualizar Argumento"""
    class Meta:
        model = LegalArgument
        fields = [
            'title', 'content', 'summary',
            'category', 'specialty', 'subcategories', 'tribunal',
            'related_precedents', 'status',
        ]


class ArgumentCollectionSerializer(serializers.ModelSerializer):
    """Serializer para Coleção de Argumentos"""
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', read_only=True)
    arguments_count = serializers.IntegerField(
        source='arguments.count', read_only=True)
    arguments_list = LegalArgumentListSerializer(
        source='arguments',
        many=True,
        read_only=True
    )

    class Meta:
        model = ArgumentCollection
        fields = [
            'id', 'name', 'description',
            'arguments', 'arguments_count', 'arguments_list',
            'created_by', 'created_by_name',
            'is_public', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class ArgumentUsageSerializer(serializers.ModelSerializer):
    """Serializer para Uso de Argumento"""
    argument_title = serializers.CharField(
        source='argument.title', read_only=True)
    outcome_display = serializers.CharField(
        source='get_outcome_display', read_only=True)

    class Meta:
        model = ArgumentUsage
        fields = [
            'id', 'argument', 'argument_title',
            'document_id', 'case_id', 'section_title',
            'outcome', 'outcome_display',
            'used_at', 'outcome_recorded_at',
        ]
        read_only_fields = ['id', 'used_at']


class ArgumentUsageCreateSerializer(serializers.ModelSerializer):
    """Serializer para registrar uso de Argumento"""
    class Meta:
        model = ArgumentUsage
        fields = [
            'argument', 'document_id', 'case_id', 'section_title',
        ]

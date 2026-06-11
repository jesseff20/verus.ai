from rest_framework import serializers
from .models import Organ, Unit


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ('id', 'name', 'short_name', 'unit_type', 'description', 'is_active')


class OrganSerializer(serializers.ModelSerializer):
    units = UnitSerializer(many=True, read_only=True)

    class Meta:
        model = Organ
        fields = (
            'id', 'name', 'short_name', 'organ_type',
            'cnpj', 'state', 'city', 'address',
            'phone', 'email', 'website', 'logo',
            'is_active', 'units',
        )
        read_only_fields = ('id',)


class OrganMinimalSerializer(serializers.ModelSerializer):
    """Serializer leve para uso em FKs (ex: User.organ)."""
    class Meta:
        model = Organ
        fields = ('id', 'name', 'short_name', 'state', 'city')

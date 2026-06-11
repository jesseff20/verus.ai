from django.contrib import admin
from .models import Organ, Unit


class UnitInline(admin.TabularInline):
    model = Unit
    extra = 1
    fields = ('name', 'short_name', 'unit_type', 'is_active')


@admin.register(Organ)
class OrganAdmin(admin.ModelAdmin):
    list_display = ('short_name', 'name', 'organ_type', 'city', 'state', 'is_active')
    list_filter = ('organ_type', 'state', 'is_active')
    search_fields = ('name', 'short_name', 'city', 'cnpj')
    inlines = [UnitInline]


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'organ', 'unit_type', 'is_active')
    list_filter = ('unit_type', 'is_active', 'organ__state')
    search_fields = ('name', 'organ__name', 'organ__short_name')
    raw_id_fields = ('organ',)

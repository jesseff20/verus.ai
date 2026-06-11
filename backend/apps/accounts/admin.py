"""
Admin para gerenciamento de usuários
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Notification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin customizado para User"""
    list_display = ['username', 'email', 'role', 'first_name', 'last_name', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'is_staff', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-created_at']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informações Adicionais', {
            'fields': ('role', 'phone', 'department', 'position', 'avatar', 'preferred_llm_provider')
        }),
        ('Metadados', {
            'fields': ('metadata', 'last_login_ip', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ['created_at', 'updated_at', 'last_login_ip']

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informações Adicionais', {
            'fields': ('role', 'email', 'first_name', 'last_name', 'phone', 'department', 'position')
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin para notificações"""
    list_display = ['title', 'user', 'type', 'priority', 'is_read', 'created_at']
    list_filter = ['type', 'priority', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__username']
    ordering = ['-created_at']
    raw_id_fields = ['user']

"""
URLs de Auditoria de Acessos — Feature #23.
"""
from django.urls import path
from . import views_audit

urlpatterns = [
    path('auditoria/', views_audit.audit_log_list, name='audit-log-list'),
    path('auditoria/stats/', views_audit.audit_log_stats, name='audit-log-stats'),
    path('auditoria/usuario/<uuid:user_id>/', views_audit.audit_log_user_activity, name='audit-log-user-activity'),
]

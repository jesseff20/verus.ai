"""
URLs para Templates de E-mail (#19).
"""
from django.urls import path
from . import views_email_templates as views

urlpatterns = [
    path('', views.email_templates_list_create, name='email-templates-list'),
    path('<uuid:template_id>/', views.email_template_detail, name='email-template-detail'),
    path('preview/', views.email_template_preview, name='email-template-preview'),
    path('generate-ai/', views.email_template_generate_ai, name='email-template-generate-ai'),
]

"""
URLs para Dashboard Customizável — Feature #24.
"""
from django.urls import path
from . import views_dashboard_config

urlpatterns = [
    path('', views_dashboard_config.dashboard_config_get_or_create, name='dashboard-config'),
    path('widgets/', views_dashboard_config.dashboard_widgets_data, name='dashboard-widgets-data'),
]

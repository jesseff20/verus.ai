"""
URLs de Clientes — Gestão de Clientes do Verus.AI.
"""
from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.clients_list_create, name='clients-list'),
    path('<uuid:client_id>/', views.client_detail, name='client-detail'),
]

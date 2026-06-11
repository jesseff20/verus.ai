"""
URLs do módulo Financeiro - Copilot/IA.
"""
from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    # Copilot Financeiro
    path('copilot/prever-fluxo/', views.copilot_predict_cashflow, name='copilot-predict-cashflow'),
    path('copilot/sugerir-honorarios/', views.copilot_suggest_fees, name='copilot-suggest-fees'),
    path('copilot/analisar-risco/', views.copilot_analyze_risk, name='copilot-analyze-risk'),
    path('copilot/gerar-cobranca/', views.copilot_generate_collection, name='copilot-generate-collection'),
]

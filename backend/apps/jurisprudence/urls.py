"""
URLs do app Jurisprudência — Radar de Precedentes.
"""
from django.urls import path

from .views.radar_views import (
    analyze_precedents,
    list_tribunais_stats,
    list_theses_stats,
    get_precedent_detail,
    list_specialties,
    jurisprudence_searches,
    jurisprudence_searches_stream,
    delete_search,
    clear_all_searches,
    scrape_jurisprudencia,
)

app_name = 'jurisprudence'

urlpatterns = [
    # Radar de Precedentes
    path('radar/analyze/', analyze_precedents, name='radar-analyze'),
    path('radar/tribunais/', list_tribunais_stats, name='radar-tribunais'),
    path('radar/teses/', list_theses_stats, name='radar-teses'),
    path('radar/precedents/<int:precedent_id>/', get_precedent_detail, name='radar-precedent-detail'),

    # Endpoints requeridos pelo frontend
    path('specialties/', list_specialties, name='specialties'),
    path('searches/', jurisprudence_searches, name='searches'),
    path('searches/stream/', jurisprudence_searches_stream, name='searches-stream'),
    path('searches/clear/', clear_all_searches, name='searches-clear'),
    path('searches/<uuid:search_id>/', delete_search, name='delete-search'),
    path('scrape/', scrape_jurisprudencia, name='scrape'),
]

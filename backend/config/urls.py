"""
URLs do Verus.AI — Projeto Django.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # API v1 — Autenticação e usuários
    path('api/v1/auth/', include('apps.accounts.urls', namespace='accounts')),

    # API v1 — Apps base
    path('api/v1/intelligent-assistant/', include('apps.intelligent_assistant.urls', namespace='intelligent_assistant')),
    path('api/v1/processos/', include('apps.cases.urls', namespace='cases')),
    path('api/v1/core/', include('apps.core.urls', namespace='core')),
    # Rota de clientes desativada — não aplicável a procuradorias
    # path('api/v1/clientes/', include('apps.cases.urls_clients', namespace='clients')),

    # API v1 — Apps adicionais
    path('api/v1/agents/', include('apps.agents.urls', namespace='agents')),
    path('api/v1/copilot/', include('apps.copilot.urls')),
    path('api/v1/documents/', include('apps.documents.urls', namespace='documents')),
    path('api/v1/forms/', include('apps.forms.urls', namespace='forms')),
    path('api/v1/integration/', include('apps.integration.urls', namespace='integration')),
    path('api/v1/kb/', include('apps.kb.urls', namespace='kb')),
    path('api/v1/legal-library/', include('apps.legal_library.urls', namespace='legal_library')),
    path('api/v1/rag/', include('apps.rag.urls', namespace='rag')),
    path('api/v1/templates/', include('apps.templates.urls', namespace='templates')),
    path('api/v1/collaboration/', include('apps.collaboration.urls', namespace='collaboration')),
    path('api/v1/jurisprudence/', include('apps.jurisprudence.urls', namespace='jurisprudence')),
    path('api/v1/simulations/', include('apps.simulations.urls', namespace='simulations')),

    # Financeiro desativado — não aplicável a procuradorias
    # path('api/v1/processos/financeiro/', include('apps.financeiro.urls', namespace='financeiro')),

    # API v1 — Organização (Órgãos e Unidades)
    path('api/v1/organization/', include('apps.organization.urls', namespace='organization')),

    # API v1 — Workflows (definição de fluxos)
    path('api/v1/workflows/', include('apps.workflow_definition.urls', namespace='workflow_definition')),

    # API v1 — Workflow Execution (instâncias em runtime)
    path('api/v1/workflow-execution/', include('apps.workflow_execution.urls')),

    # API v1 — Assinaturas Digitais
    path('api/v1/signatures/', include('apps.signature.urls')),
]

# Media files em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

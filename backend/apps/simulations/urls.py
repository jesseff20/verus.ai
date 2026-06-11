from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'simulations'

router = DefaultRouter()
router.register(r'simulations', views.SimulationViewSet, basename='simulation')
router.register(r'judges', views.JudgeProfileViewSet, basename='judge-profile')
router.register(r'courts', views.CourtViewSet, basename='court')

urlpatterns = [
    # ViewSets principais
    path('', include(router.urls)),

    # Nested: documentos da simulação
    path(
        'simulations/<uuid:simulation_pk>/documents/',
        views.SimulationDocumentViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='simulation-documents-list',
    ),
    path(
        'simulations/<uuid:simulation_pk>/documents/<uuid:pk>/',
        views.SimulationDocumentViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}),
        name='simulation-documents-detail',
    ),

    # Nested: jurados da simulação
    path(
        'simulations/<uuid:simulation_pk>/jury-members/',
        views.JuryMemberViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='simulation-jury-members-list',
    ),
    path(
        'simulations/<uuid:simulation_pk>/jury-members/<uuid:pk>/',
        views.JuryMemberViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}),
        name='simulation-jury-members-detail',
    ),

    # SSE Streaming
    path(
        'simulations/<uuid:simulation_pk>/jury/start/',
        views.start_jury_debate,
        name='simulation-jury-start',
    ),
    path(
        'simulations/<uuid:simulation_pk>/judge/start/',
        views.start_judge_simulation,
        name='simulation-judge-start',
    ),

    # Questionamento de simulação
    path(
        'simulations/<uuid:simulation_pk>/question/',
        views.question_simulation,
        name='simulation-question',
    ),

    # Questionamento específico do veredicto do júri
    path(
        'simulations/<uuid:simulation_pk>/question-verdict/',
        views.question_verdict,
        name='simulation-question-verdict',
    ),

    # Geração de PDF da simulação
    path(
        'simulations/<uuid:simulation_pk>/generate-pdf/',
        views.generate_simulation_pdf,
        name='simulation-generate-pdf',
    ),

    # STF Simulation
    path(
        'simulations/<uuid:simulation_pk>/stf/start/',
        views.start_stf_simulation,
        name='simulation-stf-start',
    ),

    # Acordao 2a Instancia Simulation
    path(
        'simulations/<uuid:simulation_pk>/acordao/start/',
        views.start_acordao_simulation,
        name='simulation-acordao-start',
    ),

    # STJ Simulation
    path(
        'simulations/<uuid:simulation_pk>/stj/start/',
        views.start_stj_simulation,
        name='simulation-stj-start',
    ),

    # JEC Simulation
    path(
        'simulations/<uuid:simulation_pk>/jec/start/',
        views.start_jec_simulation,
        name='simulation-jec-start',
    ),

    # JECRIM Simulation
    path(
        'simulations/<uuid:simulation_pk>/jecrim/start/',
        views.start_jecrim_simulation,
        name='simulation-jecrim-start',
    ),

    # Eleitoral Simulation (Juiz Eleitoral - 1a instancia)
    path(
        'simulations/<uuid:simulation_pk>/eleitoral/start/',
        views.start_eleitoral_simulation,
        name='simulation-eleitoral-start',
    ),

    # TRE Simulation (7 membros)
    path(
        'simulations/<uuid:simulation_pk>/tre/start/',
        views.start_tre_simulation,
        name='simulation-tre-start',
    ),

    # TSE Simulation (7 ministros)
    path(
        'simulations/<uuid:simulation_pk>/tse/start/',
        views.start_tse_simulation,
        name='simulation-tse-start',
    ),

    # Vara do Trabalho (1a instancia trabalhista)
    path(
        'simulations/<uuid:simulation_pk>/trabalho/start/',
        views.start_trabalho_simulation,
        name='simulation-trabalho-start',
    ),

    # TRT (2a instancia trabalhista)
    path(
        'simulations/<uuid:simulation_pk>/trt/start/',
        views.start_trt_simulation,
        name='simulation-trt-start',
    ),

    # TST (Tribunal Superior do Trabalho)
    path(
        'simulations/<uuid:simulation_pk>/tst/start/',
        views.start_tst_simulation,
        name='simulation-tst-start',
    ),

    # Turma Recursal (recurso dos Juizados Especiais)
    path(
        'simulations/<uuid:simulation_pk>/turma-recursal/start/',
        views.start_turma_recursal_simulation,
        name='simulation-turma-recursal-start',
    ),

    # Auditoria de Justica Militar (1a instancia)
    path(
        'simulations/<uuid:simulation_pk>/militar/start/',
        views.start_militar_simulation,
        name='simulation-militar-start',
    ),

    # STM - Superior Tribunal Militar
    path(
        'simulations/<uuid:simulation_pk>/stm/start/',
        views.start_stm_simulation,
        name='simulation-stm-start',
    ),

    # Minister profiles
    path(
        'ministers/',
        views.list_minister_profiles,
        name='minister-profiles-list',
    ),
]

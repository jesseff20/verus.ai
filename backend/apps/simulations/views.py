import json
import logging

from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Simulation, SimulationDocument, JuryMember,
    JuryDebateMessage, JudgeProfile, Court,
    MinisterProfile, CourtVote,
)
from .serializers import (
    SimulationSerializer, SimulationListSerializer,
    SimulationDocumentSerializer, JuryMemberSerializer,
    JuryDebateMessageSerializer, JudgeProfileSerializer,
    CourtSerializer, MinisterProfileSerializer,
)
from .services import (
    JurySimulationService, JudgeSimulationService, STFSimulationService,
    AcordaoSimulationService, STJSimulationService,
    JECSimulationService, JECRIMSimulationService, EleitoralSimulationService,
    TrabalhoSimulationService, TRTSimulationService, TSTSimulationService,
    TurmaRecursalSimulationService, MilitarSimulationService, STMSimulationService,
)
from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

logger = logging.getLogger(__name__)


class SimulationViewSet(viewsets.ModelViewSet):
    """CRUD de simulações (Júri e Sentença)."""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['simulation_type', 'status']
    search_fields = ['title', 'description']

    def get_serializer_class(self):
        if self.action == 'list':
            return SimulationListSerializer
        return SimulationSerializer

    def get_queryset(self):
        return Simulation.objects.filter(
            user=self.request.user,
            is_deleted=False,
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        """Soft delete instead of hard delete."""
        instance.is_deleted = True
        instance.save(update_fields=['is_deleted'])

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Clone a simulation to re-run with the same config."""
        original = self.get_object()
        new_sim = Simulation.objects.create(
            user=request.user,
            simulation_type=original.simulation_type,
            title=f'{original.title} (cópia)',
            description=original.description,
            case=original.case,
            config=original.config,
            status='draft',
        )
        serializer = SimulationSerializer(new_sim)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SimulationDocumentViewSet(viewsets.ModelViewSet):
    """Upload e gestão de documentos da simulação."""
    serializer_class = SimulationDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SimulationDocument.objects.filter(
            simulation__user=self.request.user,
            simulation_id=self.kwargs.get('simulation_pk'),
        )

    def perform_create(self, serializer):
        simulation = Simulation.objects.get(
            pk=self.kwargs['simulation_pk'],
            user=self.request.user,
        )
        serializer.save(simulation=simulation)


class JuryMemberViewSet(viewsets.ModelViewSet):
    """CRUD de jurados (nested em simulação)."""
    serializer_class = JuryMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JuryMember.objects.filter(
            simulation__user=self.request.user,
            simulation_id=self.kwargs.get('simulation_pk'),
        )

    def perform_create(self, serializer):
        simulation = Simulation.objects.get(
            pk=self.kwargs['simulation_pk'],
            user=self.request.user,
        )
        serializer.save(simulation=simulation)


class JudgeProfileViewSet(viewsets.ModelViewSet):
    """CRUD de perfis de juízes."""
    serializer_class = JudgeProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = JudgeProfile.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['state', 'court', 'comarca', 'specialization']
    search_fields = ['name']


class CourtViewSet(viewsets.ModelViewSet):
    """CRUD de tribunais/comarcas."""
    serializer_class = CourtSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Court.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['state', 'court_type']


# ── SSE Streaming Views ─────────────────────────────────────────────────────


def _sse_event(data: dict) -> str:
    """Formata um evento SSE."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _safe_event_stream(generator):
    """Wrap a SSE generator to stop cleanly on client disconnect.

    Django's StreamingHttpResponse only detects a closed connection when
    the next ``yield`` fails.  Expensive LLM calls that happen *between*
    yields would keep running even after the client is gone.  By catching
    the connection-error family of exceptions at the outermost layer we
    ensure the generator (and any pending LLM work) is abandoned as soon
    as the broken pipe is detected.
    """
    try:
        yield from generator
    except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError, OSError) as exc:
        logger.info('Client disconnected during SSE stream: %s', exc)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_jury_debate(request, simulation_pk):
    """
    Inicia simulação completa do Tribunal do Júri via SSE streaming.

    O serviço JurySimulationService orquestra todas as 8 fases do rito
    (CPP art. 447+): abertura, acusação, defesa, réplica, tréplica,
    deliberação, votação dos quesitos e sentença.
    """
    try:
        simulation = Simulation.objects.get(
            pk=simulation_pk,
            user=request.user,
            simulation_type='jury',
        )
    except Simulation.DoesNotExist:
        return Response(
            {'error': 'Simulação de júri não encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if simulation.status == 'completed':
        return Response(
            {'error': 'Esta simulação já foi concluída.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if simulation.status == 'running':
        return Response(
            {'error': 'Esta simulação já está em execução.'},
            status=status.HTTP_409_CONFLICT,
        )

    service = JurySimulationService(str(simulation_pk))

    def event_stream():
        try:
            for event in service.stream_simulation():
                yield _sse_event(event)
        except Exception as e:
            logger.exception(f'[jury_debate] Erro no stream SSE: {e}')
            yield _sse_event({'event': 'error', 'content': str(e)})

    response = StreamingHttpResponse(
        _safe_event_stream(event_stream()),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_judge_simulation(request, simulation_pk):
    """
    Inicia simulação de sentença do juiz via SSE streaming.

    O serviço JudgeSimulationService analisa o perfil do juiz,
    os documentos do processo e gera uma sentença completa
    (relatório, fundamentação e dispositivo).
    """
    try:
        simulation = Simulation.objects.get(
            pk=simulation_pk,
            user=request.user,
            simulation_type='judge',
        )
    except Simulation.DoesNotExist:
        return Response(
            {'error': 'Simulação de sentença não encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if simulation.status == 'completed':
        return Response(
            {'error': 'Esta simulação já foi concluída.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if simulation.status == 'running':
        return Response(
            {'error': 'Esta simulação já está em execução.'},
            status=status.HTTP_409_CONFLICT,
        )

    service = JudgeSimulationService(str(simulation_pk))

    def event_stream():
        try:
            for event in service.stream_simulation():
                yield _sse_event(event)
        except Exception as e:
            logger.exception(f'[judge_simulation] Erro no stream SSE: {e}')
            yield _sse_event({'event': 'error', 'content': str(e)})

    response = StreamingHttpResponse(
        _safe_event_stream(event_stream()),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def question_simulation(request, simulation_pk):
    """Permite questionar qualquer simulação (júri ou sentença)."""
    simulation = get_object_or_404(
        Simulation, id=simulation_pk, user=request.user, is_deleted=False,
    )
    question = request.data.get('question', '')

    if not question.strip():
        return Response(
            {'error': 'A pergunta não pode ser vazia.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if simulation.status != 'completed':
        return Response(
            {'error': 'A simulação precisa estar concluída para aceitar perguntas.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    result_data = simulation.result or {}
    context = json.dumps(result_data, ensure_ascii=False)
    docs_text = '\n'.join(
        [d.extracted_text for d in simulation.documents.all() if d.extracted_text]
    )

    # Build a richer context depending on simulation type
    if simulation.simulation_type == 'judge':
        sentence = result_data.get('sentence', '')
        strategic = result_data.get('strategic_report', '')
        dispositivo = result_data.get('dispositivo', '')
        prompt = (
            "Você é um consultor jurídico analisando uma simulação de sentença.\n\n"
            f"DISPOSITIVO: {dispositivo}\n\n"
            f"SENTENÇA:\n{sentence}\n\n"
            f"RELATÓRIO ESTRATÉGICO:\n{strategic}\n\n"
            f"DADOS COMPLETOS DA SIMULAÇÃO:\n{context}\n\n"
            f"DOCUMENTOS DO PROCESSO:\n{docs_text}\n\n"
            f"PERGUNTA DO USUÁRIO:\n{question}\n\n"
            "Responda de forma prática e específica, com recomendações acionáveis.\n"
            "Cite legislação e jurisprudência quando relevante."
        )
    else:
        prompt = (
            "Você é um consultor jurídico analisando uma simulação de julgamento.\n\n"
            f"RESULTADO DA SIMULAÇÃO:\n{context}\n\n"
            f"DOCUMENTOS DO PROCESSO:\n{docs_text}\n\n"
            f"PERGUNTA DO USUÁRIO:\n{question}\n\n"
            "Responda de forma prática e específica, com recomendações acionáveis.\n"
            "Cite legislação e jurisprudência quando relevante."
        )

    try:
        llm = UnifiedLLMService()
        result = llm.generate(
            user_prompt=prompt,
            system_prompt='Você é um consultor jurídico brasileiro experiente e prático.',
            temperature=0.7,
            max_tokens=2048,
        )
        answer = result.get('content', '')
        return Response({'answer': answer, 'question': question})
    except Exception as e:
        logger.exception(f'[question_simulation] Erro: {e}')
        return Response(
            {'error': f'Erro ao processar a pergunta: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_simulation_pdf(request, simulation_pk):
    """Gera PDF de uma simulação concluída usando WeasyPrint."""
    simulation = get_object_or_404(
        Simulation, id=simulation_pk, user=request.user, is_deleted=False,
    )

    if simulation.status != 'completed':
        return Response(
            {'error': 'A simulação precisa estar concluída para gerar PDF.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    result_data = simulation.result or {}

    if simulation.simulation_type == 'judge':
        sentence = result_data.get('sentence', '')
        strategic_report = result_data.get('strategic_report', '')
        dispositivo = result_data.get('dispositivo', '')
        judge_name = result_data.get('judge_name', 'Juiz')
        process_type = result_data.get('process_type', '')
        case_value = result_data.get('case_value', '')
        comarca = result_data.get('comarca', '')
        state = result_data.get('state', '')

        dispositivo_label = {
            'procedente': 'PROCEDENTE',
            'improcedente': 'IMPROCEDENTE',
            'parcialmente_procedente': 'PARCIALMENTE PROCEDENTE',
        }.get(dispositivo, '')

        from datetime import datetime
        date_str = datetime.now().strftime('%d/%m/%Y')

        markdown_content = f"""# SENTENÇA SIMULADA

**Juiz:** {judge_name}
**Comarca:** {comarca}/{state}
**Tipo:** {process_type}
{f'**Valor da Causa:** {case_value}' if case_value else ''}
**Data:** {date_str}
**Dispositivo:** {dispositivo_label}

---

## Texto da Sentença

{sentence}

---

## Relatório Estratégico

{strategic_report}

---

*Documento gerado automaticamente pelo Verus.AI - Simulação de Sentença.*
*Este documento é uma simulação e não possui valor jurídico.*
"""
    else:
        # Jury simulation
        markdown_content = f"""# SIMULAÇÃO DE TRIBUNAL DO JÚRI

**Título:** {simulation.title}

{json.dumps(result_data, ensure_ascii=False, indent=2)}

---

*Documento gerado automaticamente pelo Verus.AI - Simulação de Júri.*
*Este documento é uma simulação e não possui valor jurídico.*
"""

    try:
        from apps.intelligent_assistant.services.pdf_service import PDFService
        pdf_service = PDFService()

        header_html = f"""
        <div class="document-header">
            <h1>{simulation.title}</h1>
        </div>
        """

        footer_html = """
        <div class="document-footer">
            <p>Verus.AI - Simulação de Sentença</p>
            <p>Este documento é uma simulação e não possui valor jurídico.</p>
        </div>
        """

        pdf_bytes = pdf_service.markdown_to_pdf(
            markdown_content=markdown_content,
            title=simulation.title,
            header_html=header_html,
            footer_html=footer_html,
        )

        if pdf_bytes is None:
            return Response(
                {'error': 'Falha ao gerar PDF. Verifique se o WeasyPrint está instalado.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        from django.http import HttpResponse
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        safe_title = simulation.title.replace(' ', '_')[:50]
        response['Content-Disposition'] = f'attachment; filename="simulacao_{safe_title}.pdf"'
        return response

    except Exception as e:
        logger.exception(f'[generate_simulation_pdf] Erro: {e}')
        return Response(
            {'error': f'Erro ao gerar PDF: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def question_verdict(request, simulation_pk):
    """Permite ao usuário questionar especificamente o veredicto do júri.

    Diferente de ``question_simulation`` (genérico), este endpoint é
    especializado em análise do veredicto: perfil de jurados, votos,
    argumentos decisivos e cenários hipotéticos.
    """
    simulation = get_object_or_404(
        Simulation, id=simulation_pk, user=request.user, simulation_type='jury',
    )
    question = request.data.get('question', '').strip()

    if not question:
        return Response(
            {'error': 'A pergunta não pode estar vazia.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if simulation.status != 'completed':
        return Response(
            {'error': 'A simulação precisa estar concluída para aceitar perguntas.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    result = simulation.result or {}
    result_text = json.dumps(result, ensure_ascii=False)

    prompt = (
        "Você é um analista jurídico especializado em Tribunal do Júri brasileiro. "
        "O usuário questiona o resultado de uma simulação de júri.\n\n"
        f"RESULTADO DO JULGAMENTO:\n{result_text}\n\n"
        f"PERGUNTA DO USUÁRIO:\n{question}\n\n"
        "Responda de forma fundamentada, citando os momentos específicos do "
        "julgamento que justificam sua análise. Seja detalhado e cite legislação "
        "quando pertinente."
    )

    try:
        llm = UnifiedLLMService()
        response_data = llm.generate(
            user_prompt=prompt,
            system_prompt=(
                "Você é um analista jurídico que responde perguntas sobre simulações "
                "de Tribunal do Júri. Seja preciso, fundamentado e cite dados concretos "
                "do julgamento ao responder."
            ),
            temperature=0.7,
            max_tokens=2048,
        )
        answer = response_data.get('content', '')
        return Response({'answer': answer, 'question': question})
    except Exception as e:
        logger.exception(f'[question_verdict] Erro: {e}')
        return Response(
            {'error': f'Erro ao processar a pergunta: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ── STF Views ──────────────────────────────────────────────────────────────


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_stf_simulation(request, simulation_pk):
    """
    Inicia simulação de julgamento do STF via SSE streaming.

    O serviço STFSimulationService orquestra relatório, votos individuais
    dos ministros, proclamação do resultado e relatório estratégico.
    """
    try:
        simulation = Simulation.objects.get(
            pk=simulation_pk,
            user=request.user,
            simulation_type='stf',
        )
    except Simulation.DoesNotExist:
        return Response(
            {'error': 'Simulação STF não encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if simulation.status == 'completed':
        return Response(
            {'error': 'Esta simulação já foi concluída.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if simulation.status == 'running':
        return Response(
            {'error': 'Esta simulação já está em execução.'},
            status=status.HTTP_409_CONFLICT,
        )

    service = STFSimulationService(str(simulation_pk))

    def event_stream():
        try:
            for event in service.stream_simulation():
                yield _sse_event(event)
        except Exception as e:
            logger.exception(f'[stf_simulation] Erro no stream SSE: {e}')
            yield _sse_event({'event': 'error', 'content': str(e)})

    response = StreamingHttpResponse(
        _safe_event_stream(event_stream()),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_acordao_simulation(request, simulation_pk):
    """
    Inicia simulacao de acordao de 2a Instancia via SSE streaming.

    O servico AcordaoSimulationService orquestra relatorio, votos dos 3
    desembargadores (Relator, Revisor, Vogal), proclamacao e relatorio estrategico.
    """
    try:
        simulation = Simulation.objects.get(
            pk=simulation_pk,
            user=request.user,
            simulation_type='acordao_2inst',
        )
    except Simulation.DoesNotExist:
        return Response(
            {'error': 'Simulacao de acordao nao encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if simulation.status == 'completed':
        return Response(
            {'error': 'Esta simulacao ja foi concluida.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if simulation.status == 'running':
        return Response(
            {'error': 'Esta simulacao ja esta em execucao.'},
            status=status.HTTP_409_CONFLICT,
        )

    service = AcordaoSimulationService(str(simulation_pk))

    def event_stream():
        try:
            for event in service.stream_simulation():
                yield _sse_event(event)
        except Exception as e:
            logger.exception(f'[acordao_simulation] Erro no stream SSE: {e}')
            yield _sse_event({'event': 'error', 'content': str(e)})

    response = StreamingHttpResponse(
        _safe_event_stream(event_stream()),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_stj_simulation(request, simulation_pk):
    """
    Inicia simulacao de julgamento do STJ via SSE streaming.

    O servico STJSimulationService orquestra relatorio, votos individuais
    dos ministros, proclamacao do resultado e relatorio estrategico.
    """
    try:
        simulation = Simulation.objects.get(
            pk=simulation_pk,
            user=request.user,
            simulation_type='stj',
        )
    except Simulation.DoesNotExist:
        return Response(
            {'error': 'Simulacao STJ nao encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if simulation.status == 'completed':
        return Response(
            {'error': 'Esta simulacao ja foi concluida.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if simulation.status == 'running':
        return Response(
            {'error': 'Esta simulacao ja esta em execucao.'},
            status=status.HTTP_409_CONFLICT,
        )

    service = STJSimulationService(str(simulation_pk))

    def event_stream():
        try:
            for event in service.stream_simulation():
                yield _sse_event(event)
        except Exception as e:
            logger.exception(f'[stj_simulation] Erro no stream SSE: {e}')
            yield _sse_event({'event': 'error', 'content': str(e)})

    response = StreamingHttpResponse(
        _safe_event_stream(event_stream()),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_minister_profiles(request):
    """Lista perfis de ministros (STF/STJ) com filtro opcional por court_type."""
    court_type = request.query_params.get('court_type', None)
    qs = MinisterProfile.objects.filter(is_active=True)
    if court_type:
        qs = qs.filter(court_type=court_type)
    serializer = MinisterProfileSerializer(qs, many=True)
    return Response(serializer.data)


# ── JEC / JECRIM Views ───────────────────────────────────────────────────


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_jec_simulation(request, simulation_pk):
    """
    Inicia simulação do Juizado Especial Cível via SSE streaming.

    O serviço JECSimulationService orquestra triagem, conciliação,
    instrução (se necessário), sentença simplificada e relatório estratégico.
    """
    try:
        simulation = Simulation.objects.get(
            pk=simulation_pk,
            user=request.user,
            simulation_type='jec',
        )
    except Simulation.DoesNotExist:
        return Response(
            {'error': 'Simulação JEC não encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if simulation.status == 'completed':
        return Response(
            {'error': 'Esta simulação já foi concluída.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if simulation.status == 'running':
        return Response(
            {'error': 'Esta simulação já está em execução.'},
            status=status.HTTP_409_CONFLICT,
        )

    service = JECSimulationService(str(simulation_pk))

    def event_stream():
        try:
            for event in service.stream_simulation():
                yield _sse_event(event)
        except Exception as e:
            logger.exception(f'[jec_simulation] Erro no stream SSE: {e}')
            yield _sse_event({'event': 'error', 'content': str(e)})

    response = StreamingHttpResponse(
        _safe_event_stream(event_stream()),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_jecrim_simulation(request, simulation_pk):
    """
    Inicia simulação do Juizado Especial Criminal via SSE streaming.

    O serviço JECRIMSimulationService orquestra audiência preliminar,
    transação penal, suspensão condicional, instrução criminal (se necessário),
    sentença e relatório estratégico.
    """
    try:
        simulation = Simulation.objects.get(
            pk=simulation_pk,
            user=request.user,
            simulation_type='jecrim',
        )
    except Simulation.DoesNotExist:
        return Response(
            {'error': 'Simulação JECRIM não encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if simulation.status == 'completed':
        return Response(
            {'error': 'Esta simulação já foi concluída.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if simulation.status == 'running':
        return Response(
            {'error': 'Esta simulação já está em execução.'},
            status=status.HTTP_409_CONFLICT,
        )

    service = JECRIMSimulationService(str(simulation_pk))

    def event_stream():
        try:
            for event in service.stream_simulation():
                yield _sse_event(event)
        except Exception as e:
            logger.exception(f'[jecrim_simulation] Erro no stream SSE: {e}')
            yield _sse_event({'event': 'error', 'content': str(e)})

    response = StreamingHttpResponse(
        _safe_event_stream(event_stream()),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


# ── Eleitoral Views ─────────────────────────────────────────────────────


def _start_eleitoral_view(request, simulation_pk, sim_type, label):
    """Helper generico para iniciar simulacoes eleitorais (eleitoral, tre, tse)."""
    try:
        simulation = Simulation.objects.get(
            pk=simulation_pk,
            user=request.user,
            simulation_type=sim_type,
        )
    except Simulation.DoesNotExist:
        return Response(
            {'error': f'Simulacao {label} nao encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if simulation.status == 'completed':
        return Response(
            {'error': 'Esta simulacao ja foi concluida.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if simulation.status == 'running':
        return Response(
            {'error': 'Esta simulacao ja esta em execucao.'},
            status=status.HTTP_409_CONFLICT,
        )

    service = EleitoralSimulationService(str(simulation_pk))

    def event_stream():
        try:
            for event in service.stream_simulation():
                yield _sse_event(event)
        except Exception as e:
            logger.exception(f'[{sim_type}_simulation] Erro no stream SSE: {e}')
            yield _sse_event({'event': 'error', 'content': str(e)})

    response = StreamingHttpResponse(
        _safe_event_stream(event_stream()),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_eleitoral_simulation(request, simulation_pk):
    """Inicia simulacao do Juiz Eleitoral (1a instancia) via SSE streaming."""
    return _start_eleitoral_view(request, simulation_pk, 'eleitoral', 'Juiz Eleitoral')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_tre_simulation(request, simulation_pk):
    """Inicia simulacao do TRE (7 membros) via SSE streaming."""
    return _start_eleitoral_view(request, simulation_pk, 'tre', 'TRE')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_tse_simulation(request, simulation_pk):
    """Inicia simulacao do TSE (7 ministros) via SSE streaming."""
    return _start_eleitoral_view(request, simulation_pk, 'tse', 'TSE')


# ── Justica do Trabalho Views ──────────────────────────────────────────


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_trabalho_simulation(request, simulation_pk):
    """
    Inicia simulacao da Vara do Trabalho (1a instancia) via SSE streaming.

    O servico TrabalhoSimulationService orquestra conciliacao obrigatoria (CLT art. 846),
    audiencia de instrucao, razoes finais, sentenca trabalhista com analise por pedido
    e relatorio estrategico.
    """
    try:
        simulation = Simulation.objects.get(
            pk=simulation_pk,
            user=request.user,
            simulation_type='trabalho',
        )
    except Simulation.DoesNotExist:
        return Response(
            {'error': 'Simulacao da Vara do Trabalho nao encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if simulation.status == 'completed':
        return Response(
            {'error': 'Esta simulacao ja foi concluida.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if simulation.status == 'running':
        return Response(
            {'error': 'Esta simulacao ja esta em execucao.'},
            status=status.HTTP_409_CONFLICT,
        )

    service = TrabalhoSimulationService(str(simulation_pk))

    def event_stream():
        try:
            for event in service.stream_simulation():
                yield _sse_event(event)
        except Exception as e:
            logger.exception(f'[trabalho_simulation] Erro no stream SSE: {e}')
            yield _sse_event({'event': 'error', 'content': str(e)})

    response = StreamingHttpResponse(
        _safe_event_stream(event_stream()),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_trt_simulation(request, simulation_pk):
    """
    Inicia simulacao do TRT (2a instancia trabalhista) via SSE streaming.

    O servico TRTSimulationService orquestra relatorio, votos dos 3
    desembargadores (Relator, Revisor, Vogal), ementa, proclamacao
    e relatorio estrategico no contexto trabalhista.
    """
    try:
        simulation = Simulation.objects.get(
            pk=simulation_pk,
            user=request.user,
            simulation_type='trt',
        )
    except Simulation.DoesNotExist:
        return Response(
            {'error': 'Simulacao do TRT nao encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if simulation.status == 'completed':
        return Response(
            {'error': 'Esta simulacao ja foi concluida.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if simulation.status == 'running':
        return Response(
            {'error': 'Esta simulacao ja esta em execucao.'},
            status=status.HTTP_409_CONFLICT,
        )

    service = TRTSimulationService(str(simulation_pk))

    def event_stream():
        try:
            for event in service.stream_simulation():
                yield _sse_event(event)
        except Exception as e:
            logger.exception(f'[trt_simulation] Erro no stream SSE: {e}')
            yield _sse_event({'event': 'error', 'content': str(e)})

    response = StreamingHttpResponse(
        _safe_event_stream(event_stream()),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_tst_simulation(request, simulation_pk):
    """
    Inicia simulacao do TST (Tribunal Superior do Trabalho) via SSE streaming.

    O servico TSTSimulationService orquestra relatorio, votos individuais
    dos ministros, proclamacao do resultado e relatorio estrategico
    no contexto de Recurso de Revista e materia trabalhista.
    """
    try:
        simulation = Simulation.objects.get(
            pk=simulation_pk,
            user=request.user,
            simulation_type='tst',
        )
    except Simulation.DoesNotExist:
        return Response(
            {'error': 'Simulacao do TST nao encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if simulation.status == 'completed':
        return Response(
            {'error': 'Esta simulacao ja foi concluida.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if simulation.status == 'running':
        return Response(
            {'error': 'Esta simulacao ja esta em execucao.'},
            status=status.HTTP_409_CONFLICT,
        )

    service = TSTSimulationService(str(simulation_pk))

    def event_stream():
        try:
            for event in service.stream_simulation():
                yield _sse_event(event)
        except Exception as e:
            logger.exception(f'[tst_simulation] Erro no stream SSE: {e}')
            yield _sse_event({'event': 'error', 'content': str(e)})

    response = StreamingHttpResponse(
        _safe_event_stream(event_stream()),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


# ── Turma Recursal Views ─────────────────────────────────────────────


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_turma_recursal_simulation(request, simulation_pk):
    """Inicia simulacao de Turma Recursal (Juizados Especiais) via SSE streaming."""
    try:
        simulation = Simulation.objects.get(
            pk=simulation_pk,
            user=request.user,
            simulation_type='turma_recursal',
        )
    except Simulation.DoesNotExist:
        return Response(
            {'error': 'Simulacao de Turma Recursal nao encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if simulation.status == 'completed':
        return Response(
            {'error': 'Esta simulacao ja foi concluida.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if simulation.status == 'running':
        return Response(
            {'error': 'Esta simulacao ja esta em execucao.'},
            status=status.HTTP_409_CONFLICT,
        )

    service = TurmaRecursalSimulationService(str(simulation_pk))

    def event_stream():
        try:
            for event in service.stream_simulation():
                yield _sse_event(event)
        except Exception as e:
            logger.exception(f'[turma_recursal_simulation] Erro no stream SSE: {e}')
            yield _sse_event({'event': 'error', 'content': str(e)})

    response = StreamingHttpResponse(
        _safe_event_stream(event_stream()),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


# ── Justica Militar Views ────────────────────────────────────────────


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_militar_simulation(request, simulation_pk):
    """Inicia simulacao da Auditoria de Justica Militar (1a instancia) via SSE streaming."""
    try:
        simulation = Simulation.objects.get(
            pk=simulation_pk,
            user=request.user,
            simulation_type='militar',
        )
    except Simulation.DoesNotExist:
        return Response(
            {'error': 'Simulacao de Justica Militar nao encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if simulation.status == 'completed':
        return Response(
            {'error': 'Esta simulacao ja foi concluida.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if simulation.status == 'running':
        return Response(
            {'error': 'Esta simulacao ja esta em execucao.'},
            status=status.HTTP_409_CONFLICT,
        )

    service = MilitarSimulationService(str(simulation_pk))

    def event_stream():
        try:
            for event in service.stream_simulation():
                yield _sse_event(event)
        except Exception as e:
            logger.exception(f'[militar_simulation] Erro no stream SSE: {e}')
            yield _sse_event({'event': 'error', 'content': str(e)})

    response = StreamingHttpResponse(
        _safe_event_stream(event_stream()),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_stm_simulation(request, simulation_pk):
    """Inicia simulacao do Superior Tribunal Militar (STM) via SSE streaming."""
    try:
        simulation = Simulation.objects.get(
            pk=simulation_pk,
            user=request.user,
            simulation_type='stm',
        )
    except Simulation.DoesNotExist:
        return Response(
            {'error': 'Simulacao do STM nao encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if simulation.status == 'completed':
        return Response(
            {'error': 'Esta simulacao ja foi concluida.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if simulation.status == 'running':
        return Response(
            {'error': 'Esta simulacao ja esta em execucao.'},
            status=status.HTTP_409_CONFLICT,
        )

    service = STMSimulationService(str(simulation_pk))

    def event_stream():
        try:
            for event in service.stream_simulation():
                yield _sse_event(event)
        except Exception as e:
            logger.exception(f'[stm_simulation] Erro no stream SSE: {e}')
            yield _sse_event({'event': 'error', 'content': str(e)})

    response = StreamingHttpResponse(
        _safe_event_stream(event_stream()),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response

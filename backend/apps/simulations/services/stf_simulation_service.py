"""
STFSimulationService — Simula julgamento colegiado do STF.

Fases:
  1. Relatório do Relator (resumo do caso)
  2. Voto do Relator
  3. Votos dos demais ministros (loop)
  4. Proclamação do resultado
  5. Relatório estratégico
"""
import json
import logging
import time
from typing import Dict, Generator, List, Optional

from ..models import Simulation, MinisterProfile, CourtVote

logger = logging.getLogger(__name__)

SIMULATION_PROVIDER = 'watsonx'
SIMULATION_MODEL = 'mistralai/mistral-medium-2505'
SIMULATION_TEMPERATURE = 0.6
SIMULATION_MAX_TOKENS = 4096


class STFSimulationService:
    """Simula um julgamento colegiado do STF com votos individuais dos ministros."""

    def __init__(self, simulation_id: str):
        self.simulation = Simulation.objects.get(id=simulation_id)
        self.documents = list(self.simulation.documents.all())
        self.config = self.simulation.config or {}

        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService
        self.llm = UnifiedLLMService()

        self.provider = self.config.get('provider', SIMULATION_PROVIDER)
        self.model = self.config.get('model', SIMULATION_MODEL)

        self.ministers = self._load_ministers()
        self.relator = self._pick_relator()

    def _load_ministers(self) -> List[MinisterProfile]:
        """Carrega ministros com base na composição configurada."""
        composition = self.config.get('composition', 'plenario')
        qs = MinisterProfile.objects.filter(court_type='STF', is_active=True)

        if composition == '1a_turma':
            qs = qs.filter(turma__in=['1a Turma', 'Presidente'])
        elif composition == '2a_turma':
            qs = qs.filter(turma__in=['2a Turma', 'Vice-Presidente'])
        # plenario: todos

        return list(qs)

    def _pick_relator(self) -> Optional[MinisterProfile]:
        """Seleciona o relator (configurado ou primeiro da lista)."""
        relator_name = self.config.get('relator')
        if relator_name:
            for m in self.ministers:
                if m.name == relator_name:
                    return m
        return self.ministers[0] if self.ministers else None

    # ── API principal ───────────────────────────────────────────────────────

    def stream_simulation(self) -> Generator[Dict, None, None]:
        """Generator que produz eventos SSE para a simulação do STF."""

        self.simulation.status = 'running'
        self.simulation.save(update_fields=['status'])

        try:
            case_context = self._build_case_context()

            if not case_context.strip():
                yield self._event(
                    'error',
                    'Nenhum documento ou informação do caso encontrado. '
                    'Preencha a descrição do caso antes de iniciar.',
                )
                return

            if not self.ministers:
                yield self._event('error', 'Nenhum ministro encontrado para a composição selecionada.')
                return

            total_ministers = len(self.ministers)
            relator = self.relator or self.ministers[0]

            # Emit minister list
            yield self._event('ministers', '', extra={
                'ministers': [
                    {
                        'name': m.name,
                        'turma': m.turma,
                        'philosophy': m.judicial_philosophy,
                        'is_relator': m.id == relator.id,
                    }
                    for m in self.ministers
                ],
            })

            # Phase 1: Relatório do Relator
            yield self._progress_event('relatorio', 'Relatório do Relator', f'Min. {relator.name} elaborando relatório...', 10)
            yield self._event('phase', 'Relatório do Relator')
            relatorio_text = yield from self._phase_relatorio(case_context, relator)

            # Phase 2: Voto do Relator
            progress_per_minister = 60 // total_ministers
            yield self._progress_event('voto_relator', 'Voto do Relator', f'Min. {relator.name} proferindo voto...', 20)
            yield self._event('phase', f'Voto do Min. {relator.name} (Relator)')
            relator_vote = yield from self._phase_vote(case_context, relator, relatorio_text, is_relator=True)

            votes = [{
                'minister': relator.name,
                'vote': relator_vote['vote'],
                'is_relator': True,
            }]
            yield self._event('vote_result', '', extra={
                'minister': relator.name,
                'vote': relator_vote['vote'],
                'is_relator': True,
                'votes_so_far': votes,
            })

            # Phase 3: Votos dos demais
            other_ministers = [m for m in self.ministers if m.id != relator.id]
            for idx, minister in enumerate(other_ministers):
                progress = 20 + ((idx + 1) * progress_per_minister)
                yield self._progress_event(
                    f'voto_{idx}',
                    f'Voto do Min. {minister.name}',
                    f'Min. {minister.name} proferindo voto...',
                    min(progress, 80),
                )
                yield self._event('phase', f'Voto do Min. {minister.name}')
                minister_vote = yield from self._phase_vote(
                    case_context, minister, relatorio_text,
                    is_relator=False,
                    previous_votes=votes,
                )
                votes.append({
                    'minister': minister.name,
                    'vote': minister_vote['vote'],
                    'is_relator': False,
                })
                yield self._event('vote_result', '', extra={
                    'minister': minister.name,
                    'vote': minister_vote['vote'],
                    'is_relator': False,
                    'votes_so_far': votes,
                })

            # Phase 4: Proclamação
            yield self._progress_event('proclamacao', 'Proclamação do Resultado', 'Contabilizando votos...', 85)
            yield self._event('phase', 'Proclamação do Resultado')
            proclamacao = yield from self._phase_proclamacao(votes, case_context)

            # Phase 5: Relatório estratégico
            yield self._progress_event('report', 'Relatório Estratégico', 'Analisando implicações...', 95)
            yield self._event('phase', 'Relatório Estratégico')
            strategic = yield from self._phase_strategic_report(case_context, votes, proclamacao)

            # Persist
            provimento_count = sum(1 for v in votes if 'provimento' in v['vote'].lower() or 'procedente' in v['vote'].lower() or 'deferido' in v['vote'].lower())
            desprovimento_count = len(votes) - provimento_count

            self.simulation.status = 'completed'
            self.simulation.result = {
                'composition': self.config.get('composition', 'plenario'),
                'action_type': self.config.get('action_type', ''),
                'relator': relator.name,
                'votes': votes,
                'provimento': provimento_count,
                'desprovimento': desprovimento_count,
                'resultado': 'Provido' if provimento_count > desprovimento_count else 'Desprovido',
                'relatorio': relatorio_text,
                'proclamacao': proclamacao,
                'strategic_report': strategic,
            }
            self.simulation.save(update_fields=['status', 'result'])

            yield self._progress_event('complete', 'Concluído', 'Simulação finalizada', 100)
            yield self._event('complete', 'Simulação do STF concluída.')

        except Exception as e:
            logger.exception(f'[stf_simulation] Erro na simulação {self.simulation.id}: {e}')
            self.simulation.status = 'failed'
            self.simulation.save(update_fields=['status'])
            yield self._event('error', f'Erro na simulação: {str(e)}')

    # ── Fases ───────────────────────────────────────────────────────────────

    def _phase_relatorio(self, case_context: str, relator: MinisterProfile) -> Generator[Dict, None, str]:
        """Gera o relatório do caso pelo relator."""
        action_type = self.config.get('action_type', 'RE')

        prompt = (
            f"Você é o Ministro {relator.name} do Supremo Tribunal Federal.\n"
            f"Ação: {action_type}\n\n"
            f"Elabore o RELATÓRIO do caso a seguir, no formato tradicional do STF:\n"
            f"1. Identificação das partes\n"
            f"2. Síntese dos fatos\n"
            f"3. Questão constitucional em debate\n"
            f"4. Argumentos das partes\n"
            f"5. Parecer do PGR/AGU (se aplicável)\n\n"
            f"CASO:\n{case_context}\n\n"
            f"Seja objetivo e técnico, no estilo dos relatórios do STF."
        )

        full_text = ''
        for chunk_text in self._stream_llm(prompt, 'Você é um ministro do STF elaborando relatório.'):
            full_text += chunk_text
            yield self._event('relatorio', chunk_text)

        return full_text

    def _phase_vote(
        self,
        case_context: str,
        minister: MinisterProfile,
        relatorio: str,
        is_relator: bool = False,
        previous_votes: Optional[List[Dict]] = None,
    ) -> Generator[Dict, None, Dict]:
        """Gera o voto de um ministro."""
        profile_data = minister.profile_data or {}
        philosophy = minister.get_judicial_philosophy_display()
        specialties = ', '.join(minister.specialty_areas or [])
        positions = '\n'.join(f'- {p}' for p in (minister.notable_positions or []))
        tendencies = ', '.join(profile_data.get('tendencies', []))
        writing_style = profile_data.get('writing_style', '')
        framework = profile_data.get('key_framework', '')

        action_type = self.config.get('action_type', 'RE')

        previous_context = ''
        if previous_votes:
            prev_lines = [f"- Min. {v['minister']}: {v['vote']}" for v in previous_votes]
            previous_context = f"\nVOTOS JÁ PROFERIDOS:\n" + '\n'.join(prev_lines) + '\n'

        prompt = (
            f"Você é o Ministro {minister.name} do Supremo Tribunal Federal.\n"
            f"Filosofia judicial: {philosophy}\n"
            f"Especialidades: {specialties}\n"
            f"Estilo de escrita: {writing_style}\n"
            f"Framework decisório: {framework}\n"
            f"Tendências: {tendencies}\n"
            f"Posições notáveis:\n{positions}\n\n"
            f"Ação: {action_type}\n\n"
            f"RELATÓRIO DO CASO:\n{relatorio}\n\n"
            f"CASO COMPLETO:\n{case_context}\n"
            f"{previous_context}\n"
            f"{'Você é o RELATOR deste caso.' if is_relator else 'Profira seu voto após o relator.'}\n\n"
            f"PROFIRA SEU VOTO no estilo característico do Min. {minister.name}:\n"
            f"1. Fundamente com base na sua filosofia judicial ({philosophy})\n"
            f"2. Cite legislação e jurisprudência relevante\n"
            f"3. Ao final, DECLARE EXPRESSAMENTE se vota pelo PROVIMENTO ou DESPROVIMENTO "
            f"(ou PROCEDÊNCIA/IMPROCEDÊNCIA conforme a ação)\n"
            f"4. Se divergir do relator, justifique a divergência\n\n"
            f"Mantenha o tom e estilo de escrita: {writing_style}"
        )

        full_text = ''
        for chunk_text in self._stream_llm(
            prompt,
            f'Você é o Min. {minister.name} do STF proferindo voto. '
            f'Filosofia: {philosophy}. Estilo: {writing_style}.',
        ):
            full_text += chunk_text
            yield self._event('vote_text', chunk_text, extra={
                'minister': minister.name,
                'is_relator': is_relator,
            })

        # Detect vote direction
        vote_direction = self._detect_vote(full_text)

        # Save CourtVote (only if minister is persisted in DB)
        if minister.pk:
            CourtVote.objects.create(
                simulation=self.simulation,
                voter_name=minister.name,
                voter_role='ministro',
                minister_profile=minister,
                vote=vote_direction,
                vote_text=full_text,
                is_relator=is_relator,
                is_dissent=(
                    not is_relator and previous_votes and
                    vote_direction != previous_votes[0].get('vote', '')
                ),
            )

        return {'vote': vote_direction, 'text': full_text}

    def _phase_proclamacao(self, votes: List[Dict], case_context: str) -> Generator[Dict, None, str]:
        """Gera a proclamação do resultado pelo presidente."""
        votes_summary = '\n'.join(f"- Min. {v['minister']}: {v['vote']}" for v in votes)

        provimento = sum(1 for v in votes if 'provimento' in v['vote'].lower() or 'procedente' in v['vote'].lower() or 'deferido' in v['vote'].lower())
        desprovimento = len(votes) - provimento

        prompt = (
            f"Você é o Presidente do STF proclamando o resultado de um julgamento.\n\n"
            f"VOTOS:\n{votes_summary}\n\n"
            f"PLACAR: {provimento} x {desprovimento}\n\n"
            f"Proclame o resultado no formato oficial do STF:\n"
            f"1. Resumo do placar\n"
            f"2. Resultado (provido/desprovido, procedente/improcedente)\n"
            f"3. Quem votou com o relator e quem divergiu\n"
            f"4. Determinações decorrentes do julgamento\n"
            f"5. Tese fixada (se aplicável)\n\n"
            f"Use o formato oficial: 'O Tribunal, por maioria/unanimidade...'"
        )

        full_text = ''
        for chunk_text in self._stream_llm(prompt, 'Você é o Presidente do STF proclamando resultado.'):
            full_text += chunk_text
            yield self._event('proclamacao', chunk_text)

        return full_text

    def _phase_strategic_report(
        self, case_context: str, votes: List[Dict], proclamacao: str,
    ) -> Generator[Dict, None, str]:
        """Gera relatório estratégico com base no resultado."""
        votes_summary = '\n'.join(f"- Min. {v['minister']}: {v['vote']}" for v in votes)

        provimento = sum(1 for v in votes if 'provimento' in v['vote'].lower() or 'procedente' in v['vote'].lower() or 'deferido' in v['vote'].lower())
        is_victory = provimento > (len(votes) - provimento)

        prompt = (
            f"Você é um consultor jurídico estratégico de alto nível.\n"
            f"Analise o resultado do julgamento no STF:\n\n"
            f"CASO:\n{case_context}\n\n"
            f"PLACAR:\n{votes_summary}\n\n"
            f"PROCLAMAÇÃO:\n{proclamacao}\n\n"
            f"{'O cliente VENCEU.' if is_victory else 'O cliente PERDEU.'}\n\n"
            f"Produza um RELATÓRIO ESTRATÉGICO:\n"
            f"1. Análise do placar e votos vencedores/vencidos\n"
            f"2. Ministros-chave e fundamentos decisivos\n"
            f"3. Votos divergentes e potencial de embargos\n"
            f"4. Impacto da decisão (tese fixada, repercussão geral)\n"
            f"5. Providências imediatas e próximos passos\n"
            f"6. Análise de risco recursal (embargos de declaração, etc.)\n\n"
            f"Seja específico e prático."
        )

        full_text = ''
        for chunk_text in self._stream_llm(
            prompt,
            'Você é um consultor jurídico estratégico especializado em STF.',
        ):
            full_text += chunk_text
            yield self._event('relatorio_estrategico', chunk_text, extra={
                'type': 'strategic_report',
                'is_victory': is_victory,
            })

        return full_text

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _detect_vote(self, text: str) -> str:
        """Detecta direção do voto no texto."""
        lower = text.lower()
        # Check for negative first (desprovimento, improcedência)
        if 'nego provimento' in lower or 'desprovimento' in lower or 'desprovido' in lower:
            return 'desprovimento'
        if 'improcedente' in lower or 'improcedência' in lower:
            return 'improcedente'
        if 'indefiro' in lower or 'indeferido' in lower:
            return 'indeferido'
        # Positive
        if 'dou provimento' in lower or 'provimento' in lower or 'provido' in lower:
            return 'provimento'
        if 'procedente' in lower or 'procedência' in lower:
            return 'procedente'
        if 'defiro' in lower or 'deferido' in lower:
            return 'deferido'
        # Partial
        if 'parcial' in lower:
            return 'provimento_parcial'
        return 'indeterminado'

    def _build_case_context(self) -> str:
        """Monta contexto do caso a partir de documentos e config."""
        texts = []
        for doc in self.documents:
            if doc.extracted_text:
                label = doc.title
                try:
                    label += f' ({doc.get_document_type_display()})'
                except Exception:
                    logger.debug("get_document_type_display failed for doc %s", doc.id)
                texts.append(f"## {label}\n{doc.extracted_text}")

        doc_context = '\n\n---\n\n'.join(texts)

        # Also include description from config
        extra = []
        if self.config.get('case_description'):
            extra.append(f"Descrição do caso:\n{self.config['case_description']}")
        if self.config.get('action_type'):
            extra.append(f"Tipo de ação: {self.config['action_type']}")
        if self.config.get('case_text'):
            extra.append(f"Texto do caso:\n{self.config['case_text']}")

        config_context = '\n'.join(extra)

        if doc_context and config_context:
            return f"{config_context}\n\n---\n\n{doc_context}"
        return doc_context or config_context

    def _stream_llm(self, prompt: str, system_prompt: str) -> Generator[str, None, None]:
        """Helper to stream LLM and yield text chunks."""
        _buf: list[str] = []
        _last_flush = time.time()

        for chunk, final_result in self.llm.generate_stream(
            user_prompt=prompt,
            system_prompt=system_prompt,
            temperature=SIMULATION_TEMPERATURE,
            max_tokens=SIMULATION_MAX_TOKENS,
            provider=self.provider,
            model=self.model,
        ):
            if final_result is not None:
                break
            if chunk:
                _buf.append(chunk)
                _now = time.time()
                if _now - _last_flush >= 0.15 or len(_buf) >= 20:
                    text = ''.join(_buf)
                    _buf = []
                    _last_flush = _now
                    yield text

        if _buf:
            yield ''.join(_buf)

    def _event(
        self,
        event_type: str,
        content: str,
        extra: Optional[Dict] = None,
    ) -> Dict:
        """Formata evento SSE."""
        event = {
            'event': event_type,
            'content': content,
        }
        if extra:
            event.update(extra)
        return event

    def _progress_event(
        self,
        phase: str,
        label: str,
        description: str,
        progress: int,
    ) -> Dict:
        """Emite evento de mudança de fase com progresso."""
        return {
            'event': 'progress',
            'content': label,
            'type': 'phase_change',
            'phase': phase,
            'label': label,
            'description': description,
            'progress': progress,
        }

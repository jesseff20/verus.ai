"""
STMSimulationService -- Simula julgamento colegiado do Superior Tribunal Militar.

Composicao: 15 ministros
  - 5 civis (3 advogados + 1 juiz auditor + 1 membro do MPM)
  - 10 militares (3 Exercito + 4 Marinha + 3 Aeronautica -- generais/almirantes)

Fases:
  1. Relatorio do Relator
  2. Voto do Relator
  3. Votos dos demais ministros
  4. Proclamacao do resultado
  5. Relatorio Estrategico
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


class STMSimulationService:
    """Simula um julgamento colegiado do STM com 15 ministros."""

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
        """Carrega ministros do STM."""
        qs = MinisterProfile.objects.filter(court_type='STM', is_active=True)
        # Exclui perfis de Auditoria (1a instancia)
        qs = qs.exclude(turma__icontains='Auditoria')
        return list(qs)

    def _pick_relator(self) -> Optional[MinisterProfile]:
        """Seleciona o relator."""
        relator_name = self.config.get('relator')
        if relator_name:
            for m in self.ministers:
                if m.name == relator_name:
                    return m
        return self.ministers[0] if self.ministers else None

    # -- API principal ---

    def stream_simulation(self) -> Generator[Dict, None, None]:
        """Generator que produz eventos SSE para a simulacao do STM."""

        self.simulation.status = 'running'
        self.simulation.save(update_fields=['status'])

        try:
            case_context = self._build_case_context()

            if not case_context.strip():
                yield self._event(
                    'error',
                    'Nenhum documento ou informacao do caso encontrado. '
                    'Preencha a descricao do caso antes de iniciar.',
                )
                return

            if not self.ministers:
                yield self._event('error', 'Nenhum ministro do STM encontrado. Execute seed_stm_ministers.')
                return

            total_ministers = len(self.ministers)
            relator = self.relator or self.ministers[0]

            # Emit minister list
            yield self._event('ministers', '', extra={
                'ministers': [
                    {
                        'name': m.name,
                        'turma': m.turma or '',
                        'philosophy': m.judicial_philosophy,
                        'is_relator': m.id == relator.id if m.pk and relator.pk else m.name == relator.name,
                        'category': (m.profile_data or {}).get('category', ''),
                    }
                    for m in self.ministers
                ],
            })

            # Phase 1: Relatorio do Relator
            yield self._progress_event('relatorio', 'Relatorio do Relator', f'Min. {relator.name} elaborando relatorio...', 10)
            yield self._event('phase', 'Relatorio do Relator')
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
            other_ministers = [m for m in self.ministers if m.name != relator.name]
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

            # Phase 4: Proclamacao
            yield self._progress_event('proclamacao', 'Proclamacao do Resultado', 'Contabilizando votos...', 85)
            yield self._event('phase', 'Proclamacao do Resultado')
            proclamacao = yield from self._phase_proclamacao(votes, case_context)

            # Phase 5: Relatorio Estrategico
            yield self._progress_event('report', 'Relatorio Estrategico', 'Analisando implicacoes...', 95)
            yield self._event('phase', 'Relatorio Estrategico')
            strategic = yield from self._phase_strategic_report(case_context, votes, proclamacao)

            # Persist
            provimento_count = sum(1 for v in votes if 'provimento' in v['vote'].lower() or 'procedente' in v['vote'].lower() or 'deferido' in v['vote'].lower() or 'absolvicao' in v['vote'].lower())
            desprovimento_count = len(votes) - provimento_count

            self.simulation.status = 'completed'
            self.simulation.result = {
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

            yield self._progress_event('complete', 'Concluido', 'Simulacao finalizada', 100)
            yield self._event('complete', 'Simulacao do STM concluida.')

        except Exception as e:
            logger.exception(f'[stm_simulation] Erro na simulacao {self.simulation.id}: {e}')
            self.simulation.status = 'failed'
            self.simulation.save(update_fields=['status'])
            yield self._event('error', f'Erro na simulacao: {str(e)}')

    # -- Fases ---

    def _phase_relatorio(self, case_context: str, relator: MinisterProfile) -> Generator[Dict, None, str]:
        """Gera o relatorio do caso pelo relator."""
        action_type = self.config.get('action_type', 'Apelacao Militar')
        category = (relator.profile_data or {}).get('category', 'civil')

        prompt = (
            f"Voce e o Ministro {relator.name} do Superior Tribunal Militar (STM).\n"
            f"Voce e um ministro {'civil (togado)' if 'civil' in category.lower() else 'militar'}.\n"
            f"Recurso/Acao: {action_type}\n\n"
            f"Elabore o RELATORIO do caso, no formato do STM:\n"
            f"1. Identificacao das partes e do recurso\n"
            f"2. Sintese dos fatos (crime militar)\n"
            f"3. Decisao da Auditoria Militar (1a instancia)\n"
            f"4. Razoes recursais\n"
            f"5. Parecer do Ministerio Publico Militar\n\n"
            f"CASO:\n{case_context}\n\n"
            f"Seja tecnico, no estilo do STM."
        )

        full_text = ''
        for chunk_text in self._stream_llm(prompt, 'Voce e um ministro do STM elaborando relatorio.'):
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
        """Gera o voto de um ministro do STM."""
        profile_data = minister.profile_data or {}
        philosophy = minister.get_judicial_philosophy_display()
        specialties = ', '.join(minister.specialty_areas or [])
        positions = '\n'.join(f'- {p}' for p in (minister.notable_positions or []))
        tendencies = ', '.join(profile_data.get('tendencies', []))
        writing_style = profile_data.get('writing_style', '')
        framework = profile_data.get('key_framework', '')
        category = profile_data.get('category', '')

        action_type = self.config.get('action_type', 'Apelacao Militar')

        previous_context = ''
        if previous_votes:
            prev_lines = [f"- Min. {v['minister']}: {v['vote']}" for v in previous_votes]
            previous_context = f"\nVOTOS JA PROFERIDOS:\n" + '\n'.join(prev_lines) + '\n'

        minister_type = 'civil (togado)' if 'civil' in category.lower() else 'militar'

        prompt = (
            f"Voce e o Ministro {minister.name} do Superior Tribunal Militar.\n"
            f"Tipo: Ministro {minister_type}\n"
            f"Filosofia judicial: {philosophy}\n"
            f"Especialidades: {specialties}\n"
            f"Estilo: {writing_style}\n"
            f"Framework: {framework}\n"
            f"Tendencias: {tendencies}\n"
            f"Posicoes notaveis:\n{positions}\n\n"
            f"Recurso/Acao: {action_type}\n\n"
            f"RELATORIO:\n{relatorio}\n\n"
            f"CASO:\n{case_context}\n"
            f"{previous_context}\n"
            f"{'Voce e o RELATOR deste caso.' if is_relator else 'Profira seu voto apos o relator.'}\n\n"
            f"PROFIRA SEU VOTO:\n"
            f"1. Fundamente com base no CPM, CPPM e jurisprudencia do STM\n"
            f"2. {'Considere a perspectiva militar' if 'militar' in minister_type else 'Fundamente juridicamente'}\n"
            f"3. Ao final, DECLARE: PROVIMENTO ou DESPROVIMENTO "
            f"(ou ABSOLVICAO/CONDENACAO conforme o caso)\n"
            f"4. Se divergir do relator, justifique\n\n"
            f"Estilo: {writing_style}"
        )

        full_text = ''
        for chunk_text in self._stream_llm(
            prompt,
            f'Voce e Min. {minister.name} do STM ({minister_type}). '
            f'Filosofia: {philosophy}.',
        ):
            full_text += chunk_text
            yield self._event('vote_text', chunk_text, extra={
                'minister': minister.name,
                'is_relator': is_relator,
            })

        vote_direction = self._detect_vote(full_text)

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
        """Gera a proclamacao do resultado."""
        votes_summary = '\n'.join(f"- Min. {v['minister']}: {v['vote']}" for v in votes)

        provimento = sum(1 for v in votes if 'provimento' in v['vote'].lower() or 'procedente' in v['vote'].lower() or 'deferido' in v['vote'].lower() or 'absolvicao' in v['vote'].lower())
        desprovimento = len(votes) - provimento

        prompt = (
            f"Voce e o Presidente do Superior Tribunal Militar proclamando o resultado.\n\n"
            f"VOTOS:\n{votes_summary}\n\n"
            f"PLACAR: {provimento} x {desprovimento}\n\n"
            f"Proclame o resultado no formato oficial do STM:\n"
            f"1. Resumo do placar\n"
            f"2. Resultado\n"
            f"3. Quem votou com o relator e quem divergiu\n"
            f"4. Determinacoes\n\n"
            f"Use o formato oficial: 'O Tribunal, por maioria/unanimidade...'"
        )

        full_text = ''
        for chunk_text in self._stream_llm(prompt, 'Voce e o Presidente do STM proclamando resultado.'):
            full_text += chunk_text
            yield self._event('proclamacao', chunk_text)

        return full_text

    def _phase_strategic_report(
        self, case_context: str, votes: List[Dict], proclamacao: str,
    ) -> Generator[Dict, None, str]:
        """Gera relatorio estrategico."""
        votes_summary = '\n'.join(f"- Min. {v['minister']}: {v['vote']}" for v in votes)

        provimento = sum(1 for v in votes if 'provimento' in v['vote'].lower() or 'procedente' in v['vote'].lower() or 'deferido' in v['vote'].lower() or 'absolvicao' in v['vote'].lower())
        is_victory = provimento > (len(votes) - provimento)

        prompt = (
            f"Voce e um consultor juridico estrategico especializado em Justica Militar.\n"
            f"Analise o resultado do julgamento no STM:\n\n"
            f"CASO:\n{case_context}\n\n"
            f"PLACAR:\n{votes_summary}\n\n"
            f"PROCLAMACAO:\n{proclamacao}\n\n"
            f"{'O cliente VENCEU.' if is_victory else 'O cliente PERDEU.'}\n\n"
            f"Produza um RELATORIO ESTRATEGICO:\n"
            f"1. Analise do placar (civis vs militares)\n"
            f"2. Ministros-chave e fundamentos decisivos\n"
            f"3. Votos divergentes e potencial de embargos\n"
            f"4. Possibilidade de RE ao STF (materia constitucional)\n"
            f"5. Consequencias administrativas e carreira militar\n"
            f"6. Providencias imediatas e proximos passos\n\n"
            f"Seja especifico e pratico."
        )

        full_text = ''
        for chunk_text in self._stream_llm(
            prompt,
            'Voce e um consultor juridico estrategico especializado em STM.',
        ):
            full_text += chunk_text
            yield self._event('relatorio_estrategico', chunk_text, extra={
                'type': 'strategic_report',
                'is_victory': is_victory,
            })

        return full_text

    # -- Helpers ---

    def _detect_vote(self, text: str) -> str:
        """Detecta direcao do voto."""
        lower = text.lower()
        if 'nego provimento' in lower or 'desprovimento' in lower or 'desprovido' in lower:
            return 'desprovimento'
        if 'condenacao' in lower or 'condeno' in lower or 'culpado' in lower:
            return 'condenacao'
        if 'improcedente' in lower:
            return 'improcedente'
        if 'absolvicao' in lower or 'absolvo' in lower or 'inocente' in lower:
            return 'absolvicao'
        if 'dou provimento' in lower or 'provimento' in lower or 'provido' in lower:
            return 'provimento'
        if 'procedente' in lower:
            return 'procedente'
        if 'parcial' in lower:
            return 'provimento_parcial'
        return 'indeterminado'

    def _build_case_context(self) -> str:
        """Monta contexto do caso."""
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

        extra = []
        if self.config.get('case_description'):
            extra.append(f"Descricao do caso:\n{self.config['case_description']}")
        if self.config.get('action_type'):
            extra.append(f"Tipo de acao/recurso: {self.config['action_type']}")
        if self.config.get('case_text'):
            extra.append(f"Texto do caso:\n{self.config['case_text']}")

        config_context = '\n'.join(extra)

        if doc_context and config_context:
            return f"{config_context}\n\n---\n\n{doc_context}"
        return doc_context or config_context

    def _stream_llm(self, prompt: str, system_prompt: str) -> Generator[str, None, None]:
        """Helper to stream LLM."""
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

    def _event(self, event_type: str, content: str, extra: Optional[Dict] = None) -> Dict:
        event = {'event': event_type, 'content': content}
        if extra:
            event.update(extra)
        return event

    def _progress_event(self, phase: str, label: str, description: str, progress: int) -> Dict:
        return {
            'event': 'progress',
            'content': label,
            'type': 'phase_change',
            'phase': phase,
            'label': label,
            'description': description,
            'progress': progress,
        }

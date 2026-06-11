"""
TSTSimulationService -- Simula julgamento colegiado do TST (Tribunal Superior do Trabalho).

Composicao: 5 Ministros por Turma (8 turmas), SDI-1, SDI-2, SDC.
Input: Recurso de Revista (RR), Embargos, entre outros.

Fases:
  1. Relatorio do Relator
  2. Voto do Relator
  3. Votos dos demais ministros (loop)
  4. Proclamacao do resultado
  5. Relatorio estrategico
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


class TSTSimulationService:
    """Simula um julgamento colegiado do TST com votos individuais dos ministros."""

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
        """Carrega ministros do TST com base na composicao configurada."""
        composition = self.config.get('composition', '1a_turma')
        qs = MinisterProfile.objects.filter(court_type='TST', is_active=True)

        turma_map = {
            '1a_turma': '1a Turma',
            '2a_turma': '2a Turma',
            '3a_turma': '3a Turma',
            '4a_turma': '4a Turma',
            '5a_turma': '5a Turma',
            '6a_turma': '6a Turma',
            '7a_turma': '7a Turma',
            '8a_turma': '8a Turma',
            'sdi_1': 'SDI-1',
            'sdi_2': 'SDI-2',
            'sdc': 'SDC',
        }

        filter_val = turma_map.get(composition)
        if filter_val:
            qs = qs.filter(turma=filter_val)

        ministers = list(qs)

        if not ministers:
            ministers = self._create_generic_profiles(composition)

        return ministers

    def _create_generic_profiles(self, composition: str) -> List[MinisterProfile]:
        """Cria perfis genericos de ministros do TST."""
        count = 5
        turma = turma_map = {
            '1a_turma': '1a Turma',
            '2a_turma': '2a Turma',
            '3a_turma': '3a Turma',
            '4a_turma': '4a Turma',
            '5a_turma': '5a Turma',
            '6a_turma': '6a Turma',
            '7a_turma': '7a Turma',
            '8a_turma': '8a Turma',
            'sdi_1': 'SDI-1',
            'sdi_2': 'SDI-2',
            'sdc': 'SDC',
        }.get(composition, '1a Turma')

        if composition in ('sdi_1', 'sdi_2', 'sdc'):
            count = 7  # Secoes tem mais ministros

        generic_names = [
            ('Min. Carlos Eduardo Araujo', 'progressista', 'Protecionista e didatico, com forte fundamentacao na CLT'),
            ('Min. Maria Lucia Fernandes', 'centrista', 'Equilibrado e tecnico, analise detalhada de provas'),
            ('Min. Roberto Carlos Lima', 'conservador', 'Formal e processualista, enfase no onus da prova'),
            ('Min. Ana Paula Martins', 'pragmatico', 'Pragmatico e conciso, foco em sumulas'),
            ('Min. Jose Ricardo Santos', 'progressista', 'Garantista, valoriza o principio protetor'),
            ('Min. Claudia Beatriz Oliveira', 'centrista', 'Moderado, busca consenso'),
            ('Min. Paulo Henrique Costa', 'conservador', 'Legalista, prevalencia do negociado'),
        ]

        profiles = []
        for i in range(min(count, len(generic_names))):
            name, philosophy, style = generic_names[i]
            profile = MinisterProfile(
                court_type='TST',
                name=name,
                turma=turma,
                judicial_philosophy=philosophy,
                specialty_areas=['Direito do Trabalho', 'Direito Processual do Trabalho'],
                notable_positions=[],
                profile_data={
                    'writing_style': style,
                    'tendencies': [],
                    'key_framework': 'CLT, sumulas do TST e OJs da SDI',
                },
            )
            profiles.append(profile)

        return profiles

    def _pick_relator(self) -> Optional[MinisterProfile]:
        relator_name = self.config.get('relator')
        if relator_name:
            for m in self.ministers:
                if m.name == relator_name:
                    return m
        return self.ministers[0] if self.ministers else None

    # -- API principal ---

    def stream_simulation(self) -> Generator[Dict, None, None]:
        """Generator que produz eventos SSE para a simulacao do TST."""

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
                yield self._event('error', 'Nenhum ministro encontrado para a composicao selecionada.')
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
                        'is_relator': m == relator,
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
            other_ministers = [m for m in self.ministers if m != relator]
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

            # Phase 5: Relatorio estrategico
            yield self._progress_event('report', 'Relatorio Estrategico', 'Analisando implicacoes...', 95)
            yield self._event('phase', 'Relatorio Estrategico')
            strategic = yield from self._phase_strategic_report(case_context, votes, proclamacao)

            # Persist
            provimento_count = sum(1 for v in votes if 'provimento' in v['vote'].lower() or 'procedente' in v['vote'].lower() or 'deferido' in v['vote'].lower())
            desprovimento_count = len(votes) - provimento_count

            self.simulation.status = 'completed'
            self.simulation.result = {
                'composition': self.config.get('composition', '1a_turma'),
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
            yield self._event('complete', 'Simulacao do TST concluida.')

        except Exception as e:
            logger.exception(f'[tst_simulation] Erro na simulacao {self.simulation.id}: {e}')
            self.simulation.status = 'failed'
            self.simulation.save(update_fields=['status'])
            yield self._event('error', f'Erro na simulacao: {str(e)}')

    # -- Fases ---

    def _phase_relatorio(self, case_context: str, relator: MinisterProfile) -> Generator[Dict, None, str]:
        action_type = self.config.get('action_type', 'RR')

        prompt = (
            f"Voce e o Ministro {relator.name} do Tribunal Superior do Trabalho (TST).\n"
            f"Tipo de recurso: {action_type}\n\n"
            f"Elabore o RELATORIO do caso trabalhista, no formato tradicional do TST:\n"
            f"1. Identificacao das partes e do recurso\n"
            f"2. Sintese do acordao recorrido (TRT)\n"
            f"3. Razoes do recurso de revista\n"
            f"4. Contrarrazoes\n"
            f"5. Parecer do Ministerio Publico do Trabalho (se aplicavel)\n"
            f"6. Admissibilidade do recurso (art. 896 CLT)\n\n"
            f"CASO:\n{case_context}\n\n"
            f"Use terminologia trabalhista. O TST analisa violacao a CLT, leis trabalhistas, "
            f"sumulas vinculantes e divergencia jurisprudencial."
        )

        full_text = ''
        for chunk_text in self._stream_llm(prompt, 'Voce e um ministro do TST elaborando relatorio.'):
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
        profile_data = minister.profile_data or {}
        philosophy = minister.get_judicial_philosophy_display()
        specialties = ', '.join(minister.specialty_areas or [])
        positions = '\n'.join(f'- {p}' for p in (minister.notable_positions or []))
        tendencies = ', '.join(profile_data.get('tendencies', []))
        writing_style = profile_data.get('writing_style', '')
        framework = profile_data.get('key_framework', '')

        action_type = self.config.get('action_type', 'RR')

        previous_context = ''
        if previous_votes:
            prev_lines = [f"- Min. {v['minister']}: {v['vote']}" for v in previous_votes]
            previous_context = f"\nVOTOS JA PROFERIDOS:\n" + '\n'.join(prev_lines) + '\n'

        prompt = (
            f"Voce e o Ministro {minister.name} do Tribunal Superior do Trabalho (TST).\n"
            f"Filosofia judicial: {philosophy}\n"
            f"Especialidades: {specialties}\n"
            f"Estilo de escrita: {writing_style}\n"
            f"Framework decisorio: {framework}\n"
            f"Tendencias: {tendencies}\n"
            f"Posicoes notaveis:\n{positions}\n\n"
            f"Tipo de recurso: {action_type}\n\n"
            f"RELATORIO DO CASO:\n{relatorio}\n\n"
            f"CASO COMPLETO:\n{case_context}\n"
            f"{previous_context}\n"
            f"{'Voce e o RELATOR deste recurso.' if is_relator else 'Profira seu voto apos o relator.'}\n\n"
            f"PROFIRA SEU VOTO no estilo do TST:\n"
            f"1. Fundamente com CLT, sumulas do TST, OJs da SDI\n"
            f"2. Analise se houve violacao a lei trabalhista ou divergencia jurisprudencial\n"
            f"3. Verifique os pressupostos de admissibilidade do recurso (art. 896 CLT)\n"
            f"4. Ao final, DECLARE EXPRESSAMENTE se vota pelo CONHECIMENTO e PROVIMENTO, "
            f"CONHECIMENTO e DESPROVIMENTO, ou NAO CONHECIMENTO do recurso\n"
            f"5. Se divergir do relator, justifique a divergencia\n\n"
            f"IMPORTANTE: O TST analisa materia trabalhista (CLT, sumulas, OJs). "
            f"Foque na legislacao trabalhista e jurisprudencia do TST.\n\n"
            f"Mantenha o tom: {writing_style}"
        )

        full_text = ''
        for chunk_text in self._stream_llm(
            prompt,
            f'Voce e o Min. {minister.name} do TST proferindo voto. '
            f'Filosofia: {philosophy}. Estilo: {writing_style}.',
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
        votes_summary = '\n'.join(f"- Min. {v['minister']}: {v['vote']}" for v in votes)
        provimento = sum(1 for v in votes if 'provimento' in v['vote'].lower() or 'procedente' in v['vote'].lower() or 'deferido' in v['vote'].lower())
        desprovimento = len(votes) - provimento

        prompt = (
            f"Voce e o Presidente da Turma do TST proclamando o resultado.\n\n"
            f"VOTOS:\n{votes_summary}\n\n"
            f"PLACAR: {provimento} x {desprovimento}\n\n"
            f"Proclame o resultado no formato oficial do TST:\n"
            f"'A Turma, por maioria/unanimidade...'\n"
            f"Inclua determinacoes decorrentes."
        )

        full_text = ''
        for chunk_text in self._stream_llm(prompt, 'Voce e o Presidente da Turma do TST proclamando resultado.'):
            full_text += chunk_text
            yield self._event('proclamacao', chunk_text)

        return full_text

    def _phase_strategic_report(
        self, case_context: str, votes: List[Dict], proclamacao: str,
    ) -> Generator[Dict, None, str]:
        votes_summary = '\n'.join(f"- Min. {v['minister']}: {v['vote']}" for v in votes)
        provimento = sum(1 for v in votes if 'provimento' in v['vote'].lower() or 'procedente' in v['vote'].lower() or 'deferido' in v['vote'].lower())
        is_victory = provimento > (len(votes) - provimento)

        prompt = (
            f"Voce e um consultor juridico trabalhista estrategico de alto nivel.\n"
            f"Analise o resultado do julgamento no TST:\n\n"
            f"CASO:\n{case_context}\n\n"
            f"PLACAR:\n{votes_summary}\n\n"
            f"PROCLAMACAO:\n{proclamacao}\n\n"
            f"{'O cliente VENCEU.' if is_victory else 'O cliente PERDEU.'}\n\n"
            f"Produza um RELATORIO ESTRATEGICO:\n"
            f"1. Analise do placar e votos vencedores/vencidos\n"
            f"2. Ministros-chave e fundamentos decisivos\n"
            f"3. Possibilidade de embargos ao Pleno (SDI-1)\n"
            f"4. Viabilidade de Recurso Extraordinario ao STF (materia constitucional)\n"
            f"5. Impacto da decisao (sumula, IRDR)\n"
            f"6. Providencias imediatas e proximos passos\n"
            f"7. Analise de risco recursal\n\n"
            f"Cite CLT, sumulas do TST, OJs e jurisprudencia."
        )

        full_text = ''
        for chunk_text in self._stream_llm(
            prompt,
            'Voce e um consultor juridico trabalhista estrategico especializado em TST.',
        ):
            full_text += chunk_text
            yield self._event('relatorio_estrategico', chunk_text, extra={
                'type': 'strategic_report',
                'is_victory': is_victory,
            })

        return full_text

    # -- Helpers ---

    def _detect_vote(self, text: str) -> str:
        lower = text.lower()
        if 'nao conheco' in lower or 'nao conhecido' in lower:
            return 'nao_conhecido'
        if 'nego provimento' in lower or 'desprovimento' in lower or 'desprovido' in lower:
            return 'desprovimento'
        if 'provimento parcial' in lower or 'parcial provimento' in lower:
            return 'provimento_parcial'
        if 'dou provimento' in lower or 'provimento' in lower or 'provido' in lower:
            return 'provimento'
        if 'improcedente' in lower:
            return 'improcedente'
        if 'procedente' in lower:
            return 'procedente'
        if 'parcial' in lower:
            return 'provimento_parcial'
        return 'indeterminado'

    def _build_case_context(self) -> str:
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
            extra.append(f"Tipo de recurso: {self.config['action_type']}")
        if self.config.get('case_text'):
            extra.append(f"Texto do caso:\n{self.config['case_text']}")

        config_context = '\n'.join(extra)

        if doc_context and config_context:
            return f"{config_context}\n\n---\n\n{doc_context}"
        return doc_context or config_context

    def _stream_llm(self, prompt: str, system_prompt: str) -> Generator[str, None, None]:
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

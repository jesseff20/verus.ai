"""
TRTSimulationService -- Simula julgamento colegiado do TRT (2a Instancia Trabalhista).

Composicao: 3 Desembargadores (Relator, Revisor, Vogal).
Contexto: Recurso Ordinario (RO) contra sentenca da Vara do Trabalho.

Fases:
  1. Relatorio (resumo do caso pelo Relator)
  2. Voto do Relator
  3. Voto do Revisor (acompanha ou diverge)
  4. Voto do Vogal (desempate se necessario)
  5. Proclamacao do resultado
  6. Ementa do Acordao
  7. Relatorio Estrategico
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

ROLES = ['Relator', 'Revisor', 'Vogal']


class TRTSimulationService:
    """Simula um julgamento colegiado do TRT com 3 desembargadores."""

    def __init__(self, simulation_id: str):
        self.simulation = Simulation.objects.get(id=simulation_id)
        self.documents = list(self.simulation.documents.all())
        self.config = self.simulation.config or {}

        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService
        self.llm = UnifiedLLMService()

        self.provider = self.config.get('provider', SIMULATION_PROVIDER)
        self.model = self.config.get('model', SIMULATION_MODEL)

        self.desembargadores = self._load_desembargadores()

    def _load_desembargadores(self) -> List[MinisterProfile]:
        tribunal = self.config.get('tribunal', '')
        qs = MinisterProfile.objects.filter(court_type='TRT', is_active=True)

        if tribunal:
            qs = qs.filter(turma__icontains=tribunal)

        desembargadores = list(qs[:3])

        if len(desembargadores) < 3:
            desembargadores = self._create_generic_profiles()

        return desembargadores[:3]

    def _create_generic_profiles(self) -> List[MinisterProfile]:
        tribunal = self.config.get('tribunal', 'TRT-2')
        profiles = []
        generic_data = [
            {
                'name': 'Des. Ricardo Ferreira Lima',
                'judicial_philosophy': 'progressista',
                'specialty_areas': ['Direito do Trabalho', 'Direito Processual do Trabalho'],
                'profile_data': {
                    'writing_style': 'Detalhado e protecionista, com forte fundamentacao na CLT e sumulas do TST',
                    'tendencies': ['Principio protetor', 'In dubio pro operario', 'Irrenunciabilidade de direitos'],
                    'key_framework': 'Principio da protecao e dignidade do trabalhador',
                },
            },
            {
                'name': 'Des. Ana Claudia Santos',
                'judicial_philosophy': 'centrista',
                'specialty_areas': ['Direito Coletivo do Trabalho', 'Direito Sindical'],
                'profile_data': {
                    'writing_style': 'Equilibrado e tecnico, com analise detalhada de provas',
                    'tendencies': ['Equilibrio entre capital e trabalho', 'Valorizacao da negociacao coletiva'],
                    'key_framework': 'Ponderacao entre flexibilizacao e protecao trabalhista',
                },
            },
            {
                'name': 'Des. Marcos Antonio Oliveira',
                'judicial_philosophy': 'conservador',
                'specialty_areas': ['Direito Empresarial do Trabalho', 'Reforma Trabalhista'],
                'profile_data': {
                    'writing_style': 'Formal e processualista, com enfase no onus da prova',
                    'tendencies': ['Prevalencia do negociado sobre legislado', 'Reforma Trabalhista', 'Seguranca juridica'],
                    'key_framework': 'Autonomia da vontade e modernizacao das relacoes de trabalho',
                },
            },
        ]

        for i, data in enumerate(generic_data):
            profile = MinisterProfile(
                court_type='TRT',
                name=data['name'],
                turma=f'{tribunal} - Turma',
                judicial_philosophy=data['judicial_philosophy'],
                specialty_areas=data['specialty_areas'],
                notable_positions=[],
                profile_data=data['profile_data'],
            )
            profiles.append(profile)

        return profiles

    # -- API principal ---

    def stream_simulation(self) -> Generator[Dict, None, None]:
        """Generator que produz eventos SSE para a simulacao do TRT."""

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

            if len(self.desembargadores) < 3:
                yield self._event('error', 'Sao necessarios 3 desembargadores para a simulacao.')
                return

            relator = self.desembargadores[0]
            revisor = self.desembargadores[1]
            vogal = self.desembargadores[2]

            # Emit desembargadores list
            yield self._event('ministers', '', extra={
                'ministers': [
                    {
                        'name': d.name,
                        'turma': d.turma or '',
                        'philosophy': d.judicial_philosophy,
                        'is_relator': i == 0,
                        'role': ROLES[i],
                    }
                    for i, d in enumerate(self.desembargadores)
                ],
            })

            # Phase 1: Relatorio
            yield self._progress_event('relatorio', 'Relatorio', f'Des. {relator.name} (Relator) elaborando relatorio...', 10)
            yield self._event('phase', 'Relatorio do Relator')
            relatorio_text = yield from self._phase_relatorio(case_context, relator)

            # Phase 2: Voto do Relator
            yield self._progress_event('voto_relator', 'Voto do Relator', f'Des. {relator.name} proferindo voto...', 25)
            yield self._event('phase', f'Voto do Des. {relator.name} (Relator)')
            relator_vote = yield from self._phase_vote(case_context, relator, relatorio_text, role='Relator', is_relator=True)

            votes = [{
                'minister': relator.name,
                'vote': relator_vote['vote'],
                'is_relator': True,
                'role': 'Relator',
            }]
            yield self._event('vote_result', '', extra={
                'minister': relator.name,
                'vote': relator_vote['vote'],
                'is_relator': True,
                'role': 'Relator',
                'votes_so_far': votes,
            })

            # Phase 3: Voto do Revisor
            yield self._progress_event('voto_revisor', 'Voto do Revisor', f'Des. {revisor.name} proferindo voto...', 45)
            yield self._event('phase', f'Voto do Des. {revisor.name} (Revisor)')
            revisor_vote = yield from self._phase_vote(
                case_context, revisor, relatorio_text,
                role='Revisor', is_relator=False, previous_votes=votes,
            )
            votes.append({
                'minister': revisor.name,
                'vote': revisor_vote['vote'],
                'is_relator': False,
                'role': 'Revisor',
            })
            yield self._event('vote_result', '', extra={
                'minister': revisor.name,
                'vote': revisor_vote['vote'],
                'is_relator': False,
                'role': 'Revisor',
                'votes_so_far': votes,
            })

            # Phase 4: Voto do Vogal
            yield self._progress_event('voto_vogal', 'Voto do Vogal', f'Des. {vogal.name} proferindo voto...', 65)
            yield self._event('phase', f'Voto do Des. {vogal.name} (Vogal)')
            vogal_vote = yield from self._phase_vote(
                case_context, vogal, relatorio_text,
                role='Vogal', is_relator=False, previous_votes=votes,
            )
            votes.append({
                'minister': vogal.name,
                'vote': vogal_vote['vote'],
                'is_relator': False,
                'role': 'Vogal',
            })
            yield self._event('vote_result', '', extra={
                'minister': vogal.name,
                'vote': vogal_vote['vote'],
                'is_relator': False,
                'role': 'Vogal',
                'votes_so_far': votes,
            })

            # Phase 5: Proclamacao
            yield self._progress_event('proclamacao', 'Proclamacao do Resultado', 'Contabilizando votos...', 80)
            yield self._event('phase', 'Proclamacao do Resultado')
            proclamacao = yield from self._phase_proclamacao(votes, case_context)

            # Phase 6: Ementa
            yield self._progress_event('ementa', 'Ementa do Acordao', 'Elaborando ementa...', 88)
            yield self._event('phase', 'Ementa do Acordao')
            ementa = yield from self._phase_ementa(case_context, votes, proclamacao)

            # Phase 7: Relatorio estrategico
            yield self._progress_event('report', 'Relatorio Estrategico', 'Analisando implicacoes...', 95)
            yield self._event('phase', 'Relatorio Estrategico')
            strategic = yield from self._phase_strategic_report(case_context, votes, proclamacao)

            # Persist
            provimento_count = sum(1 for v in votes if 'provimento' in v['vote'].lower() or 'procedente' in v['vote'].lower() or 'deferido' in v['vote'].lower())
            desprovimento_count = len(votes) - provimento_count

            self.simulation.status = 'completed'
            self.simulation.result = {
                'tribunal': self.config.get('tribunal', ''),
                'recurso_type': self.config.get('recurso_type', 'Recurso Ordinario'),
                'relator': relator.name,
                'revisor': revisor.name,
                'vogal': vogal.name,
                'votes': votes,
                'provimento': provimento_count,
                'desprovimento': desprovimento_count,
                'resultado': 'Provido' if provimento_count > desprovimento_count else 'Desprovido' if desprovimento_count > provimento_count else 'Provimento Parcial',
                'relatorio': relatorio_text,
                'proclamacao': proclamacao,
                'ementa': ementa,
                'strategic_report': strategic,
            }
            self.simulation.save(update_fields=['status', 'result'])

            yield self._progress_event('complete', 'Concluido', 'Simulacao finalizada', 100)
            yield self._event('complete', 'Simulacao do TRT concluida.')

        except Exception as e:
            logger.exception(f'[trt_simulation] Erro na simulacao {self.simulation.id}: {e}')
            self.simulation.status = 'failed'
            self.simulation.save(update_fields=['status'])
            yield self._event('error', f'Erro na simulacao: {str(e)}')

    # -- Fases ---

    def _phase_relatorio(self, case_context: str, relator: MinisterProfile) -> Generator[Dict, None, str]:
        recurso_type = self.config.get('recurso_type', 'Recurso Ordinario')
        tribunal = self.config.get('tribunal', 'TRT')

        prompt = (
            f"Voce e o Desembargador {relator.name}, Relator no {tribunal}.\n"
            f"Recurso: {recurso_type}\n\n"
            f"Elabore o RELATORIO do caso trabalhista:\n"
            f"1. Identificacao das partes e do recurso\n"
            f"2. Sintese da sentenca da Vara do Trabalho\n"
            f"3. Razoes do recurso ordinario\n"
            f"4. Contrarrazoes\n"
            f"5. Parecer do Ministerio Publico do Trabalho (se aplicavel)\n\n"
            f"CASO:\n{case_context}\n\n"
            f"Use terminologia trabalhista. Cite CLT, sumulas do TST e OJs da SDI."
        )

        full_text = ''
        for chunk_text in self._stream_llm(prompt, 'Voce e um desembargador do TRT elaborando relatorio de acordao trabalhista.'):
            full_text += chunk_text
            yield self._event('relatorio', chunk_text)

        return full_text

    def _phase_vote(
        self,
        case_context: str,
        desembargador: MinisterProfile,
        relatorio: str,
        role: str = 'Relator',
        is_relator: bool = False,
        previous_votes: Optional[List[Dict]] = None,
    ) -> Generator[Dict, None, Dict]:
        profile_data = desembargador.profile_data or {}
        philosophy = desembargador.get_judicial_philosophy_display()
        specialties = ', '.join(desembargador.specialty_areas or [])
        writing_style = profile_data.get('writing_style', '')
        framework = profile_data.get('key_framework', '')
        tendencies = ', '.join(profile_data.get('tendencies', []))

        recurso_type = self.config.get('recurso_type', 'Recurso Ordinario')
        tribunal = self.config.get('tribunal', 'TRT')

        previous_context = ''
        if previous_votes:
            prev_lines = [f"- Des. {v['minister']} ({v.get('role', '')}): {v['vote']}" for v in previous_votes]
            previous_context = f"\nVOTOS JA PROFERIDOS:\n" + '\n'.join(prev_lines) + '\n'

        role_instruction = {
            'Relator': 'Voce e o RELATOR deste recurso. Profira seu voto apos apresentar o relatorio.',
            'Revisor': 'Voce e o REVISOR. Analise o voto do Relator e decida se acompanha ou diverge.',
            'Vogal': 'Voce e o VOGAL (3o voto). Se houver divergencia, seu voto sera decisivo.',
        }.get(role, '')

        prompt = (
            f"Voce e o Desembargador {desembargador.name} ({role}) no {tribunal}.\n"
            f"Filosofia judicial: {philosophy}\n"
            f"Especialidades: {specialties}\n"
            f"Estilo de escrita: {writing_style}\n"
            f"Framework decisorio: {framework}\n"
            f"Tendencias: {tendencies}\n\n"
            f"Recurso: {recurso_type}\n\n"
            f"RELATORIO DO CASO:\n{relatorio}\n\n"
            f"CASO COMPLETO:\n{case_context}\n"
            f"{previous_context}\n"
            f"{role_instruction}\n\n"
            f"PROFIRA SEU VOTO TRABALHISTA:\n"
            f"1. Fundamente com CLT, sumulas do TST, OJs da SDI\n"
            f"2. Analise verbas trabalhistas individualmente\n"
            f"3. Ao final, DECLARE EXPRESSAMENTE se vota pelo PROVIMENTO, DESPROVIMENTO "
            f"ou PROVIMENTO PARCIAL do recurso\n"
            f"4. Se divergir do relator, justifique a divergencia\n\n"
            f"Mantenha o tom: {writing_style}"
        )

        full_text = ''
        for chunk_text in self._stream_llm(
            prompt,
            f'Voce e o Des. {desembargador.name} ({role}) proferindo voto em acordao trabalhista. '
            f'Filosofia: {philosophy}.',
        ):
            full_text += chunk_text
            yield self._event('vote_text', chunk_text, extra={
                'minister': desembargador.name,
                'is_relator': is_relator,
                'role': role,
            })

        vote_direction = self._detect_vote(full_text)

        if desembargador.pk:
            CourtVote.objects.create(
                simulation=self.simulation,
                voter_name=desembargador.name,
                voter_role=role.lower(),
                minister_profile=desembargador,
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
        votes_summary = '\n'.join(f"- Des. {v['minister']} ({v.get('role', '')}): {v['vote']}" for v in votes)
        provimento = sum(1 for v in votes if 'provimento' in v['vote'].lower() or 'procedente' in v['vote'].lower() or 'deferido' in v['vote'].lower())
        desprovimento = len(votes) - provimento

        prompt = (
            f"Voce e o Presidente da Turma do TRT proclamando o resultado de um julgamento trabalhista.\n\n"
            f"VOTOS:\n{votes_summary}\n\n"
            f"PLACAR: {provimento} x {desprovimento}\n\n"
            f"Proclame o resultado no formato oficial:\n"
            f"'Acordam os Desembargadores da X Turma do TRT...'\n"
            f"Inclua se foi unanime ou por maioria."
        )

        full_text = ''
        for chunk_text in self._stream_llm(prompt, 'Voce e o Presidente da Turma do TRT proclamando resultado.'):
            full_text += chunk_text
            yield self._event('proclamacao', chunk_text)

        return full_text

    def _phase_ementa(self, case_context: str, votes: List[Dict], proclamacao: str) -> Generator[Dict, None, str]:
        recurso_type = self.config.get('recurso_type', 'Recurso Ordinario')

        prompt = (
            f"Elabore a EMENTA do acordao trabalhista no formato padrao dos TRTs.\n\n"
            f"RECURSO: {recurso_type}\n"
            f"CASO:\n{case_context}\n\n"
            f"PROCLAMACAO:\n{proclamacao}\n\n"
            f"A ementa deve conter:\n"
            f"1. DIREITO DO TRABALHO. Tema principal\n"
            f"2. Sintese da decisao\n"
            f"3. Resultado final\n"
            f"Cite CLT, sumulas do TST e OJs quando aplicavel."
        )

        full_text = ''
        for chunk_text in self._stream_llm(prompt, 'Voce e um assessor elaborando ementa de acordao trabalhista.'):
            full_text += chunk_text
            yield self._event('ementa', chunk_text)

        return full_text

    def _phase_strategic_report(
        self, case_context: str, votes: List[Dict], proclamacao: str,
    ) -> Generator[Dict, None, str]:
        votes_summary = '\n'.join(f"- Des. {v['minister']} ({v.get('role', '')}): {v['vote']}" for v in votes)
        provimento = sum(1 for v in votes if 'provimento' in v['vote'].lower() or 'procedente' in v['vote'].lower() or 'deferido' in v['vote'].lower())
        is_victory = provimento > (len(votes) - provimento)

        prompt = (
            f"Voce e um consultor juridico trabalhista estrategico.\n"
            f"Analise o resultado do julgamento no TRT:\n\n"
            f"CASO:\n{case_context}\n\n"
            f"PLACAR:\n{votes_summary}\n\n"
            f"PROCLAMACAO:\n{proclamacao}\n\n"
            f"{'O cliente VENCEU.' if is_victory else 'O cliente PERDEU.'}\n\n"
            f"Produza um RELATORIO ESTRATEGICO:\n"
            f"1. Analise do placar e votos\n"
            f"2. Viabilidade de Recurso de Revista (RR) ao TST\n"
            f"3. Possibilidade de embargos de declaracao\n"
            f"4. Requisitos de admissibilidade do RR (art. 896 CLT)\n"
            f"5. Providencias imediatas\n"
            f"6. Analise de risco recursal\n\n"
            f"Seja especifico. Cite CLT, sumulas do TST e OJs."
        )

        full_text = ''
        for chunk_text in self._stream_llm(
            prompt,
            'Voce e um consultor juridico trabalhista estrategico.',
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
        if self.config.get('recurso_type'):
            extra.append(f"Tipo de recurso: {self.config['recurso_type']}")
        if self.config.get('tribunal'):
            extra.append(f"Tribunal: {self.config['tribunal']}")
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

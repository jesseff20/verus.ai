"""
TurmaRecursalSimulationService -- Simula julgamento de Turma Recursal dos Juizados Especiais.

Composicao: 3 Juizes de Primeiro Grau (NAO desembargadores).

Fases:
  1. Relatorio (resumo do caso pelo Relator)
  2. Voto do Relator
  3. Voto do 2o Juiz (acompanha ou diverge)
  4. Voto do 3o Juiz (desempate se necessario)
  5. Proclamacao do resultado
  6. Relatorio Estrategico

Input: Sentenca do JEC/JECRIM + Recurso Inominado
Output: Acordao simplificado (reforma/mantem/reforma parcial)
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

ROLES = ['Relator', '2o Juiz', '3o Juiz']


class TurmaRecursalSimulationService:
    """Simula um julgamento de Turma Recursal com 3 juizes de primeiro grau."""

    def __init__(self, simulation_id: str):
        self.simulation = Simulation.objects.get(id=simulation_id)
        self.documents = list(self.simulation.documents.all())
        self.config = self.simulation.config or {}

        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService
        self.llm = UnifiedLLMService()

        self.provider = self.config.get('provider', SIMULATION_PROVIDER)
        self.model = self.config.get('model', SIMULATION_MODEL)

        self.juizes = self._load_juizes()

    def _load_juizes(self) -> List[MinisterProfile]:
        """Carrega juizes de primeiro grau para a Turma Recursal."""
        # Turma Recursal nao usa desembargadores -- usa juizes de 1o grau
        # Tenta carregar perfis do tipo TJ marcados como turma recursal
        qs = MinisterProfile.objects.filter(court_type='TJ', is_active=True, turma__icontains='Turma Recursal')
        juizes = list(qs[:3])

        if len(juizes) < 3:
            juizes = self._create_generic_profiles()

        return juizes[:3]

    def _create_generic_profiles(self) -> List[MinisterProfile]:
        """Cria perfis genericos de juizes de 1o grau em memoria."""
        juizado = self.config.get('juizado', 'JEC')
        profiles = []
        generic_data = [
            {
                'name': 'Juiz(a) Ana Beatriz Campos',
                'judicial_philosophy': 'progressista',
                'specialty_areas': ['Direito do Consumidor', 'Pequenas Causas'],
                'profile_data': {
                    'writing_style': 'Objetivo e acessivel, linguagem simplificada para partes desassistidas',
                    'tendencies': ['Celeridade', 'Informalidade', 'Protecao do consumidor'],
                    'key_framework': 'Principios dos Juizados: oralidade, simplicidade, informalidade, economia processual',
                },
            },
            {
                'name': 'Juiz(a) Ricardo Mendes',
                'judicial_philosophy': 'centrista',
                'specialty_areas': ['Responsabilidade Civil', 'Obrigacoes'],
                'profile_data': {
                    'writing_style': 'Tecnico mas conciso, conforme padrao dos Juizados',
                    'tendencies': ['Equilibrio entre partes', 'Conciliacao', 'Razoabilidade'],
                    'key_framework': 'Proporcionalidade e boa-fe objetiva',
                },
            },
            {
                'name': 'Juiz(a) Patricia Almeida',
                'judicial_philosophy': 'conservador',
                'specialty_areas': ['Direito Civil', 'Contratos'],
                'profile_data': {
                    'writing_style': 'Formal e objetivo, com enfase em precedentes das Turmas Recursais',
                    'tendencies': ['Seguranca juridica', 'Legalidade', 'Autonomia da vontade'],
                    'key_framework': 'Pacta sunt servanda e legalidade estrita',
                },
            },
        ]

        for data in generic_data:
            profile = MinisterProfile(
                court_type='TJ',
                name=data['name'],
                turma=f'Turma Recursal - {juizado}',
                judicial_philosophy=data['judicial_philosophy'],
                specialty_areas=data['specialty_areas'],
                notable_positions=[],
                profile_data=data['profile_data'],
            )
            profiles.append(profile)

        return profiles

    # -- API principal ---

    def stream_simulation(self) -> Generator[Dict, None, None]:
        """Generator que produz eventos SSE para a simulacao de Turma Recursal."""

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

            if len(self.juizes) < 3:
                yield self._event('error', 'Sao necessarios 3 juizes para a Turma Recursal.')
                return

            relator = self.juizes[0]
            segundo = self.juizes[1]
            terceiro = self.juizes[2]

            # Emit juizes list
            yield self._event('ministers', '', extra={
                'ministers': [
                    {
                        'name': j.name,
                        'turma': j.turma or '',
                        'philosophy': j.judicial_philosophy,
                        'is_relator': i == 0,
                        'role': ROLES[i],
                    }
                    for i, j in enumerate(self.juizes)
                ],
            })

            # Phase 1: Relatorio
            yield self._progress_event('relatorio', 'Relatorio', f'{relator.name} (Relator) elaborando relatorio...', 10)
            yield self._event('phase', 'Relatorio do Relator')
            relatorio_text = yield from self._phase_relatorio(case_context, relator)

            # Phase 2: Voto do Relator
            yield self._progress_event('voto_relator', 'Voto do Relator', f'{relator.name} proferindo voto...', 25)
            yield self._event('phase', f'Voto de {relator.name} (Relator)')
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

            # Phase 3: Voto do 2o Juiz
            yield self._progress_event('voto_2', 'Voto do 2o Juiz', f'{segundo.name} proferindo voto...', 45)
            yield self._event('phase', f'Voto de {segundo.name} (2o Juiz)')
            segundo_vote = yield from self._phase_vote(
                case_context, segundo, relatorio_text,
                role='2o Juiz', is_relator=False, previous_votes=votes,
            )
            votes.append({
                'minister': segundo.name,
                'vote': segundo_vote['vote'],
                'is_relator': False,
                'role': '2o Juiz',
            })
            yield self._event('vote_result', '', extra={
                'minister': segundo.name,
                'vote': segundo_vote['vote'],
                'is_relator': False,
                'role': '2o Juiz',
                'votes_so_far': votes,
            })

            # Phase 4: Voto do 3o Juiz
            yield self._progress_event('voto_3', 'Voto do 3o Juiz', f'{terceiro.name} proferindo voto...', 65)
            yield self._event('phase', f'Voto de {terceiro.name} (3o Juiz)')
            terceiro_vote = yield from self._phase_vote(
                case_context, terceiro, relatorio_text,
                role='3o Juiz', is_relator=False, previous_votes=votes,
            )
            votes.append({
                'minister': terceiro.name,
                'vote': terceiro_vote['vote'],
                'is_relator': False,
                'role': '3o Juiz',
            })
            yield self._event('vote_result', '', extra={
                'minister': terceiro.name,
                'vote': terceiro_vote['vote'],
                'is_relator': False,
                'role': '3o Juiz',
                'votes_so_far': votes,
            })

            # Phase 5: Proclamacao
            yield self._progress_event('proclamacao', 'Proclamacao do Resultado', 'Contabilizando votos...', 80)
            yield self._event('phase', 'Proclamacao do Resultado')
            proclamacao = yield from self._phase_proclamacao(votes, case_context)

            # Phase 6: Relatorio Estrategico
            yield self._progress_event('report', 'Relatorio Estrategico', 'Analisando implicacoes...', 92)
            yield self._event('phase', 'Relatorio Estrategico')
            strategic = yield from self._phase_strategic_report(case_context, votes, proclamacao)

            # Persist
            provimento_count = sum(1 for v in votes if 'provimento' in v['vote'].lower() or 'procedente' in v['vote'].lower() or 'deferido' in v['vote'].lower() or 'reforma' in v['vote'].lower())
            desprovimento_count = len(votes) - provimento_count

            self.simulation.status = 'completed'
            self.simulation.result = {
                'juizado': self.config.get('juizado', 'JEC'),
                'recurso_type': 'Recurso Inominado',
                'relator': relator.name,
                'segundo_juiz': segundo.name,
                'terceiro_juiz': terceiro.name,
                'votes': votes,
                'provimento': provimento_count,
                'desprovimento': desprovimento_count,
                'resultado': 'Provido' if provimento_count > desprovimento_count else 'Desprovido' if desprovimento_count > provimento_count else 'Provimento Parcial',
                'relatorio': relatorio_text,
                'proclamacao': proclamacao,
                'strategic_report': strategic,
            }
            self.simulation.save(update_fields=['status', 'result'])

            yield self._progress_event('complete', 'Concluido', 'Simulacao finalizada', 100)
            yield self._event('complete', 'Simulacao de Turma Recursal concluida.')

        except Exception as e:
            logger.exception(f'[turma_recursal_simulation] Erro na simulacao {self.simulation.id}: {e}')
            self.simulation.status = 'failed'
            self.simulation.save(update_fields=['status'])
            yield self._event('error', f'Erro na simulacao: {str(e)}')

    # -- Fases ---

    def _phase_relatorio(self, case_context: str, relator: MinisterProfile) -> Generator[Dict, None, str]:
        """Gera o relatorio do caso pelo relator."""
        juizado = self.config.get('juizado', 'JEC')

        prompt = (
            f"Voce e o(a) {relator.name}, Juiz(a) Relator(a) na Turma Recursal do {juizado}.\n"
            f"Recurso: Recurso Inominado (Lei 9.099/95)\n\n"
            f"Elabore o RELATORIO SIMPLIFICADO do caso, no formato de acordao de Turma Recursal:\n"
            f"1. Identificacao das partes e do recurso inominado\n"
            f"2. Sintese da sentenca recorrida do Juizado\n"
            f"3. Razoes do recurso inominado\n"
            f"4. Contrarrazoes (se houver)\n\n"
            f"CASO:\n{case_context}\n\n"
            f"Seja objetivo e conciso, no estilo simplificado dos Juizados Especiais. "
            f"O acordao de Turma Recursal e mais curto que o de TJ."
        )

        full_text = ''
        for chunk_text in self._stream_llm(prompt, 'Voce e um juiz de primeiro grau elaborando relatorio em Turma Recursal.'):
            full_text += chunk_text
            yield self._event('relatorio', chunk_text)

        return full_text

    def _phase_vote(
        self,
        case_context: str,
        juiz: MinisterProfile,
        relatorio: str,
        role: str = 'Relator',
        is_relator: bool = False,
        previous_votes: Optional[List[Dict]] = None,
    ) -> Generator[Dict, None, Dict]:
        """Gera o voto de um juiz da Turma Recursal."""
        profile_data = juiz.profile_data or {}
        philosophy = juiz.get_judicial_philosophy_display()
        specialties = ', '.join(juiz.specialty_areas or [])
        tendencies = ', '.join(profile_data.get('tendencies', []))
        writing_style = profile_data.get('writing_style', '')
        framework = profile_data.get('key_framework', '')

        juizado = self.config.get('juizado', 'JEC')

        previous_context = ''
        if previous_votes:
            prev_lines = [f"- {v['minister']} ({v.get('role', '')}): {v['vote']}" for v in previous_votes]
            previous_context = f"\nVOTOS JA PROFERIDOS:\n" + '\n'.join(prev_lines) + '\n'

        role_instruction = {
            'Relator': 'Voce e o RELATOR deste recurso inominado. Profira seu voto.',
            '2o Juiz': 'Voce e o 2o JUIZ. Analise o voto do Relator e decida se acompanha ou diverge.',
            '3o Juiz': 'Voce e o 3o JUIZ. Se houver divergencia, seu voto sera decisivo.',
        }.get(role, '')

        prompt = (
            f"Voce e o(a) {juiz.name} ({role}) na Turma Recursal do {juizado}.\n"
            f"IMPORTANTE: Voce e JUIZ DE PRIMEIRO GRAU, nao desembargador.\n"
            f"Filosofia judicial: {philosophy}\n"
            f"Especialidades: {specialties}\n"
            f"Estilo: {writing_style}\n"
            f"Framework: {framework}\n"
            f"Tendencias: {tendencies}\n\n"
            f"Recurso: Recurso Inominado (Lei 9.099/95)\n\n"
            f"RELATORIO DO CASO:\n{relatorio}\n\n"
            f"CASO COMPLETO:\n{case_context}\n"
            f"{previous_context}\n"
            f"{role_instruction}\n\n"
            f"PROFIRA SEU VOTO de forma SIMPLIFICADA (padrao Turma Recursal):\n"
            f"1. Fundamente com base na Lei 9.099/95 e legislacao aplicavel\n"
            f"2. Seja conciso -- votos de Turma Recursal sao mais curtos\n"
            f"3. Ao final, DECLARE se vota por CONHECER E DAR PROVIMENTO, "
            f"CONHECER E NEGAR PROVIMENTO, ou DAR PROVIMENTO PARCIAL\n"
            f"4. Se divergir do relator, justifique brevemente\n\n"
            f"Mantenha o tom: {writing_style}"
        )

        full_text = ''
        for chunk_text in self._stream_llm(
            prompt,
            f'Voce e {juiz.name} ({role}), juiz de 1o grau em Turma Recursal. '
            f'Filosofia: {philosophy}. Estilo: {writing_style}.',
        ):
            full_text += chunk_text
            yield self._event('vote_text', chunk_text, extra={
                'minister': juiz.name,
                'is_relator': is_relator,
                'role': role,
            })

        vote_direction = self._detect_vote(full_text)

        if juiz.pk:
            CourtVote.objects.create(
                simulation=self.simulation,
                voter_name=juiz.name,
                voter_role=role.lower(),
                minister_profile=juiz,
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
        votes_summary = '\n'.join(f"- {v['minister']} ({v.get('role', '')}): {v['vote']}" for v in votes)

        provimento = sum(1 for v in votes if 'provimento' in v['vote'].lower() or 'procedente' in v['vote'].lower() or 'deferido' in v['vote'].lower() or 'reforma' in v['vote'].lower())
        desprovimento = len(votes) - provimento

        prompt = (
            f"Voce e o Presidente da Turma Recursal proclamando o resultado.\n\n"
            f"VOTOS:\n{votes_summary}\n\n"
            f"PLACAR: {provimento} x {desprovimento}\n\n"
            f"Proclame o resultado no formato simplificado de Turma Recursal:\n"
            f"1. Resumo do placar\n"
            f"2. Resultado: recurso PROVIDO / DESPROVIDO / PARCIALMENTE PROVIDO\n"
            f"3. Se unanime ou por maioria\n"
            f"4. Reforma/mantem/reforma parcial a sentenca do Juizado\n\n"
            f"Use formato: 'Acordam os Juizes da Turma Recursal...'\n"
            f"Seja conciso -- padrao de Turma Recursal."
        )

        full_text = ''
        for chunk_text in self._stream_llm(prompt, 'Voce e o Presidente da Turma Recursal proclamando resultado.'):
            full_text += chunk_text
            yield self._event('proclamacao', chunk_text)

        return full_text

    def _phase_strategic_report(
        self, case_context: str, votes: List[Dict], proclamacao: str,
    ) -> Generator[Dict, None, str]:
        """Gera relatorio estrategico."""
        votes_summary = '\n'.join(f"- {v['minister']} ({v.get('role', '')}): {v['vote']}" for v in votes)

        provimento = sum(1 for v in votes if 'provimento' in v['vote'].lower() or 'procedente' in v['vote'].lower() or 'deferido' in v['vote'].lower() or 'reforma' in v['vote'].lower())
        is_victory = provimento > (len(votes) - provimento)

        prompt = (
            f"Voce e um consultor juridico estrategico.\n"
            f"Analise o resultado do julgamento na Turma Recursal:\n\n"
            f"CASO:\n{case_context}\n\n"
            f"PLACAR:\n{votes_summary}\n\n"
            f"PROCLAMACAO:\n{proclamacao}\n\n"
            f"{'O cliente VENCEU.' if is_victory else 'O cliente PERDEU.'}\n\n"
            f"Produza um RELATORIO ESTRATEGICO considerando que se trata de Juizados Especiais:\n"
            f"1. Analise do placar e votos\n"
            f"2. Fundamentos decisivos\n"
            f"3. ATENCAO: Da decisao de Turma Recursal NAO cabe apelacao nem recurso especial (STJ)\n"
            f"4. Cabe apenas: Embargos de Declaracao, Recurso Extraordinario (STF) se materia constitucional, "
            f"ou Reclamacao ao STJ para uniformizacao\n"
            f"5. Providencias imediatas e proximos passos\n"
            f"6. Analise de risco\n\n"
            f"Seja especifico e pratico."
        )

        full_text = ''
        for chunk_text in self._stream_llm(
            prompt,
            'Voce e um consultor juridico estrategico especializado em Juizados Especiais.',
        ):
            full_text += chunk_text
            yield self._event('relatorio_estrategico', chunk_text, extra={
                'type': 'strategic_report',
                'is_victory': is_victory,
            })

        return full_text

    # -- Helpers ---

    def _detect_vote(self, text: str) -> str:
        """Detecta direcao do voto no texto."""
        lower = text.lower()
        if 'nego provimento' in lower or 'desprovimento' in lower or 'desprovido' in lower:
            return 'desprovimento'
        if 'mantenho' in lower or 'mantem' in lower:
            return 'desprovimento'
        if 'improcedente' in lower or 'improcedencia' in lower:
            return 'improcedente'
        if 'provimento parcial' in lower or 'parcial provimento' in lower or 'reforma parcial' in lower:
            return 'provimento_parcial'
        if 'dou provimento' in lower or 'provimento' in lower or 'provido' in lower:
            return 'provimento'
        if 'reforma' in lower:
            return 'provimento'
        if 'procedente' in lower or 'procedencia' in lower:
            return 'procedente'
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

        extra = []
        if self.config.get('case_description'):
            extra.append(f"Descricao do caso:\n{self.config['case_description']}")
        if self.config.get('juizado'):
            extra.append(f"Juizado: {self.config['juizado']}")
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

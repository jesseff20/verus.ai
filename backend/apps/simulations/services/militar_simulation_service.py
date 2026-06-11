"""
MilitarSimulationService -- Simula julgamento na Auditoria de Justica Militar (1a Instancia).

Composicao unica -- Conselho de Justica:
  - 1 Juiz Auditor (togado, presidente)
  - 4 Oficiais Militares (nao sao advogados -- trazem perspectiva militar)

Fases:
  1. Relatorio do Juiz Auditor (resumo do caso)
  2. Interrogatorio (questionamento do reu)
  3. Debates (Acusacao e Defesa)
  4. Votacao do Conselho (5 membros votam -- voto secreto sobre culpa/inocencia)
  5. Sentenca (lida pelo Juiz Auditor)
  6. Relatorio Estrategico
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


class MilitarSimulationService:
    """Simula um julgamento na Auditoria de Justica Militar com Conselho de Justica."""

    def __init__(self, simulation_id: str):
        self.simulation = Simulation.objects.get(id=simulation_id)
        self.documents = list(self.simulation.documents.all())
        self.config = self.simulation.config or {}

        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService
        self.llm = UnifiedLLMService()

        self.provider = self.config.get('provider', SIMULATION_PROVIDER)
        self.model = self.config.get('model', SIMULATION_MODEL)

        self.membros = self._load_conselho()

    def _load_conselho(self) -> List[MinisterProfile]:
        """Carrega membros do Conselho de Justica (1 juiz auditor + 4 oficiais)."""
        qs = MinisterProfile.objects.filter(court_type='STM', is_active=True, turma__icontains='Auditoria')
        membros = list(qs[:5])

        if len(membros) < 5:
            membros = self._create_generic_profiles()

        return membros[:5]

    def _create_generic_profiles(self) -> List[MinisterProfile]:
        """Cria perfis genericos do Conselho de Justica Militar."""
        forca = self.config.get('forca', 'Exercito')
        profiles = []
        generic_data = [
            {
                'name': 'Juiz Auditor Dr. Fernando Costa',
                'judicial_philosophy': 'centrista',
                'specialty_areas': ['Direito Penal Militar', 'Direito Processual Penal Militar'],
                'profile_data': {
                    'writing_style': 'Tecnico e formal, com conhecimento do CPM e CPPM',
                    'tendencies': ['Legalidade estrita', 'Devido processo legal', 'Hierarquia e disciplina'],
                    'key_framework': 'Codigo Penal Militar (Decreto-Lei 1.001/69) e CPPM',
                    'role': 'juiz_auditor',
                    'is_togado': True,
                },
            },
            {
                'name': f'Cel. Marcos Ribeiro ({forca})',
                'judicial_philosophy': 'conservador',
                'specialty_areas': ['Disciplina Militar', 'Hierarquia'],
                'profile_data': {
                    'writing_style': 'Objetivo e disciplinado, perspectiva de comando',
                    'tendencies': ['Preservacao da hierarquia', 'Disciplina', 'Exemplo para a tropa'],
                    'key_framework': 'Regulamento Disciplinar e valores militares',
                    'role': 'oficial',
                    'patente': 'Coronel',
                    'forca': forca,
                    'is_togado': False,
                },
            },
            {
                'name': f'Ten. Cel. Paulo Ferreira ({forca})',
                'judicial_philosophy': 'conservador',
                'specialty_areas': ['Administracao Militar', 'Comando'],
                'profile_data': {
                    'writing_style': 'Direto e pragmatico, visao operacional',
                    'tendencies': ['Operacionalidade', 'Coesao da tropa', 'Responsabilidade'],
                    'key_framework': 'Dever militar e comprometimento institucional',
                    'role': 'oficial',
                    'patente': 'Tenente-Coronel',
                    'forca': forca,
                    'is_togado': False,
                },
            },
            {
                'name': f'Maj. Ricardo Santos ({forca})',
                'judicial_philosophy': 'centrista',
                'specialty_areas': ['Logistica Militar', 'Gestao de Pessoal'],
                'profile_data': {
                    'writing_style': 'Analitico, considera circunstancias atenuantes',
                    'tendencies': ['Justica', 'Proporcionalidade', 'Reintegracao'],
                    'key_framework': 'Equilibrio entre disciplina e direitos individuais',
                    'role': 'oficial',
                    'patente': 'Major',
                    'forca': forca,
                    'is_togado': False,
                },
            },
            {
                'name': f'Cap. Andre Oliveira ({forca})',
                'judicial_philosophy': 'pragmatico',
                'specialty_areas': ['Instrucao Militar', 'Treinamento'],
                'profile_data': {
                    'writing_style': 'Pratico, foco nos fatos e circunstancias',
                    'tendencies': ['Pragmatismo', 'Contexto operacional', 'Formacao do militar'],
                    'key_framework': 'Circunstancias concretas e impacto na unidade',
                    'role': 'oficial',
                    'patente': 'Capitao',
                    'forca': forca,
                    'is_togado': False,
                },
            },
        ]

        for data in generic_data:
            profile = MinisterProfile(
                court_type='STM',
                name=data['name'],
                turma=f'Auditoria - {forca}',
                judicial_philosophy=data['judicial_philosophy'],
                specialty_areas=data['specialty_areas'],
                notable_positions=[],
                profile_data=data['profile_data'],
            )
            profiles.append(profile)

        return profiles

    # -- API principal ---

    def stream_simulation(self) -> Generator[Dict, None, None]:
        """Generator que produz eventos SSE para a simulacao da Auditoria Militar."""

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

            if len(self.membros) < 5:
                yield self._event('error', 'Sao necessarios 5 membros para o Conselho de Justica.')
                return

            juiz_auditor = self.membros[0]
            oficiais = self.membros[1:]

            # Emit conselho list
            yield self._event('ministers', '', extra={
                'ministers': [
                    {
                        'name': m.name,
                        'turma': m.turma or '',
                        'philosophy': m.judicial_philosophy,
                        'is_relator': i == 0,
                        'role': 'Juiz Auditor' if i == 0 else f'Oficial {i}',
                        'is_togado': (m.profile_data or {}).get('is_togado', i == 0),
                        'patente': (m.profile_data or {}).get('patente', ''),
                    }
                    for i, m in enumerate(self.membros)
                ],
            })

            # Phase 1: Relatorio do Juiz Auditor
            yield self._progress_event('relatorio', 'Relatorio do Juiz Auditor', f'{juiz_auditor.name} elaborando relatorio...', 8)
            yield self._event('phase', 'Relatorio do Juiz Auditor')
            relatorio_text = yield from self._phase_relatorio(case_context, juiz_auditor)

            # Phase 2: Interrogatorio
            yield self._progress_event('interrogatorio', 'Interrogatorio', 'Interrogatorio do acusado...', 20)
            yield self._event('phase', 'Interrogatorio do Acusado')
            interrogatorio_text = yield from self._phase_interrogatorio(case_context, juiz_auditor)

            # Phase 3: Debates
            yield self._progress_event('debates', 'Debates', 'Debates entre acusacao e defesa...', 35)
            yield self._event('phase', 'Debates - Acusacao e Defesa')
            debates_text = yield from self._phase_debates(case_context, relatorio_text)

            # Phase 4: Votacao do Conselho (5 membros)
            votes = []
            total = len(self.membros)
            for idx, membro in enumerate(self.membros):
                progress = 50 + ((idx + 1) * 8)
                role_label = 'Juiz Auditor' if idx == 0 else f'Oficial {idx}'
                yield self._progress_event(
                    f'voto_{idx}', f'Voto - {membro.name}',
                    f'{membro.name} votando...', min(progress, 85),
                )
                yield self._event('phase', f'Voto de {membro.name} ({role_label})')

                vote_result = yield from self._phase_vote(
                    case_context, membro, relatorio_text, debates_text,
                    role=role_label, is_togado=(idx == 0),
                    previous_votes=votes,
                )

                votes.append({
                    'minister': membro.name,
                    'vote': vote_result['vote'],
                    'is_relator': idx == 0,
                    'role': role_label,
                })
                yield self._event('vote_result', '', extra={
                    'minister': membro.name,
                    'vote': vote_result['vote'],
                    'is_relator': idx == 0,
                    'role': role_label,
                    'votes_so_far': votes,
                })

            # Phase 5: Sentenca
            yield self._progress_event('sentenca', 'Sentenca', 'Juiz Auditor redigindo sentenca...', 88)
            yield self._event('phase', 'Sentenca')
            sentenca_text = yield from self._phase_sentenca(case_context, votes, juiz_auditor)

            # Phase 6: Relatorio Estrategico
            yield self._progress_event('report', 'Relatorio Estrategico', 'Analisando implicacoes...', 95)
            yield self._event('phase', 'Relatorio Estrategico')
            strategic = yield from self._phase_strategic_report(case_context, votes, sentenca_text)

            # Persist
            condenacao_count = sum(1 for v in votes if 'condenacao' in v['vote'].lower() or 'culpado' in v['vote'].lower() or 'procedente' in v['vote'].lower())
            absolvicao_count = len(votes) - condenacao_count

            self.simulation.status = 'completed'
            self.simulation.result = {
                'forca': self.config.get('forca', 'Exercito'),
                'crime_militar': self.config.get('crime_militar', ''),
                'juiz_auditor': juiz_auditor.name,
                'votes': votes,
                'condenacao': condenacao_count,
                'absolvicao': absolvicao_count,
                'resultado': 'Condenacao' if condenacao_count > absolvicao_count else 'Absolvicao',
                'relatorio': relatorio_text,
                'interrogatorio': interrogatorio_text,
                'debates': debates_text,
                'sentenca': sentenca_text,
                'strategic_report': strategic,
            }
            self.simulation.save(update_fields=['status', 'result'])

            yield self._progress_event('complete', 'Concluido', 'Simulacao finalizada', 100)
            yield self._event('complete', 'Simulacao de Auditoria Militar concluida.')

        except Exception as e:
            logger.exception(f'[militar_simulation] Erro na simulacao {self.simulation.id}: {e}')
            self.simulation.status = 'failed'
            self.simulation.save(update_fields=['status'])
            yield self._event('error', f'Erro na simulacao: {str(e)}')

    # -- Fases ---

    def _phase_relatorio(self, case_context: str, juiz_auditor: MinisterProfile) -> Generator[Dict, None, str]:
        """Gera o relatorio do caso pelo Juiz Auditor."""
        crime = self.config.get('crime_militar', 'crime militar')
        forca = self.config.get('forca', 'Exercito')

        prompt = (
            f"Voce e o {juiz_auditor.name}, Juiz Auditor da Auditoria de Justica Militar ({forca}).\n"
            f"Crime imputado: {crime}\n\n"
            f"Elabore o RELATORIO do caso conforme o rito do Codigo de Processo Penal Militar (CPPM):\n"
            f"1. Identificacao do acusado (patente, unidade, tempo de servico)\n"
            f"2. Tipificacao penal militar (CPM)\n"
            f"3. Sintese dos fatos do IPM (Inquerito Policial Militar)\n"
            f"4. Resumo da instrucao criminal\n"
            f"5. Alegacoes finais da acusacao (MPM) e defesa\n\n"
            f"CASO:\n{case_context}\n\n"
            f"Seja tecnico e formal, no estilo da Justica Militar."
        )

        full_text = ''
        for chunk_text in self._stream_llm(prompt, 'Voce e um Juiz Auditor da Justica Militar elaborando relatorio.'):
            full_text += chunk_text
            yield self._event('relatorio', chunk_text)

        return full_text

    def _phase_interrogatorio(self, case_context: str, juiz_auditor: MinisterProfile) -> Generator[Dict, None, str]:
        """Simula o interrogatorio do acusado."""
        crime = self.config.get('crime_militar', 'crime militar')

        prompt = (
            f"Voce e o {juiz_auditor.name}, Juiz Auditor, conduzindo o INTERROGATORIO do acusado.\n"
            f"Crime: {crime}\n\n"
            f"Simule o interrogatorio conforme o CPPM:\n"
            f"1. Qualificacao do acusado\n"
            f"2. Perguntas sobre os fatos\n"
            f"3. Respostas do acusado (simule com base no contexto)\n"
            f"4. Perguntas sobre circunstancias atenuantes/agravantes\n"
            f"5. Direito ao silencio (mencionar art. 5o, LXIII, CF)\n\n"
            f"CASO:\n{case_context}\n\n"
            f"Formate como dialogo entre Juiz e Acusado."
        )

        full_text = ''
        for chunk_text in self._stream_llm(prompt, 'Voce simula um interrogatorio na Justica Militar.'):
            full_text += chunk_text
            yield self._event('interrogatorio', chunk_text)

        return full_text

    def _phase_debates(self, case_context: str, relatorio: str) -> Generator[Dict, None, str]:
        """Simula os debates entre acusacao (MPM) e defesa."""
        crime = self.config.get('crime_militar', 'crime militar')

        prompt = (
            f"Simule os DEBATES ORAIS na Auditoria de Justica Militar.\n"
            f"Crime: {crime}\n\n"
            f"RELATORIO:\n{relatorio}\n\n"
            f"CASO:\n{case_context}\n\n"
            f"Gere:\n"
            f"1. ACUSACAO (Ministerio Publico Militar):\n"
            f"   - Peca a condenacao, com fundamento no CPM\n"
            f"   - Argumente sobre a gravidade do crime militar\n"
            f"   - Impacto na disciplina e hierarquia\n\n"
            f"2. DEFESA:\n"
            f"   - Peca a absolvicao ou atenuacao\n"
            f"   - Argumente sobre circunstancias atenuantes\n"
            f"   - Questione provas ou procedimentos\n\n"
            f"Formate claramente cada parte dos debates."
        )

        full_text = ''
        for chunk_text in self._stream_llm(prompt, 'Voce simula debates na Justica Militar.'):
            full_text += chunk_text
            yield self._event('debates', chunk_text)

        return full_text

    def _phase_vote(
        self,
        case_context: str,
        membro: MinisterProfile,
        relatorio: str,
        debates: str,
        role: str = 'Oficial',
        is_togado: bool = False,
        previous_votes: Optional[List[Dict]] = None,
    ) -> Generator[Dict, None, Dict]:
        """Gera o voto de um membro do Conselho de Justica."""
        profile_data = membro.profile_data or {}
        philosophy = membro.get_judicial_philosophy_display()
        specialties = ', '.join(membro.specialty_areas or [])
        tendencies = ', '.join(profile_data.get('tendencies', []))
        writing_style = profile_data.get('writing_style', '')
        patente = profile_data.get('patente', '')
        forca = profile_data.get('forca', self.config.get('forca', ''))

        previous_context = ''
        if previous_votes:
            # Voto secreto -- nao mostra votos anteriores
            previous_context = f"\n(Votacao secreta -- {len(previous_votes)} votos ja proferidos)\n"

        if is_togado:
            role_desc = (
                f"Voce e o {membro.name}, Juiz Auditor (togado, presidente do Conselho).\n"
                f"Voce e formado em Direito e conhece profundamente o CPM e CPPM.\n"
            )
        else:
            role_desc = (
                f"Voce e o {membro.name}, {patente} do {forca}, membro do Conselho de Justica.\n"
                f"Voce NAO e advogado -- voce e um oficial militar que traz a perspectiva da caserna.\n"
                f"Considere: hierarquia, disciplina, impacto na tropa, regulamentos militares.\n"
            )

        prompt = (
            f"{role_desc}"
            f"Filosofia: {philosophy}\n"
            f"Especialidades: {specialties}\n"
            f"Tendencias: {tendencies}\n\n"
            f"RELATORIO:\n{relatorio}\n\n"
            f"DEBATES:\n{debates}\n\n"
            f"CASO:\n{case_context}\n"
            f"{previous_context}\n"
            f"PROFIRA SEU VOTO (secreto):\n"
            f"1. Analise os fatos e provas\n"
            f"2. {'Fundamente juridicamente (CPM/CPPM)' if is_togado else 'Considere a perspectiva militar e o impacto na unidade'}\n"
            f"3. Ao final, declare: CULPADO (CONDENACAO) ou INOCENTE (ABSOLVICAO)\n"
            f"4. Se condenar, sugira a pena aplicavel\n\n"
            f"Estilo: {writing_style}"
        )

        full_text = ''
        for chunk_text in self._stream_llm(
            prompt,
            f'Voce e {membro.name} ({role}), membro do Conselho de Justica Militar. '
            f'{"Juiz togado." if is_togado else "Oficial militar, nao advogado."}',
        ):
            full_text += chunk_text
            yield self._event('vote_text', chunk_text, extra={
                'minister': membro.name,
                'is_relator': is_togado,
                'role': role,
            })

        vote_direction = self._detect_vote_militar(full_text)

        if membro.pk:
            CourtVote.objects.create(
                simulation=self.simulation,
                voter_name=membro.name,
                voter_role=role.lower(),
                minister_profile=membro,
                vote=vote_direction,
                vote_text=full_text,
                is_relator=is_togado,
                is_dissent=False,  # voto secreto
            )

        return {'vote': vote_direction, 'text': full_text}

    def _phase_sentenca(self, case_context: str, votes: List[Dict], juiz_auditor: MinisterProfile) -> Generator[Dict, None, str]:
        """Gera a sentenca lida pelo Juiz Auditor apos a votacao."""
        condenacao = sum(1 for v in votes if 'condenacao' in v['vote'].lower() or 'culpado' in v['vote'].lower() or 'procedente' in v['vote'].lower())
        absolvicao = len(votes) - condenacao
        resultado = 'CONDENACAO' if condenacao > absolvicao else 'ABSOLVICAO'

        crime = self.config.get('crime_militar', 'crime militar')

        prompt = (
            f"Voce e o {juiz_auditor.name}, Juiz Auditor, lendo a SENTENCA do Conselho de Justica.\n\n"
            f"RESULTADO DA VOTACAO: {resultado} (por {max(condenacao, absolvicao)} a {min(condenacao, absolvicao)})\n"
            f"Crime: {crime}\n\n"
            f"CASO:\n{case_context}\n\n"
            f"Redija a SENTENCA no formato da Justica Militar:\n"
            f"1. RELATORIO (breve)\n"
            f"2. FUNDAMENTACAO\n"
            f"   - Tipificacao no CPM (Decreto-Lei 1.001/69)\n"
            f"   - Analise das provas\n"
            f"   - Circunstancias atenuantes/agravantes\n"
            f"3. DISPOSITIVO\n"
            f"   - {'CONDENAR o acusado, fixando a pena' if resultado == 'CONDENACAO' else 'ABSOLVER o acusado, com fundamento legal'}\n"
            f"   - Custas, detalhes da execucao penal militar\n\n"
            f"Siga o formato oficial da Justica Militar."
        )

        full_text = ''
        for chunk_text in self._stream_llm(prompt, 'Voce e um Juiz Auditor redigindo sentenca da Justica Militar.'):
            full_text += chunk_text
            yield self._event('sentenca', chunk_text)

        return full_text

    def _phase_strategic_report(
        self, case_context: str, votes: List[Dict], sentenca: str,
    ) -> Generator[Dict, None, str]:
        """Gera relatorio estrategico."""
        condenacao = sum(1 for v in votes if 'condenacao' in v['vote'].lower() or 'culpado' in v['vote'].lower() or 'procedente' in v['vote'].lower())
        absolvicao = len(votes) - condenacao
        is_absolvido = absolvicao > condenacao

        prompt = (
            f"Voce e um consultor juridico estrategico especializado em Direito Militar.\n"
            f"Analise o resultado do julgamento na Auditoria de Justica Militar:\n\n"
            f"CASO:\n{case_context}\n\n"
            f"PLACAR: {condenacao} votos pela condenacao x {absolvicao} pela absolvicao\n"
            f"{'O acusado foi ABSOLVIDO.' if is_absolvido else 'O acusado foi CONDENADO.'}\n\n"
            f"SENTENCA:\n{sentenca}\n\n"
            f"Produza um RELATORIO ESTRATEGICO:\n"
            f"1. Analise do placar do Conselho de Justica\n"
            f"2. Fundamentos decisivos\n"
            f"3. Possibilidade de Apelacao ao STM (Superior Tribunal Militar)\n"
            f"4. Consequencias administrativas para o militar\n"
            f"5. Impacto na carreira militar do acusado\n"
            f"6. Providencias imediatas e proximos passos\n"
            f"7. Analise de risco recursal\n\n"
            f"Seja especifico e pratico."
        )

        full_text = ''
        for chunk_text in self._stream_llm(
            prompt,
            'Voce e um consultor juridico estrategico especializado em Justica Militar.',
        ):
            full_text += chunk_text
            yield self._event('relatorio_estrategico', chunk_text, extra={
                'type': 'strategic_report',
                'is_victory': is_absolvido,
            })

        return full_text

    # -- Helpers ---

    def _detect_vote_militar(self, text: str) -> str:
        """Detecta direcao do voto em contexto militar."""
        lower = text.lower()
        if 'culpado' in lower or 'condenacao' in lower or 'condeno' in lower:
            return 'condenacao'
        if 'inocente' in lower or 'absolvicao' in lower or 'absolvo' in lower:
            return 'absolvicao'
        if 'procedente' in lower or 'procedencia' in lower:
            return 'condenacao'
        if 'improcedente' in lower or 'improcedencia' in lower:
            return 'absolvicao'
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
        if self.config.get('crime_militar'):
            extra.append(f"Crime militar: {self.config['crime_militar']}")
        if self.config.get('forca'):
            extra.append(f"Forca Armada: {self.config['forca']}")
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

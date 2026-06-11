"""
EleitoralSimulationService -- Simula julgamentos na Justica Eleitoral.

Tres modalidades:
  1. Juiz Eleitoral (1a instancia) -- sentenca simples (reusa padrao JudgeSimulationService)
  2. TRE -- 7 membros com composicao mista:
     - 2 desembargadores TJ
     - 2 juizes de direito
     - 1 juiz federal
     - 2 advogados (nomeados pelo Presidente da Republica a partir de lista do STF)
  3. TSE -- 7 ministros:
     - 3 do STF
     - 2 do STJ
     - 2 advogados (nomeados pelo Presidente)

Fases (TRE/TSE):
  1. Relatorio do Relator
  2. Voto do Relator
  3. Votos dos demais membros (6 votos)
  4. Proclamacao
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


class EleitoralSimulationService:
    """Simula julgamentos na Justica Eleitoral (Juiz Eleitoral, TRE e TSE)."""

    def __init__(self, simulation_id: str):
        self.simulation = Simulation.objects.get(id=simulation_id)
        self.documents = list(self.simulation.documents.all())
        self.config = self.simulation.config or {}

        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService
        self.llm = UnifiedLLMService()

        self.provider = self.config.get('provider', SIMULATION_PROVIDER)
        self.model = self.config.get('model', SIMULATION_MODEL)

        # Determine sub-type: eleitoral (juiz), tre, tse
        self.sub_type = self.simulation.simulation_type  # 'eleitoral', 'tre', 'tse'

        if self.sub_type in ('tre', 'tse'):
            self.members = self._load_members()
            self.relator = self._pick_relator()

    # ── Member loading ────────────────────────────────────────────────────

    def _load_members(self) -> List[MinisterProfile]:
        """Carrega membros do tribunal eleitoral."""
        if self.sub_type == 'tse':
            qs = MinisterProfile.objects.filter(court_type='TSE', is_active=True)
            members = list(qs)
            if not members:
                members = self._create_generic_tse_profiles()
            return members
        elif self.sub_type == 'tre':
            qs = MinisterProfile.objects.filter(court_type='TRE', is_active=True)
            members = list(qs)
            if not members:
                members = self._create_generic_tre_profiles()
            return members
        return []

    def _create_generic_tre_profiles(self) -> List[MinisterProfile]:
        """Cria 7 perfis genericos para o TRE."""
        generic = [
            ('Des. Marcos Ribeiro', 'centrista', 'Tecnico e processualista', 'Desembargador TJ'),
            ('Des. Ana Paula Vieira', 'progressista', 'Didatica e fundamentada', 'Desembargadora TJ'),
            ('Juiz Carlos Mendes', 'conservador', 'Formal e objetivo', 'Juiz de Direito'),
            ('Juiz Fernanda Lopes', 'pragmatico', 'Pragmatica e concisa', 'Juiza de Direito'),
            ('Juiz Federal Roberto Santos', 'centrista', 'Equilibrado e doutrinario', 'Juiz Federal'),
            ('Adv. Luisa Carvalho', 'progressista', 'Garantista e detalhada', 'Advogada'),
            ('Adv. Paulo Henrique Silva', 'conservador', 'Legalista e tecnico', 'Advogado'),
        ]

        profiles = []
        for name, philosophy, style, role in generic:
            profile = MinisterProfile(
                court_type='TRE',
                name=name,
                turma='TRE',
                judicial_philosophy=philosophy,
                specialty_areas=['Direito Eleitoral', 'Direito Constitucional'],
                notable_positions=[],
                profile_data={
                    'writing_style': style,
                    'tendencies': [],
                    'key_framework': 'Codigo Eleitoral e legislacao eleitoral',
                    'role_origin': role,
                },
            )
            profiles.append(profile)

        return profiles

    def _create_generic_tse_profiles(self) -> List[MinisterProfile]:
        """Cria 7 perfis genericos para o TSE."""
        generic = [
            ('Min. Antonio Barreto', 'centrista', 'Tecnico e didatico', 'STF'),
            ('Min. Patricia Moreira', 'progressista', 'Academica e fundamentada', 'STF'),
            ('Min. Ricardo Alves', 'conservador', 'Formal e processualista', 'STF'),
            ('Min. Helena Duarte', 'pragmatico', 'Pragmatica e objetiva', 'STJ'),
            ('Min. Marcos Oliveira', 'centrista', 'Equilibrado e doutrinario', 'STJ'),
            ('Adv. Claudia Ferreira', 'progressista', 'Garantista e detalhada', 'Advogada'),
            ('Adv. Jose Almeida', 'conservador', 'Legalista estrito', 'Advogado'),
        ]

        profiles = []
        for name, philosophy, style, origin in generic:
            profile = MinisterProfile(
                court_type='TSE',
                name=name,
                turma='TSE',
                judicial_philosophy=philosophy,
                specialty_areas=['Direito Eleitoral', 'Direito Constitucional'],
                notable_positions=[],
                profile_data={
                    'writing_style': style,
                    'tendencies': [],
                    'key_framework': 'Codigo Eleitoral e Constituicao Federal',
                    'court_origin': origin,
                },
            )
            profiles.append(profile)

        return profiles

    def _pick_relator(self) -> Optional[MinisterProfile]:
        """Seleciona o relator."""
        relator_name = self.config.get('relator')
        if relator_name:
            for m in self.members:
                if m.name == relator_name:
                    return m
        return self.members[0] if self.members else None

    # ── Main API ──────────────────────────────────────────────────────────

    def stream_simulation(self) -> Generator[Dict, None, None]:
        """Generator que produz eventos SSE para a simulacao eleitoral."""

        if self.sub_type == 'eleitoral':
            yield from self._stream_juiz_eleitoral()
        elif self.sub_type in ('tre', 'tse'):
            yield from self._stream_colegiado()

    def _stream_juiz_eleitoral(self) -> Generator[Dict, None, None]:
        """Simulacao simples de juiz eleitoral (1a instancia)."""
        self.simulation.status = 'running'
        self.simulation.save(update_fields=['status'])

        try:
            case_context = self._build_case_context()
            if not case_context.strip():
                yield self._event('error', 'Nenhum documento ou informacao do caso encontrado.')
                return

            case_type = self.config.get('case_type', 'propaganda_irregular')
            case_type_label = {
                'propaganda_irregular': 'Propaganda Irregular',
                'registro_candidatura': 'Registro de Candidatura',
                'prestacao_contas': 'Prestacao de Contas',
                'cassacao': 'Cassacao de Mandato',
                'abuso_poder': 'Abuso de Poder',
                'outros': 'Outros',
            }.get(case_type, case_type)

            # Phase 1: Analise
            yield self._progress_event('analise', 'Analise do Caso', 'Juiz Eleitoral analisando...', 20)
            yield self._event('phase', 'Analise do Caso Eleitoral')

            analise_prompt = (
                f"Voce e um Juiz Eleitoral de 1a instancia no Brasil.\n"
                f"Tipo de acao eleitoral: {case_type_label}\n\n"
                f"Analise o caso a seguir e emita uma SENTENCA ELEITORAL completa:\n"
                f"1. Relatorio (partes, fatos, pedidos)\n"
                f"2. Fundamentacao (Codigo Eleitoral, Lei 9.504/97, LC 64/90, jurisprudencia do TSE)\n"
                f"3. Dispositivo (procedente/improcedente e consequencias)\n\n"
                f"CASO:\n{case_context}\n\n"
                f"Seja tecnico e objetivo, no estilo das sentencas eleitorais. "
                f"Cite a legislacao eleitoral especifica aplicavel."
            )

            full_text = ''
            for chunk_text in self._stream_llm(
                analise_prompt,
                'Voce e um Juiz Eleitoral emitindo sentenca em acao eleitoral.',
            ):
                full_text += chunk_text
                yield self._event('sentenca', chunk_text)

            # Phase 2: Relatorio estrategico
            yield self._progress_event('report', 'Relatorio Estrategico', 'Analisando implicacoes...', 75)
            yield self._event('phase', 'Relatorio Estrategico')

            strategic_prompt = (
                f"Voce e um consultor juridico estrategico especializado em Direito Eleitoral.\n\n"
                f"SENTENCA DO JUIZ ELEITORAL:\n{full_text}\n\n"
                f"CASO:\n{case_context}\n\n"
                f"Produza um RELATORIO ESTRATEGICO:\n"
                f"1. Analise da sentenca e seus fundamentos\n"
                f"2. Viabilidade de recurso ao TRE\n"
                f"3. Chances de reforma da sentenca\n"
                f"4. Prazos e procedimentos recursais eleitorais\n"
                f"5. Impacto na candidatura/mandato\n"
                f"6. Providencias imediatas\n\n"
                f"Seja especifico e pratico."
            )

            strategic_text = ''
            for chunk_text in self._stream_llm(
                strategic_prompt,
                'Voce e um consultor juridico especializado em Direito Eleitoral.',
            ):
                strategic_text += chunk_text
                yield self._event('relatorio_estrategico', chunk_text, extra={'type': 'strategic_report'})

            # Detect disposition
            lower = full_text.lower()
            if 'improcedente' in lower:
                dispositivo = 'improcedente'
            elif 'parcialmente procedente' in lower:
                dispositivo = 'parcialmente_procedente'
            else:
                dispositivo = 'procedente'

            self.simulation.status = 'completed'
            self.simulation.result = {
                'case_type': case_type,
                'sentence': full_text,
                'strategic_report': strategic_text,
                'dispositivo': dispositivo,
            }
            self.simulation.save(update_fields=['status', 'result'])

            yield self._progress_event('complete', 'Concluido', 'Simulacao finalizada', 100)
            yield self._event('complete', 'Simulacao do Juiz Eleitoral concluida.')

        except Exception as e:
            logger.exception(f'[eleitoral_simulation] Erro: {e}')
            self.simulation.status = 'failed'
            self.simulation.save(update_fields=['status'])
            yield self._event('error', f'Erro na simulacao: {str(e)}')

    def _stream_colegiado(self) -> Generator[Dict, None, None]:
        """Simulacao colegiada para TRE (7 membros) ou TSE (7 ministros)."""
        self.simulation.status = 'running'
        self.simulation.save(update_fields=['status'])

        court_label = 'TSE' if self.sub_type == 'tse' else 'TRE'
        member_label = 'Ministro' if self.sub_type == 'tse' else 'Membro'

        try:
            case_context = self._build_case_context()
            if not case_context.strip():
                yield self._event('error', 'Nenhum documento ou informacao do caso encontrado.')
                return

            if not self.members:
                yield self._event('error', f'Nenhum membro encontrado para o {court_label}.')
                return

            total_members = len(self.members)
            relator = self.relator or self.members[0]

            case_type = self.config.get('case_type', 'propaganda_irregular')
            action_type = self.config.get('action_type', 'Recurso Eleitoral')

            # Emit member list
            yield self._event('ministers', '', extra={
                'ministers': [
                    {
                        'name': m.name,
                        'turma': m.turma or '',
                        'philosophy': m.judicial_philosophy,
                        'is_relator': m == relator,
                        'role_origin': (m.profile_data or {}).get('role_origin', '') or (m.profile_data or {}).get('court_origin', ''),
                    }
                    for m in self.members
                ],
            })

            # Phase 1: Relatorio do Relator
            yield self._progress_event('relatorio', 'Relatorio do Relator', f'{relator.name} elaborando relatorio...', 10)
            yield self._event('phase', 'Relatorio do Relator')
            relatorio_text = yield from self._phase_relatorio(case_context, relator, court_label, action_type)

            # Phase 2: Voto do Relator
            progress_per_member = 60 // total_members
            yield self._progress_event('voto_relator', 'Voto do Relator', f'{relator.name} proferindo voto...', 20)
            yield self._event('phase', f'Voto de {relator.name} (Relator)')
            relator_vote = yield from self._phase_vote(case_context, relator, relatorio_text, court_label, is_relator=True)

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
            other_members = [m for m in self.members if m != relator]
            for idx, member in enumerate(other_members):
                progress = 20 + ((idx + 1) * progress_per_member)
                yield self._progress_event(
                    f'voto_{idx}',
                    f'Voto de {member.name}',
                    f'{member.name} proferindo voto...',
                    min(progress, 80),
                )
                yield self._event('phase', f'Voto de {member.name}')
                member_vote = yield from self._phase_vote(
                    case_context, member, relatorio_text, court_label,
                    is_relator=False, previous_votes=votes,
                )
                votes.append({
                    'minister': member.name,
                    'vote': member_vote['vote'],
                    'is_relator': False,
                })
                yield self._event('vote_result', '', extra={
                    'minister': member.name,
                    'vote': member_vote['vote'],
                    'is_relator': False,
                    'votes_so_far': votes,
                })

            # Phase 4: Proclamacao
            yield self._progress_event('proclamacao', 'Proclamacao do Resultado', 'Contabilizando votos...', 85)
            yield self._event('phase', 'Proclamacao do Resultado')
            proclamacao = yield from self._phase_proclamacao(votes, case_context, court_label)

            # Phase 5: Relatorio estrategico
            yield self._progress_event('report', 'Relatorio Estrategico', 'Analisando implicacoes...', 95)
            yield self._event('phase', 'Relatorio Estrategico')
            strategic = yield from self._phase_strategic_report(case_context, votes, proclamacao, court_label)

            # Persist
            provimento_count = sum(
                1 for v in votes
                if 'provimento' in v['vote'].lower()
                or 'procedente' in v['vote'].lower()
                or 'deferido' in v['vote'].lower()
            )
            desprovimento_count = len(votes) - provimento_count

            self.simulation.status = 'completed'
            self.simulation.result = {
                'court': court_label,
                'case_type': case_type,
                'action_type': action_type,
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
            yield self._event('complete', f'Simulacao do {court_label} concluida.')

        except Exception as e:
            logger.exception(f'[{self.sub_type}_simulation] Erro: {e}')
            self.simulation.status = 'failed'
            self.simulation.save(update_fields=['status'])
            yield self._event('error', f'Erro na simulacao: {str(e)}')

    # ── Phases ────────────────────────────────────────────────────────────

    def _phase_relatorio(self, case_context: str, relator: MinisterProfile, court_label: str, action_type: str) -> Generator[Dict, None, str]:
        """Gera o relatorio do caso pelo relator."""
        composition_desc = ''
        if court_label == 'TRE':
            composition_desc = (
                'O TRE e composto por: 2 desembargadores do TJ, 2 juizes de direito, '
                '1 juiz federal e 2 advogados nomeados pelo Presidente da Republica.'
            )
        elif court_label == 'TSE':
            composition_desc = (
                'O TSE e composto por: 3 ministros do STF, 2 ministros do STJ e '
                '2 advogados nomeados pelo Presidente da Republica.'
            )

        prompt = (
            f"Voce e {relator.name}, relator no {court_label}.\n"
            f"{composition_desc}\n\n"
            f"Tipo de acao: {action_type}\n\n"
            f"Elabore o RELATORIO do caso a seguir, no formato tradicional da Justica Eleitoral:\n"
            f"1. Identificacao das partes e da acao\n"
            f"2. Sintese dos fatos e do pedido\n"
            f"3. Argumentos das partes\n"
            f"4. Parecer do Ministerio Publico Eleitoral (se aplicavel)\n"
            f"5. Admissibilidade\n\n"
            f"CASO:\n{case_context}\n\n"
            f"Seja objetivo e tecnico. Cite a legislacao eleitoral aplicavel "
            f"(Codigo Eleitoral, Lei 9.504/97, LC 64/90, resolucoes do TSE)."
        )

        full_text = ''
        for chunk_text in self._stream_llm(prompt, f'Voce e um relator no {court_label} elaborando relatorio.'):
            full_text += chunk_text
            yield self._event('relatorio', chunk_text)

        return full_text

    def _phase_vote(
        self,
        case_context: str,
        member: MinisterProfile,
        relatorio: str,
        court_label: str,
        is_relator: bool = False,
        previous_votes: Optional[List[Dict]] = None,
    ) -> Generator[Dict, None, Dict]:
        """Gera o voto de um membro do tribunal eleitoral."""
        profile_data = member.profile_data or {}
        philosophy = member.get_judicial_philosophy_display()
        specialties = ', '.join(member.specialty_areas or [])
        writing_style = profile_data.get('writing_style', '')
        role_origin = profile_data.get('role_origin', '') or profile_data.get('court_origin', '')

        previous_context = ''
        if previous_votes:
            prev_lines = [f"- {v['minister']}: {v['vote']}" for v in previous_votes]
            previous_context = f"\nVOTOS JA PROFERIDOS:\n" + '\n'.join(prev_lines) + '\n'

        prompt = (
            f"Voce e {member.name}, membro do {court_label}.\n"
            f"Origem: {role_origin}\n"
            f"Filosofia judicial: {philosophy}\n"
            f"Especialidades: {specialties}\n"
            f"Estilo de escrita: {writing_style}\n\n"
            f"RELATORIO DO CASO:\n{relatorio}\n\n"
            f"CASO COMPLETO:\n{case_context}\n"
            f"{previous_context}\n"
            f"{'Voce e o RELATOR deste caso.' if is_relator else 'Profira seu voto apos o relator.'}\n\n"
            f"PROFIRA SEU VOTO no estilo da Justica Eleitoral:\n"
            f"1. Fundamente com base na legislacao eleitoral (Codigo Eleitoral, Lei 9.504/97, LC 64/90)\n"
            f"2. Cite jurisprudencia do TSE e do TRE\n"
            f"3. Analise os fatos eleitorais relevantes\n"
            f"4. Ao final, DECLARE EXPRESSAMENTE se vota pelo PROVIMENTO ou DESPROVIMENTO, "
            f"PROCEDENCIA ou IMPROCEDENCIA\n"
            f"5. Se divergir do relator, justifique a divergencia\n\n"
            f"Mantenha o tom e estilo: {writing_style}"
        )

        full_text = ''
        for chunk_text in self._stream_llm(
            prompt,
            f'Voce e {member.name} do {court_label} proferindo voto eleitoral. '
            f'Filosofia: {philosophy}. Estilo: {writing_style}.',
        ):
            full_text += chunk_text
            yield self._event('vote_text', chunk_text, extra={
                'minister': member.name,
                'is_relator': is_relator,
            })

        vote_direction = self._detect_vote(full_text)

        # Save CourtVote if minister has pk
        if member.pk:
            CourtVote.objects.create(
                simulation=self.simulation,
                voter_name=member.name,
                voter_role='membro',
                minister_profile=member,
                vote=vote_direction,
                vote_text=full_text,
                is_relator=is_relator,
                is_dissent=(
                    not is_relator and previous_votes and
                    vote_direction != previous_votes[0].get('vote', '')
                ),
            )

        return {'vote': vote_direction, 'text': full_text}

    def _phase_proclamacao(self, votes: List[Dict], case_context: str, court_label: str) -> Generator[Dict, None, str]:
        """Gera a proclamacao do resultado."""
        votes_summary = '\n'.join(f"- {v['minister']}: {v['vote']}" for v in votes)

        provimento = sum(
            1 for v in votes
            if 'provimento' in v['vote'].lower()
            or 'procedente' in v['vote'].lower()
            or 'deferido' in v['vote'].lower()
        )
        desprovimento = len(votes) - provimento

        prompt = (
            f"Voce e o Presidente do {court_label} proclamando o resultado de um julgamento eleitoral.\n\n"
            f"VOTOS:\n{votes_summary}\n\n"
            f"PLACAR: {provimento} x {desprovimento}\n\n"
            f"Proclame o resultado no formato oficial da Justica Eleitoral:\n"
            f"1. Resumo do placar\n"
            f"2. Resultado (provido/desprovido, procedente/improcedente)\n"
            f"3. Quem votou com o relator e quem divergiu\n"
            f"4. Determinacoes decorrentes (cassacao, inelegibilidade, etc.)\n\n"
            f"Use o formato oficial: 'O Tribunal, por maioria/unanimidade...'"
        )

        full_text = ''
        for chunk_text in self._stream_llm(prompt, f'Voce e o Presidente do {court_label} proclamando resultado eleitoral.'):
            full_text += chunk_text
            yield self._event('proclamacao', chunk_text)

        return full_text

    def _phase_strategic_report(
        self, case_context: str, votes: List[Dict], proclamacao: str, court_label: str,
    ) -> Generator[Dict, None, str]:
        """Gera relatorio estrategico com base no resultado."""
        votes_summary = '\n'.join(f"- {v['minister']}: {v['vote']}" for v in votes)

        provimento = sum(
            1 for v in votes
            if 'provimento' in v['vote'].lower()
            or 'procedente' in v['vote'].lower()
            or 'deferido' in v['vote'].lower()
        )
        is_victory = provimento > (len(votes) - provimento)

        next_court = 'TSE' if court_label == 'TRE' else 'STF'

        prompt = (
            f"Voce e um consultor juridico estrategico especializado em Direito Eleitoral.\n"
            f"Analise o resultado do julgamento no {court_label}:\n\n"
            f"CASO:\n{case_context}\n\n"
            f"PLACAR:\n{votes_summary}\n\n"
            f"PROCLAMACAO:\n{proclamacao}\n\n"
            f"{'O cliente VENCEU.' if is_victory else 'O cliente PERDEU.'}\n\n"
            f"Produza um RELATORIO ESTRATEGICO:\n"
            f"1. Analise do placar e votos vencedores/vencidos\n"
            f"2. Membros-chave e fundamentos decisivos\n"
            f"3. Viabilidade de recurso ao {next_court}\n"
            f"4. Prazos recursais eleitorais (atencao: prazos eleitorais sao curtos!)\n"
            f"5. Impacto na candidatura/mandato\n"
            f"6. Risco de inelegibilidade (LC 64/90)\n"
            f"7. Providencias imediatas e proximos passos\n\n"
            f"Seja especifico e pratico. Lembre-se que a Justica Eleitoral tem prazos exiguos."
        )

        full_text = ''
        for chunk_text in self._stream_llm(
            prompt,
            'Voce e um consultor juridico especializado em Direito Eleitoral.',
        ):
            full_text += chunk_text
            yield self._event('relatorio_estrategico', chunk_text, extra={
                'type': 'strategic_report',
                'is_victory': is_victory,
            })

        return full_text

    # ── Helpers ───────────────────────────────────────────────────────────

    def _detect_vote(self, text: str) -> str:
        """Detecta direcao do voto no texto."""
        lower = text.lower()
        if 'nego provimento' in lower or 'desprovimento' in lower or 'desprovido' in lower:
            return 'desprovimento'
        if 'improcedente' in lower or 'improcedencia' in lower:
            return 'improcedente'
        if 'indefiro' in lower or 'indeferido' in lower:
            return 'indeferido'
        if 'dou provimento' in lower or 'provimento' in lower or 'provido' in lower:
            return 'provimento'
        if 'procedente' in lower or 'procedencia' in lower:
            return 'procedente'
        if 'defiro' in lower or 'deferido' in lower:
            return 'deferido'
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
        if self.config.get('case_type'):
            extra.append(f"Tipo de acao eleitoral: {self.config['case_type']}")
        if self.config.get('action_type'):
            extra.append(f"Tipo de recurso: {self.config['action_type']}")
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

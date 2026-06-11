"""
JurySimulationService — Orquestra a simulação completa do Tribunal do Júri.

Segue o rito do CPP art. 447+:
  1. Abertura pelo Juiz Presidente
  2. Sustentação oral da Acusação (Promotor)
  3. Sustentação oral da Defesa (Defensor)
  4. Réplica do Promotor (facultativa)
  5. Tréplica do Defensor (facultativa)
  6. Deliberação dos Jurados em sala secreta
  7. Votação dos Quesitos
  8. Sentença do Juiz Presidente baseada no veredicto
  9. Relatório Analítico pós-veredicto
"""
import json
import logging
import re
from typing import Dict, Generator, List, Optional

from ..models import Simulation, JuryDebateMessage, JuryMember


# ── ContextHarness ─────────────────────────────────────────────────────────


class ContextHarness:
    """Mantém contexto contínuo SEM limite artificial de tokens.

    Estratégia: compactação progressiva por importância, não por tamanho.
    Cada fase é resumida preservando TODOS os pontos essenciais.
    O contexto cresce mas é organizado hierarquicamente.
    """

    def __init__(self):
        # SEM max_context_tokens — usar o máximo disponível
        self._raw_entries: List[Dict] = []
        self._phase_summaries: Dict[str, str] = {}  # Resumo por fase
        self._key_arguments: List[str] = []    # Argumentos-chave (nunca truncados)
        self._evidence_cited: List[str] = []   # Provas citadas (nunca truncadas)
        self._opinion_history: List[Dict] = []  # Evolução de opiniões
        self._summaries: List[Dict] = []
        self._running_summary: str = ""

    def add_entry(self, phase: str, role: str, speaker: str, content: str):
        """Adiciona uma entrada ao contexto."""
        self._raw_entries.append({
            'phase': phase,
            'role': role,
            'speaker': speaker,
            'content': content,
            'timestamp': len(self._raw_entries),
        })

    def compact_phase(self, phase: str, llm_service, provider: str, model: str):
        """Ao final de cada fase, compacta as entradas daquela fase em um resumo."""
        phase_entries = [e for e in self._raw_entries if e['phase'] == phase]
        if not phase_entries:
            return

        phase_text = "\n".join([
            f"{e['speaker']} ({e['role']}): {e['content']}"
            for e in phase_entries
        ])

        prompt = (
            "Resuma os pontos ESSENCIAIS desta fase do julgamento em 3-5 bullet points.\n"
            "Mantenha: argumentos-chave, provas citadas, reações dos jurados, mudanças de posição.\n\n"
            f"FASE: {phase}\n"
            f"CONTEÚDO:\n{phase_text}\n\n"
            "RESUMO (3-5 bullet points):"
        )

        result = llm_service.generate(
            user_prompt=prompt,
            system_prompt="Você é um assistente jurídico que resume fases de julgamento de forma objetiva.",
            temperature=0.3,
            max_tokens=500,
            provider=provider,
            model=model,
        )
        summary = result.get('content', '')
        self._summaries.append({'phase': phase, 'summary': summary})
        self._phase_summaries[phase] = summary

        self._running_summary = "\n".join([
            f"**{s['phase'].upper()}**: {s['summary']}"
            for s in self._summaries
        ])

    def get_context_for_prompt(self, current_phase: str) -> str:
        """Retorna TODO o contexto disponível, organizado por importância."""
        if not self._running_summary:
            return "Início do julgamento."

        return self.get_full_context()

    def get_full_context(self) -> str:
        """Retorna TODO o contexto disponível, organizado por importância."""
        sections = []

        # 1. Argumentos-chave (sempre incluídos na íntegra)
        if self._key_arguments:
            sections.append("## ARGUMENTOS-CHAVE\n" + "\n".join(self._key_arguments))

        # 2. Provas citadas (sempre incluídas)
        if self._evidence_cited:
            sections.append("## PROVAS CITADAS\n" + "\n".join(self._evidence_cited))

        # 3. Resumos por fase (compactados mas completos)
        for phase, summary in self._phase_summaries.items():
            sections.append(f"## FASE: {phase.upper()}\n{summary}")

        # 4. Evolução de opiniões
        if self._opinion_history:
            sections.append("## EVOLUÇÃO DE OPINIÕES\n" + "\n".join(
                [f"- {o['speaker']}: {o['stance']} ({o['confidence']}% confiança) — {o['reason']}"
                 for o in self._opinion_history]
            ))

        # 5. Resumo corrente (fallback se nenhuma seção acima)
        if not sections and self._running_summary:
            return self._running_summary

        return "\n\n".join(sections) if sections else "Início do julgamento."

logger = logging.getLogger(__name__)

# Configurações padrão de modelo/provider para as simulações
SIMULATION_PROVIDER = 'watsonx'
SIMULATION_MODEL = 'mistralai/mistral-medium-2505'
SIMULATION_TEMPERATURE = 0.8
SIMULATION_MAX_TOKENS = 2048


class JurySimulationService:
    """Orquestra a simulação completa do tribunal do júri com IA."""

    # Mapeamento de labels de educacao do frontend para valores do modelo
    EDUCATION_MAP = {
        'Ensino Fundamental': 'fundamental',
        'Ensino Médio': 'medio',
        'Superior Incompleto': 'medio',
        'Superior Completo': 'superior',
        'Pós-graduação': 'pos_graduacao',
        'Mestrado': 'pos_graduacao',
        'Doutorado': 'pos_graduacao',
    }

    GENDER_MAP = {
        'Masculino': 'masculino',
        'Feminino': 'feminino',
    }

    def __init__(self, simulation_id: str):
        self.simulation = Simulation.objects.get(id=simulation_id)
        self.documents = list(self.simulation.documents.all())
        self.config = self.simulation.config or {}
        self._debate_history: List[Dict] = []
        self._votes: Dict[str, List[Dict]] = {}  # quesito -> [{member, vote}]
        self._conversation_memory: List[Dict] = []  # Historico completo do debate
        self._juror_opinions: Dict[str, Dict] = {}  # {juror_id: {stance, confidence, reasons}}
        self._opinion_history: List[Dict] = []  # Evolucao de opiniao ao longo do debate

        # Context Harness — memória compactada progressiva entre fases
        self.context_harness = ContextHarness()

        # LLM service — mesmo usado pelo copilot
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService
        self.llm = UnifiedLLMService()

        # Provider/modelo configuráveis via simulation.config
        self.provider = self.config.get('provider', SIMULATION_PROVIDER)
        self.model = self.config.get('model', SIMULATION_MODEL)

        # Criar jurados no banco se existem na config mas nao no DB
        self._ensure_jury_members()
        self.jury_members = list(self.simulation.jury_members.all())

    def _ensure_jury_members(self):
        """Cria jurados no banco a partir da config, se nao existirem."""
        existing = self.simulation.jury_members.count()
        jurors_config = self.config.get('jurors', [])
        if existing == 0 and jurors_config:
            for juror_data in jurors_config:
                education_label = juror_data.get('education', '')
                education_value = self.EDUCATION_MAP.get(education_label, 'medio')
                gender_label = juror_data.get('gender', '')
                gender_value = self.GENDER_MAP.get(gender_label, 'masculino')
                try:
                    JuryMember.objects.create(
                        simulation=self.simulation,
                        name=juror_data.get('name', 'Jurado'),
                        age=juror_data.get('age', 30),
                        gender=gender_value,
                        profession=juror_data.get('profession', ''),
                        education=education_value,
                        personality_traits=juror_data.get('personality_traits', []),
                        background=juror_data.get('background', ''),
                    )
                except Exception as e:
                    logger.warning(f'[jury_simulation] Erro ao criar jurado: {e}')

    def _save_intermediate_state(self, phase_completed: str):
        """Salva estado intermediário da simulação no banco após cada fase."""
        try:
            if not self.simulation.result:
                self.simulation.result = {}
            self.simulation.result['last_completed_phase'] = phase_completed
            self.simulation.result['intermediate_opinions'] = {
                k: {
                    'stance': v['stance'],
                    'confidence': v['confidence'],
                    'member_name': v.get('member_name', ''),
                }
                for k, v in self._juror_opinions.items()
            }
            self.simulation.result['opinion_evolution'] = self._opinion_history
            self.simulation.save(update_fields=['result'])
        except Exception as e:
            logger.warning(f'[jury_simulation] Erro ao salvar estado intermediario: {e}')

    # ── API principal ───────────────────────────────────────────────────────

    def stream_simulation(self) -> Generator[Dict, None, None]:
        """Generator que produz eventos SSE para cada fase do julgamento."""

        # Marcar simulação como em execução
        self.simulation.status = 'running'
        self.simulation.save(update_fields=['status'])

        try:
            # Extrair texto dos documentos
            case_context = self._build_case_context()

            # Se nao ha documentos, montar contexto a partir da config
            if not case_context.strip():
                case_context = self._build_context_from_config()

            if not case_context.strip():
                yield self._format_event(
                    'error', 'sistema',
                    'Nenhum documento ou informacao do caso encontrado. '
                    'Faca upload de documentos ou preencha os dados do caso antes de iniciar.',
                )
                return

            if len(self.jury_members) < 7:
                yield self._format_event(
                    'aviso', 'sistema',
                    f'O conselho de sentença possui {len(self.jury_members)} jurado(s). '
                    f'O Tribunal do Júri requer no mínimo 7 jurados (CPP art. 447).',
                )

            # Fase 1: Abertura pelo Juiz Presidente
            yield from self._phase_opening(case_context)
            self._save_intermediate_state('abertura')

            # Fase 2: Sustentação da Acusação (Promotor)
            yield from self._phase_prosecution(case_context)
            self._save_intermediate_state('acusacao')

            # Fase 3: Sustentação da Defesa (Defensor)
            yield from self._phase_defense(case_context)
            self._save_intermediate_state('defesa')

            # Fase 4: Réplica (se configurado)
            if self.config.get('include_replicas', True):
                yield from self._phase_replica(case_context)
                self._save_intermediate_state('replicas')

            # Fase 5: Tréplica (se configurado)
            if self.config.get('include_replicas', True):
                yield from self._phase_treplica(case_context)
                self._save_intermediate_state('treplicas')

            # Fase 6: Deliberação dos Jurados
            self.simulation.status = 'deliberating'
            self.simulation.save(update_fields=['status'])

            num_rounds = self.config.get('debate_rounds', 3)
            yield from self._phase_deliberation(case_context, num_rounds)
            self._save_intermediate_state('deliberacao')

            # Fase 7: Votação dos Quesitos
            yield from self._phase_voting(case_context)
            self._save_intermediate_state('quesitos')

            # Fase 8: Sentença
            yield from self._phase_sentence(case_context)
            self._save_intermediate_state('veredicto')

            # Compactar deliberação antes do relatório
            self.context_harness.compact_phase('deliberacao', self.llm, self.provider, self.model)

            # Fase 9: Relatório Analítico pós-veredicto
            yield from self._phase_report(case_context)

            # Persistir resultado
            self.simulation.status = 'completed'
            self.simulation.result = self._build_result()
            self.simulation.save(update_fields=['status', 'result'])

            # Emitir evento de veredicto com dados completos para o frontend
            result = self.simulation.result
            yield self._format_event(
                'veredicto', 'sistema',
                'Simulação do Tribunal do Júri concluída.',
                extra={
                    'type': 'verdict',
                    'final_verdict': 'absolvido' if result.get('verdict') == 'absolvicao' else 'condenado',
                    'probabilities': result.get('probabilities', {}),
                    'juror_opinions': result.get('juror_opinions', {}),
                    'opinion_evolution': result.get('opinion_evolution', []),
                    'score': result.get('deliberation_votes', {}),
                },
            )

            yield self._format_event(
                'concluido', 'sistema',
                'Simulação do Tribunal do Júri concluída.',
                extra={'type': 'completed', 'result': result},
            )

        except Exception as e:
            logger.exception(f'[jury_simulation] Erro na simulação {self.simulation.id}: {e}')
            self.simulation.status = 'failed'
            self.simulation.save(update_fields=['status'])
            yield self._format_event('erro', 'sistema', f'Erro na simulação: {str(e)}')

    # ── Fases ───────────────────────────────────────────────────────────────

    def _phase_opening(self, case_context: str) -> Generator[Dict, None, None]:
        """Juiz Presidente abre a sessão e explica os quesitos."""
        yield self._format_event('abertura', 'sistema', 'Abertura da Sessão do Tribunal do Júri',
                                 extra={'type': 'phase_change'})
        yield self._format_event('abertura', 'juiz', '', extra={'type': 'speaker_start'})

        crime_type = self.config.get('crime_type', 'Não especificado')
        quesitos = self._get_quesitos()
        quesitos_text = '\n'.join(f'  {i+1}. {q}' for i, q in enumerate(quesitos))

        prompt = (
            "Você é o JUIZ PRESIDENTE da sessão do Tribunal do Júri brasileiro.\n\n"
            "Sua função é ABRIR a sessão solemnemente, conforme CPP art. 472+.\n"
            "Faça o seguinte:\n"
            "1. Declare aberta a sessão\n"
            "2. Explique brevemente os fatos da denúncia\n"
            "3. Leia os quesitos que serão votados pelos jurados\n"
            "4. Instrua os jurados sobre seus deveres (sigilo, incomunicabilidade)\n\n"
            f"Tipo de crime: {crime_type}\n\n"
            f"QUESITOS:\n{quesitos_text}\n\n"
            f"RESUMO DO CASO (documentos):\n{case_context}\n\n"
            "Faça a abertura em 3-4 parágrafos, usando linguagem formal de plenário."
        )

        full_text = yield from self._stream_llm_phase('abertura', 'juiz', prompt)
        self._persist_message('abertura', 'juiz', full_text)
        yield self._format_event('abertura', 'juiz', '', extra={'type': 'speaker_end'})

    def _phase_prosecution(self, case_context: str) -> Generator[Dict, None, None]:
        """Promotor faz sustentação oral da acusação."""
        yield self._format_event('acusacao', 'sistema', 'Sustentação Oral da Acusação',
                                 extra={'type': 'phase_change'})
        yield self._format_event('acusacao', 'promotor', '', extra={'type': 'speaker_start'})

        crime_type = self.config.get('crime_type', 'Não especificado')
        prompt = (
            "Você é o PROMOTOR DE JUSTIÇA nesta sessão do Tribunal do Júri.\n\n"
            "Sua função é ACUSAR o réu com base nos documentos do processo.\n"
            "Faça uma sustentação oral convincente, citando provas, testemunhos e a lei.\n"
            "Seja firme, técnico e persuasivo. Use linguagem adequada ao plenário.\n"
            "Dirija-se aos senhores jurados e ao Excelentíssimo Juiz Presidente.\n\n"
            f"Tipo de crime: {crime_type}\n\n"
            f"DOCUMENTOS DO PROCESSO:\n{case_context}\n\n"
            "Faça sua sustentação oral da acusação em 4-6 parágrafos.\n"
            "Cite artigos do Código Penal e do CPP quando pertinente.\n"
            "Conclua pedindo a CONDENAÇÃO do réu."
        )

        full_text = yield from self._stream_llm_phase('acusacao', 'promotor', prompt)
        yield self._format_event('acusacao', 'promotor', '', extra={'type': 'speaker_end'})
        self._persist_message('acusacao', 'promotor', full_text)
        self._debate_history.append({'role': 'promotor', 'phase': 'acusacao', 'content': full_text})
        self.context_harness.add_entry('acusacao', 'promotor', 'Promotor de Justiça', full_text)
        self.context_harness.compact_phase('acusacao', self.llm, self.provider, self.model)

    def _phase_defense(self, case_context: str) -> Generator[Dict, None, None]:
        """Defensor faz sustentação oral da defesa."""
        yield self._format_event('defesa', 'sistema', 'Sustentação Oral da Defesa',
                                 extra={'type': 'phase_change'})
        yield self._format_event('defesa', 'defensor', '', extra={'type': 'speaker_start'})

        crime_type = self.config.get('crime_type', 'Não especificado')
        prosecution_summary = self._get_history_summary('acusacao')

        prompt = (
            "Você é o DEFENSOR PÚBLICO / ADVOGADO DE DEFESA nesta sessão do Tribunal do Júri.\n\n"
            "Sua função é DEFENDER o réu, rebatendo as acusações do Promotor.\n"
            "Aponte inconsistências nas provas, explore o in dubio pro reo, "
            "e busque a absolvição ou desclassificação do crime.\n"
            "Seja eloquente e emotivo quando necessário, mas sempre técnico.\n\n"
            f"Tipo de crime: {crime_type}\n\n"
            f"RESUMO DA ACUSAÇÃO DO PROMOTOR:\n{prosecution_summary}\n\n"
            f"DOCUMENTOS DO PROCESSO:\n{case_context}\n\n"
            "Faça sua sustentação oral da defesa em 4-6 parágrafos.\n"
            "Cite artigos da CF/88, Código Penal e CPP quando pertinente.\n"
            "Conclua pedindo a ABSOLVIÇÃO do réu (art. 386 do CPP) ou a "
            "desclassificação do crime para um tipo menos grave."
        )

        full_text = yield from self._stream_llm_phase('defesa', 'defensor', prompt)
        yield self._format_event('defesa', 'defensor', '', extra={'type': 'speaker_end'})
        self._persist_message('defesa', 'defensor', full_text)
        self._debate_history.append({'role': 'defensor', 'phase': 'defesa', 'content': full_text})
        self.context_harness.add_entry('defesa', 'defensor', 'Defensor', full_text)
        self.context_harness.compact_phase('defesa', self.llm, self.provider, self.model)

    def _phase_replica(self, case_context: str) -> Generator[Dict, None, None]:
        """Réplica do Promotor."""
        yield self._format_event('replicas', 'sistema', 'Réplica da Acusação',
                                 extra={'type': 'phase_change'})
        yield self._format_event('replicas', 'promotor', '', extra={'type': 'speaker_start'})

        defense_summary = self._get_history_summary('defesa')
        prompt = (
            "Você é o PROMOTOR DE JUSTIÇA em RÉPLICA nesta sessão do Tribunal do Júri.\n\n"
            "O Defensor acabou de apresentar seus argumentos. Agora é sua vez de replicar.\n"
            "Rebata os principais pontos da defesa, reforce suas provas e reitere o pedido "
            "de condenação.\n\n"
            f"ARGUMENTOS DA DEFESA:\n{defense_summary}\n\n"
            f"DOCUMENTOS DO PROCESSO:\n{case_context}\n\n"
            "Faça a réplica em 2-3 parágrafos, de forma incisiva e objetiva."
        )

        full_text = yield from self._stream_llm_phase('replicas', 'promotor', prompt)
        yield self._format_event('replicas', 'promotor', '', extra={'type': 'speaker_end'})
        self._persist_message('replicas', 'promotor', full_text)
        self._debate_history.append({'role': 'promotor', 'phase': 'replicas', 'content': full_text})
        self.context_harness.add_entry('replicas', 'promotor', 'Promotor (Réplica)', full_text)
        self.context_harness.compact_phase('replicas', self.llm, self.provider, self.model)

    def _phase_treplica(self, case_context: str) -> Generator[Dict, None, None]:
        """Tréplica do Defensor."""
        yield self._format_event('treplicas', 'sistema', 'Tréplica da Defesa',
                                 extra={'type': 'phase_change'})
        yield self._format_event('treplicas', 'defensor', '', extra={'type': 'speaker_start'})

        replica_summary = self._get_history_summary('replicas')
        prompt = (
            "Você é o DEFENSOR em TRÉPLICA nesta sessão do Tribunal do Júri.\n\n"
            "O Promotor acabou de fazer sua réplica. Agora é sua última oportunidade "
            "de convencer os jurados.\n"
            "Rebata os pontos da réplica, reforce a tese de defesa e apele ao senso "
            "de justiça dos jurados.\n\n"
            f"RÉPLICA DO PROMOTOR:\n{replica_summary}\n\n"
            f"DOCUMENTOS DO PROCESSO:\n{case_context}\n\n"
            "Faça a tréplica em 2-3 parágrafos, de forma emotiva mas fundamentada."
        )

        full_text = yield from self._stream_llm_phase('treplicas', 'defensor', prompt)
        yield self._format_event('treplicas', 'defensor', '', extra={'type': 'speaker_end'})
        self._persist_message('treplicas', 'defensor', full_text)
        self._debate_history.append({'role': 'defensor', 'phase': 'treplicas', 'content': full_text})
        self.context_harness.add_entry('treplicas', 'defensor', 'Defensor (Tréplica)', full_text)
        self.context_harness.compact_phase('treplicas', self.llm, self.provider, self.model)

    def _phase_deliberation(self, case_context: str, num_rounds: int) -> Generator[Dict, None, None]:
        """Jurados debatem entre si na sala secreta."""
        yield self._format_event('deliberacao', 'sistema', 'Deliberação do Conselho de Sentença (Sala Secreta)',
                                 extra={'type': 'phase_change'})

        if not self.jury_members:
            yield self._format_event(
                'aviso', 'sistema',
                'Nenhum jurado cadastrado. Adicione jurados antes de deliberar.',
            )
            return

        # Resumo dos argumentos para os jurados
        debate_summary = self._build_debate_summary()

        # Contexto compactado pelo harness para manter coerência entre fases
        harness_context = self.context_harness.get_context_for_prompt('deliberacao')

        for round_num in range(num_rounds):
            yield self._format_event(
                'deliberacao', 'sistema',
                f'Rodada de deliberação {round_num + 1} de {num_rounds}',
                extra={'type': 'round_update', 'round': round_num + 1, 'total_rounds': num_rounds},
            )

            for member in self.jury_members:
                previous_messages = self._get_deliberation_messages(round_num)

                traits_text = ', '.join(member.personality_traits) if member.personality_traits else 'Não definidos'
                other_opinions = self._get_other_jurors_opinions(member.id)
                prev_opinion = self._juror_opinions.get(str(member.id), {})
                prev_stance = prev_opinion.get('stance', 'indeciso')
                prev_confidence = prev_opinion.get('confidence', 0.5) * 100

                prompt = (
                    f"Você é {member.name}, um jurado no Tribunal do Júri brasileiro.\n\n"
                    f"SEU PERFIL:\n"
                    f"- Idade: {member.age} anos\n"
                    f"- Gênero: {member.get_gender_display()}\n"
                    f"- Profissão: {member.profession}\n"
                    f"- Escolaridade: {member.get_education_display()}\n"
                    f"- Traços de personalidade: {traits_text}\n"
                    f"- Background: {member.background or 'Não especificado'}\n\n"
                    "Você ouviu a acusação do promotor e a defesa do advogado.\n"
                    "Agora está na sala secreta deliberando com os outros jurados.\n\n"
                    f"RESUMO DO JULGAMENTO ATÉ AGORA:\n{harness_context}\n\n"
                    f"MEMÓRIA DO DEBATE (o que você já ouviu):\n"
                    f"- Promotor argumentou: {self._get_prosecution_summary()}\n"
                    f"- Defensor argumentou: {self._get_defense_summary()}\n"
                    f"- Outros jurados disseram:\n{other_opinions}\n\n"
                    f"Sua posição ANTERIOR era: {prev_stance}\n"
                    f"Confiança anterior: {prev_confidence:.0f}%\n\n"
                    f"RESUMO DOS ARGUMENTOS:\n{debate_summary}\n\n"
                    f"DOCUMENTOS DO PROCESSO:\n{case_context}\n\n"
                )

                if previous_messages:
                    prompt += f"MENSAGENS ANTERIORES DO DEBATE:\n{previous_messages}\n\n"

                prompt += (
                    "Você pode MUDAR de opinião se os argumentos forem convincentes.\n"
                    "Dê sua opinião sobre o caso em 2-3 frases, considerando seu perfil pessoal.\n"
                    "Seja natural, como uma pessoa real falaria nessa situação.\n"
                    "NÃO use linguagem jurídica sofisticada a menos que seu perfil justifique.\n"
                    "Considere as opiniões dos outros jurados se houver mensagens anteriores.\n"
                    "Indique sua posição atual (condenação ou absolvição) e sua confiança (0-100%)."
                )

                yield self._format_event('deliberacao', 'jurado', '',
                                         member_id=str(member.id),
                                         extra={'type': 'speaker_start', 'member_name': member.name})

                full_text = yield from self._stream_llm_phase(
                    'deliberacao', 'jurado', prompt,
                    member_id=str(member.id),
                    extra={'member_name': member.name, 'round': round_num + 1},
                    max_tokens=512,
                )

                yield self._format_event('deliberacao', 'jurado', '',
                                         member_id=str(member.id),
                                         extra={'type': 'speaker_end', 'member_name': member.name})
                self._persist_message('deliberacao', 'jurado', full_text, jury_member=member)
                self._debate_history.append({
                    'role': 'jurado',
                    'phase': 'deliberacao',
                    'member_name': member.name,
                    'member_id': str(member.id),
                    'round': round_num + 1,
                    'content': full_text,
                })
                self.context_harness.add_entry('deliberacao', 'jurado', member.name, full_text)

                # MiroFish: Atualizar opiniao e emitir tendencia
                self._update_juror_opinion(member.id, member.name, full_text, round_num + 1)
                probabilities = self._calculate_verdict_probabilities()

                yield self._format_event('deliberacao', 'sistema', '', None, {
                    'type': 'juror_tendency',
                    'member_id': str(member.id),
                    'member_name': member.name,
                    'stance': self._juror_opinions[str(member.id)]['stance'],
                    'confidence': self._juror_opinions[str(member.id)]['confidence'],
                    'probabilities': probabilities,
                    'round': round_num + 1,
                })

    def _phase_report(self, case_context: str) -> Generator[Dict, None, None]:
        """Gera relatório analítico detalhado do julgamento (Fase 9)."""
        yield self._format_event('relatorio', 'sistema', 'Relatório Analítico do Julgamento',
                                 extra={'type': 'phase_change'})

        debate_summary = self._compile_debate_summary()
        votes_summary = self._compile_votes_summary()

        prompt = (
            "Você é um analista jurídico especializado em Tribunal do Júri.\n"
            "Com base no julgamento simulado abaixo, produza um RELATÓRIO ANALÍTICO DETALHADO.\n\n"
            f"CASO:\n{case_context}\n\n"
            f"RESUMO DO DEBATE:\n{debate_summary}\n\n"
            f"VOTAÇÃO:\n{votes_summary}\n\n"
            "RELATÓRIO DEVE CONTER:\n\n"
            "## 1. SÍNTESE DO JULGAMENTO\n"
            "Resumo do caso, das partes e do resultado.\n\n"
            "## 2. ANÁLISE DA ACUSAÇÃO\n"
            "- Pontos fortes da argumentação do Promotor\n"
            "- Pontos fracos e vulnerabilidades\n"
            "- Provas utilizadas e seu impacto nos jurados\n\n"
            "## 3. ANÁLISE DA DEFESA\n"
            "- Pontos fortes da argumentação do Defensor\n"
            "- Pontos fracos e vulnerabilidades\n"
            "- Teses defensivas utilizadas e eficácia\n\n"
            "## 4. PERFIL E COMPORTAMENTO DOS JURADOS\n"
            "Para cada jurado, analisar:\n"
            "- Como seu perfil pessoal influenciou o voto\n"
            "- Momentos em que mudou de opinião (se houve)\n"
            "- Argumentos que mais o influenciaram\n\n"
            "## 5. FATORES DETERMINANTES DO VEREDICTO\n"
            "- Quais argumentos foram decisivos\n"
            "- Quais provas tiveram maior peso\n"
            "- Momentos-chave do julgamento\n\n"
            "## 6. ARGUMENTOS QUE PODERIAM ALTERAR O RESULTADO\n"
            "Se o resultado foi condenação:\n"
            "- Quais argumentos a defesa poderia ter apresentado\n"
            "- Quais provas poderiam fortalecer a defesa\n"
            "- Estratégias alternativas\n\n"
            "Se o resultado foi absolvição:\n"
            "- Quais argumentos a acusação poderia ter reforçado\n"
            "- Quais provas poderiam fortalecer a acusação\n"
            "- Pontos negligenciados pelo Promotor\n\n"
            "## 7. RECOMENDAÇÕES ESTRATÉGICAS\n"
            "- Para o advogado de defesa: como melhorar a estratégia\n"
            "- Para o promotor: como fortalecer a acusação\n"
            "- Pontos de atenção para um eventual recurso\n\n"
            "## 8. CONCLUSÃO\n"
            "Análise final sobre a solidez do veredicto e probabilidade de "
            "reforma em instância superior."
        )

        full_text = yield from self._stream_llm_phase(
            'relatorio', 'sistema', prompt, max_tokens=4096,
        )
        self._persist_message('relatorio', 'sistema', full_text)

        # Salvar relatório no resultado da simulação
        if not self.simulation.result:
            self.simulation.result = {}
        self.simulation.result['report'] = full_text
        self.simulation.save(update_fields=['result'])

    def _compile_debate_summary(self) -> str:
        """Compila resumo completo do debate para o relatório."""
        harness_ctx = self.context_harness.get_context_for_prompt('relatorio')
        if harness_ctx and harness_ctx != "Início do julgamento.":
            return harness_ctx
        return self._build_debate_summary()

    def _compile_votes_summary(self) -> str:
        """Compila resumo da votação dos quesitos para o relatório."""
        if not self._votes:
            return '(Nenhuma votação registrada)'
        lines = []
        for quesito, result in self._votes.items():
            if isinstance(result, dict):
                lines.append(
                    f'- "{quesito}": {result.get("resultado", "?")} '
                    f'(SIM: {result.get("sim", 0)} x NÃO: {result.get("nao", 0)})'
                )
        # Adicionar resumo de opiniões dos jurados
        for jid, opinion in self._juror_opinions.items():
            name = opinion.get('member_name', jid)
            stance = opinion.get('stance', '?')
            conf = opinion.get('confidence', 0) * 100
            lines.append(f'- {name}: {stance} (confiança: {conf:.0f}%)')
        return '\n'.join(lines)

    def _phase_voting(self, case_context: str) -> Generator[Dict, None, None]:
        """Cada jurado vota nos quesitos (sim/não)."""
        yield self._format_event('quesitos', 'sistema', 'Votação dos Quesitos',
                                 extra={'type': 'phase_change'})

        quesitos = self._get_quesitos()
        debate_summary = self._build_debate_summary()
        harness_context = self.context_harness.get_context_for_prompt('votacao')

        if not self.jury_members:
            yield self._format_event('aviso', 'sistema', 'Nenhum jurado para votar.')
            return

        for quesito in quesitos:
            yield self._format_event(
                'quesito', 'sistema',
                f'Quesito: "{quesito}"',
                extra={'quesito': quesito},
            )

            votes_sim = 0
            votes_nao = 0

            for member in self.jury_members:
                traits_text = ', '.join(member.personality_traits) if member.personality_traits else ''

                prompt = (
                    f"Você é {member.name} ({member.profession}, {member.age} anos, "
                    f"{member.get_education_display()}).\n"
                    f"Traços: {traits_text}\n\n"
                    "Com base em tudo que ouviu no julgamento e na deliberação, "
                    f"vote SIM ou NÃO para o quesito:\n\n"
                    f'"{quesito}"\n\n'
                    f"CONTEXTO ACUMULADO DO JULGAMENTO:\n{harness_context}\n\n"
                    f"RESUMO DO JULGAMENTO:\n{debate_summary}\n\n"
                    "Responda APENAS no formato:\n"
                    "VOTO: SIM (ou NÃO)\n"
                    "JUSTIFICATIVA: (uma frase breve)"
                )

                result = self.llm.generate(
                    user_prompt=prompt,
                    system_prompt=(
                        "Você é um jurado brasileiro votando em plenário. "
                        "Responda APENAS no formato solicitado."
                    ),
                    temperature=SIMULATION_TEMPERATURE,
                    max_tokens=200,
                    provider=self.provider,
                    model=self.model,
                )
                response_text = result.get('content', '')

                # Extrair voto
                vote = self._extract_vote(response_text)
                if vote == 'sim':
                    votes_sim += 1
                else:
                    votes_nao += 1

                # Persistir voto no JuryMember
                self._record_vote(member, quesito, vote, response_text)

                yield self._format_event(
                    'quesitos', 'jurado',
                    f'{member.name}: {response_text.strip()}',
                    member_id=str(member.id),
                    extra={
                        'quesito': quesito,
                        'vote': vote,
                        'member_name': member.name,
                    },
                )

            # Resultado do quesito
            total = votes_sim + votes_nao
            resultado = 'SIM' if votes_sim > votes_nao else 'NÃO'

            if quesito not in self._votes:
                self._votes[quesito] = []
            self._votes[quesito] = {
                'sim': votes_sim,
                'nao': votes_nao,
                'total': total,
                'resultado': resultado,
            }

            yield self._format_event(
                'resultado_quesito', 'sistema',
                f'Resultado: {resultado} (SIM: {votes_sim} x NÃO: {votes_nao})',
                extra={
                    'quesito': quesito,
                    'sim': votes_sim,
                    'nao': votes_nao,
                    'resultado': resultado,
                },
            )

    def _phase_sentence(self, case_context: str) -> Generator[Dict, None, None]:
        """Juiz Presidente profere a sentença com base no veredicto dos jurados."""
        yield self._format_event('veredicto', 'sistema', 'Sentença do Juiz Presidente',
                                 extra={'type': 'phase_change'})
        yield self._format_event('veredicto', 'juiz', '', extra={'type': 'speaker_start'})

        # Montar veredicto
        veredicto_lines = []
        for quesito, result in self._votes.items():
            veredicto_lines.append(
                f'- "{quesito}": {result["resultado"]} '
                f'(SIM: {result["sim"]} x NÃO: {result["nao"]})'
            )
        veredicto_text = '\n'.join(veredicto_lines) if veredicto_lines else 'Sem votação registrada.'

        crime_type = self.config.get('crime_type', 'Não especificado')

        prompt = (
            "Você é o JUIZ PRESIDENTE do Tribunal do Júri.\n\n"
            "Os jurados votaram nos quesitos e o resultado é o seguinte:\n\n"
            f"RESULTADO DA VOTAÇÃO:\n{veredicto_text}\n\n"
            f"Tipo de crime: {crime_type}\n\n"
            f"DOCUMENTOS DO PROCESSO:\n{case_context}\n\n"
            "Com base no veredicto dos jurados (que é soberano, CF art. 5º XXXVIII), "
            "profira a SENTENÇA.\n\n"
            "Estrutura da sentença:\n"
            "1. RELATÓRIO (resumo dos fatos)\n"
            "2. FUNDAMENTAÇÃO (com base no veredicto dos jurados)\n"
            "3. DISPOSITIVO (condenação ou absolvição, com dosimetria se condenação)\n\n"
            "Use linguagem formal, cite legislação (CP, CPP, CF).\n"
            "Se condenação, aplique a dosimetria da pena (art. 59 e 68 do CP)."
        )

        full_text = yield from self._stream_llm_phase('veredicto', 'juiz', prompt, max_tokens=4096)
        yield self._format_event('veredicto', 'juiz', '', extra={'type': 'speaker_end'})
        self._persist_message('veredicto', 'juiz', full_text)

    # ── MiroFish-style: Memoria e Opiniao ─────────────────────────────────

    def _get_prosecution_summary(self) -> str:
        """Retorna resumo completo dos argumentos da acusacao."""
        entries = [h for h in self._debate_history if h['role'] == 'promotor']
        if not entries:
            return '(Ainda nao apresentou argumentos)'
        return entries[-1]['content']

    def _get_defense_summary(self) -> str:
        """Retorna resumo completo dos argumentos da defesa."""
        entries = [h for h in self._debate_history if h['role'] == 'defensor']
        if not entries:
            return '(Ainda nao apresentou argumentos)'
        return entries[-1]['content']

    def _get_other_jurors_opinions(self, current_member_id) -> str:
        """Retorna resumo das opinioes dos outros jurados."""
        lines = []
        for jid, opinion in self._juror_opinions.items():
            if jid == str(current_member_id):
                continue
            # Encontrar nome do jurado
            name = jid
            for h in self._debate_history:
                if h.get('member_id') == jid:
                    name = h.get('member_name', jid)
                    break
            stance_label = 'condenacao' if opinion['stance'] == 'condenacao' else 'absolvicao'
            conf = opinion['confidence'] * 100
            lines.append(f"  - {name}: {stance_label} (confianca: {conf:.0f}%)")
        return '\n'.join(lines) if lines else '  (Nenhum jurado se pronunciou ainda)'

    def _update_juror_opinion(self, member_id, member_name: str, response_text: str, round_num: int):
        """Extrai posicao e confianca da resposta do jurado."""
        stance = 'absolvicao'
        lower_text = response_text.lower()
        conviction_words = ['culpado', 'condenação', 'condeno', 'condenar', 'condenacao', 'culpa']
        if any(word in lower_text for word in conviction_words):
            stance = 'condenacao'

        # Extrair confianca (procura por percentual)
        confidence_match = re.search(r'(\d{1,3})\s*%', response_text)
        confidence = int(confidence_match.group(1)) / 100 if confidence_match else 0.6
        confidence = min(confidence, 1.0)

        str_id = str(member_id)
        previous = self._juror_opinions.get(str_id, {})

        self._juror_opinions[str_id] = {
            'stance': stance,
            'confidence': confidence,
            'reasons': response_text,
            'member_name': member_name,
        }

        # Registrar evolucao
        self._opinion_history.append({
            'member_id': str_id,
            'member_name': member_name,
            'round': round_num,
            'stance': stance,
            'confidence': confidence,
            'previous_stance': previous.get('stance'),
            'changed': previous.get('stance') is not None and previous.get('stance') != stance,
        })

    def _calculate_verdict_probabilities(self) -> Dict:
        """Calcula probabilidades baseadas nos votos e confianca dos jurados."""
        total_conviction_weight = 0.0
        total_acquittal_weight = 0.0

        for opinion in self._juror_opinions.values():
            if opinion['stance'] == 'condenacao':
                total_conviction_weight += opinion['confidence']
            else:
                total_acquittal_weight += opinion['confidence']

        total = total_conviction_weight + total_acquittal_weight
        if total == 0:
            return {'condenacao': 50.0, 'absolvicao': 50.0}

        return {
            'condenacao': round(total_conviction_weight / total * 100, 1),
            'absolvicao': round(total_acquittal_weight / total * 100, 1),
        }

    # ── Helpers internos ────────────────────────────────────────────────────

    def _build_context_from_config(self) -> str:
        """Monta contexto minimo a partir da config da simulacao (quando nao ha documentos)."""
        parts = []
        if self.config.get('crime_type'):
            parts.append(f"Tipo de crime: {self.config['crime_type']}")
        if self.config.get('case_description') or self.simulation.description:
            desc = self.config.get('case_description') or self.simulation.description
            parts.append(f"Descricao do caso:\n{desc}")
        if self.config.get('case_title') or self.simulation.title:
            title = self.config.get('case_title') or self.simulation.title
            parts.append(f"Titulo do caso: {title}")
        # Jurors info from config (when not in DB)
        jurors_config = self.config.get('jurors', [])
        if jurors_config and not self.jury_members:
            parts.append(f"Numero de jurados: {len(jurors_config)}")
        if self.config.get('case_text'):
            parts.append(f"Texto do caso:\n{self.config['case_text']}")
        return '\n'.join(parts)

    def _build_case_context(self) -> str:
        """Monta contexto COMPLETO do caso — sem truncamento."""
        texts = []
        for doc in self.documents:
            if doc.extracted_text:
                label = doc.title
                try:
                    label += f' ({doc.get_document_type_display()})'
                except Exception:
                    logger.debug("get_document_type_display failed for doc %s", doc.id)
                # Usa TODO o texto extraído, sem limite
                texts.append(f"## {label}\n{doc.extracted_text}")
        return '\n\n---\n\n'.join(texts)

    def _get_quesitos(self) -> List[str]:
        """Retorna quesitos configurados ou os padrão do CPP art. 482+."""
        return self.config.get('quesitos', [
            'A materialidade do fato está provada?',
            'O acusado é autor ou partícipe do fato?',
            'O jurado absolve o acusado?',
        ])

    def _stream_llm_phase(
        self,
        phase: str,
        role: str,
        prompt: str,
        member_id: Optional[str] = None,
        extra: Optional[Dict] = None,
        max_tokens: int = SIMULATION_MAX_TOKENS,
    ) -> Generator[Dict, None, str]:
        """
        Faz streaming de uma chamada LLM e emite eventos SSE.
        Inclui retry com backoff exponencial para resiliência a falhas de API.

        Returns:
            O texto completo gerado (via generator return).
        """
        import time as _time

        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                full_text = ''
                _buf: list[str] = []
                _last_flush = _time.time()

                for chunk, final_result in self.llm.generate_stream(
                    user_prompt=prompt,
                    system_prompt=self._get_system_prompt(role),
                    temperature=SIMULATION_TEMPERATURE,
                    max_tokens=max_tokens,
                    provider=self.provider,
                    model=self.model,
                ):
                    if final_result is not None:
                        break
                    if chunk:
                        full_text += chunk
                        _buf.append(chunk)
                        _now = _time.time()
                        if _now - _last_flush >= 0.15 or len(_buf) >= 20:
                            yield self._format_event(phase, role, ''.join(_buf), member_id, extra)
                            _buf = []
                            _last_flush = _now

                # Flush remaining buffered chunks
                if _buf:
                    yield self._format_event(phase, role, ''.join(_buf), member_id, extra)

                return full_text  # Success — exit retry loop

            except Exception as e:
                last_error = e
                logger.warning(
                    f'[jury_simulation] LLM call failed in phase={phase} role={role} '
                    f'(attempt {attempt + 1}/{max_retries}): {e}'
                )
                if attempt < max_retries - 1:
                    delay = 2 * (2 ** attempt)  # 2s, 4s, 8s
                    _time.sleep(delay)
                    yield self._format_event(
                        phase, 'sistema',
                        f'Reconectando ao modelo de IA... (tentativa {attempt + 2}/{max_retries})',
                        extra={'type': 'message'},
                    )

        # All retries exhausted — yield error and return empty
        logger.error(
            f'[jury_simulation] LLM call exhausted retries in phase={phase}: {last_error}'
        )
        yield self._format_event(
            'erro', 'sistema',
            f'Erro ao gerar conteudo na fase {phase} apos {max_retries} tentativas.',
            extra={'type': 'error'},
        )
        return ''

    def _get_system_prompt(self, role: str) -> str:
        """Retorna system prompt adequado para cada papel."""
        prompts = {
            'juiz': (
                'Você é um Juiz Presidente do Tribunal do Júri brasileiro. '
                'Use linguagem formal, cite legislação e siga o rito do CPP.'
            ),
            'promotor': (
                'Você é um Promotor de Justiça em sessão do Tribunal do Júri. '
                'Seja firme, técnico e persuasivo na acusação.'
            ),
            'defensor': (
                'Você é um Defensor/Advogado em sessão do Tribunal do Júri. '
                'Defenda o réu com todos os argumentos disponíveis.'
            ),
            'jurado': (
                'Você é um jurado brasileiro, cidadão comum. '
                'Fale de forma natural e de acordo com seu perfil.'
            ),
        }
        return prompts.get(role, 'Você participa de uma sessão do Tribunal do Júri.')

    def _get_history_summary(self, phase: str) -> str:
        """Retorna resumo do histórico de uma fase específica."""
        entries = [h for h in self._debate_history if h['phase'] == phase]
        if not entries:
            return '(Nenhum argumento registrado)'
        parts = []
        for e in entries:
            parts.append(f"[{e['role'].upper()}]: {e['content']}")
        return '\n\n'.join(parts)

    def _build_debate_summary(self) -> str:
        """Monta resumo de toda a discussão até agora."""
        if not self._debate_history:
            return '(Nenhuma discussão registrada ainda)'
        parts = []
        for h in self._debate_history:
            label = h['role'].upper()
            if 'member_name' in h:
                label = f"JURADO {h['member_name']}"
            parts.append(f"[{label} — {h['phase']}]: {h['content']}")
        return '\n\n'.join(parts)

    def _get_deliberation_messages(self, current_round: int) -> str:
        """Retorna mensagens da deliberação de rodadas anteriores + rodada atual."""
        entries = [
            h for h in self._debate_history
            if h['phase'] == 'deliberacao'
        ]
        if not entries:
            return ''
        parts = []
        for e in entries:
            parts.append(f"{e.get('member_name', 'Jurado')}: {e['content']}")
        return '\n'.join(parts)

    def _extract_vote(self, response_text: str) -> str:
        """Extrai SIM/NÃO do texto de resposta do jurado."""
        text_upper = response_text.upper().strip()
        # Procurar padrão "VOTO: SIM" ou "VOTO: NÃO"
        if 'VOTO: SIM' in text_upper or 'VOTO:SIM' in text_upper:
            return 'sim'
        if 'VOTO: NÃO' in text_upper or 'VOTO:NÃO' in text_upper or 'VOTO: NAO' in text_upper:
            return 'nao'
        # Fallback: checar primeiros 20 chars
        start = text_upper[:20]
        if 'SIM' in start:
            return 'sim'
        return 'nao'

    def _record_vote(self, member, quesito: str, vote: str, reasoning: str):
        """Registra o voto do jurado no banco."""
        # Mapear para o campo vote do modelo (último quesito define o voto final)
        quesitos = self._get_quesitos()
        # Se é o quesito de absolvição, inverter a lógica
        if 'absolve' in quesito.lower():
            if vote == 'sim':
                member.vote = 'absolvicao'
            else:
                member.vote = 'condenacao'
        elif 'autor' in quesito.lower() or 'materialidade' in quesito.lower():
            # Quesitos de autoria/materialidade não mudam o voto final diretamente
            pass
        member.reasoning = reasoning.strip()
        member.save(update_fields=['vote', 'reasoning'])

    def _persist_message(
        self,
        phase: str,
        role: str,
        content: str,
        jury_member=None,
    ):
        """Salva mensagem de debate no banco."""
        try:
            JuryDebateMessage.objects.create(
                simulation=self.simulation,
                jury_member=jury_member,
                role=role,
                content=content,
                phase=phase,
            )
        except Exception as e:
            logger.warning(f'[jury_simulation] Erro ao persistir mensagem: {e}')

    def _build_result(self) -> Dict:
        """Monta o resultado final da simulacao com estatisticas MiroFish-style."""
        probabilities = self._calculate_verdict_probabilities()

        # Calcular votos e confianca media
        conviction_votes = sum(
            1 for o in self._juror_opinions.values() if o['stance'] == 'condenacao'
        )
        acquittal_votes = sum(
            1 for o in self._juror_opinions.values() if o['stance'] == 'absolvicao'
        )
        confidences = [o['confidence'] for o in self._juror_opinions.values()]
        avg_confidence = round(sum(confidences) / len(confidences), 3) if confidences else 0.5

        return {
            'votes': self._votes,
            'total_jurors': len(self.jury_members),
            'debate_rounds': self.config.get('debate_rounds', 3),
            'include_replicas': self.config.get('include_replicas', True),
            'quesitos': self._get_quesitos(),
            # MiroFish-style statistics
            'verdict': 'condenacao' if conviction_votes > acquittal_votes else 'absolvicao',
            'deliberation_votes': {
                'condenacao': conviction_votes,
                'absolvicao': acquittal_votes,
            },
            'probabilities': probabilities,
            'juror_opinions': {
                k: {
                    'stance': v['stance'],
                    'confidence': v['confidence'],
                    'reasons': v['reasons'],
                    'member_name': v.get('member_name', ''),
                }
                for k, v in self._juror_opinions.items()
            },
            'opinion_evolution': self._opinion_history,
            'confidence_level': avg_confidence,
            'unanimity': conviction_votes == len(self.jury_members) or acquittal_votes == len(self.jury_members),
        }

    def _format_event(
        self,
        phase: str,
        role: str,
        content: str,
        member_id: Optional[str] = None,
        extra: Optional[Dict] = None,
    ) -> Dict:
        """Formata evento SSE.

        Campos emitidos:
          - type: tipo do evento ('message', 'phase_change', 'juror_tendency', etc.)
          - event: alias de type (retrocompatibilidade)
          - phase: fase atual ('abertura', 'acusacao', ...)
          - role / sender_role: papel do emissor ('juiz', 'promotor', ...)
          - sender: nome do emissor (derivado de extra ou role)
          - content: conteúdo textual
          - member_id: ID do jurado (quando aplicável)
        """
        # Determinar tipo de evento
        event_type = 'message'
        if extra and 'type' in extra:
            event_type = extra['type']

        # Mapear role para sender_role (formato que o frontend espera)
        role_to_sender_role = {
            'juiz': 'judge',
            'promotor': 'prosecutor',
            'defensor': 'defense',
            'jurado': 'juror',
            'sistema': 'judge',
        }
        sender_role = role_to_sender_role.get(role, role)

        # Derivar nome do sender
        sender_name_map = {
            'juiz': 'Juiz Presidente',
            'promotor': 'Promotor de Justiça',
            'defensor': 'Defensor',
            'sistema': 'Sistema',
        }
        sender = sender_name_map.get(role, role)
        if extra and extra.get('member_name'):
            sender = extra['member_name']

        event = {
            'type': event_type,
            'event': event_type,
            'phase': phase,
            'role': role,
            'sender_role': sender_role,
            'sender': sender,
            'content': content,
        }
        if member_id:
            event['member_id'] = member_id
        if extra:
            event.update(extra)
        return event

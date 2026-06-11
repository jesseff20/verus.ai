"""
JudgeSimulationService — Simula a sentença de um juiz com base no perfil
e histórico de decisões.

Fases:
  1. Análise do perfil do juiz (estilo, padrões de decisão)
  2. Análise dos documentos do processo
  3. Geração da sentença completa (relatório, fundamentação, dispositivo)
"""
import json
import logging
import time
from typing import Dict, Generator, List, Optional

from ..models import Simulation, JudgeProfile

logger = logging.getLogger(__name__)

# Configurações padrão
JUDGE_PROVIDER = 'watsonx'
JUDGE_MODEL = 'mistralai/mistral-medium-2505'
JUDGE_TEMPERATURE = 0.6
JUDGE_MAX_TOKENS = 4096


class JudgeSimulationService:
    """Simula a sentença de um juiz com base no perfil e histórico de decisões."""

    def __init__(self, simulation_id: str):
        self.simulation = Simulation.objects.get(id=simulation_id)
        self.documents = list(self.simulation.documents.all())
        self.config = self.simulation.config or {}
        self.judge_profile = self._load_judge_profile()

        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService
        self.llm = UnifiedLLMService()

        self.provider = self.config.get('provider', JUDGE_PROVIDER)
        self.model = self.config.get('model', JUDGE_MODEL)

    def _load_judge_profile(self) -> Optional[JudgeProfile]:
        """Carrega perfil do juiz configurado na simulação."""
        judge_id = self.config.get('judge_id')
        if judge_id:
            try:
                return JudgeProfile.objects.get(id=judge_id)
            except JudgeProfile.DoesNotExist:
                logger.warning(f'[judge_simulation] Perfil de juiz {judge_id} não encontrado.')
        return None

    # ── API principal ───────────────────────────────────────────────────────

    def stream_simulation(self) -> Generator[Dict, None, None]:
        """Generator que produz eventos SSE para a simulação de sentença."""

        self.simulation.status = 'running'
        self.simulation.save(update_fields=['status'])

        try:
            case_context = self._build_case_context()

            # Se nao ha documentos, montar contexto a partir da config
            if not case_context.strip():
                case_context = self._build_context_from_config()

            if not case_context.strip():
                yield self._event(
                    'error',
                    'Nenhum documento ou informacao do caso encontrado. '
                    'Faca upload de documentos ou preencha os dados do caso antes de iniciar.',
                )
                return

            # Fase 1: Análise do perfil do juiz
            yield self._progress_event(
                'profile',
                'Analisando perfil do juiz',
                'Consultando histórico de decisões e padrões de julgamento...',
                16,
            )
            yield from self._phase_profile_analysis()

            # Fase 2: Análise dos documentos
            yield self._progress_event(
                'documents',
                'Analisando documentos',
                'Lendo petição inicial, contestação e provas anexadas...',
                33,
            )
            yield from self._phase_document_analysis(case_context)

            # Fase 3: Consulta de jurisprudência (implícita na geração)
            yield self._progress_event(
                'jurisprudence',
                'Consultando jurisprudência',
                'Buscando precedentes e súmulas aplicáveis ao caso...',
                50,
            )

            # Fase 4: Fundamentação
            yield self._progress_event(
                'fundamentacao',
                'Elaborando fundamentação',
                'Construindo a fundamentação jurídica da sentença...',
                66,
            )

            # Fase 5: Geração da sentença
            yield self._progress_event(
                'sentence',
                'Redigindo sentença',
                'Redigindo o relatório, fundamentação e dispositivo...',
                83,
            )
            sentence_text = yield from self._phase_sentence(case_context)

            # Fase 6: Relatório estratégico
            dispositivo = self._detect_dispositivo(sentence_text)
            yield self._progress_event(
                'report',
                'Gerando relatório estratégico',
                'Analisando pontos fortes, fracos e recomendações...',
                100,
            )
            strategic_report = yield from self._phase_strategic_report(
                case_context, sentence_text, dispositivo,
            )

            # Persistir resultado
            self.simulation.status = 'completed'
            self.simulation.result = {
                'judge_name': self.judge_profile.name if self.judge_profile else 'Juiz Genérico',
                'sentence': sentence_text,
                'dispositivo': dispositivo,
                'strategic_report': strategic_report,
                'process_type': self.config.get('process_type', ''),
                'case_value': self.config.get('case_value', ''),
                'state': self.config.get('state', ''),
                'comarca': self.config.get('comarca', ''),
            }
            self.simulation.save(update_fields=['status', 'result'])

            yield self._event('complete', 'Simulação de sentença concluída.')

        except Exception as e:
            logger.exception(f'[judge_simulation] Erro na simulação {self.simulation.id}: {e}')
            self.simulation.status = 'failed'
            self.simulation.save(update_fields=['status'])
            yield self._event('error', f'Erro na simulação: {str(e)}')

    # ── Fases ───────────────────────────────────────────────────────────────

    def _phase_profile_analysis(self) -> Generator[Dict, None, None]:
        """Analisa o perfil do juiz e informa ao usuário."""
        yield self._event('phase', 'Análise do Perfil do Juiz')

        if not self.judge_profile:
            yield self._event(
                'info',
                'Nenhum perfil de juiz selecionado. Será gerada uma sentença '
                'com base em um juiz genérico, sem viés específico.',
            )
            return

        profile_info = (
            f"Juiz: {self.judge_profile.name}\n"
            f"Tribunal: {self.judge_profile.court}\n"
            f"Comarca: {self.judge_profile.comarca}/{self.judge_profile.state}\n"
            f"Vara: {self.judge_profile.vara or 'Não especificada'}\n"
            f"Especialização: {self.judge_profile.specialization or 'Generalista'}"
        )

        yield self._event('profile', profile_info, extra={
            'judge_name': self.judge_profile.name,
            'court': self.judge_profile.court,
            'comarca': self.judge_profile.comarca,
            'state': self.judge_profile.state,
        })

        # Se houver padrões de decisão, informar
        if self.judge_profile.decision_patterns:
            patterns_text = json.dumps(
                self.judge_profile.decision_patterns,
                ensure_ascii=False,
                indent=2,
            )
            yield self._event(
                'patterns',
                f'Padrões de decisão identificados:\n{patterns_text}',
            )

    def _phase_document_analysis(self, case_context: str) -> Generator[Dict, None, None]:
        """Analisa os documentos do processo e gera resumo."""
        yield self._event('phase', 'Análise dos Documentos do Processo')

        prompt = (
            "Você é um analista jurídico. Analise os documentos do processo abaixo e "
            "produza um RESUMO ANALÍTICO contendo:\n\n"
            "1. PARTES: Autor/Réu/Terceiros envolvidos\n"
            "2. OBJETO: O que está sendo discutido\n"
            "3. FATOS RELEVANTES: Cronologia dos fatos\n"
            "4. QUESTÕES JURÍDICAS: Pontos de direito a decidir\n"
            "5. PROVAS: Provas documentais e periciais disponíveis\n\n"
            f"DOCUMENTOS:\n{case_context}\n\n"
            "Seja objetivo e conciso."
        )

        full_text = ''
        _buf: list[str] = []
        _last_flush = time.time()
        for chunk, final_result in self.llm.generate_stream(
            user_prompt=prompt,
            system_prompt='Você é um analista jurídico brasileiro experiente.',
            temperature=0.5,
            max_tokens=2048,
            provider=self.provider,
            model=self.model,
        ):
            if final_result is not None:
                break
            if chunk:
                full_text += chunk
                _buf.append(chunk)
                _now = time.time()
                if _now - _last_flush >= 0.15 or len(_buf) >= 20:
                    yield self._event('analysis', ''.join(_buf))
                    _buf = []
                    _last_flush = _now
        if _buf:
            yield self._event('analysis', ''.join(_buf))

    def _phase_sentence(self, case_context: str) -> Generator[Dict, None, str]:
        """Gera a sentença simulada no estilo do juiz."""
        yield self._event('phase', 'Geração da Sentença')

        judge_style = ''
        if self.judge_profile:
            patterns_json = ''
            if self.judge_profile.decision_patterns:
                patterns_json = json.dumps(
                    self.judge_profile.decision_patterns,
                    ensure_ascii=False,
                )

            profile_json = ''
            if self.judge_profile.profile_data:
                profile_json = json.dumps(
                    self.judge_profile.profile_data,
                    ensure_ascii=False,
                )

            judge_style = (
                f"\nPERFIL DO JUIZ: {self.judge_profile.name}\n"
                f"Tribunal: {self.judge_profile.court}\n"
                f"Comarca: {self.judge_profile.comarca}, {self.judge_profile.state}\n"
                f"Vara: {self.judge_profile.vara or 'Não especificada'}\n"
                f"Especialização: {self.judge_profile.specialization or 'Generalista'}\n"
            )
            if patterns_json:
                judge_style += f"Padrões de decisão: {patterns_json}\n"
            if profile_json:
                judge_style += f"Dados do perfil: {profile_json}\n"

        crime_type = self.config.get('crime_type', '')
        area = self.config.get('area', '')

        prompt = (
            "Você é um juiz de direito brasileiro. Gere uma SENTENÇA completa "
            "para o caso descrito nos documentos.\n\n"
            f"{judge_style}\n"
        )

        if crime_type:
            prompt += f"Tipo de crime/ação: {crime_type}\n"
        if area:
            prompt += f"Área do direito: {area}\n"

        prompt += (
            f"\nDOCUMENTOS DO PROCESSO:\n{case_context}\n\n"
            "Gere a sentença completa seguindo a estrutura:\n\n"
            "1. **RELATÓRIO** — Resumo dos fatos, pedidos do autor e contestação do réu\n"
            "2. **FUNDAMENTAÇÃO** — Análise jurídica detalhada com citação de:\n"
            "   - Legislação (CF/88, Códigos, Leis especiais)\n"
            "   - Jurisprudência (STF, STJ, tribunais estaduais)\n"
            "   - Doutrina quando pertinente\n"
            "3. **DISPOSITIVO** — Decisão final:\n"
            "   - Procedente / Improcedente / Parcialmente procedente\n"
            "   - Se condenação criminal: dosimetria da pena (arts. 59 e 68 do CP)\n"
            "   - Honorários, custas e demais providências\n\n"
            "A sentença deve ser realista, fundamentada e consistente com o perfil "
            "do juiz indicado (se houver)."
        )

        full_text = ''
        _buf: list[str] = []
        _last_flush = time.time()
        for chunk, final_result in self.llm.generate_stream(
            user_prompt=prompt,
            system_prompt=(
                'Você é um juiz de direito brasileiro redigindo uma sentença. '
                'Use linguagem formal, cite legislação e jurisprudência.'
            ),
            temperature=JUDGE_TEMPERATURE,
            max_tokens=JUDGE_MAX_TOKENS,
            provider=self.provider,
            model=self.model,
        ):
            if final_result is not None:
                break
            if chunk:
                full_text += chunk
                _buf.append(chunk)
                _now = time.time()
                if _now - _last_flush >= 0.15 or len(_buf) >= 20:
                    yield self._event('sentence', ''.join(_buf))
                    _buf = []
                    _last_flush = _now
        if _buf:
            yield self._event('sentence', ''.join(_buf))

        return full_text

    def _detect_dispositivo(self, sentence_text: str) -> str:
        """Detecta o dispositivo (procedente/improcedente/parcialmente) na sentença."""
        lower = sentence_text.lower()
        if 'parcialmente procedente' in lower:
            return 'parcialmente_procedente'
        if 'improcedente' in lower:
            return 'improcedente'
        if 'procedente' in lower:
            return 'procedente'
        return 'indeterminado'

    def _phase_strategic_report(
        self, case_context: str, sentence_text: str, dispositivo: str,
    ) -> Generator[Dict, None, str]:
        """Gera relatorio estrategico completo baseado na sentenca simulada."""
        yield self._event('phase', 'Relatório Estratégico')

        is_victory = dispositivo in ('procedente', 'parcialmente_procedente')

        if is_victory:
            header = '## RELATÓRIO DE VITÓRIA'
            sec1_title = '### 1. O QUE GARANTIU A VITÓRIA'
            sec1_body = (
                '- Liste todos os argumentos que foram determinantes para o resultado favorável\n'
                '- Identifique as provas que mais impactaram a decisão\n'
                '- Destaque os fundamentos jurídicos mais fortes'
            )
            sec2_body = (
                '- Liste TODOS os pontos fracos da nossa argumentação, mesmo tendo vencido\n'
                '- Identifique argumentos que o adversário poderia usar em recurso\n'
                '- Aponte riscos de reforma da sentença em 2ª instância'
            )
            sec3_title = '#### Se o adversário recorrer:'
            sec3_body = (
                '- Estratégia para manter a sentença em 2ª instância\n'
                '- Argumentos para contrarrazões\n'
                '- Jurisprudência de apoio para sustentar o resultado\n'
                '- Pontos que devem ser reforçados'
            )
            sec4_body = (
                '- O que fazer para blindar a sentença contra recursos\n'
                '- Providências imediatas (cumprimento provisório, cautelares)\n'
                '- Monitoramento de prazos recursais do adversário'
            )
            checklist = (
                '[ ] Verificar trânsito em julgado\n'
                '[ ] Iniciar cumprimento provisório (se cabível)\n'
                '[ ] Preparar contrarrazões preventivamente\n'
                '[ ] Monitorar prazo recursal do adversário\n'
                '[ ] Avaliar necessidade de cautelar'
            )
            result_desc = 'O cliente VENCEU a causa.'
        else:
            header = '## RELATÓRIO DE DERROTA'
            sec1_title = '### 1. POR QUE PERDEMOS'
            sec1_body = (
                '- Analise cada ponto da fundamentação do juiz que levou à improcedência\n'
                '- Identifique as falhas nos argumentos apresentados\n'
                '- Aponte as provas que faltaram ou foram insuficientes'
            )
            sec2_body = (
                '- Liste todos os argumentos que poderiam ter sido apresentados mas não foram\n'
                '- Identifique as teses jurídicas alternativas que poderiam mudar o resultado\n'
                '- Aponte as provas que deveriam ter sido produzidas'
            )
            sec3_title = '#### Para reverter a decisão em recurso:'
            sec3_body = (
                '- Tipo de recurso recomendado (apelação, embargos, etc.)\n'
                '- Argumentos específicos para as razões recursais\n'
                '- Jurisprudência favorável para fundamentar o recurso\n'
                '- Provas que podem ser requeridas em 2ª instância'
            )
            sec4_body = (
                '- Reformulação completa da estratégia processual\n'
                '- Novos documentos/provas a serem juntados\n'
                '- Pedidos incidentais que poderiam fortalecer a posição'
            )
            checklist = (
                '[ ] Interpor recurso dentro do prazo\n'
                '[ ] Requerer efeito suspensivo (se cabível)\n'
                '[ ] Solicitar gratuidade de justiça para recurso (se aplicável)\n'
                '[ ] Reunir novas provas/documentos\n'
                '[ ] Consultar especialista na matéria'
            )
            result_desc = 'O cliente PERDEU a causa.'

        prompt = (
            "Você é um consultor jurídico estratégico de alto nível.\n"
            "Analise a sentença simulada abaixo e produza um RELATÓRIO ESTRATÉGICO DETALHADO.\n\n"
            f"DOCUMENTOS DO PROCESSO:\n{case_context}\n\n"
            f"SENTENÇA SIMULADA:\n{sentence_text}\n\n"
            f"DISPOSITIVO: {dispositivo}\n\n"
            f"{result_desc}\n\n"
            "PRODUZA O SEGUINTE RELATÓRIO:\n\n"
            f"{header}\n\n"
            f"{sec1_title}\n{sec1_body}\n\n"
            f"### 2. PONTOS DE VULNERABILIDADE\n{sec2_body}\n\n"
            f"### 3. PLANO DE AÇÃO\n{sec3_title}\n{sec3_body}\n\n"
            f"### 4. AJUSTES RECOMENDADOS NO PROCESSO\n{sec4_body}\n\n"
            "### 5. ANÁLISE DE RISCO\n"
            "- Probabilidade de reforma em 2ª instância: X%\n"
            "- Pontos mais vulneráveis a ataque recursal\n"
            "- Cenários possíveis (melhor caso, pior caso, mais provável)\n"
            "- Recomendação final: o que fazer AGORA\n\n"
            f"### 6. CHECKLIST DE PROVIDÊNCIAS IMEDIATAS\n{checklist}\n\n"
            "Seja ESPECÍFICO e PRÁTICO. Cite artigos de lei, súmulas e jurisprudência quando possível.\n"
            "Não use linguagem genérica — refira-se aos fatos e argumentos CONCRETOS do caso."
        )

        full_text = ''
        _buf: list[str] = []
        _last_flush = time.time()
        for chunk, final_result in self.llm.generate_stream(
            user_prompt=prompt,
            system_prompt=(
                'Você é um consultor jurídico estratégico brasileiro de alto nível. '
                'Produza análises práticas, específicas e acionáveis.'
            ),
            temperature=0.5,
            max_tokens=JUDGE_MAX_TOKENS,
            provider=self.provider,
            model=self.model,
        ):
            if final_result is not None:
                break
            if chunk:
                full_text += chunk
                _buf.append(chunk)
                _now = time.time()
                if _now - _last_flush >= 0.15 or len(_buf) >= 20:
                    yield self._event('relatorio', ''.join(_buf), extra={
                        'type': 'strategic_report',
                        'dispositivo': dispositivo,
                        'is_victory': is_victory,
                    })
                    _buf = []
                    _last_flush = _now
        if _buf:
            yield self._event('relatorio', ''.join(_buf), extra={
                'type': 'strategic_report',
                'dispositivo': dispositivo,
                'is_victory': is_victory,
            })

        return full_text

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _build_context_from_config(self) -> str:
        """Monta contexto minimo a partir da config da simulacao (quando nao ha documentos)."""
        parts = []
        if self.config.get('process_type'):
            parts.append(f"Tipo de processo: {self.config['process_type']}")
        if self.config.get('case_value'):
            parts.append(f"Valor da causa: {self.config['case_value']}")
        if self.config.get('state'):
            parts.append(f"Estado: {self.config['state']}")
        if self.config.get('tribunal'):
            parts.append(f"Tribunal: {self.config['tribunal']}")
        if self.config.get('comarca'):
            parts.append(f"Comarca: {self.config['comarca']}")
        if self.config.get('case_description'):
            parts.append(f"Descricao do caso:\n{self.config['case_description']}")
        # Caso tenha sido enviado texto do caso diretamente na config
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

"""
TrabalhoSimulationService -- Simula sentenca da Vara do Trabalho (1a Instancia).

Fases:
  1. Audiencia Inicial (Conciliacao) -- CLT art. 846, tentativa obrigatoria
  2. Audiencia de Instrucao -- Depoimentos, provas
  3. Razoes Finais -- Breve resumo das partes
  4. Sentenca Trabalhista -- Analise individual por pedido (procedente/improcedente)
  5. Relatorio Estrategico
"""
import json
import logging
import time
from typing import Dict, Generator, List, Optional

from ..models import Simulation, JudgeProfile

logger = logging.getLogger(__name__)

SIMULATION_PROVIDER = 'watsonx'
SIMULATION_MODEL = 'mistralai/mistral-medium-2505'
SIMULATION_TEMPERATURE = 0.6
SIMULATION_MAX_TOKENS = 4096


class TrabalhoSimulationService:
    """Simula uma sentenca da Vara do Trabalho (1a instancia trabalhista)."""

    def __init__(self, simulation_id: str):
        self.simulation = Simulation.objects.get(id=simulation_id)
        self.documents = list(self.simulation.documents.all())
        self.config = self.simulation.config or {}
        self.judge_profile = self._load_judge_profile()

        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService
        self.llm = UnifiedLLMService()

        self.provider = self.config.get('provider', SIMULATION_PROVIDER)
        self.model = self.config.get('model', SIMULATION_MODEL)

    def _load_judge_profile(self) -> Optional[JudgeProfile]:
        judge_id = self.config.get('judge_id')
        if judge_id:
            try:
                return JudgeProfile.objects.get(id=judge_id)
            except JudgeProfile.DoesNotExist:
                logger.warning(f'[trabalho_simulation] Perfil de juiz {judge_id} nao encontrado.')
        return None

    # -- API principal ---

    def stream_simulation(self) -> Generator[Dict, None, None]:
        """Generator que produz eventos SSE para a simulacao trabalhista."""

        self.simulation.status = 'running'
        self.simulation.save(update_fields=['status'])

        try:
            case_context = self._build_case_context()

            if not case_context.strip():
                case_context = self._build_context_from_config()

            if not case_context.strip():
                yield self._event(
                    'error',
                    'Nenhum documento ou informacao do caso encontrado. '
                    'Faca upload de documentos ou preencha os dados do caso antes de iniciar.',
                )
                return

            # Fase 1: Audiencia Inicial (Conciliacao)
            yield self._progress_event(
                'conciliacao', 'Audiencia Inicial (Conciliacao)',
                'Tentativa obrigatoria de conciliacao conforme CLT art. 846...', 10,
            )
            yield self._event('phase', 'Audiencia Inicial - Conciliacao (CLT art. 846)')
            conciliacao_text = yield from self._phase_conciliacao(case_context)

            # Fase 2: Audiencia de Instrucao
            yield self._progress_event(
                'instrucao', 'Audiencia de Instrucao',
                'Colhendo depoimentos e analisando provas...', 30,
            )
            yield self._event('phase', 'Audiencia de Instrucao')
            instrucao_text = yield from self._phase_instrucao(case_context)

            # Fase 3: Razoes Finais
            yield self._progress_event(
                'razoes_finais', 'Razoes Finais',
                'Resumo dos argumentos das partes...', 50,
            )
            yield self._event('phase', 'Razoes Finais')
            razoes_text = yield from self._phase_razoes_finais(case_context)

            # Fase 4: Sentenca Trabalhista
            yield self._progress_event(
                'sentenca', 'Sentenca Trabalhista',
                'Analisando cada pedido individualmente...', 70,
            )
            yield self._event('phase', 'Sentenca Trabalhista')
            sentenca_text = yield from self._phase_sentenca(case_context, conciliacao_text, instrucao_text)

            # Fase 5: Relatorio Estrategico
            dispositivo = self._detect_dispositivo(sentenca_text)
            yield self._progress_event(
                'report', 'Relatorio Estrategico',
                'Analisando pontos fortes, fracos e recomendacoes...', 90,
            )
            yield self._event('phase', 'Relatorio Estrategico')
            strategic_report = yield from self._phase_strategic_report(case_context, sentenca_text, dispositivo)

            # Persist
            self.simulation.status = 'completed'
            self.simulation.result = {
                'judge_name': self.judge_profile.name if self.judge_profile else 'Juiz do Trabalho Generico',
                'conciliacao': conciliacao_text,
                'instrucao': instrucao_text,
                'razoes_finais': razoes_text,
                'sentence': sentenca_text,
                'dispositivo': dispositivo,
                'strategic_report': strategic_report,
                'process_type': self.config.get('process_type', ''),
                'case_value': self.config.get('case_value', ''),
                'claims': self.config.get('claims', []),
            }
            self.simulation.save(update_fields=['status', 'result'])

            yield self._progress_event('complete', 'Concluido', 'Simulacao finalizada', 100)
            yield self._event('complete', 'Simulacao da Vara do Trabalho concluida.')

        except Exception as e:
            logger.exception(f'[trabalho_simulation] Erro na simulacao {self.simulation.id}: {e}')
            self.simulation.status = 'failed'
            self.simulation.save(update_fields=['status'])
            yield self._event('error', f'Erro na simulacao: {str(e)}')

    # -- Fases ---

    def _phase_conciliacao(self, case_context: str) -> Generator[Dict, None, str]:
        """Fase 1: Audiencia de Conciliacao obrigatoria (CLT art. 846)."""
        claims = self.config.get('claims', [])
        claims_text = '\n'.join(f'- {c}' for c in claims) if claims else 'Nao especificados'

        prompt = (
            f"Voce e um juiz do trabalho presidindo a audiencia inicial de conciliacao "
            f"conforme CLT art. 846.\n\n"
            f"CASO:\n{case_context}\n\n"
            f"PEDIDOS DO RECLAMANTE:\n{claims_text}\n\n"
            f"Simule a AUDIENCIA DE CONCILIACAO:\n"
            f"1. Abertura formal da audiencia\n"
            f"2. Tentativa de acordo entre as partes\n"
            f"3. Propostas de conciliacao\n"
            f"4. Resultado: ACORDO NAO ALCANCADO (para prosseguir com instrucao)\n\n"
            f"Lembre-se: A conciliacao e OBRIGATORIA na Justica do Trabalho. "
            f"Mesmo que frustrada, deve constar na ata."
        )

        full_text = ''
        for chunk_text in self._stream_llm(prompt, 'Voce e um juiz do trabalho conduzindo audiencia de conciliacao.'):
            full_text += chunk_text
            yield self._event('conciliacao', chunk_text)

        return full_text

    def _phase_instrucao(self, case_context: str) -> Generator[Dict, None, str]:
        """Fase 2: Audiencia de instrucao e julgamento."""
        prompt = (
            f"Voce e um juiz do trabalho conduzindo a audiencia de instrucao.\n\n"
            f"CASO:\n{case_context}\n\n"
            f"Simule a AUDIENCIA DE INSTRUCAO:\n"
            f"1. Depoimento do reclamante\n"
            f"2. Depoimento do preposto do reclamado\n"
            f"3. Oitiva de testemunhas (se houver)\n"
            f"4. Analise de documentos juntados\n"
            f"5. Provas periciais (se aplicavel - insalubridade, periculosidade)\n\n"
            f"Foque nos fatos relevantes para a decisao. Seja objetivo."
        )

        full_text = ''
        for chunk_text in self._stream_llm(prompt, 'Voce e um juiz do trabalho conduzindo audiencia de instrucao.'):
            full_text += chunk_text
            yield self._event('instrucao', chunk_text)

        return full_text

    def _phase_razoes_finais(self, case_context: str) -> Generator[Dict, None, str]:
        """Fase 3: Razoes finais das partes."""
        prompt = (
            f"Voce e o relator resumindo as razoes finais das partes em reclamacao trabalhista.\n\n"
            f"CASO:\n{case_context}\n\n"
            f"Apresente as RAZOES FINAIS:\n"
            f"1. Razoes finais do reclamante (pedidos, fundamentos)\n"
            f"2. Razoes finais do reclamado (defesa, contestacao)\n\n"
            f"Seja breve e objetivo."
        )

        full_text = ''
        for chunk_text in self._stream_llm(prompt, 'Voce e um assessor juridico resumindo razoes finais trabalhistas.'):
            full_text += chunk_text
            yield self._event('razoes_finais', chunk_text)

        return full_text

    def _phase_sentenca(
        self, case_context: str, conciliacao: str, instrucao: str,
    ) -> Generator[Dict, None, str]:
        """Fase 4: Sentenca trabalhista com analise por pedido."""
        claims = self.config.get('claims', [])
        claims_text = '\n'.join(f'- {c}' for c in claims) if claims else 'Nao especificados'
        case_value = self.config.get('case_value', '')

        judge_style = ''
        if self.judge_profile:
            judge_style = (
                f"\nPERFIL DO JUIZ: {self.judge_profile.name}\n"
                f"Tribunal: {self.judge_profile.court}\n"
                f"Vara: {self.judge_profile.vara or 'Nao especificada'}\n"
                f"Especializacao: {self.judge_profile.specialization or 'Trabalhista'}\n"
            )
            if self.judge_profile.decision_patterns:
                judge_style += f"Padroes de decisao: {json.dumps(self.judge_profile.decision_patterns, ensure_ascii=False)}\n"

        prompt = (
            f"Voce e um juiz do trabalho proferindo SENTENCA em reclamacao trabalhista.\n"
            f"{judge_style}\n"
            f"CASO:\n{case_context}\n\n"
            f"CONCILIACAO:\n{conciliacao[:500]}\n\n"
            f"INSTRUCAO:\n{instrucao[:500]}\n\n"
            f"PEDIDOS DO RECLAMANTE:\n{claims_text}\n"
            f"{'VALOR DA CAUSA: ' + case_value if case_value else ''}\n\n"
            f"Gere a SENTENCA TRABALHISTA completa:\n\n"
            f"1. **RELATORIO** - Resumo dos fatos e pedidos\n"
            f"2. **FUNDAMENTACAO** - Para CADA PEDIDO, analise individualmente:\n"
            f"   - Verbas rescisorias (saldo de salario, aviso previo, 13o, ferias + 1/3)\n"
            f"   - Horas extras e reflexos\n"
            f"   - FGTS + multa de 40%\n"
            f"   - Adicional de insalubridade/periculosidade\n"
            f"   - Dano moral trabalhista\n"
            f"   - Outros pedidos especificos\n"
            f"   - Para cada: PROCEDENTE ou IMPROCEDENTE com fundamentacao\n"
            f"3. **DISPOSITIVO** - Decisao final:\n"
            f"   - Lista de pedidos procedentes e improcedentes\n"
            f"   - Valor total da condenacao (quando procedente)\n"
            f"   - Juros e correcao monetaria\n"
            f"   - Custas processuais\n"
            f"   - Contribuicoes previdenciarias e fiscais\n\n"
            f"Fundamente com CLT, sumulas do TST, OJs da SDI e jurisprudencia trabalhista."
        )

        full_text = ''
        for chunk_text in self._stream_llm(
            prompt,
            'Voce e um juiz do trabalho redigindo sentenca. '
            'Use linguagem formal, cite CLT, sumulas do TST e jurisprudencia trabalhista.',
        ):
            full_text += chunk_text
            yield self._event('sentence', chunk_text)

        return full_text

    def _phase_strategic_report(
        self, case_context: str, sentenca: str, dispositivo: str,
    ) -> Generator[Dict, None, str]:
        """Fase 5: Relatorio estrategico."""
        is_victory = dispositivo in ('procedente', 'parcialmente_procedente')

        prompt = (
            f"Voce e um consultor juridico trabalhista estrategico de alto nivel.\n"
            f"Analise a sentenca trabalhista simulada:\n\n"
            f"CASO:\n{case_context}\n\n"
            f"SENTENCA:\n{sentenca}\n\n"
            f"DISPOSITIVO: {dispositivo}\n\n"
            f"{'O cliente VENCEU.' if is_victory else 'O cliente PERDEU.'}\n\n"
            f"Produza um RELATORIO ESTRATEGICO:\n"
            f"1. Analise dos pedidos procedentes e improcedentes\n"
            f"2. Calculos trabalhistas estimados\n"
            f"3. Viabilidade de Recurso Ordinario (RO) ao TRT\n"
            f"4. Pontos fortes e vulneraveis da sentenca\n"
            f"5. Estrategia para o recurso (se cabivel)\n"
            f"6. Possibilidade de acordo em 2a instancia\n"
            f"7. Providencias imediatas e proximos passos\n\n"
            f"Seja especifico, cite CLT, sumulas do TST e OJs."
        )

        full_text = ''
        for chunk_text in self._stream_llm(
            prompt,
            'Voce e um consultor juridico trabalhista estrategico.',
        ):
            full_text += chunk_text
            yield self._event('relatorio_estrategico', chunk_text, extra={
                'type': 'strategic_report',
                'dispositivo': dispositivo,
                'is_victory': is_victory,
            })

        return full_text

    # -- Helpers ---

    def _detect_dispositivo(self, sentenca: str) -> str:
        lower = sentenca.lower()
        if 'parcialmente procedente' in lower:
            return 'parcialmente_procedente'
        if 'improcedente' in lower and 'procedente' not in lower.replace('improcedente', ''):
            return 'improcedente'
        if 'procedente' in lower:
            return 'procedente'
        return 'indeterminado'

    def _build_context_from_config(self) -> str:
        parts = []
        if self.config.get('process_type'):
            parts.append(f"Tipo de processo: {self.config['process_type']}")
        if self.config.get('case_value'):
            parts.append(f"Valor da causa: {self.config['case_value']}")
        if self.config.get('claims'):
            parts.append(f"Pedidos: {', '.join(self.config['claims'])}")
        if self.config.get('case_description'):
            parts.append(f"Descricao do caso:\n{self.config['case_description']}")
        if self.config.get('case_text'):
            parts.append(f"Texto do caso:\n{self.config['case_text']}")
        return '\n'.join(parts)

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
        if self.config.get('claims'):
            extra.append(f"Pedidos: {', '.join(self.config['claims'])}")
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

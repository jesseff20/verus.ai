"""
JECSimulationService — Simula procedimento do Juizado Especial Cível (Lei 9.099/95).

Fases:
  1. Triagem — Verificação de competência (valor < 40 SM)
  2. Audiência de Conciliação — Tentativa obrigatória de acordo (50% chance)
  3. Audiência de Instrução e Julgamento — Se conciliação falhar
  4. Sentença Simplificada — Art. 38: sem relatório formal
  5. Relatório Estratégico — Análise e recomendações

JECRIMSimulationService — Simula procedimento do Juizado Especial Criminal (Lei 9.099/95).

Fases:
  1. Audiência Preliminar
  2. Proposta de Transação Penal (art. 76)
  3. Análise da Transação (aceitação/rejeição)
  4. Se rejeitada: Suspensão Condicional do Processo (art. 89)
  5. Se tudo rejeitado: Instrução + Sentença
  6. Relatório Estratégico
"""
import json
import logging
import random
import time
from typing import Dict, Generator, Optional

from ..models import Simulation

logger = logging.getLogger(__name__)

# Configurações padrão
JEC_PROVIDER = 'watsonx'
JEC_MODEL = 'mistralai/mistral-medium-2505'
JEC_TEMPERATURE = 0.6
JEC_MAX_TOKENS = 4096


class JECSimulationService:
    """Simula procedimento do Juizado Especial Cível (Lei 9.099/95)."""

    def __init__(self, simulation_id: str):
        self.simulation = Simulation.objects.get(id=simulation_id)
        self.documents = list(self.simulation.documents.all())
        self.config = self.simulation.config or {}

        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService
        self.llm = UnifiedLLMService()

        self.provider = self.config.get('provider', JEC_PROVIDER)
        self.model = self.config.get('model', JEC_MODEL)

    # ── API principal ───────────────────────────────────────────────────────

    def stream_simulation(self) -> Generator[Dict, None, None]:
        """Generator que produz eventos SSE para a simulação JEC."""

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

            # Fase 1: Triagem
            yield self._progress_event(
                'triagem', 'Triagem de Competência',
                'Verificando se o caso é elegível para o Juizado Especial Cível (valor < 40 SM)...',
                10,
            )
            yield from self._phase_triagem(case_context)

            # Fase 2: Audiência de Conciliação
            yield self._progress_event(
                'conciliacao', 'Audiência de Conciliação',
                'Simulando tentativa obrigatória de conciliação entre as partes...',
                30,
            )
            conciliation_result = yield from self._phase_conciliacao(case_context)

            sentence_text = ''
            dispositivo = ''

            if conciliation_result.get('acordo'):
                # Acordo alcançado
                yield self._progress_event(
                    'acordo', 'Acordo Homologado',
                    'As partes chegaram a um acordo. Homologando...',
                    70,
                )
                sentence_text = conciliation_result.get('text', '')
                dispositivo = 'acordo'
            else:
                # Fase 3: Audiência de Instrução e Julgamento
                yield self._progress_event(
                    'instrucao', 'Audiência de Instrução e Julgamento',
                    'Conciliação frustrada. Iniciando audiência de instrução e julgamento...',
                    50,
                )
                yield from self._phase_instrucao(case_context)

                # Fase 4: Sentença Simplificada
                yield self._progress_event(
                    'sentenca', 'Sentença Simplificada',
                    'Redigindo sentença simplificada (art. 38 - dispensado relatório formal)...',
                    70,
                )
                sentence_text = yield from self._phase_sentenca(case_context)
                dispositivo = self._detect_dispositivo(sentence_text)

            # Fase 5: Relatório Estratégico
            yield self._progress_event(
                'relatorio', 'Relatório Estratégico',
                'Analisando resultado e gerando recomendações...',
                90,
            )
            strategic_report = yield from self._phase_relatorio_estrategico(
                case_context, sentence_text, dispositivo,
            )

            # Persistir resultado
            self.simulation.status = 'completed'
            self.simulation.result = {
                'sentence': sentence_text,
                'dispositivo': dispositivo,
                'strategic_report': strategic_report,
                'conciliation_achieved': conciliation_result.get('acordo', False),
                'process_type': self.config.get('process_type', ''),
                'case_value': self.config.get('case_value', ''),
                'claim_type': self.config.get('claim_type', ''),
            }
            self.simulation.save(update_fields=['status', 'result'])

            yield self._progress_event(
                'complete', 'Simulação Concluída',
                'Simulação do Juizado Especial Cível finalizada.',
                100,
            )
            yield self._event('complete', 'Simulação JEC concluída.')

        except Exception as e:
            logger.exception(f'[jec_simulation] Erro na simulação {self.simulation.id}: {e}')
            self.simulation.status = 'failed'
            self.simulation.save(update_fields=['status'])
            yield self._event('error', f'Erro na simulação: {str(e)}')

    # ── Fases ───────────────────────────────────────────────────────────────

    def _phase_triagem(self, case_context: str) -> Generator[Dict, None, None]:
        """Verifica elegibilidade do caso para o JEC."""
        yield self._event('phase', 'Triagem de Competência — Juizado Especial Cível')

        prompt = (
            "Você é um servidor do Juizado Especial Cível analisando a admissibilidade de uma demanda.\n\n"
            "Analise o caso abaixo e verifique se atende aos requisitos da Lei 9.099/95:\n"
            "1. Valor da causa inferior a 40 salários mínimos\n"
            "2. Matéria compatível com o rito sumaríssimo\n"
            "3. Partes legitimadas (pessoa física, microempresa, EPP)\n"
            "4. Não necessita de prova pericial complexa\n\n"
            f"CASO:\n{case_context}\n\n"
            "Produza uma ANÁLISE DE ADMISSIBILIDADE concisa indicando se o caso é elegível "
            "e eventuais ressalvas."
        )

        full_text = ''
        _buf: list[str] = []
        _last_flush = time.time()
        for chunk, final_result in self.llm.generate_stream(
            user_prompt=prompt,
            system_prompt='Você é um servidor do Juizado Especial Cível brasileiro.',
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
                    yield self._event('triagem', ''.join(_buf))
                    _buf = []
                    _last_flush = _now
        if _buf:
            yield self._event('triagem', ''.join(_buf))

    def _phase_conciliacao(self, case_context: str) -> Generator[Dict, None, dict]:
        """Simula audiência de conciliação obrigatória. 50% chance de acordo."""
        yield self._event('phase', 'Audiência de Conciliação')

        acordo = random.random() < 0.5

        if acordo:
            prompt = (
                "Você é um conciliador do Juizado Especial Cível.\n\n"
                "As partes chegaram a um ACORDO na audiência de conciliação.\n"
                "Redija o TERMO DE ACORDO com:\n"
                "1. Identificação das partes\n"
                "2. Objeto do acordo\n"
                "3. Obrigações assumidas por cada parte\n"
                "4. Prazo para cumprimento\n"
                "5. Multa por descumprimento\n"
                "6. Cláusula de homologação judicial\n\n"
                f"CASO:\n{case_context}\n\n"
                "Redija um termo de acordo realista e equilibrado."
            )
            system = 'Você é um conciliador do Juizado Especial Cível brasileiro redigindo um termo de acordo.'
        else:
            prompt = (
                "Você é um conciliador do Juizado Especial Cível.\n\n"
                "A audiência de conciliação foi realizada, mas as partes NÃO chegaram a um acordo.\n"
                "Descreva brevemente:\n"
                "1. As propostas apresentadas por cada parte\n"
                "2. Os pontos de divergência\n"
                "3. Por que a conciliação foi frustrada\n"
                "4. Encaminhamento para audiência de instrução e julgamento\n\n"
                f"CASO:\n{case_context}\n\n"
                "Seja objetivo e conciso."
            )
            system = 'Você é um conciliador do Juizado Especial Cível brasileiro.'

        full_text = ''
        _buf: list[str] = []
        _last_flush = time.time()
        for chunk, final_result in self.llm.generate_stream(
            user_prompt=prompt,
            system_prompt=system,
            temperature=JEC_TEMPERATURE,
            max_tokens=JEC_MAX_TOKENS,
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
                    yield self._event('conciliacao', ''.join(_buf), extra={
                        'acordo': acordo,
                    })
                    _buf = []
                    _last_flush = _now
        if _buf:
            yield self._event('conciliacao', ''.join(_buf), extra={
                'acordo': acordo,
            })

        return {'acordo': acordo, 'text': full_text}

    def _phase_instrucao(self, case_context: str) -> Generator[Dict, None, None]:
        """Simula audiência de instrução e julgamento."""
        yield self._event('phase', 'Audiência de Instrução e Julgamento')

        prompt = (
            "Você é um juiz leigo do Juizado Especial Cível presidindo a audiência de "
            "instrução e julgamento.\n\n"
            "Produza um RESUMO DA AUDIÊNCIA contendo:\n"
            "1. Depoimento pessoal das partes (resumo)\n"
            "2. Oitiva de testemunhas (se houver)\n"
            "3. Análise das provas documentais apresentadas\n"
            "4. Alegações finais orais de cada parte\n"
            "5. Principais questões fáticas e jurídicas identificadas\n\n"
            f"CASO:\n{case_context}\n\n"
            "Seja realista e coerente com o rito sumaríssimo."
        )

        full_text = ''
        _buf: list[str] = []
        _last_flush = time.time()
        for chunk, final_result in self.llm.generate_stream(
            user_prompt=prompt,
            system_prompt='Você é um juiz leigo do Juizado Especial Cível brasileiro.',
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
                    yield self._event('instrucao', ''.join(_buf))
                    _buf = []
                    _last_flush = _now
        if _buf:
            yield self._event('instrucao', ''.join(_buf))

    def _phase_sentenca(self, case_context: str) -> Generator[Dict, None, str]:
        """Gera sentença simplificada conforme art. 38 da Lei 9.099/95."""
        yield self._event('phase', 'Sentença Simplificada')

        claim_type = self.config.get('claim_type', '')
        case_value = self.config.get('case_value', '')

        prompt = (
            "Você é um juiz do Juizado Especial Cível.\n\n"
            "Redija uma SENTENÇA SIMPLIFICADA conforme o art. 38 da Lei 9.099/95.\n"
            "IMPORTANTE: A sentença do JEC é DISPENSADA de relatório formal.\n"
            "Estrutura obrigatória:\n\n"
            "1. **FUNDAMENTAÇÃO BREVE** — Análise jurídica concisa, citando:\n"
            "   - Lei 9.099/95 e artigos pertinentes\n"
            "   - CDC (se relação de consumo)\n"
            "   - CC/2002 quando aplicável\n"
            "   - Jurisprudência das Turmas Recursais\n"
            "2. **DISPOSITIVO** — Decisão final:\n"
            "   - Procedente / Improcedente / Parcialmente procedente\n"
            "   - Condenação em obrigação de fazer/não fazer ou pagamento\n"
            "   - Sem condenação em honorários em 1o grau (art. 55)\n"
            "   - Custas conforme art. 54 e 55\n\n"
        )

        if claim_type:
            prompt += f"Tipo de pretensão: {claim_type}\n"
        if case_value:
            prompt += f"Valor da causa: {case_value}\n"

        prompt += (
            f"\nCASO:\n{case_context}\n\n"
            "A sentença deve ser concisa, direta e fundamentada."
        )

        full_text = ''
        _buf: list[str] = []
        _last_flush = time.time()
        for chunk, final_result in self.llm.generate_stream(
            user_prompt=prompt,
            system_prompt=(
                'Você é um juiz do Juizado Especial Cível brasileiro. '
                'Redija sentenças simplificadas conforme a Lei 9.099/95.'
            ),
            temperature=JEC_TEMPERATURE,
            max_tokens=JEC_MAX_TOKENS,
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

    def _phase_relatorio_estrategico(
        self, case_context: str, sentence_text: str, dispositivo: str,
    ) -> Generator[Dict, None, str]:
        """Gera relatório estratégico para o caso JEC."""
        yield self._event('phase', 'Relatório Estratégico')

        is_victory = dispositivo in ('procedente', 'parcialmente_procedente', 'acordo')

        prompt = (
            "Você é um consultor jurídico especializado em Juizados Especiais Cíveis.\n"
            "Analise o resultado da simulação e produza um RELATÓRIO ESTRATÉGICO.\n\n"
            f"CASO:\n{case_context}\n\n"
            f"RESULTADO DA SIMULAÇÃO:\n{sentence_text}\n\n"
            f"DISPOSITIVO: {dispositivo}\n\n"
            "PRODUZA:\n"
            "### 1. ANÁLISE DO RESULTADO\n"
            "- Pontos determinantes para o resultado\n"
            "- Fundamentos jurídicos mais relevantes\n\n"
            "### 2. PONTOS FORTES E FRACOS\n"
            "- Argumentos que funcionaram\n"
            "- Vulnerabilidades identificadas\n\n"
            "### 3. RECURSO INOMINADO (art. 41-46)\n"
            "- Cabimento e prazo (10 dias)\n"
            "- Chances de reforma pela Turma Recursal\n"
            "- Argumentos recomendados para o recurso\n"
            "- Preparo recursal (art. 42)\n\n"
            "### 4. EXECUÇÃO (se procedente)\n"
            "- Cumprimento de sentença no JEC\n"
            "- Título executivo judicial\n"
            "- Prazo para pagamento voluntário\n\n"
            "### 5. RECOMENDAÇÕES PRÁTICAS\n"
            "- Próximos passos imediatos\n"
            "- Providências cautelares\n\n"
            "### 6. CHECKLIST\n"
            "[ ] Verificar prazo para recurso inominado (10 dias)\n"
            "[ ] Avaliar necessidade de preparo recursal\n"
            "[ ] Providenciar cumprimento/execução\n"
            "[ ] Monitorar prazo do adversário\n"
            "[ ] Consultar Turma Recursal competente\n\n"
            "Seja ESPECÍFICO e cite artigos da Lei 9.099/95."
        )

        full_text = ''
        _buf: list[str] = []
        _last_flush = time.time()
        for chunk, final_result in self.llm.generate_stream(
            user_prompt=prompt,
            system_prompt=(
                'Você é um consultor jurídico especializado em Juizados Especiais. '
                'Produza análises práticas e acionáveis.'
            ),
            temperature=0.5,
            max_tokens=JEC_MAX_TOKENS,
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

    def _detect_dispositivo(self, sentence_text: str) -> str:
        lower = sentence_text.lower()
        if 'parcialmente procedente' in lower:
            return 'parcialmente_procedente'
        if 'improcedente' in lower:
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
        if self.config.get('claim_type'):
            parts.append(f"Tipo de pretensão: {self.config['claim_type']}")
        if self.config.get('parties'):
            parts.append(f"Partes: {self.config['parties']}")
        if self.config.get('case_description'):
            parts.append(f"Descrição do caso:\n{self.config['case_description']}")
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
        return '\n\n---\n\n'.join(texts)

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


class JECRIMSimulationService:
    """Simula procedimento do Juizado Especial Criminal (Lei 9.099/95)."""

    def __init__(self, simulation_id: str):
        self.simulation = Simulation.objects.get(id=simulation_id)
        self.documents = list(self.simulation.documents.all())
        self.config = self.simulation.config or {}

        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService
        self.llm = UnifiedLLMService()

        self.provider = self.config.get('provider', JEC_PROVIDER)
        self.model = self.config.get('model', JEC_MODEL)

    # ── API principal ───────────────────────────────────────────────────────

    def stream_simulation(self) -> Generator[Dict, None, None]:
        """Generator que produz eventos SSE para a simulação JECRIM."""

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

            # Fase 1: Audiência Preliminar
            yield self._progress_event(
                'preliminar', 'Audiência Preliminar',
                'Realizando audiência preliminar obrigatória...',
                10,
            )
            yield from self._phase_audiencia_preliminar(case_context)

            # Fase 2: Proposta de Transação Penal
            yield self._progress_event(
                'transacao', 'Proposta de Transação Penal',
                'Ministério Público elaborando proposta de transação penal (art. 76)...',
                25,
            )
            transacao_result = yield from self._phase_transacao_penal(case_context)

            sentence_text = ''
            dispositivo = ''

            if transacao_result.get('aceita'):
                # Transação aceita
                sentence_text = transacao_result.get('text', '')
                dispositivo = 'transacao_aceita'
            else:
                # Fase 4: Suspensão Condicional do Processo
                yield self._progress_event(
                    'suspensao', 'Suspensão Condicional do Processo',
                    'Transação rejeitada. Avaliando suspensão condicional (art. 89)...',
                    45,
                )
                suspensao_result = yield from self._phase_suspensao_condicional(case_context)

                if suspensao_result.get('aceita'):
                    sentence_text = suspensao_result.get('text', '')
                    dispositivo = 'suspensao_aceita'
                else:
                    # Fase 5: Instrução + Sentença
                    yield self._progress_event(
                        'instrucao', 'Instrução Criminal',
                        'Todas as propostas rejeitadas. Iniciando instrução criminal simplificada...',
                        60,
                    )
                    yield from self._phase_instrucao_criminal(case_context)

                    yield self._progress_event(
                        'sentenca', 'Sentença Criminal',
                        'Redigindo sentença criminal simplificada...',
                        75,
                    )
                    sentence_text = yield from self._phase_sentenca_criminal(case_context)
                    dispositivo = self._detect_dispositivo_criminal(sentence_text)

            # Fase 6: Relatório Estratégico
            yield self._progress_event(
                'relatorio', 'Relatório Estratégico',
                'Analisando resultado e gerando recomendações...',
                90,
            )
            strategic_report = yield from self._phase_relatorio_estrategico(
                case_context, sentence_text, dispositivo,
            )

            # Persistir resultado
            self.simulation.status = 'completed'
            self.simulation.result = {
                'sentence': sentence_text,
                'dispositivo': dispositivo,
                'strategic_report': strategic_report,
                'transacao_aceita': transacao_result.get('aceita', False),
                'crime_type': self.config.get('crime_type', ''),
                'facts': self.config.get('facts', ''),
            }
            self.simulation.save(update_fields=['status', 'result'])

            yield self._progress_event(
                'complete', 'Simulação Concluída',
                'Simulação do Juizado Especial Criminal finalizada.',
                100,
            )
            yield self._event('complete', 'Simulação JECRIM concluída.')

        except Exception as e:
            logger.exception(f'[jecrim_simulation] Erro na simulação {self.simulation.id}: {e}')
            self.simulation.status = 'failed'
            self.simulation.save(update_fields=['status'])
            yield self._event('error', f'Erro na simulação: {str(e)}')

    # ── Fases ───────────────────────────────────────────────────────────────

    def _phase_audiencia_preliminar(self, case_context: str) -> Generator[Dict, None, None]:
        """Simula audiência preliminar obrigatória."""
        yield self._event('phase', 'Audiência Preliminar')

        prompt = (
            "Você é um juiz do Juizado Especial Criminal presidindo a audiência preliminar.\n\n"
            "Realize a audiência preliminar conforme art. 72 da Lei 9.099/95:\n"
            "1. Verificação da presença das partes\n"
            "2. Tentativa de composição civil dos danos (art. 74)\n"
            "3. Esclarecimento sobre os direitos do autor do fato\n"
            "4. Informação sobre a possibilidade de transação penal\n"
            "5. Encaminhamento para a fase seguinte\n\n"
            f"CASO:\n{case_context}\n\n"
            "Produza uma narrativa realista da audiência preliminar."
        )

        full_text = ''
        _buf: list[str] = []
        _last_flush = time.time()
        for chunk, final_result in self.llm.generate_stream(
            user_prompt=prompt,
            system_prompt='Você é um juiz do Juizado Especial Criminal brasileiro.',
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
                    yield self._event('preliminar', ''.join(_buf))
                    _buf = []
                    _last_flush = _now
        if _buf:
            yield self._event('preliminar', ''.join(_buf))

    def _phase_transacao_penal(self, case_context: str) -> Generator[Dict, None, dict]:
        """Simula proposta de transação penal (art. 76) e análise de aceitação."""
        yield self._event('phase', 'Proposta de Transação Penal (art. 76)')

        # Gerar proposta do MP
        prompt_proposta = (
            "Você é o representante do Ministério Público no Juizado Especial Criminal.\n\n"
            "Elabore uma PROPOSTA DE TRANSAÇÃO PENAL conforme art. 76 da Lei 9.099/95:\n"
            "1. Identificação do autor do fato e do fato delituoso\n"
            "2. Enquadramento legal\n"
            "3. Pena proposta: restritiva de direitos OU multa\n"
            "4. Condições específicas (prestação de serviços, cestas básicas, etc.)\n"
            "5. Prazo para cumprimento\n"
            "6. Consequências do descumprimento\n\n"
            "Requisitos para transação (verificar):\n"
            "- Pena máxima não superior a 2 anos\n"
            "- Não ter sido beneficiado por transação nos últimos 5 anos\n"
            "- Antecedentes, conduta social, personalidade\n\n"
            f"CASO:\n{case_context}\n\n"
            "Redija a proposta formal de transação penal."
        )

        full_text = ''
        _buf: list[str] = []
        _last_flush = time.time()
        for chunk, final_result in self.llm.generate_stream(
            user_prompt=prompt_proposta,
            system_prompt='Você é um promotor de justiça brasileiro atuando no JECRIM.',
            temperature=JEC_TEMPERATURE,
            max_tokens=JEC_MAX_TOKENS,
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
                    yield self._event('transacao', ''.join(_buf))
                    _buf = []
                    _last_flush = _now
        if _buf:
            yield self._event('transacao', ''.join(_buf))

        # Simular aceitação/rejeição (50% chance)
        aceita = random.random() < 0.5

        # Fase 3: Análise da Transação
        yield self._progress_event(
            'analise_transacao', 'Análise da Transação',
            f"Analisando {'aceitação' if aceita else 'rejeição'} da proposta...",
            35,
        )

        prompt_analise = (
            f"Você é um advogado criminalista analisando a proposta de transação penal.\n\n"
            f"PROPOSTA DO MP:\n{full_text}\n\n"
            f"O autor do fato {'ACEITOU' if aceita else 'REJEITOU'} a proposta.\n\n"
        )
        if aceita:
            prompt_analise += (
                "Redija:\n"
                "1. Justificativa da aceitação pelo autor do fato\n"
                "2. Termo de aceitação da transação penal\n"
                "3. Homologação judicial (art. 76, §§ 3o e 4o)\n"
                "4. Natureza jurídica: NÃO importa reincidência\n"
                "5. Registro apenas para impedir nova transação em 5 anos"
            )
        else:
            prompt_analise += (
                "Redija:\n"
                "1. Motivos da rejeição pelo autor do fato\n"
                "2. Consequências processuais da rejeição\n"
                "3. Encaminhamento para a próxima fase (suspensão condicional ou denúncia)"
            )

        prompt_analise += f"\n\nCASO ORIGINAL:\n{case_context}"

        analise_text = ''
        _buf = []
        _last_flush = time.time()
        for chunk, final_result in self.llm.generate_stream(
            user_prompt=prompt_analise,
            system_prompt='Você é um advogado criminalista brasileiro.',
            temperature=JEC_TEMPERATURE,
            max_tokens=JEC_MAX_TOKENS,
            provider=self.provider,
            model=self.model,
        ):
            if final_result is not None:
                break
            if chunk:
                analise_text += chunk
                _buf.append(chunk)
                _now = time.time()
                if _now - _last_flush >= 0.15 or len(_buf) >= 20:
                    yield self._event('analise_transacao', ''.join(_buf), extra={
                        'aceita': aceita,
                    })
                    _buf = []
                    _last_flush = _now
        if _buf:
            yield self._event('analise_transacao', ''.join(_buf), extra={
                'aceita': aceita,
            })

        combined = full_text + '\n\n---\n\n' + analise_text
        return {'aceita': aceita, 'text': combined}

    def _phase_suspensao_condicional(self, case_context: str) -> Generator[Dict, None, dict]:
        """Simula proposta de suspensão condicional do processo (art. 89)."""
        yield self._event('phase', 'Suspensão Condicional do Processo (art. 89)')

        aceita = random.random() < 0.4

        prompt = (
            "Você é um juiz do JECRIM avaliando a suspensão condicional do processo.\n\n"
            "A transação penal foi REJEITADA. Analise a possibilidade de suspensão "
            "condicional do processo conforme art. 89 da Lei 9.099/95:\n\n"
            "Requisitos:\n"
            "- Pena mínima cominada igual ou inferior a 1 ano\n"
            "- Não estar sendo processado por outro crime\n"
            "- Não ter sido condenado por outro crime\n"
            "- Presentes os requisitos do art. 77 do CP (sursis)\n\n"
            f"O acusado {'ACEITOU' if aceita else 'REJEITOU'} a proposta.\n\n"
        )

        if aceita:
            prompt += (
                "Redija o TERMO DE SUSPENSÃO com:\n"
                "1. Período de prova (2 a 4 anos)\n"
                "2. Condições obrigatórias (reparação do dano, proibição de frequentar lugares, etc.)\n"
                "3. Condições facultativas\n"
                "4. Consequências do descumprimento\n"
                "5. Extinção da punibilidade ao final do período"
            )
        else:
            prompt += (
                "Redija:\n"
                "1. Análise da inviabilidade/rejeição da suspensão\n"
                "2. Oferecimento da denúncia oral (art. 77)\n"
                "3. Encaminhamento para instrução criminal"
            )

        prompt += f"\n\nCASO:\n{case_context}"

        full_text = ''
        _buf: list[str] = []
        _last_flush = time.time()
        for chunk, final_result in self.llm.generate_stream(
            user_prompt=prompt,
            system_prompt='Você é um juiz do Juizado Especial Criminal brasileiro.',
            temperature=JEC_TEMPERATURE,
            max_tokens=JEC_MAX_TOKENS,
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
                    yield self._event('suspensao', ''.join(_buf), extra={
                        'aceita': aceita,
                    })
                    _buf = []
                    _last_flush = _now
        if _buf:
            yield self._event('suspensao', ''.join(_buf), extra={
                'aceita': aceita,
            })

        return {'aceita': aceita, 'text': full_text}

    def _phase_instrucao_criminal(self, case_context: str) -> Generator[Dict, None, None]:
        """Simula instrução criminal simplificada."""
        yield self._event('phase', 'Instrução Criminal Simplificada')

        prompt = (
            "Você é um juiz do JECRIM presidindo a instrução criminal.\n\n"
            "Transação penal e suspensão condicional foram REJEITADAS.\n"
            "Denúncia oral foi oferecida e recebida.\n\n"
            "Produza o RESUMO DA INSTRUÇÃO:\n"
            "1. Interrogatório do acusado\n"
            "2. Oitiva da vítima\n"
            "3. Oitiva de testemunhas\n"
            "4. Debates orais (acusação e defesa)\n"
            "5. Questões fáticas e jurídicas relevantes\n\n"
            f"CASO:\n{case_context}\n\n"
            "Seja realista e coerente com o rito sumaríssimo criminal."
        )

        full_text = ''
        _buf: list[str] = []
        _last_flush = time.time()
        for chunk, final_result in self.llm.generate_stream(
            user_prompt=prompt,
            system_prompt='Você é um juiz do Juizado Especial Criminal brasileiro.',
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
                    yield self._event('instrucao', ''.join(_buf))
                    _buf = []
                    _last_flush = _now
        if _buf:
            yield self._event('instrucao', ''.join(_buf))

    def _phase_sentenca_criminal(self, case_context: str) -> Generator[Dict, None, str]:
        """Gera sentença criminal simplificada do JECRIM."""
        yield self._event('phase', 'Sentença Criminal')

        crime_type = self.config.get('crime_type', '')

        prompt = (
            "Você é um juiz do Juizado Especial Criminal.\n\n"
            "Redija uma SENTENÇA CRIMINAL SIMPLIFICADA para o caso abaixo.\n"
            "Estrutura:\n\n"
            "1. **BREVE RELATÓRIO** — Resumo da denúncia e da defesa\n"
            "2. **FUNDAMENTAÇÃO** — Análise de autoria e materialidade, citando:\n"
            "   - Código Penal (tipo penal, dosimetria)\n"
            "   - Lei 9.099/95\n"
            "   - Jurisprudência pertinente\n"
            "3. **DISPOSITIVO** — Decisão final:\n"
            "   - Condenação ou Absolvição\n"
            "   - Se condenação: dosimetria da pena (art. 59 CP)\n"
            "   - Regime inicial\n"
            "   - Substituição por restritiva de direitos (art. 44 CP)\n"
            "   - Custas e honorários\n\n"
        )

        if crime_type:
            prompt += f"Tipo de crime: {crime_type}\n"

        prompt += (
            f"\nCASO:\n{case_context}\n\n"
            "A sentença deve ser concisa e fundamentada."
        )

        full_text = ''
        _buf: list[str] = []
        _last_flush = time.time()
        for chunk, final_result in self.llm.generate_stream(
            user_prompt=prompt,
            system_prompt=(
                'Você é um juiz do Juizado Especial Criminal brasileiro. '
                'Redija sentenças criminais simplificadas.'
            ),
            temperature=JEC_TEMPERATURE,
            max_tokens=JEC_MAX_TOKENS,
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

    def _phase_relatorio_estrategico(
        self, case_context: str, sentence_text: str, dispositivo: str,
    ) -> Generator[Dict, None, str]:
        """Gera relatório estratégico para o caso JECRIM."""
        yield self._event('phase', 'Relatório Estratégico')

        is_victory = dispositivo in ('absolvicao', 'transacao_aceita', 'suspensao_aceita')

        prompt = (
            "Você é um consultor jurídico especializado em Direito Penal e JECRIM.\n"
            "Analise o resultado da simulação e produza um RELATÓRIO ESTRATÉGICO.\n\n"
            f"CASO:\n{case_context}\n\n"
            f"RESULTADO:\n{sentence_text}\n\n"
            f"DISPOSITIVO: {dispositivo}\n\n"
            "PRODUZA:\n"
            "### 1. ANÁLISE DO RESULTADO\n"
            "- O que determinou o resultado\n"
            "- Fundamentos jurídicos mais relevantes\n\n"
            "### 2. ANÁLISE DA DEFESA\n"
            "- Pontos fortes da defesa\n"
            "- Oportunidades perdidas\n"
            "- Teses alternativas\n\n"
            "### 3. RECURSOS CABÍVEIS\n"
            "- Apelação para Turma Recursal (prazo 10 dias)\n"
            "- Habeas corpus (se cabível)\n"
            "- Embargos de declaração\n"
            "- Chances de reforma\n\n"
            "### 4. CONSEQUÊNCIAS PENAIS\n"
            "- Antecedentes criminais\n"
            "- Reincidência\n"
            "- Efeitos civis da sentença\n\n"
            "### 5. RECOMENDAÇÕES\n"
            "- Próximos passos imediatos\n"
            "- Estratégia recursal\n\n"
            "### 6. CHECKLIST\n"
            "[ ] Verificar prazo para recurso (10 dias)\n"
            "[ ] Avaliar cabimento de HC\n"
            "[ ] Providenciar contrarrazões (se necessário)\n"
            "[ ] Monitorar cumprimento de condições\n"
            "[ ] Acompanhar extinção da punibilidade\n\n"
            "Seja ESPECÍFICO e cite legislação pertinente."
        )

        full_text = ''
        _buf: list[str] = []
        _last_flush = time.time()
        for chunk, final_result in self.llm.generate_stream(
            user_prompt=prompt,
            system_prompt=(
                'Você é um consultor jurídico especializado em Direito Penal brasileiro. '
                'Produza análises práticas e acionáveis.'
            ),
            temperature=0.5,
            max_tokens=JEC_MAX_TOKENS,
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

    def _detect_dispositivo_criminal(self, sentence_text: str) -> str:
        lower = sentence_text.lower()
        if 'absolv' in lower:
            return 'absolvicao'
        if 'conden' in lower:
            return 'condenacao'
        return 'indeterminado'

    def _build_context_from_config(self) -> str:
        parts = []
        if self.config.get('crime_type'):
            parts.append(f"Tipo de crime: {self.config['crime_type']}")
        if self.config.get('facts'):
            parts.append(f"Fatos:\n{self.config['facts']}")
        if self.config.get('case_description'):
            parts.append(f"Descrição do caso:\n{self.config['case_description']}")
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
        return '\n\n---\n\n'.join(texts)

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

'use client';

import { useEffect, useRef, useMemo } from 'react';
import { Bot, Trash2, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useCopilot } from '@/hooks/use-copilot';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';
import { ExportMenu } from './ExportMenu';
import { CopilotSessionHistory } from '@/components/copilot/CopilotSessionHistory';
import type { AgentMentionOption } from './AgentMentionDropdown';
import type { AgentPrompt } from '@/types';

// ── Blueprint suggestion keywords → route map ──────────────────────────────
// Maps common keywords that appear in user messages to document generator routes.
const BLUEPRINT_KEYWORD_MAP: Array<{
  patterns: RegExp[];
  label: string;
  documentType: string;
}> = [
  // Ações e Petições
  {
    patterns: [/peti[çc][aã]o inicial/i, /peticao inicial/i],
    label: 'Petição Inicial',
    documentType: 'peticao_inicial',
  },
  {
    patterns: [/mandado de seguran[çc]a/i],
    label: 'Mandado de Segurança',
    documentType: 'mandado_seguranca',
  },
  {
    patterns: [/a[çc][aã]o de cobran[çc]a/i, /acao de cobranca/i],
    label: 'Ação de Cobrança',
    documentType: 'acao_cobranca',
  },
  {
    patterns: [/a[çc][aã]o monit[oó]ria/i, /acao monitoria/i],
    label: 'Ação Monitória',
    documentType: 'acao_monitoria',
  },
  {
    patterns: [/a[çc][aã]o de indeniza[çc][aã]o/i, /acao de indenizacao/i],
    label: 'Ação de Indenização',
    documentType: 'acao_indenizacao_rc',
  },
  {
    patterns: [/a[çc][aã]o declarat[oó]ria/i, /acao declaratoria/i],
    label: 'Ação Declaratória',
    documentType: 'acao_declaratoria',
  },
  {
    patterns: [/a[çc][aã]o rescis[oó]ria/i, /acao rescisoria/i],
    label: 'Ação Rescisória',
    documentType: 'acao_rescisoria',
  },
  {
    patterns: [/usucapi[aã]o/i],
    label: 'Ação de Usucapião',
    documentType: 'usucapiao',
  },
  {
    patterns: [/a[çc][aã]o possess[oó]ria/i, /acao possessoria/i],
    label: 'Ação Possessória',
    documentType: 'acao_possessoria',
  },
  {
    patterns: [/a[çc][aã]o popular/i, /acao popular/i],
    label: 'Ação Popular',
    documentType: 'acao_popular',
  },
  // Defesas
  {
    patterns: [/contesta[çc][aã]o/i],
    label: 'Contestação',
    documentType: 'contestacao',
  },
  {
    patterns: [/r[eé]plica/i],
    label: 'Réplica',
    documentType: 'replica_civel',
  },
  {
    patterns: [/contrarraz[oõ]es/i, /contrarrazoes/i],
    label: 'Contrarrazões',
    documentType: 'contrarrazoes_apelacao',
  },
  {
    patterns: [/impugna[çc][aã]o/i],
    label: 'Impugnação',
    documentType: 'impugnacao_cumprimento',
  },
  {
    patterns: [/embargos de terceiro/i],
    label: 'Embargos de Terceiro',
    documentType: 'embargos_terceiro',
  },
  // Recursos
  {
    patterns: [/apela[çc][aã]o/i],
    label: 'Apelação',
    documentType: 'apelacao',
  },
  {
    patterns: [/agravo de instrumento/i],
    label: 'Agravo de Instrumento',
    documentType: 'agravo_instrumento',
  },
  {
    patterns: [/agravo interno/i],
    label: 'Agravo Interno',
    documentType: 'agravo_interno',
  },
  {
    patterns: [/embargos de declara[çc][aã]o/i, /embargos de declaracao/i],
    label: 'Embargos de Declaração',
    documentType: 'embargos_declaracao',
  },
  {
    patterns: [/recurso especial/i],
    label: 'Recurso Especial',
    documentType: 'recurso_especial',
  },
  {
    patterns: [/recurso extraordin[aá]rio/i, /recurso extraordinario/i],
    label: 'Recurso Extraordinário',
    documentType: 'recurso_extraordinario',
  },
  {
    patterns: [/recurso ordin[aá]rio/i, /recurso\s+ordin[aá]rio/i],
    label: 'Recurso Ordinário',
    documentType: 'recurso_ordinario',
  },
  // Execução
  {
    patterns: [/embargos [àa] execu[çc][aã]o/i, /embargos a execucao/i],
    label: 'Embargos à Execução',
    documentType: 'embargos_execucao',
  },
  {
    patterns: [/cumprimento de senten[çc]a/i, /cumprimento de sentenca/i],
    label: 'Cumprimento de Sentença',
    documentType: 'cumprimento_sentenca',
  },
  // Cautelares
  {
    patterns: [/tutela de urg[eê]ncia/i, /tutela de urgencia/i],
    label: 'Tutela de Urgência',
    documentType: 'tutela_urgencia',
  },
  {
    patterns: [/tutela de evid[eê]ncia/i, /tutela de evidencia/i],
    label: 'Tutela de Evidência',
    documentType: 'tutela_evidencia',
  },
  // Trabalhista
  {
    patterns: [/reclama[çc][aã]o trabalhista/i, /reclamacao trabalhista/i],
    label: 'Reclamação Trabalhista',
    documentType: 'reclamacao_trabalhista',
  },
  // Criminal
  {
    patterns: [/habeas corpus/i],
    label: 'Habeas Corpus',
    documentType: 'habeas_corpus',
  },
  {
    patterns: [/queixa[- ]crime/i],
    label: 'Queixa-Crime',
    documentType: 'queixa_crime',
  },
  // Família
  {
    patterns: [/div[oó]rcio/i, /divorcio/i],
    label: 'Petição de Divórcio',
    documentType: 'divorcio_consensual',
  },
  {
    patterns: [/a[çc][aã]o de alimentos/i, /acao de alimentos/i, /\balimentos\b/i],
    label: 'Ação de Alimentos',
    documentType: 'acao_alimentos',
  },
  {
    patterns: [/invent[aá]rio/i],
    label: 'Inventário',
    documentType: 'inventario_judicial',
  },
  {
    patterns: [/guarda/i],
    label: 'Regulamentação de Guarda',
    documentType: 'regulamentacao_guarda',
  },
  // Previdenciário
  {
    patterns: [/benef[ií]cio previdenci[aá]rio/i, /beneficio previdenciario/i],
    label: 'Ação Previdenciária',
    documentType: 'peticao_inicial_previdenciaria',
  },
  {
    patterns: [/aposentadoria/i],
    label: 'Ação de Aposentadoria',
    documentType: 'aposentadoria_especial',
  },
  // Tributário
  {
    patterns: [/execu[çc][aã]o fiscal/i, /execucao fiscal/i],
    label: 'Embargos à Execução Fiscal',
    documentType: 'embargos_execucao_fiscal',
  },
  // Extrajudicial
  {
    patterns: [/notifica[çc][aã]o extrajudicial/i, /notificacao extrajudicial/i],
    label: 'Notificação Extrajudicial',
    documentType: 'notificacao_extrajudicial',
  },
  {
    patterns: [/contrato/i],
    label: 'Contrato',
    documentType: 'contrato_particular',
  },
  {
    patterns: [/procura[çc][aã]o/i, /procuracao/i],
    label: 'Procuração',
    documentType: 'procuracao',
  },
  {
    patterns: [/parecer jur[ií]dico/i, /parecer juridico/i],
    label: 'Parecer Jurídico',
    documentType: 'parecer_juridico',
  },
  // Imobiliário
  {
    patterns: [/a[çc][aã]o de despejo/i, /acao de despejo/i, /\bdespejo\b/i],
    label: 'Ação de Despejo',
    documentType: 'acao_despejo',
  },
  // Empresarial
  {
    patterns: [/recupera[çc][aã]o judicial/i, /recuperacao judicial/i],
    label: 'Recuperação Judicial',
    documentType: 'recuperacao_judicial',
  },
  // Execução (adicionais)
  {
    patterns: [/exce[çc][aã]o de pr[eé]-executividade/i, /excecao de pre-executividade/i, /pr[eé].?executividade/i],
    label: 'Exceção de Pré-Executividade',
    documentType: 'excecao_pre_executividade',
  },
  {
    patterns: [/embargos [àa] arremata[çc][aã]o/i],
    label: 'Embargos à Arrematação',
    documentType: 'embargos_arrematacao',
  },
  // Defesas (adicionais)
  {
    patterns: [/exce[çc][aã]o de suspei[çc][aã]o/i],
    label: 'Exceção de Suspeição',
    documentType: 'excecao_suspeicao',
  },
  // Recursos (adicionais)
  {
    patterns: [/recurso de revista/i],
    label: 'Recurso de Revista',
    documentType: 'recurso_revista',
  },
  {
    patterns: [/embargos de diverg[eê]ncia/i],
    label: 'Embargos de Divergência',
    documentType: 'embargos_divergencia',
  },
  {
    patterns: [/recurso inominado/i],
    label: 'Recurso Inominado',
    documentType: 'recurso_inominado',
  },
  // Criminal (adicionais)
  {
    patterns: [/defesa preliminar/i],
    label: 'Defesa Preliminar',
    documentType: 'defesa_preliminar',
  },
  {
    patterns: [/alega[çc][oõ]es finais/i],
    label: 'Alegações Finais',
    documentType: 'alegacoes_finais',
  },
  {
    patterns: [/liberdade provis[oó]ria/i],
    label: 'Liberdade Provisória',
    documentType: 'liberdade_provisoria',
  },
  {
    patterns: [/revis[aã]o criminal/i],
    label: 'Revisão Criminal',
    documentType: 'revisao_criminal',
  },
  {
    patterns: [/apela[çc][aã]o criminal/i],
    label: 'Apelação Criminal',
    documentType: 'apelacao_criminal',
  },
  // Família (adicionais)
  {
    patterns: [/ado[çc][aã]o/i],
    label: 'Adoção',
    documentType: 'adocao',
  },
  {
    patterns: [/curatela/i],
    label: 'Curatela',
    documentType: 'curatela',
  },
  {
    patterns: [/uni[aã]o est[aá]vel/i],
    label: 'União Estável',
    documentType: 'uniao_estavel',
  },
  // Previdenciário (adicionais)
  {
    patterns: [/\bBPC\b/i, /\bLOAS\b/i, /benef[ií]cio.+continuada/i],
    label: 'BPC/LOAS',
    documentType: 'bpc_loas',
  },
  {
    patterns: [/pens[aã]o por morte/i],
    label: 'Pensão por Morte',
    documentType: 'pensao_por_morte',
  },
  {
    patterns: [/aux[ií]lio.?incapacidade/i, /aux[ií]lio.?doen[çc]a/i],
    label: 'Auxílio por Incapacidade',
    documentType: 'auxilio_incapacidade',
  },
  // Tributário (adicionais)
  {
    patterns: [/repeti[çc][aã]o de ind[eé]bito/i],
    label: 'Repetição de Indébito',
    documentType: 'repeticao_indebito',
  },
  {
    patterns: [/a[çc][aã]o anulat[oó]ria/i, /acao anulatoria/i],
    label: 'Ação Anulatória',
    documentType: 'acao_anulatoria',
  },
  // Administrativo (adicionais)
  {
    patterns: [/improbidade/i],
    label: 'Ação de Improbidade',
    documentType: 'improbidade_administrativa',
  },
  {
    patterns: [/desapropria[çc][aã]o/i],
    label: 'Desapropriação',
    documentType: 'desapropriacao',
  },
  // Constitucional
  {
    patterns: [/\bADI\b/],
    label: 'ADI',
    documentType: 'adi',
  },
  {
    patterns: [/\bADPF\b/],
    label: 'ADPF',
    documentType: 'adpf',
  },
  {
    patterns: [/habeas data/i],
    label: 'Habeas Data',
    documentType: 'habeas_data',
  },
  {
    patterns: [/mandado de injun[çc][aã]o/i],
    label: 'Mandado de Injunção',
    documentType: 'mandado_injuncao',
  },
  // Ambiental
  {
    patterns: [/\bACP\b.*ambiental/i, /a[çc][aã]o civil p[uú]blica.*ambiental/i],
    label: 'ACP Ambiental',
    documentType: 'acp_ambiental',
  },
  // Empresarial (adicionais)
  {
    patterns: [/fal[eê]ncia/i],
    label: 'Falência',
    documentType: 'falencia',
  },
  // Imobiliário (adicionais)
  {
    patterns: [/a[çc][aã]o renovat[oó]ria/i, /renovat[oó]ria de loca[çc][aã]o/i],
    label: 'Ação Renovatória',
    documentType: 'acao_renovatoria',
  },
  // Digital/LGPD
  {
    patterns: [/pol[ií]tica de privacidade/i],
    label: 'Política de Privacidade',
    documentType: 'politica_privacidade',
  },
  {
    patterns: [/termos de uso/i],
    label: 'Termos de Uso',
    documentType: 'termos_uso',
  },
  // Trabalhista (adicionais)
  {
    patterns: [/agravo de peti[çc][aã]o/i],
    label: 'Agravo de Petição',
    documentType: 'agravo_peticao',
  },
  {
    patterns: [/diss[ií]dio coletivo/i],
    label: 'Dissídio Coletivo',
    documentType: 'dissidio_coletivo',
  },
  // Cautelares (adicionais)
  {
    patterns: [/produ[çc][aã]o antecipada de provas/i],
    label: 'Produção Antecipada de Provas',
    documentType: 'producao_antecipada_provas',
  },
  // JEC
  {
    patterns: [/peti[çc][aã]o.*\bJEC\b/i, /juizado especial c[ií]vel/i],
    label: 'Petição JEC',
    documentType: 'peticao_jec',
  },
  {
    patterns: [/pedido contraposto/i],
    label: 'Pedido Contraposto',
    documentType: 'pedido_contraposto',
  },
  // Simulações
  {
    patterns: [/simula[çc][ãa]o/i, /simular/i],
    label: 'Simular Júri',
    documentType: 'jury',
  },
  {
    patterns: [/j[úu]ri/i, /tribunal do j[úu]ri/i],
    label: 'Simular Júri',
    documentType: 'jury',
  },
  {
    patterns: [/senten[çc]a.*juiz/i, /como.*juiz.*decide/i, /prever.*resultado/i],
    label: 'Simular Sentença',
    documentType: 'judge',
  },
  {
    patterns: [/chance.*ganhar/i, /probabilidade.*vencer/i],
    label: 'Simular Resultado',
    documentType: 'judge',
  },
];

function detectBlueprintSuggestions(text: string) {
  return BLUEPRINT_KEYWORD_MAP.filter(({ patterns }) =>
    patterns.some((re) => re.test(text))
  );
}

interface CopilotChatProps {
  initialPrompt?: string;
}

export function CopilotChat({ initialPrompt = '' }: CopilotChatProps) {
  const {
    messages,
    isStreaming,
    attachedFile,
    error,
    sendMessage,
    clearConversation,
    exportConversation,
    attachFile,
    stopGeneration,
    editAndRegenerate,
    deleteMessage,
    startNewSession,
    loadSession,
  } = useCopilot();

  const bottomRef = useRef<HTMLDivElement>(null);
  const initialPromptSent = useRef(false);

  // Auto-send initial prompt from notification / query param
  useEffect(() => {
    if (initialPrompt && !initialPromptSent.current && !isStreaming && messages.length === 0) {
      initialPromptSent.current = true;
      // Small delay to ensure session is ready
      const timer = setTimeout(() => {
        sendMessage(initialPrompt);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [initialPrompt, isStreaming, messages.length, sendMessage]);

  // Auto-scroll ao receber novas mensagens
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Fetch agents for @ mention
  const { data: agentsData } = useQuery({
    queryKey: ['agents-copilot-mentions'],
    queryFn: async () => {
      const response = await api.get<{ results: AgentPrompt[] }>('/api/v1/agents/', {
        params: { active_only: true, page_size: 100 },
      });
      return response.data.results ?? [];
    },
    staleTime: 5 * 60 * 1000, // 5 min cache
  });

  const agentMentions: AgentMentionOption[] = useMemo(
    () =>
      (agentsData ?? []).map((a) => ({
        id: a.id,
        name: a.name,
        agent_type: a.agent_type,
        description: a.description,
        color: a.color,
        icon: a.icon,
      })),
    [agentsData]
  );

  // Detect blueprint suggestions from the last user message
  const blueprintSuggestions = useMemo(() => {
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user');
    if (!lastUserMsg) return [];
    return detectBlueprintSuggestions(lastUserMsg.content);
  }, [messages]);

  const handleCopyAll = () => {
    const text = messages
      .map((m) => `${m.role === 'user' ? 'Usuário' : 'Copilot'}: ${m.content}`)
      .join('\n\n');
    navigator.clipboard.writeText(text);
  };

  const handleNewSession = () => {
    startNewSession();
  };

  const handleSessionSelect = async (sessionId: string) => {
    try {
      const response = await api.get(`/api/v1/copilot/session/${sessionId}/`);
      const loadedMessages = response.data.messages || [];
      loadSession(sessionId, loadedMessages);
    } catch {
      // If loading fails, just start fresh with that session ID
      loadSession(sessionId, []);
    }
  };

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-3 sm:px-4 py-2 sm:py-3 shrink-0 safe-area-top">
        <div className="flex items-center gap-2 min-w-0">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 shrink-0">
            <Bot className="h-4 w-4 text-primary" />
          </div>
          <div className="min-w-0">
            <h1 className="text-sm font-semibold truncate">Copilot</h1>
            <p className="text-xs text-muted-foreground truncate hidden sm:block">
              Copilot Jurídico · IBM WatsonX
            </p>
          </div>
          <span className="ml-1 rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary shrink-0">
            IA
          </span>
        </div>

        <div className="flex items-center gap-1 sm:gap-2 shrink-0">
          <CopilotSessionHistory
            onSessionSelect={handleSessionSelect}
            onNewSession={handleNewSession}
          />
          <Button
            variant="outline"
            size="sm"
            onClick={handleNewSession}
            disabled={isStreaming}
            title="Nova conversa"
            className="gap-1 sm:gap-2"
          >
            <Plus className="h-4 w-4" />
            <span className="hidden sm:inline">Nova Sessão</span>
          </Button>
          {messages.length > 0 && (
            <>
              <ExportMenu
                onCopy={handleCopyAll}
                onExport={(fmt) => exportConversation(fmt)}
                disabled={isStreaming}
              />
              <Button
                variant="ghost"
                size="sm"
                onClick={clearConversation}
                disabled={isStreaming}
                title="Limpar conversa atual"
                className="text-destructive hover:text-destructive hover:bg-destructive/10"
              >
                <Trash2 className="h-4 w-4 sm:mr-1.5" />
                <span className="hidden sm:inline">Limpar</span>
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Copilot proactive banner */}
      {initialPrompt && messages.length <= 2 && (
        <div className="mx-4 mt-2 flex items-center gap-2 rounded-lg border border-primary/30 bg-primary/5 px-4 py-2.5">
          <Bot className="h-4 w-4 flex-shrink-0 text-primary" />
          <p className="text-sm text-primary">
            O Copilot identificou algo que precisa da sua atenção
          </p>
        </div>
      )}

      {/* Messages */}
      <ScrollArea className="flex-1 min-h-0 overscroll-contain">
        <div className="flex flex-col gap-3 sm:gap-4 px-3 sm:px-4 py-4">
          {messages.length === 0 && !initialPrompt && (
            <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
                <Bot className="h-7 w-7 text-primary" />
              </div>
              <div>
                <h2 className="text-base font-semibold">Copilot Jurídico Verus.AI</h2>
                <p className="mt-1 text-sm text-muted-foreground max-w-sm">
                  Especialista em direito e peças processuais. Pergunte sobre jurisprudência,
                  legislação, prazos ou anexe um documento para análise.
                </p>
              </div>

              {/* Sugestões iniciais - horizontal scroll on mobile */}
              <div className="mt-2 w-full max-w-full overflow-x-auto">
                <div className="chips-scroll justify-center sm:flex-wrap sm:overflow-visible px-2 sm:px-0">
                  {[
                    'Como redigir uma petição inicial?',
                    'Qual o prazo para contestação?',
                    'Como citar jurisprudência do STJ?',
                    'Diferença entre recurso e apelação',
                  ].map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => sendMessage(suggestion)}
                      className="rounded-full border px-3 py-2 text-xs text-muted-foreground hover:bg-muted hover:text-foreground transition-colors whitespace-nowrap shrink-0 touch-target"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>

              {/* Agents quick mention hint */}
              {agentMentions.length > 0 && (
                <div className="mt-3 text-xs text-muted-foreground">
                  Use{' '}
                  <kbd className="rounded bg-muted px-1 py-0.5 font-mono text-[10px]">@</kbd>{' '}
                  para consultar um agente especializado:{' '}
                  {agentMentions.slice(0, 3).map((a, i) => (
                    <span key={a.id}>
                      <button
                        className="font-medium text-primary hover:underline"
                        onClick={() => sendMessage(`@${a.name} `)}
                      >
                        @{a.name}
                      </button>
                      {i < Math.min(agentMentions.length, 3) - 1 ? ', ' : ''}
                    </span>
                  ))}
                  {agentMentions.length > 3 && ` e mais ${agentMentions.length - 3}`}
                </div>
              )}
            </div>
          )}

          {messages.map((message, index) => (
            <MessageBubble
              key={message.id}
              message={message}
              messageIndex={index}
              onEdit={editAndRegenerate}
              onDelete={deleteMessage}
              isStreaming={isStreaming}
            />
          ))}

          {/* Blueprint action suggestions */}
          {blueprintSuggestions.length > 0 && !isStreaming && (
            <div className="rounded-lg border border-primary/20 bg-primary/5 px-3 sm:px-4 py-3">
              <p className="mb-2 text-xs font-medium text-muted-foreground">
                Ações rápidas sugeridas:
              </p>
              <div className="chips-scroll sm:flex-wrap sm:overflow-visible">
                {blueprintSuggestions.map(({ label, documentType }) => {
                  const isSimulation = ['jury', 'judge'].includes(documentType);
                  const href = isSimulation
                    ? `/dashboard/simulations/${documentType}`
                    : `/dashboard/intelligent-assistant?document_type=${documentType}`;
                  return (
                    <a
                      key={documentType}
                      href={href}
                      className="inline-flex items-center gap-1.5 rounded-md bg-primary/10 px-3 py-2 text-xs font-medium text-primary hover:bg-primary/20 transition-colors whitespace-nowrap shrink-0"
                    >
                      {isSimulation ? label : `Criar ${label}`}
                    </a>
                  );
                })}
              </div>
            </div>
          )}

          {error && (
            <div className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      {/* Input - fixed bottom with safe area padding for notch devices */}
      <div className="shrink-0 safe-area-bottom">
        <ChatInput
          onSend={sendMessage}
          onAttach={attachFile}
          onStop={stopGeneration}
          isStreaming={isStreaming}
          attachedFile={attachedFile}
          agents={agentMentions}
        />
      </div>
    </div>
  );
}

import type { User } from '@/types';

// ── Tipos ──────────────────────────────────────────────────────

export interface TourStep {
  /** Identificador único da etapa (ex: "welcome", "create-task") */
  id: string;
  /** Seletor CSS do elemento alvo (data-tour="..."). Vazio = overlay central */
  target: string;
  /** Título curto da etapa */
  title: string;
  /** Explicação clara (1-3 frases) */
  description: string;
  /** Posição do tooltip em relação ao elemento */
  placement: 'top' | 'bottom' | 'left' | 'right' | 'center';
  /** Role necessária para ver esta etapa (opcional) */
  requiredPermission?: User['role'];
  /** Feature flag (opcional, reservado para futuro) */
  featureFlag?: string;
  /** Rota onde esta etapa específica deve aparecer (opcional, default = rota do tour) */
  route?: string;
  /** Ação esperada do usuário nesta etapa */
  action?: 'none' | 'click' | 'navigate' | 'open_panel';
  /** Label do botão "Próximo" (padrão: "Próximo") */
  nextButtonLabel?: string;
  /** Label do botão "Voltar" (padrão: "Voltar") */
  backButtonLabel?: string;
}

export interface TourConfig {
  /** Identificador único do tour (ex: "tour-minhas-tarefas") */
  id: string;
  /** Rota ou regex de rota onde o tour é exibido */
  route: string | RegExp;
  /** Nome amigável do tour */
  name: string;
  /** Versão do tour — incrementar quando o tour mudar significativamente */
  version: string;
  /** Etapas do tour */
  steps: TourStep[];
  /** Role mínima necessária para ver o tour (opcional) */
  minRole?: User['role'];
}

// ── Constante de versão global ─────────────────────────────────

export const GLOBAL_TOUR_VERSION = 'v1.0';

// ── Configurações de Tour ──────────────────────────────────────

/**
 * Catálogo de tours do sistema.
 *
 * Para adicionar um novo tour:
 * 1. Crie um TourConfig com as etapas desejadas
 * 2. Adicione data-tour="<id-da-etapa>" nos elementos HTML alvo
 * 3. Adicione o config ao array `tourConfigs`
 */

export const tourConfigs: TourConfig[] = [
  // ════════════════════════════════════════════════════════════════
  // Tour: Minhas Tarefas
  // ════════════════════════════════════════════════════════════════
  {
    id: 'tour-minhas-tarefas',
    route: '/dashboard/minhas-tarefas',
    name: 'Minhas Tarefas',
    version: GLOBAL_TOUR_VERSION,
    minRole: 'distribuidor',
    steps: [
      {
        id: 'mt-welcome',
        target: '[data-tour="mt-header"]',
        title: 'Bem-vindo às suas tarefas',
        description: 'Esta é a central de tarefas do fluxo de trabalho. Aqui você encontra todas as atividades atribuídas a você nos processos em andamento.',
        placement: 'bottom',
        action: 'none',
      },
      {
        id: 'mt-filters',
        target: '[data-tour="mt-filters"]',
        title: 'Filtros de status',
        description: 'Use estes filtros para visualizar tarefas por status: Pendentes, Em andamento, Concluídas ou Todas. O número ao lado mostra a quantidade de tarefas no filtro atual.',
        placement: 'bottom',
        action: 'click',
        nextButtonLabel: 'Próximo',
      },
      {
        id: 'mt-task-card',
        target: '[data-tour="mt-task-card"]',
        title: 'Cartão de tarefa',
        description: 'Cada tarefa exibe o nome, tipo, prazo e instruções. As cores indicam a urgência: verde (ok), amarelo (próximo do prazo) e vermelho (crítico ou vencido).',
        placement: 'top',
        action: 'none',
      },
      {
        id: 'mt-complete',
        target: '[data-tour="mt-complete-btn"]',
        title: 'Concluir tarefa',
        description: 'Use este botão quando finalizar a atividade. Você pode adicionar observações e, se necessário, assinar digitalmente o documento.',
        placement: 'top',
        action: 'click',
      },
      {
        id: 'mt-request',
        target: '[data-tour="mt-request-btn"]',
        title: 'Solicitar redistribuição',
        description: 'Precisa passar a tarefa para outro colega? Use "Solicitar" para criar um pedido de redistribuição, avocação ou assessoria. O gestor será notificado para aprovação.',
        placement: 'top',
        action: 'click',
        nextButtonLabel: 'Finalizar',
      },
    ],
  },

  // ════════════════════════════════════════════════════════════════
  // Tour: Fluxos de Trabalho (templates)
  // ════════════════════════════════════════════════════════════════
  {
    id: 'tour-fluxos',
    route: '/dashboard/fluxos',
    name: 'Fluxos de Trabalho',
    version: GLOBAL_TOUR_VERSION,
    minRole: 'distribuidor',
    steps: [
      {
        id: 'fw-welcome',
        target: '[data-tour="fw-header"]',
        title: 'Fluxos de trabalho',
        description: 'Esta página lista todos os templates de fluxo BPMN do seu órgão. Os fluxos definem o passo a passo de cada tipo de processo judicial ou administrativo.',
        placement: 'bottom',
        action: 'none',
      },
      {
        id: 'fw-create',
        target: '[data-tour="fw-create-btn"]',
        title: 'Criar novo fluxo',
        description: 'Clique aqui para criar um novo template de fluxo. Você será levado ao editor visual onde pode arrastar e conectar nós para definir o roteiro do processo.',
        placement: 'left',
        action: 'click',
      },
      {
        id: 'fw-card',
        target: '[data-tour="fw-card"]',
        title: 'Template de fluxo',
        description: 'Cada card mostra as informações do template: nome, categoria, quantidade de nós e swim lanes. Use o botão "Iniciar" para executar um fluxo publicado.',
        placement: 'top',
        action: 'none',
      },
      {
        id: 'fw-editor',
        target: '[data-tour="fw-editor-link"]',
        title: 'Editor de fluxo',
        description: 'Clique em "Abrir editor" para visualizar ou modificar o diagrama BPMN. Lá você pode adicionar tarefas, gateways de decisão e definir responsáveis por cada etapa.',
        placement: 'top',
        action: 'navigate',
        nextButtonLabel: 'Finalizar',
      },
    ],
  },

  // ════════════════════════════════════════════════════════════════
  // Tour: Processos (casos)
  // ════════════════════════════════════════════════════════════════
  {
    id: 'tour-processos',
    route: '/dashboard/processos',
    name: 'Processos',
    version: GLOBAL_TOUR_VERSION,
    minRole: 'distribuidor',
    steps: [
      {
        id: 'pr-welcome',
        target: '[data-tour="pr-header"]',
        title: 'Processos do sistema',
        description: 'Aqui você gerencia todos os processos judiciais e administrativos do órgão. Cada processo pode ter um ou mais fluxos de trabalho em andamento.',
        placement: 'bottom',
        action: 'none',
      },
      {
        id: 'pr-flow-status',
        target: '[data-tour="pr-flow-status"]',
        title: 'Status do fluxo no processo',
        description: 'A coluna "Fluxo" indica se o processo possui um fluxo de trabalho ativo. Você pode iniciar múltiplos fluxos independentes para o mesmo processo, se necessário.',
        placement: 'top',
        action: 'none',
      },
      {
        id: 'pr-actions',
        target: '[data-tour="pr-actions"]',
        title: 'Ações do processo',
        description: 'Cada processo oferece ações como ver detalhes, editar informações ou iniciar um novo fluxo de trabalho diretamente do painel do processo.',
        placement: 'left',
        action: 'click',
        nextButtonLabel: 'Finalizar',
      },
    ],
  },
];

// ── Helpers ────────────────────────────────────────────────────

/**
 * Retorna as etapas de um tour filtrando por permissão do usuário.
 * Etapas que exigem `requiredPermission` só são incluídas se o
 * usuário tiver o nível mínimo de acesso.
 */
export function getFilteredSteps(
  config: TourConfig,
  hasPermission: (role: User['role']) => boolean,
): TourStep[] {
  return config.steps.filter((step) => {
    if (step.requiredPermission && !hasPermission(step.requiredPermission)) {
      return false;
    }
    return true;
  });
}
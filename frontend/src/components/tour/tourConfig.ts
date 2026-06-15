import type { User } from '@/types';

// ── Tipos ──────────────────────────────────────────────────────

export interface TourStep {
  id: string;
  target: string;
  title: string;
  description: string;
  placement: 'top' | 'bottom' | 'left' | 'right' | 'center';
  requiredPermission?: User['role'];
  featureFlag?: string;
  route?: string;
  action?: 'none' | 'click' | 'navigate' | 'open_panel';
  nextButtonLabel?: string;
  backButtonLabel?: string;
}

export interface TourConfig {
  id: string;
  route: string | RegExp;
  name: string;
  version: string;
  steps: TourStep[];
  minRole?: User['role'];
}

export const GLOBAL_TOUR_VERSION = 'v1.0';

// ═══════════════════════════════════════════════════════════════════
// CATÁLOGO DE TOURS
// ═══════════════════════════════════════════════════════════════════

export const tourConfigs: TourConfig[] = [

  // ── Dashboard Home ─────────────────────────────────────────────
  {
    id: 'tour-dashboard',
    route: '/dashboard$',
    name: 'Painel Inicial',
    version: GLOBAL_TOUR_VERSION,
    minRole: 'visualizador',
    steps: [
      {
        id: 'db-welcome',
        target: '[data-tour="db-header"]',
        title: 'Painel principal',
        description: 'Bem-vindo ao Verus.AI! Este é o painel central do sistema. Aqui você encontra um resumo dos indicadores, tarefas pendentes, documentos recentes e acesso rápido às principais funcionalidades.',
        placement: 'bottom',
        action: 'none',
      },
      {
        id: 'db-stats',
        target: '[data-tour="db-stats"]',
        title: 'Indicadores rápidos',
        description: 'Os cards de estatísticas mostram um resumo do seu órgão: total de processos, tarefas pendentes, prazos críticos e documentos gerados. Use esses números para ter uma visão geral do andamento dos trabalhos.',
        placement: 'bottom',
        action: 'none',
      },
      {
        id: 'db-tasks',
        target: '[data-tour="db-tasks"]',
        title: 'Minhas tarefas',
        description: 'Esta seção lista as tarefas atribuídas a você que necessitam de ação. Clique em uma tarefa para ir diretamente à página de detalhes ou concluí-la.',
        placement: 'top',
        action: 'click',
      },
      {
        id: 'db-recent',
        target: '[data-tour="db-recent"]',
        title: 'Documentos e atividades recentes',
        description: 'Aqui você acompanha os documentos atualizados recentemente e as atividades mais recentes do sistema. Use para saber o que aconteceu desde seu último acesso.',
        placement: 'top',
        action: 'none',
        nextButtonLabel: 'Finalizar',
      },
    ],
  },

  // ── Minhas Tarefas ─────────────────────────────────────────────
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

  // ── Fluxos de Trabalho ─────────────────────────────────────────
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
        description: 'Clique aqui para criar um novo template. Você será levado ao editor visual onde pode arrastar nós e conectá-los para definir o roteiro do processo.',
        placement: 'left',
        action: 'click',
      },
      {
        id: 'fw-card',
        target: '[data-tour="fw-card"]',
        title: 'Template de fluxo',
        description: 'Cada card mostra nome, categoria, quantidade de nós e swim lanes. Use o botão "Iniciar" para executar um fluxo publicado.',
        placement: 'top',
        action: 'none',
      },
      {
        id: 'fw-editor',
        target: '[data-tour="fw-editor-link"]',
        title: 'Editor de fluxo',
        description: 'Clique em "Abrir editor" para visualizar ou modificar o diagrama BPMN. Adicione tarefas, gateways de decisão e defina responsáveis por cada etapa do processo.',
        placement: 'top',
        action: 'navigate',
        nextButtonLabel: 'Finalizar',
      },
    ],
  },

  // ── Editor BPMN ────────────────────────────────────────────────
  {
    id: 'tour-editor-fluxo',
    route: /^\/dashboard\/fluxos\/editor\/.+/,
    name: 'Editor de Fluxo BPMN',
    version: GLOBAL_TOUR_VERSION,
    minRole: 'distribuidor',
    steps: [
      {
        id: 'ef-toolbar',
        target: '[data-tour="ef-toolbar"]',
        title: 'Barra de ferramentas',
        description: 'A barra superior contém as ações principais: salvar o template, publicar (disponibilizar para uso), desfazer/refazer alterações e configurar propriedades gerais do fluxo.',
        placement: 'bottom',
        action: 'none',
      },
      {
        id: 'ef-palette',
        target: '[data-tour="ef-palette"]',
        title: 'Paleta de nós',
        description: 'Arraste os nós da paleta para o canvas: tarefas (atividades humanas), gateways (decisões), eventos de início/fim e swim lanes (responsáveis). Cada nó tem propriedades configuráveis.',
        placement: 'right',
        action: 'click',
      },
      {
        id: 'ef-canvas',
        target: '[data-tour="ef-canvas"]',
        title: 'Canvas BPMN',
        description: 'O canvas é onde você desenha o fluxo. Conecte nós arrastando de um ponto de saída para um ponto de entrada. Use o scroll para zoom e clique em um nó para editar suas propriedades.',
        placement: 'top',
        action: 'none',
      },
      {
        id: 'ef-properties',
        target: '[data-tour="ef-properties"]',
        title: 'Painel de propriedades',
        description: 'Ao selecionar um nó, este painel exibe suas configurações: label, role responsável, instruções para o usuário e condições (para gateways). Preencha para orientar a execução.',
        placement: 'left',
        action: 'click',
        nextButtonLabel: 'Finalizar',
      },
    ],
  },

  // ── Processos (lista) ──────────────────────────────────────────
  {
    id: 'tour-processos',
    route: '/dashboard/processos$',
    name: 'Processos',
    version: GLOBAL_TOUR_VERSION,
    minRole: 'distribuidor',
    steps: [
      {
        id: 'pr-welcome',
        target: '[data-tour="pr-header"]',
        title: 'Processos do órgão',
        description: 'Aqui você gerencia todos os processos judiciais e administrativos. Cada processo pode ter fluxos de trabalho em andamento, prazos vinculados e documentos associados.',
        placement: 'bottom',
        action: 'none',
      },
      {
        id: 'pr-search',
        target: '[data-tour="pr-search"]',
        title: 'Busca e filtros',
        description: 'Use a barra de busca para localizar processos por número CNJ, título, cliente ou parte contrária. Os filtros permitem refinar por status, especialidade ou tribunal.',
        placement: 'bottom',
        action: 'click',
      },
      {
        id: 'pr-flow-status',
        target: '[data-tour="pr-flow-status"]',
        title: 'Status do fluxo',
        description: 'Cada processo exibe indicadores visuais: status do fluxo ativo, quantidade de tarefas pendentes e prazos. Você pode iniciar múltiplos fluxos independentes para o mesmo processo.',
        placement: 'top',
        action: 'none',
      },
      {
        id: 'pr-actions',
        target: '[data-tour="pr-actions"]',
        title: 'Ações do processo',
        description: 'Clique em um processo para ver detalhes completos, editar informações, iniciar fluxo de trabalho ou acessar documentos e prazos vinculados.',
        placement: 'left',
        action: 'click',
        nextButtonLabel: 'Finalizar',
      },
    ],
  },

  // ── Detalhe do Processo ────────────────────────────────────────
  {
    id: 'tour-processo-detalhe',
    route: /^\/dashboard\/processos\/[^\/]+\/?$/,
    name: 'Detalhe do Processo',
    version: GLOBAL_TOUR_VERSION,
    minRole: 'distribuidor',
    steps: [
      {
        id: 'pd-header',
        target: '[data-tour="pd-header"]',
        title: 'Detalhes do processo',
        description: 'Esta página exibe todas as informações do processo: dados principais, partes envolvidas, tribunal, valor da causa e prazos. Use as abas para navegar entre as seções.',
        placement: 'bottom',
        action: 'none',
      },
      {
        id: 'pd-flow-panel',
        target: '[data-tour="pd-flow-panel"]',
        title: 'Painel de fluxo',
        description: 'O painel "Fluxo de Trabalho" mostra o status do fluxo ativo. Se não houver fluxo em andamento, você pode iniciar um novo. Acompanhe tarefas pendentes e visualize o andamento.',
        placement: 'top',
        action: 'click',
      },
      {
        id: 'pd-tabs',
        target: '[data-tour="pd-tabs"]',
        title: 'Abas de navegação',
        description: 'Navegue entre as abas para acessar: Informações do processo, Documentos, Prazos, Fluxo de trabalho, Histórico de alterações e muito mais.',
        placement: 'bottom',
        action: 'click',
      },
      {
        id: 'pd-actions',
        target: '[data-tour="pd-actions"]',
        title: 'Ações disponíveis',
        description: 'Botões de ação permitem editar o processo, anexar documentos, criar novo fluxo de trabalho ou acessar funcionalidades específicas como simulação e geração de peças.',
        placement: 'left',
        action: 'click',
        nextButtonLabel: 'Finalizar',
      },
    ],
  },

  // ── Execuções (lista) ──────────────────────────────────────────
  {
    id: 'tour-execucoes',
    route: '/dashboard/execucoes$',
    name: 'Execuções de Fluxo',
    version: GLOBAL_TOUR_VERSION,
    minRole: 'distribuidor',
    steps: [
      {
        id: 'ex-header',
        target: '[data-tour="ex-header"]',
        title: 'Execuções de fluxo',
        description: 'Aqui você acompanha todas as instâncias de fluxo em execução no seu órgão. Cada linha representa um fluxo iniciado a partir de um template.',
        placement: 'bottom',
        action: 'none',
      },
      {
        id: 'ex-status',
        target: '[data-tour="ex-status"]',
        title: 'Status da execução',
        description: 'Cada execução exibe seu status atual: Aguardando, Em andamento, Concluído ou Cancelado. A cor do indicador muda conforme o estado.',
        placement: 'top',
        action: 'none',
      },
      {
        id: 'ex-pending',
        target: '[data-tour="ex-pending"]',
        title: 'Tarefas pendentes',
        description: 'O badge de tarefas pendentes mostra quantas atividades aguardam ação humana. Clique na execução para ver os detalhes e avançar o fluxo.',
        placement: 'top',
        action: 'click',
        nextButtonLabel: 'Finalizar',
      },
    ],
  },

  // ── Detalhe da Execução ────────────────────────────────────────
  {
    id: 'tour-execucao-detalhe',
    route: /^\/dashboard\/execucoes\/[^\/]+\/?$/,
    name: 'Detalhe da Execução',
    version: GLOBAL_TOUR_VERSION,
    minRole: 'distribuidor',
    steps: [
      {
        id: 'ed-header',
        target: '[data-tour="ed-header"]',
        title: 'Acompanhamento do fluxo',
        description: 'Esta página mostra o andamento detalhado de uma execução de fluxo. Aqui você vê todas as tarefas, eventos e o progresso geral.',
        placement: 'bottom',
        action: 'none',
      },
      {
        id: 'ed-tasks',
        target: '[data-tour="ed-tasks"]',
        title: 'Tarefas da execução',
        description: 'Lista de todas as tarefas desta instância de fluxo, com status, responsável e opções de ação. Tarefas pendentes podem ser concluídas diretamente aqui.',
        placement: 'top',
        action: 'click',
      },
      {
        id: 'ed-timeline',
        target: '[data-tour="ed-timeline"]',
        title: 'Linha do tempo',
        description: 'O histórico de eventos registra cada ação no fluxo: quando foi iniciado, tarefas concluídas, decisões tomadas em gateways e solicitações aprovadas ou rejeitadas.',
        placement: 'top',
        action: 'none',
        nextButtonLabel: 'Finalizar',
      },
    ],
  },

  // ── Solicitações (gerentes) ────────────────────────────────────
  {
    id: 'tour-solicitacoes',
    route: '/dashboard/solicitacoes',
    name: 'Solicitações',
    version: GLOBAL_TOUR_VERSION,
    minRole: 'gerente',
    steps: [
      {
        id: 'sl-header',
        target: '[data-tour="sl-header"]',
        title: 'Solicitações de tarefas',
        description: 'Esta página é exclusiva para gerentes e chefias. Aqui você gerencia pedidos de redistribuição, avocação e assessoria feitos pelos membros da sua equipe.',
        placement: 'bottom',
        action: 'none',
      },
      {
        id: 'sl-card',
        target: '[data-tour="sl-card"]',
        title: 'Cartão de solicitação',
        description: 'Cada solicitação mostra o tipo (Redistribuição, Avocação ou Assessoria), quem solicitou, para quem (quando aplicável) e a justificativa.',
        placement: 'top',
        action: 'none',
      },
      {
        id: 'sl-actions',
        target: '[data-tour="sl-actions"]',
        title: 'Aprovar ou rejeitar',
        description: 'Use os botões "Aprovar" ou "Rejeitar" para resolver a solicitação. Ao aprovar uma redistribuição, a tarefa é automaticamente transferida para o usuário de destino.',
        placement: 'top',
        action: 'click',
        nextButtonLabel: 'Finalizar',
      },
    ],
  },

  // ── Usuários (admin) ───────────────────────────────────────────
  {
    id: 'tour-users',
    route: '/dashboard/users',
    name: 'Usuários',
    version: GLOBAL_TOUR_VERSION,
    minRole: 'admin',
    steps: [
      {
        id: 'us-header',
        target: '[data-tour="us-header"]',
        title: 'Gestão de usuários',
        description: 'Área administrativa para gerenciar todos os usuários do sistema. Aqui você pode criar, editar, ativar ou desativar contas.',
        placement: 'bottom',
        action: 'none',
      },
      {
        id: 'us-create',
        target: '[data-tour="us-create"]',
        title: 'Adicionar usuário',
        description: 'Clique em "Novo usuário" para criar uma conta. Defina nome, email, role (cargo/função) e permissões de acesso. O usuário receberá instruções de acesso por email.',
        placement: 'top',
        action: 'click',
      },
      {
        id: 'us-table',
        target: '[data-tour="us-table"]',
        title: 'Tabela de usuários',
        description: 'A tabela lista todos os usuários com nome, email, role e status (ativo/inativo). Use os botões de ação para editar, desativar ou redefinir senha.',
        placement: 'top',
        action: 'click',
        nextButtonLabel: 'Finalizar',
      },
    ],
  },

  // ── Equipe ─────────────────────────────────────────────────────
  {
    id: 'tour-equipe',
    route: '/dashboard/equipe',
    name: 'Equipes',
    version: GLOBAL_TOUR_VERSION,
    minRole: 'gerente',
    steps: [
      {
        id: 'eq-header',
        target: '[data-tour="eq-header"]',
        title: 'Gestão de equipes',
        description: 'Organize os usuários em equipes de trabalho. As equipes facilitam a distribuição de tarefas e o acompanhamento por grupo de atuação.',
        placement: 'bottom',
        action: 'none',
      },
      {
        id: 'eq-teams',
        target: '[data-tour="eq-teams"]',
        title: 'Times e membros',
        description: 'Visualize as equipes existentes e seus membros. Use "Nova equipe" para criar um grupo e adicione membros com as roles apropriadas para cada tipo de atividade.',
        placement: 'top',
        action: 'click',
      },
      {
        id: 'eq-assignments',
        target: '[data-tour="eq-assignments"]',
        title: 'Atribuições da equipe',
        description: 'Defina quais tipos de fluxo ou especialidades cada equipe pode tratar. Isso ajuda o sistema a distribuir tarefas automaticamente para o grupo correto.',
        placement: 'top',
        action: 'click',
        nextButtonLabel: 'Finalizar',
      },
    ],
  },

  // ── Blueprints ─────────────────────────────────────────────────
  {
    id: 'tour-blueprints',
    route: '/dashboard/blueprints',
    name: 'Blueprints',
    version: GLOBAL_TOUR_VERSION,
    minRole: 'procurador',
    steps: [
      {
        id: 'bp-header',
        target: '[data-tour="bp-header"]',
        title: 'Blueprints de documentos',
        description: 'Blueprints são modelos estruturados de documentos jurídicos. Cada blueprint define seções, campos e agentes de IA que auxiliam na geração automatizada de peças processuais e documentos administrativos.',
        placement: 'bottom',
        action: 'none',
      },
      {
        id: 'bp-list',
        target: '[data-tour="bp-list"]',
        title: 'Lista de blueprints',
        description: 'Navegue pelos blueprints disponíveis. Cada card mostra o tipo de documento, versão, quantidade de seções e status (ativo/inativo). Use a busca para localizar rapidamente.',
        placement: 'top',
        action: 'click',
      },
      {
        id: 'bp-actions',
        target: '[data-tour="bp-actions"]',
        title: 'Ações do blueprint',
        description: 'Cada blueprint oferece ações: editar (configurar seções e agentes), ativar/desativar, duplicar ou excluir. Blueprints ativos podem ser usados na geração de documentos.',
        placement: 'top',
        action: 'click',
        nextButtonLabel: 'Finalizar',
      },
    ],
  },

  // ── Agentes IA ─────────────────────────────────────────────────
  {
    id: 'tour-agentes',
    route: '/dashboard/agents',
    name: 'Agentes de IA',
    version: GLOBAL_TOUR_VERSION,
    minRole: 'procurador',
    steps: [
      {
        id: 'ag-header',
        target: '[data-tour="ag-header"]',
        title: 'Agentes de inteligência artificial',
        description: 'Os agentes de IA são assistentes especializados que auxiliam em tarefas jurídicas. Cada agente tem uma área de atuação (licitações, jurisprudência, petições etc.) e pode usar RAG para buscar em bases de conhecimento.',
        placement: 'bottom',
        action: 'none',
      },
      {
        id: 'ag-list',
        target: '[data-tour="ag-list"]',
        title: 'Catálogo de agentes',
        description: 'A lista mostra todos os agentes disponíveis com seu ícone, nome, provedor LLM e status. Agentes podem ser configurados com prompts personalizados e fontes de conhecimento específicas.',
        placement: 'top',
        action: 'click',
      },
      {
        id: 'ag-chat',
        target: '[data-tour="ag-chat"]',
        title: 'Conversar com agente',
        description: 'Clique em um agente para iniciar uma conversa. Você pode fazer perguntas jurídicas, pedir análises de documentos ou solicitar minutas. O agente responde com base no conhecimento configurado.',
        placement: 'top',
        action: 'click',
        nextButtonLabel: 'Finalizar',
      },
    ],
  },

  // ── Configurações ──────────────────────────────────────────────
  {
    id: 'tour-settings',
    route: /^\/dashboard\/settings\//,
    name: 'Configurações',
    version: GLOBAL_TOUR_VERSION,
    minRole: 'visualizador',
    steps: [
      {
        id: 'st-profile',
        target: '[data-tour="st-profile"]',
        title: 'Seu perfil',
        description: 'Gerencie suas informações pessoais: nome, email, foto, assinatura digital e preferências de IA. Estas configurações são pessoais e não afetam outros usuários.',
        placement: 'bottom',
        action: 'none',
      },
      {
        id: 'st-brand',
        target: '[data-tour="st-brand"]',
        title: 'Personalização do sistema',
        description: 'Configure a identidade visual do seu órgão: nome do sistema, logotipo, cores primárias e secundárias. As alterações são aplicadas em tempo real para todos os usuários.',
        placement: 'top',
        action: 'click',
      },
      {
        id: 'st-roles',
        target: '[data-tour="st-roles"]',
        title: 'Roles e permissões',
        description: 'Visualize a matriz de permissões do sistema. Cada role (cargo) tem um nível hierárquico que define quais ações pode executar, como distribuir tarefas, assinar documentos ou aprovar solicitações.',
        placement: 'top',
        action: 'click',
        nextButtonLabel: 'Finalizar',
      },
    ],
  },
];

// ── Helpers ────────────────────────────────────────────────────

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

/**
 * Retorna o tour configurado para uma rota, ou null se não houver.
 * Usa match exato para string, test para RegExp.
 */
export function findTourForRoute(pathname: string): TourConfig | undefined {
  return tourConfigs.find((cfg) => {
    if (typeof cfg.route === 'string') return pathname === cfg.route;
    return cfg.route.test(pathname);
  });
}
/**
 * vote-utils.ts — Utilitários compartilhados para categorização e cores de votos.
 *
 * Fornece um sistema padronizado de categorias de votos usado por todas as
 * páginas de simulação colegiada, garantindo placar correto e cores consistentes.
 */

// ─── Categorias de Voto ───

export interface VoteCategory {
  /** Identificador único da categoria */
  id: string;
  /** Rótulo amigável para exibição no placar */
  label: string;
  /** Rótulo completo (usado em resultados) */
  labelFull: string;
  /** Padrões para matching (case-insensitive, verificados com .includes()) */
  patterns: string[];
  /** Classes Tailwind para o badge/card */
  badgeClass: string;
  /** Cor do texto do número no placar */
  scoreClass: string;
  /** Classe para o ícone/círculo do voto */
  iconClass: string;
  /** Classe para borda de card */
  borderClass: string;
}

export const VOTE_CATEGORIES: VoteCategory[] = [
  {
    id: 'provimento',
    label: 'Provimento',
    labelFull: 'Provimento / Procedente',
    patterns: ['provimento', 'procedente', 'deferido', 'defiro', 'dou provimento', 'provido', 'absolvicao'],
    badgeClass: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    scoreClass: 'text-green-600',
    iconClass: 'bg-green-100 dark:bg-green-900',
    borderClass: 'border-green-300 bg-green-50 dark:border-green-800 dark:bg-green-950/20',
  },
  {
    id: 'desprovimento',
    label: 'Desprovimento',
    labelFull: 'Desprovimento / Improcedente',
    patterns: ['desprovimento', 'nego provimento', 'desprovido', 'improcedente', 'indeferido', 'indefiro', 'condenacao', 'culpado'],
    badgeClass: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    scoreClass: 'text-red-600',
    iconClass: 'bg-red-100 dark:bg-red-900',
    borderClass: 'border-red-300 bg-red-50 dark:border-red-800 dark:bg-red-950/20',
  },
  {
    id: 'parcial',
    label: 'Parcial',
    labelFull: 'Provimento Parcial',
    patterns: ['parcial'],
    badgeClass: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
    scoreClass: 'text-amber-600',
    iconClass: 'bg-amber-100 dark:bg-amber-900',
    borderClass: 'border-amber-300 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/20',
  },
  {
    id: 'sem_merito',
    label: 'Sem Mérito',
    labelFull: 'Não Conhecido / Sem Mérito',
    patterns: ['nao_conhecido', 'nao conhecido', 'nao_admitido', 'nao admitido', 'prejudicado', 'extinto', 'nao se conhece'],
    badgeClass: 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200',
    scoreClass: 'text-slate-500',
    iconClass: 'bg-slate-100 dark:bg-slate-800',
    borderClass: 'border-slate-300 bg-slate-50 dark:border-slate-600 dark:bg-slate-900/30',
  },
  {
    id: 'indeterminado',
    label: 'Indeterminado',
    labelFull: 'Voto Indeterminado',
    patterns: ['indeterminado'],
    badgeClass: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
    scoreClass: 'text-orange-500',
    iconClass: 'bg-orange-100 dark:bg-orange-900',
    borderClass: 'border-orange-300 bg-orange-50 dark:border-orange-800 dark:bg-orange-950/20',
  },
];

// ─── Funções de matching ───

/**
 * Classifica um valor de voto em uma categoria.
 * Percorre as categorias na ordem de prioridade e retorna a primeira que match.
 * @param voteValue - O valor do voto (ex: "provimento", "provimento_parcial")
 * @returns A categoria de voto correspondente
 */
export function categorizeVote(voteValue: string): VoteCategory {
  if (!voteValue) return VOTE_CATEGORIES[4]; // indeterminado
  const lower = voteValue.toLowerCase();

  // Verifica "parcial" PRIMEIRO para evitar que "provimento_parcial" seja pego por "provimento"
  if (lower.includes('parcial')) return VOTE_CATEGORIES[2];

  for (const cat of VOTE_CATEGORIES) {
    for (const pattern of cat.patterns) {
      if (lower.includes(pattern)) return cat;
    }
  }

  return VOTE_CATEGORIES[4]; // indeterminado
}

/**
 * Conta os votos em cada categoria.
 * @param votes - Array de objetos com propriedade `vote`
 * @returns Um mapa de categoryId → contagem
 */
export function countVotesByCategory(votes: { vote: string }[]): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const cat of VOTE_CATEGORIES) {
    counts[cat.id] = 0;
  }
  for (const v of votes) {
    const cat = categorizeVote(v.vote);
    counts[cat.id] = (counts[cat.id] || 0) + 1;
  }
  return counts;
}

/**
 * Obtém a categoria de voto dominante (maioria).
 * @param votes - Array de objetos com propriedade `vote`
 * @returns O id da categoria vencedora, ou empate entre as duas primeiras
 */
export function getDominantCategory(votes: { vote: string }[]): { id: string; count: number } {
  const counts = countVotesByCategory(votes);
  let maxCat = 'indeterminado';
  let maxCount = 0;
  for (const cat of VOTE_CATEGORIES) {
    if ((counts[cat.id] || 0) > maxCount) {
      maxCount = counts[cat.id];
      maxCat = cat.id;
    }
  }
  return { id: maxCat, count: maxCount };
}

/**
 * Obtém a categoria para um array de votos, considerando maioria.
 * Retorna as categorias ordenadas por contagem (maior primeiro).
 */
export function getSortedCategories(votes: { vote: string }[]): { category: VoteCategory; count: number }[] {
  const counts = countVotesByCategory(votes);
  return VOTE_CATEGORIES
    .map(cat => ({ category: cat, count: counts[cat.id] || 0 }))
    .filter(item => item.count > 0)
    .sort((a, b) => b.count - a.count);
}

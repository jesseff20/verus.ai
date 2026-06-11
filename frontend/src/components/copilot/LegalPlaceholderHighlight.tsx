/**
 * Plugin de destaque de placeholders jurídicos para TinyMCE
 * Destaca visualmente marcadores que precisam de ação do advogado
 */

export interface PlaceholderMatch {
  text: string;
  type: 'jurisprudencia' | 'informacao_necessaria' | 'tese_controvertida' | 'verificar_base' | 'sugestao_ia';
  severity: 'critical' | 'warning' | 'info';
}

export const PLACEHOLDER_PATTERNS: Record<string, {
  pattern: RegExp;
  bgColor: string;
  borderColor: string;
  label: string;
  severity: 'critical' | 'warning' | 'info';
}> = {
  jurisprudencia: {
    pattern: /\[PESQUISAR JURISPRUDÊNCIA:[^\]]+\]/g,
    bgColor: '#FFF3CD',
    borderColor: '#FFC107',
    label: 'Jurisprudência a verificar',
    severity: 'warning',
  },
  informacao_necessaria: {
    pattern: /\[INFORMAÇÃO NECESSÁRIA:[^\]]+\]/g,
    bgColor: '#F8D7DA',
    borderColor: '#DC3545',
    label: 'Informação obrigatória faltante',
    severity: 'critical',
  },
  tese_controvertida: {
    pattern: /\[TESE CONTROVERTIDA:[^\]]+\]/g,
    bgColor: '#D1ECF1',
    borderColor: '#17A2B8',
    label: 'Tese jurídica controvertida',
    severity: 'info',
  },
  verificar_base: {
    pattern: /\[VERIFICAR BASE LEGAL:[^\]]+\]/g,
    bgColor: '#FFE8D0',
    borderColor: '#FD7E14',
    label: 'Base legal a verificar',
    severity: 'warning',
  },
  sugestao_ia: {
    pattern: /\[SUGESTÃO DA IA[^\]]*\]/g,
    bgColor: '#D4EDDA',
    borderColor: '#28A745',
    label: 'Sugestão da IA - verificar',
    severity: 'info',
  },
};

export interface PlaceholderCount {
  total: number;
  critical: number;
  warning: number;
  info: number;
  byType: Record<string, number>;
}

export function countPlaceholders(content: string): PlaceholderCount {
  const counts: PlaceholderCount = {
    total: 0,
    critical: 0,
    warning: 0,
    info: 0,
    byType: {},
  };

  for (const [type, config] of Object.entries(PLACEHOLDER_PATTERNS)) {
    const matches = content.match(config.pattern) || [];
    counts.byType[type] = matches.length;
    counts.total += matches.length;
    counts[config.severity] += matches.length;
    // Reset regex
    config.pattern.lastIndex = 0;
  }

  return counts;
}

export function highlightPlaceholders(htmlContent: string): string {
  let result = htmlContent;

  for (const [, config] of Object.entries(PLACEHOLDER_PATTERNS)) {
    result = result.replace(config.pattern, (match) => {
      return `<mark style="background-color: ${config.bgColor}; border: 1px solid ${config.borderColor}; border-radius: 3px; padding: 1px 4px; font-family: monospace; font-size: 0.9em;" title="${config.label}">${match}</mark>`;
    });
    config.pattern.lastIndex = 0;
  }

  return result;
}

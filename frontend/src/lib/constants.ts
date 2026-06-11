/** Lista de especialidades jurídicas */
export const ESPECIALIDADES_LIST = [
  'Cível',
  'Penal',
  'Trabalhista',
  'Tributário',
  'Previdenciário',
  'Administrativo',
  'Constitucional',
  'Empresarial',
  'Consumidor',
  'Família e Sucessões',
  'Imobiliário',
  'Ambiental',
  'Digital e Tecnologia',
  'Saúde',
  'Eleitoral',
  'Desportivo',
  'Marítimo',
  'Aduaneiro',
  'Militar',
  'Internacional',
] as const;

// Mantém ESPECIALIDADES como alias para compatibilidade
export const ESPECIALIDADES = ESPECIALIDADES_LIST;

/** Mapa de especialidades com value/label para selects */
export const ESPECIALIDADES_OPTIONS = [
  { value: 'geral', label: 'Geral (Todas)' },
  { value: 'civel', label: 'Direito Civil' },
  { value: 'penal', label: 'Direito Penal' },
  { value: 'trabalhista', label: 'Direito Trabalhista' },
  { value: 'tributario', label: 'Direito Tributário' },
  { value: 'previdenciario', label: 'Direito Previdenciário' },
  { value: 'administrativo', label: 'Direito Administrativo' },
  { value: 'constitucional', label: 'Direito Constitucional' },
  { value: 'empresarial', label: 'Direito Empresarial' },
  { value: 'consumidor', label: 'Direito do Consumidor' },
  { value: 'familia', label: 'Direito de Família e Sucessões' },
  { value: 'imobiliario', label: 'Direito Imobiliário' },
  { value: 'ambiental', label: 'Direito Ambiental' },
  { value: 'digital', label: 'Direito Digital e LGPD' },
  { value: 'saude', label: 'Direito da Saúde' },
  { value: 'eleitoral', label: 'Direito Eleitoral' },
  { value: 'internacional', label: 'Direito Internacional' },
] as const;

/** Labels para status de sessão de geração */
export const STATUS_SESSAO: Record<string, { label: string; variant: string }> = {
  initialized: { label: 'Iniciada', variant: 'outline' },
  uploading: { label: 'Enviando', variant: 'secondary' },
  processing: { label: 'Processando', variant: 'secondary' },
  generating: { label: 'Gerando', variant: 'secondary' },
  validating: { label: 'Validando', variant: 'secondary' },
  formatting: { label: 'Formatando', variant: 'secondary' },
  completed: { label: 'Concluída', variant: 'default' },
  failed: { label: 'Falhou', variant: 'destructive' },
};

/** Ordem das fases no fluxo de geração */
export const PHASE_ORDER = [
  'upload',
  'generation',
  'evaluation',
  'analysis',
  'result',
  'history',
] as const;

/** Mapeamento de step (wizard) para fase */
export const STEP_TO_PHASE: Record<string, string> = {
  '0': 'upload',
  '1': 'generation',
  '2': 'evaluation',
  '3': 'analysis',
  '4': 'result',
  '5': 'history',
};

'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '@/lib/api';

/**
 * Tipos de sugestão do Copilot Jurídico
 */
export type CopilotSuggestionType =
  | 'citation'        // Sugestão de citação jurídica
  | 'jurisprudence'   // Jurisprudência relacionada
  | 'clause'          // Cláusula/modelo
  | 'deadline'        // Cálculo de prazo
  | 'argument'        // Argumento jurídico
  | 'definition'      // Definição de termo técnico
  | 'statute'         // Legislação aplicável
  | 'correction';     // Correção gramatical/técnica

export interface CopilotSuggestion {
  id: string;
  type: CopilotSuggestionType;
  title: string;
  content: string;
  source?: string;
  relevanceScore: number;
  metadata?: Record<string, unknown>;
}

export interface CopilotContext {
  /** Texto atual do documento */
  currentText: string;
  /** Posição do cursor */
  cursorPosition: number;
  /** Palavra/fragmento atual sendo digitado */
  currentFragment: string;
  /** Tipo de documento */
  documentType?: string;
  /** Especialidade jurídica */
  specialty?: string;
  /** Contexto adicional */
  extraContext?: Record<string, unknown>;
}

interface UseLegalCopilotOptions {
  /** Delay para trigger de sugestões (ms) */
  debounceMs?: number;
  /** Trigger automático ao digitar */
  autoTrigger?: boolean;
  /** Trigger manual via atalho */
  manualTrigger?: boolean;
  /** Tipos de sugestão habilitados */
  enabledTypes?: CopilotSuggestionType[];
  /** Número máximo de sugestões */
  maxSuggestions?: number;
  /** Threshold de relevância mínima */
  minRelevanceScore?: number;
}

/**
 * Hook para Copilot Jurídico - sugestões em tempo real
 *
 * @example
 * const {
 *   suggestions,
 *   isLoading,
 *   triggerSuggestions,
 *   acceptSuggestion,
 *   dismissSuggestion,
 *   isActive,
 * } = useLegalCopilot({
 *   debounceMs: 500,
 *   autoTrigger: true,
 *   enabledTypes: ['citation', 'jurisprudence', 'clause'],
 * });
 */
export function useLegalCopilot(options: UseLegalCopilotOptions = {}) {
  const {
    debounceMs = 500,
    autoTrigger = true,
    manualTrigger = true,
    enabledTypes = ['citation', 'jurisprudence', 'clause', 'argument', 'statute'],
    maxSuggestions = 5,
    minRelevanceScore = 0.3,
  } = options;

  const [suggestions, setSuggestions] = useState<CopilotSuggestion[]>([]);
  const [isActive, setIsActive] = useState(false);
  const [context, setContext] = useState<CopilotContext | null>(null);
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);

  // Mutation para buscar sugestões da API
  const suggestMutation = useMutation({
    mutationFn: async (ctx: CopilotContext) => {
      const response = await api.post<{ suggestions: CopilotSuggestion[] }>(
        '/api/v1/intelligent-assistant/copilot/suggest/',
        {
          current_text: ctx.currentText,
          cursor_position: ctx.cursorPosition,
          current_fragment: ctx.currentFragment,
          document_type: ctx.documentType,
          specialty: ctx.specialty,
          extra_context: ctx.extraContext,
          enabled_types: enabledTypes,
          max_suggestions: maxSuggestions,
        }
      );
      return response.data.suggestions;
    },
  });

  // Trigger de sugestões com debounce
  const triggerSuggestions = useCallback((ctx: CopilotContext) => {
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    debounceTimer.current = setTimeout(() => {
      setContext(ctx);
      setIsActive(true);
      suggestMutation.mutate(ctx, {
        onSuccess: (data) => {
          const filtered = data.filter(s => s.relevanceScore >= minRelevanceScore);
          setSuggestions(filtered.slice(0, maxSuggestions));
        },
        onError: () => {
          setSuggestions([]);
        },
      });
    }, debounceMs);
  }, [debounceMs, suggestMutation, enabledTypes, maxSuggestions, minRelevanceScore]);

  // Aceitar sugestão
  const acceptSuggestion = useCallback((suggestion: CopilotSuggestion) => {
    // TODO: Implementar inserção no editor
    setSuggestions(prev => prev.filter(s => s.id !== suggestion.id));
  }, []);

  // Descartar sugestão
  const dismissSuggestion = useCallback((suggestionId: string) => {
    setSuggestions(prev => prev.filter(s => s.id !== suggestionId));
  }, []);

  // Limpar sugestões
  const clearSuggestions = useCallback(() => {
    setSuggestions([]);
    setIsActive(false);
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }
  }, []);

  // Cleanup
  useEffect(() => {
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, []);

  return {
    // Estado
    suggestions,
    isLoading: suggestMutation.isPending,
    isActive,
    context,

    // Ações
    triggerSuggestions,
    acceptSuggestion,
    dismissSuggestion,
    clearSuggestions,

    // Error handling
    error: suggestMutation.error,
  };
}

/**
 * Hook para atalhos do Copilot (/, @, #)
 */
export function useCopilotShortcuts(
  onTrigger: (type: CopilotSuggestionType) => void
) {
  const [activeTrigger, setActiveTrigger] = useState<string | null>(null);

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    const target = event.target as HTMLElement;
    const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA';

    if (!isInput) return;

    // Atalhos do Copilot
    if (event.key === '/' && !event.ctrlKey && !event.metaKey) {
      event.preventDefault();
      setActiveTrigger('slash');
      onTrigger('citation');
      return;
    }

    if (event.key === '@') {
      setActiveTrigger('mention');
      onTrigger('jurisprudence');
      return;
    }

    if (event.key === '#') {
      setActiveTrigger('hashtag');
      onTrigger('statute');
      return;
    }

    if (event.key === 'Escape') {
      setActiveTrigger(null);
    }
  }, [onTrigger]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return {
    activeTrigger,
    clearTrigger: () => setActiveTrigger(null),
  };
}

/**
 * Comandos slash do Copilot
 */
export const SLASH_COMMANDS: Record<string, {
  command: string;
  description: string;
  type: CopilotSuggestionType;
  shortcut?: string;
}> = {
  citacao: {
    command: 'citacao',
    description: 'Inserir citação jurídica',
    type: 'citation',
    shortcut: '/',
  },
  juris: {
    command: 'juris',
    description: 'Buscar jurisprudência',
    type: 'jurisprudence',
    shortcut: '@',
  },
  prazo: {
    command: 'prazo',
    description: 'Calcular prazo processual',
    type: 'deadline',
  },
  modelo: {
    command: 'modelo',
    description: 'Inserir modelo/cláusula',
    type: 'clause',
  },
  argumento: {
    command: 'argumento',
    description: 'Sugerir argumento',
    type: 'argument',
  },
  definicao: {
    command: 'definicao',
    description: 'Definir termo técnico',
    type: 'definition',
  },
  lei: {
    command: 'lei',
    description: 'Buscar legislação',
    type: 'statute',
    shortcut: '#',
  },
  corregir: {
    command: 'corrigir',
    description: 'Corrigir texto',
    type: 'correction',
  },
};

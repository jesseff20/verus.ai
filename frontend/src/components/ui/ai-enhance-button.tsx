'use client';

import { useState } from 'react';
import { Sparkles, Loader2, Wand2 } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { toast } from 'sonner';
import api from '@/lib/api';

interface AIEnhanceButtonProps {
  /** Texto atual do campo */
  value: string;
  /** Callback com texto melhorado/gerado */
  onEnhance: (text: string) => void;
  /** Contexto da página (ex: "prompt de agente jurídico") */
  context?: string;
  /** Objetivo (ex: "melhorar clareza e fundamentação jurídica") */
  objective?: string;
  disabled?: boolean;
  className?: string;
  /** Modo compacto — apenas ícone, sem label */
  compact?: boolean;
  /** Variante para campos dentro de modais/painéis escuros */
  variant?: 'default' | 'dark';
}

export function AIEnhanceButton({
  value,
  onEnhance,
  context,
  objective,
  disabled,
  className,
  compact = false,
  variant = 'default',
}: AIEnhanceButtonProps) {
  const [isLoading, setIsLoading] = useState(false);
  const isEmpty = !value.trim();

  const handleClick = async () => {
    if (isLoading) return;
    setIsLoading(true);
    try {
      const response = await api.post('/api/v1/intelligent-assistant/enhance-text/', {
        text: value,
        context: context || 'campo de formulário jurídico',
        objective: isEmpty
          ? (objective || 'Gere um texto adequado para este campo com base no contexto. Seja conciso e profissional.')
          : (objective || 'Melhore a clareza, corrija erros de português e aperfeiçoe o texto mantendo o sentido original'),
      });
      onEnhance(response.data.enhanced_text);
      toast.success(isEmpty ? 'Texto gerado com IA.' : 'Texto aprimorado com IA.');
    } catch (error: any) {
      toast.error(error?.response?.data?.error || 'Não foi possível processar o texto.');
    } finally {
      setIsLoading(false);
    }
  };

  if (variant === 'dark') {
    return (
      <TooltipProvider delayDuration={300}>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              onClick={handleClick}
              disabled={disabled || isLoading}
              className={`flex items-center gap-1 text-[10px] font-medium transition-all disabled:opacity-40 px-1.5 py-0.5 rounded ${
                compact ? '' : 'px-2 py-1'
              } ${className ?? ''}`}
              style={{ color: '#8B5CF6', background: 'transparent' }}
              aria-label={isEmpty ? 'Gerar com IA' : 'Aprimorar com IA'}
            >
              {isLoading ? (
                <Loader2 size={11} className="animate-spin" />
              ) : (
                <Sparkles size={11} />
              )}
              {!compact && (
                <span>{isEmpty ? 'Gerar' : 'Aprimorar'}</span>
              )}
            </button>
          </TooltipTrigger>
          <TooltipContent side="top" className="text-xs">
            {isEmpty
              ? `Gerar conteúdo com IA${context ? ` (${context})` : ''}`
              : 'Aprimorar texto e corrigir português com IA'}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            onClick={handleClick}
            disabled={disabled || isLoading}
            className={`inline-flex items-center gap-1 rounded text-xs font-medium transition-all disabled:opacity-40
              text-violet-500 hover:text-violet-600 hover:bg-violet-50 dark:hover:bg-violet-950/30
              ${compact ? 'p-1' : 'px-2 py-1'}
              ${className ?? ''}`}
            aria-label={isEmpty ? 'Gerar com IA' : 'Aprimorar com IA'}
          >
            {isLoading ? (
              <Loader2 size={compact ? 12 : 13} className="animate-spin" />
            ) : isEmpty ? (
              <Wand2 size={compact ? 12 : 13} />
            ) : (
              <Sparkles size={compact ? 12 : 13} />
            )}
            {!compact && <span>{isEmpty ? 'Gerar' : 'Aprimorar'}</span>}
          </button>
        </TooltipTrigger>
        <TooltipContent side="top" className="text-xs">
          {isEmpty
            ? `Gerar conteúdo com IA${context ? ` (${context})` : ''}`
            : 'Aprimorar texto e corrigir português com IA'}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

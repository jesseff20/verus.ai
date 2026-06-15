'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Input } from '@/components/ui/input';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';

export interface AIInputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Contexto para a IA (descreve o que o campo representa) */
  aiContext?: string;
  /** Objetivo da melhoria/geração */
  aiObjective?: string;
  /** Callback quando a IA altera o valor */
  onAIChange?: (value: string) => void;
  /** Referência ao setter do estado React (atalho para onAIChange) */
  setValue?: (value: string) => void;
  /** Variante visual */
  variant?: 'default' | 'dark';
}

/**
 * Drop-in replacement para <Input> com botão de IA embutido.
 * Aceita todos os props do Input padrão + aiContext, aiObjective, onAIChange.
 */
export const AIInput = React.forwardRef<HTMLInputElement, AIInputProps>(
  (
    {
      aiContext,
      aiObjective,
      onAIChange,
      setValue,
      variant = 'default',
      className,
      onChange,
      value,
      ...props
    },
    ref,
  ) => {
    const handleEnhance = (enhanced: string) => {
      // Propaga via callback preferido
      if (onAIChange) {
        onAIChange(enhanced);
      } else if (setValue) {
        setValue(enhanced);
      } else if (onChange) {
        // Simula evento nativo para compatibilidade com react-hook-form, etc.
        const nativeInput = document.createElement('input');
        Object.defineProperty(nativeInput, 'value', { value: enhanced });
        onChange({ target: nativeInput } as React.ChangeEvent<HTMLInputElement>);
      }
    };

    const currentValue = typeof value === 'string' ? value : '';

    if (variant === 'dark') {
      return (
        <div className="relative flex items-center">
          <input
            ref={ref}
            value={value}
            onChange={onChange}
            className={cn(
              'w-full px-3 py-2 rounded-lg text-sm text-foreground bg-muted/50 border border-border focus:border-[#7030A0] focus:outline-none pr-16 placeholder:text-muted-foreground/50',
              className,
            )}
            {...props}
          />
          <div className="absolute right-1.5 flex items-center">
            <AIEnhanceButton
              value={currentValue}
              onEnhance={handleEnhance}
              context={aiContext}
              objective={aiObjective}
              compact
              variant="dark"
            />
          </div>
        </div>
      );
    }

    return (
      <div className="relative flex items-center">
        <Input
          ref={ref}
          value={value}
          onChange={onChange}
          className={cn('pr-10', className)}
          {...props}
        />
        <div className="absolute right-1.5 flex items-center pointer-events-auto">
          <AIEnhanceButton
            value={currentValue}
            onEnhance={handleEnhance}
            context={aiContext}
            objective={aiObjective}
            compact
          />
        </div>
      </div>
    );
  },
);

AIInput.displayName = 'AIInput';

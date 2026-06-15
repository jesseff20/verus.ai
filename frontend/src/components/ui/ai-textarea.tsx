'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Textarea } from '@/components/ui/textarea';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';

export interface AITextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
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
 * Drop-in replacement para <Textarea> com botão de IA embutido.
 * O botão aparece no canto inferior direito dentro do campo.
 */
export const AITextarea = React.forwardRef<
  HTMLTextAreaElement,
  AITextareaProps
>(
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
      rows,
      ...props
    },
    ref,
  ) => {
    const handleEnhance = (enhanced: string) => {
      if (onAIChange) {
        onAIChange(enhanced);
      } else if (setValue) {
        setValue(enhanced);
      } else if (onChange) {
        const nativeTa = document.createElement('textarea');
        Object.defineProperty(nativeTa, 'value', { value: enhanced });
        onChange({ target: nativeTa } as React.ChangeEvent<HTMLTextAreaElement>);
      }
    };

    const currentValue = typeof value === 'string' ? value : '';

    if (variant === 'dark') {
      return (
        <div className="relative">
          <textarea
            ref={ref}
            value={value}
            onChange={onChange}
            rows={rows ?? 3}
            className={cn(
              'w-full px-3 py-2 rounded-lg text-sm text-foreground bg-muted/50 border border-border focus:border-[#7030A0] focus:outline-none resize-none pb-7 placeholder:text-muted-foreground/50',
              className,
            )}
            {...props}
          />
          <div className="absolute bottom-1.5 right-1.5">
            <AIEnhanceButton
              value={currentValue}
              onEnhance={handleEnhance}
              context={aiContext}
              objective={aiObjective}
              compact={false}
              variant="dark"
            />
          </div>
        </div>
      );
    }

    return (
      <div className="relative">
        <Textarea
          ref={ref}
          value={value}
          onChange={onChange}
          rows={rows}
          className={cn('pb-8', className)}
          {...props}
        />
        <div className="absolute bottom-2 right-2">
          <AIEnhanceButton
            value={currentValue}
            onEnhance={handleEnhance}
            context={aiContext}
            objective={aiObjective}
          />
        </div>
      </div>
    );
  },
);

AITextarea.displayName = 'AITextarea';

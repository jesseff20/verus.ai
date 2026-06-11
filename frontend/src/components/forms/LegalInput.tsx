'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { useLegalValidation } from '@/hooks/use-legal-validation';
import { formatarCPF, formatarCNPJ, formatarProcessoCNJ } from '@/lib/legal-validations';
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { FormMessage } from '@/components/ui/form';

export interface LegalInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  /**
   * Tipo de validação jurídica
   */
  legalType: 'processo' | 'cpf' | 'cnpj' | 'oab';
  /**
   * UF para OAB (opcional)
   */
  uf?: string;
  /**
   * Validar enquanto digita (default: false - valida no blur)
   */
  validateOnChange?: boolean;
  /**
   * Delay para validação em ms (default: 300)
   */
  debounceMs?: number;
  /**
   * Mostrar ícone de status (default: true)
   */
  showStatusIcon?: boolean;
  /**
   * Formatar valor automaticamente
   */
  autoFormat?: boolean;
}

export const LegalInput = React.forwardRef<HTMLInputElement, LegalInputProps>(
  (
    {
      legalType,
      uf,
      validateOnChange = false,
      debounceMs = 300,
      showStatusIcon = true,
      autoFormat = true,
      className,
      value,
      onChange,
      onBlur,
      ...props
    },
    ref
  ) => {
    const [isFocused, setIsFocused] = React.useState(false);
    const [localValue, setLocalValue] = React.useState(value?.toString() || '');

    // Hook de validação
    const { valido, formatado, erro, isValidating } = useLegalValidation({
      value: localValue,
      type: legalType,
      uf,
      debounceMs,
      validateOnChange,
    });

    // Formatação automática
    const handleFormat = React.useCallback(
      (val: string): string => {
        if (!autoFormat || !val) return val;

        switch (legalType) {
          case 'cpf':
            return formatarCPF(val);
          case 'cnpj':
            return formatarCNPJ(val);
          case 'processo':
            return formatarProcessoCNJ(val);
          case 'oab':
            return val;
          default:
            return val;
        }
      },
      [legalType, autoFormat]
    );

    // Handler de mudança
    const handleChange = React.useCallback(
      (e: React.ChangeEvent<HTMLInputElement>) => {
        const newValue = e.target.value;
        const formatted = handleFormat(newValue);
        setLocalValue(formatted);

        if (onChange) {
          // Criar evento sintético com valor formatado
          const syntheticEvent = {
            ...e,
            target: { ...e.target, value: formatted },
          };
          onChange(syntheticEvent);
        }
      },
      [handleFormat, onChange]
    );

    // Handler de blur
    const handleBlur = React.useCallback(
      (e: React.FocusEvent<HTMLInputElement>) => {
        setIsFocused(false);
        if (onBlur) {
          onBlur(e);
        }
      },
      [onBlur]
    );

    // Placeholder baseado no tipo
    const placeholder = React.useMemo(() => {
      const placeholders: Record<string, string> = {
        processo: '0000000-00.0000.0.00.0000',
        cpf: '000.000.000-00',
        cnpj: '00.000.000/0000-00',
        oab: '00000/UF',
      };
      return placeholders[legalType] || props.placeholder;
    }, [legalType, props.placeholder]);

    // Ícone de status
    const StatusIcon = React.useMemo(() => {
      if (isValidating) {
        return <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />;
      }
      if (valido) {
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      }
      if (localValue && erro) {
        return <XCircle className="h-4 w-4 text-red-600" />;
      }
      return null;
    }, [valido, erro, localValue, isValidating]);

    return (
      <div className="relative">
        <Input
          ref={ref}
          type="text"
          className={cn(
            'pr-10',
            valido ? 'border-green-600 focus:border-green-600' : '',
            erro ? 'border-red-600 focus:border-red-600' : '',
            className
          )}
          placeholder={placeholder}
          value={localValue}
          onChange={handleChange}
          onBlur={handleBlur}
          onFocus={() => setIsFocused(true)}
          {...props}
        />
        {showStatusIcon && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            {StatusIcon}
          </div>
        )}
        {erro && <FormMessage className="mt-1">{erro}</FormMessage>}
      </div>
    );
  }
);

LegalInput.displayName = 'LegalInput';

/**
 * Componente de input para CPF com validação automática
 */
export function CPFInput(props: Omit<LegalInputProps, 'legalType'>) {
  return <LegalInput legalType="cpf" {...props} />;
}

/**
 * Componente de input para CNPJ com validação automática
 */
export function CNPJInput(props: Omit<LegalInputProps, 'legalType'>) {
  return <LegalInput legalType="cnpj" {...props} />;
}

/**
 * Componente de input para Número de Processo CNJ com validação automática
 */
export function ProcessoInput(props: Omit<LegalInputProps, 'legalType'>) {
  return <LegalInput legalType="processo" {...props} />;
}

/**
 * Componente de input para OAB com validação automática
 */
export interface OABInputProps extends Omit<LegalInputProps, 'legalType' | 'uf'> {
  uf: string;
}

export function OABInput({ uf, ...props }: OABInputProps) {
  return <LegalInput legalType="oab" uf={uf} {...props} />;
}

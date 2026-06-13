'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { validateLegalValue, type LegalValidationResult } from '@/lib/legal-validations';

type LegalType = 'processo' | 'cpf' | 'cnpj' | 'oab';

interface UseLegalValidationProps {
  value: string;
  type: LegalType;
  uf?: string;
  debounceMs?: number;
  validateOnChange?: boolean;
}

/**
 * Hook para validação em tempo real de dados jurídicos
 *
 * @example
 * const { valido, formatado, erro, isValidating } = useLegalValidation({
 *   value: cpfValue,
 *   type: 'cpf',
 *   validateOnChange: true,
 * });
 */
export function useLegalValidation({
  value,
  type,
  uf,
  debounceMs = 300,
  validateOnChange = false,
}: UseLegalValidationProps): LegalValidationResult & {
  isValidating: boolean;
  validate: () => void;
  reset: () => void;
} {
  const [result, setResult] = useState<LegalValidationResult>({
    valido: false,
    formatado: value,
    erro: undefined,
  });
  const [isValidating, setIsValidating] = useState(false);
  const [touched, setTouched] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  // Função de validação
  const validate = useCallback(() => {
    if (!value && !validateOnChange) {
      setResult({ valido: false, formatado: value, erro: undefined });
      return;
    }

    setIsValidating(true);

    // Limpar timeout anterior para debounce correto
    if (debounceRef.current) clearTimeout(debounceRef.current);

    // Simular pequeno delay para UX (evita flicker)
    debounceRef.current = setTimeout(() => {
      const validation = validateLegalValue(value, type, uf);
      setResult(validation);
      setIsValidating(false);
      setTouched(true);
    }, debounceMs);
  }, [value, type, uf, debounceMs, validateOnChange]);

  // Validar quando value mudar (se validateOnChange estiver ativo)
  useEffect(() => {
    if (validateOnChange && touched) {
      validate();
    }
  }, [value, validateOnChange, touched, validate]);

  // Reset do estado
  const reset = useCallback(() => {
    setResult({ valido: false, formatado: '', erro: undefined });
    setTouched(false);
    setIsValidating(false);
  }, []);

  // Validar apenas se touched ou validateOnChange
  useEffect(() => {
    if (!touched && !validateOnChange) {
      return;
    }
    validate();
  }, [value, touched, validateOnChange, validate]);

  return {
    ...result,
    isValidating,
    validate,
    reset,
  };
}

/**
 * Hook para validação de múltiplos campos jurídicos
 *
 * @example
 * const { values, errors, validateAll, isValid } = useLegalFormValidation({
 *   cpf: { value: cpfValue, type: 'cpf' },
 *   oab: { value: oabValue, type: 'oab', uf: 'SP' },
 *   processo: { value: processoValue, type: 'processo' },
 * });
 */
export interface LegalFieldConfig {
  value: string;
  type: LegalType;
  uf?: string;
  required?: boolean;
}

export interface LegalFormValidationResult {
  isValid: boolean;
  errors: Record<string, string | undefined>;
  validateAll: () => Promise<boolean>;
  validateField: (fieldKey: string) => void;
  touched: Record<string, boolean>;
}

export function useLegalFormValidation(
  fields: Record<string, LegalFieldConfig>
): LegalFormValidationResult {
  const [errors, setErrors] = useState<Record<string, string | undefined>>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [isValid, setIsValid] = useState(false);

  const validateField = useCallback((fieldKey: string) => {
    const field = fields[fieldKey];
    if (!field) return;

    // Verificar required
    if (field.required && !field.value.trim()) {
      setErrors((prev) => ({ ...prev, [fieldKey]: 'Campo obrigatório' }));
      setTouched((prev) => ({ ...prev, [fieldKey]: true }));
      setIsValid(false);
      return;
    }

    // Validar valor
    if (field.value.trim()) {
      const validation = validateLegalValue(field.value, field.type, field.uf);
      setErrors((prev) => ({ ...prev, [fieldKey]: validation.erro }));
    } else {
      setErrors((prev) => ({ ...prev, [fieldKey]: undefined }));
    }

    setTouched((prev) => ({ ...prev, [fieldKey]: true }));
  }, [fields]);

  const validateAll = useCallback(async (): Promise<boolean> => {
    const newErrors: Record<string, string | undefined> = {};
    let allValid = true;

    for (const [key, field] of Object.entries(fields)) {
      // Verificar required
      if (field.required && !field.value.trim()) {
        newErrors[key] = 'Campo obrigatório';
        allValid = false;
        continue;
      }

      // Validar valor
      if (field.value.trim()) {
        const validation = validateLegalValue(field.value, field.type, field.uf);
        if (!validation.valido) {
          newErrors[key] = validation.erro;
          allValid = false;
        }
      }

      setTouched((prev) => ({ ...prev, [key]: true }));
    }

    setErrors(newErrors);
    setIsValid(allValid);
    return allValid;
  }, [fields]);

  // Auto-validar quando campos mudam (após touch)
  useEffect(() => {
    const newErrors: Record<string, string | undefined> = { ...errors };
    let allValid = true;
    let hasChanges = false;

    for (const [key, field] of Object.entries(fields)) {
      if (touched[key]) {
        hasChanges = true;

        if (field.required && !field.value.trim()) {
          newErrors[key] = 'Campo obrigatório';
          allValid = false;
        } else if (field.value.trim()) {
          const validation = validateLegalValue(field.value, field.type, field.uf);
          if (!validation.valido) {
            newErrors[key] = validation.erro;
            allValid = false;
          } else {
            delete newErrors[key];
          }
        } else {
          delete newErrors[key];
        }
      }
    }

    if (hasChanges) {
      setErrors(newErrors);
      setIsValid(allValid);
    }
  }, [fields, errors, touched]);

  return {
    isValid,
    errors,
    validateAll,
    validateField,
    touched,
  };
}

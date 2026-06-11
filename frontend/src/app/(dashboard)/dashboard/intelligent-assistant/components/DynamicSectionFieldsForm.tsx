'use client';

import * as React from 'react';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  CPFInput,
  CNPJInput,
  ProcessoInput,
  OABInput,
} from '@/components/forms/LegalInput';
import { cn } from '@/lib/utils';

/** Definição de um campo do section_fields JSON */
export interface SectionFieldDef {
  name: string;
  label: string;
  type: 'text' | 'email' | 'tel' | 'number' | 'date' | 'select' | 'textarea' | 'array' | 'cpf' | 'cnpj' | 'processo' | 'oab';
  required?: boolean;
  placeholder?: string;
  options?: { value: string; label: string }[];
  /** Para campos do tipo array */
  item_fields?: SectionFieldDef[];
  /** Validação adicional */
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    message?: string;
  };
}

interface DynamicSectionFieldsFormProps {
  /** Lista de definições de campos */
  fields: SectionFieldDef[];
  /** Valores atuais */
  values: Record<string, any>;
  /** Callback quando valores mudam */
  onChange: (name: string, value: any) => void;
  /** Erros de validação por campo */
  errors?: Record<string, string>;
  /** UF para campo OAB */
  uf?: string;
  /** Desabilitar todos os campos */
  disabled?: boolean;
}

/**
 * Formulário dinâmico que lê section_fields JSON e renderiza campos
 * com validação e máscaras jurídicas (CPF, CNPJ, Processo CNJ, OAB).
 */
export function DynamicSectionFieldsForm({
  fields,
  values,
  onChange,
  errors = {},
  uf = 'PB',
  disabled = false,
}: DynamicSectionFieldsFormProps) {
  if (!fields || fields.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-4 text-center">
        Nenhum campo definido para esta seção.
      </p>
    );
  }

  const handleChange = (name: string, value: any) => {
    onChange(name, value);
  };

  return (
    <div className="space-y-4">
      {fields.map((field) => {
        const fieldValue = values?.[field.name] ?? '';
        const fieldError = errors?.[field.name];

        if (field.type === 'array') {
          return (
            <ArrayFieldRenderer
              key={field.name}
              field={field}
              value={fieldValue}
              onChange={(val) => handleChange(field.name, val)}
              error={fieldError}
              disabled={disabled}
            />
          );
        }

        return (
          <div key={field.name} className="space-y-2">
            <Label
              htmlFor={field.name}
              className={cn(
                field.required && "after:content-['*'] after:ml-0.5 after:text-red-500"
              )}
            >
              {field.label}
            </Label>
            <FieldRenderer
              field={field}
              value={fieldValue}
              onChange={(val) => handleChange(field.name, val)}
              error={fieldError}
              disabled={disabled}
              uf={uf}
            />
            {fieldError && (
              <p className="text-sm text-red-500">{fieldError}</p>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Field Renderer (campo individual)
// ---------------------------------------------------------------------------

interface FieldRendererProps {
  field: SectionFieldDef;
  value: any;
  onChange: (value: any) => void;
  error?: string;
  disabled?: boolean;
  uf?: string;
}

function FieldRenderer({
  field,
  value,
  onChange,
  error,
  disabled = false,
  uf = 'PB',
}: FieldRendererProps) {
  const legalTypes = ['cpf', 'cnpj', 'processo', 'oab'] as const;

  if (legalTypes.includes(field.type as any)) {
    switch (field.type) {
      case 'cpf':
        return (
          <CPFInput
            id={field.name}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            placeholder={field.placeholder}
          />
        );
      case 'cnpj':
        return (
          <CNPJInput
            id={field.name}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            placeholder={field.placeholder}
          />
        );
      case 'processo':
        return (
          <ProcessoInput
            id={field.name}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            placeholder={field.placeholder}
          />
        );
      case 'oab':
        return (
          <OABInput
            id={field.name}
            uf={uf}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            placeholder={field.placeholder}
          />
        );
    }
  }

  switch (field.type) {
    case 'select':
      return (
        <Select
          value={value?.toString() || ''}
          onValueChange={onChange}
          disabled={disabled}
        >
          <SelectTrigger
            id={field.name}
            className={cn(error && 'border-red-500')}
          >
            <SelectValue placeholder={field.placeholder || `Selecione...`} />
          </SelectTrigger>
          <SelectContent>
            {(field.options || []).map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      );

    case 'textarea':
      return (
        <Textarea
          id={field.name}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder}
          disabled={disabled}
          className={cn(error && 'border-red-500')}
          rows={4}
        />
      );

    case 'number':
      return (
        <Input
          id={field.name}
          type="number"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder}
          disabled={disabled}
          className={cn(error && 'border-red-500')}
          min={field.validation?.min}
          max={field.validation?.max}
        />
      );

    case 'date':
      return (
        <Input
          id={field.name}
          type="date"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          className={cn(error && 'border-red-500')}
        />
      );

    case 'email':
      return (
        <Input
          id={field.name}
          type="email"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder}
          disabled={disabled}
          className={cn(error && 'border-red-500')}
        />
      );

    case 'tel':
      return (
        <Input
          id={field.name}
          type="tel"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder}
          disabled={disabled}
          className={cn(error && 'border-red-500')}
        />
      );

    default:
      return (
        <Input
          id={field.name}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder}
          disabled={disabled}
          className={cn(error && 'border-red-500')}
        />
      );
  }
}

// ---------------------------------------------------------------------------
// Array Field Renderer (campos repetitivos estilo tabela)
// ---------------------------------------------------------------------------

interface ArrayFieldRendererProps {
  field: SectionFieldDef;
  value: any[];
  onChange: (value: any[]) => void;
  error?: string;
  disabled?: boolean;
}

function ArrayFieldRenderer({
  field,
  value,
  onChange,
  error,
  disabled = false,
}: ArrayFieldRendererProps) {
  const items = Array.isArray(value) ? value : [];
  const itemFields = field.item_fields || [];

  const addItem = () => {
    const newItem: Record<string, string> = {};
    itemFields.forEach((f) => {
      newItem[f.name] = '';
    });
    onChange([...items, newItem]);
  };

  const removeItem = (index: number) => {
    const updated = items.filter((_, i) => i !== index);
    onChange(updated);
  };

  const updateItem = (index: number, fieldName: string, val: string) => {
    const updated = items.map((item, i) => {
      if (i === index) {
        return { ...item, [fieldName]: val };
      }
      return item;
    });
    onChange(updated);
  };

  return (
    <div className="space-y-3">
      <Label
        className={cn(
          'font-medium',
          field.required && "after:content-['*'] after:ml-0.5 after:text-red-500"
        )}
      >
        {field.label}
      </Label>

      {items.length === 0 && (
        <p className="text-sm text-muted-foreground">
          Nenhum item adicionado.
        </p>
      )}

      {items.map((item, index) => (
        <div
          key={index}
          className="border rounded-md p-3 space-y-3 relative"
        >
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">
              Item {index + 1}
            </span>
            {!disabled && (
              <button
                type="button"
                onClick={() => removeItem(index)}
                className="text-sm text-red-500 hover:text-red-700"
              >
                Remover
              </button>
            )}
          </div>
          {itemFields.map((subField) => (
            <div key={subField.name} className="space-y-1">
              <Label htmlFor={`${field.name}[${index}].${subField.name}`}>
                {subField.label}
              </Label>
              <FieldRenderer
                field={subField}
                value={item[subField.name] || ''}
                onChange={(val) => updateItem(index, subField.name, val)}
                disabled={disabled}
              />
            </div>
          ))}
        </div>
      ))}

      {!disabled && (
        <button
          type="button"
          onClick={addItem}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          + Adicionar item
        </button>
      )}

      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  );
}

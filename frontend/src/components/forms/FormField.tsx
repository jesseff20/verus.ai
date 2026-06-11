'use client';

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
import { AlertCircle } from 'lucide-react';

interface Field {
  name: string;
  label: string;
  type: 'text' | 'textarea' | 'select' | 'date' | 'number' | 'email';
  required?: boolean;
  placeholder?: string;
  options?: string[];
  help_text?: string;
}

interface FormFieldProps {
  field: Field;
  value: any;
  onChange: (value: any) => void;
}

export function FormField({ field, value, onChange }: FormFieldProps) {
  const renderField = () => {
    switch (field.type) {
      case 'textarea':
        return (
          <Textarea
            id={field.name}
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={field.placeholder}
            rows={6}
            className="resize-y"
          />
        );

      case 'select':
        return (
          <Select value={value || ''} onValueChange={onChange}>
            <SelectTrigger id={field.name}>
              <SelectValue placeholder={field.placeholder || 'Selecione uma opção'} />
            </SelectTrigger>
            <SelectContent>
              {field.options?.map((option, index) => {
                // Suporta options como string ou objeto {value, label}
                const isObject = typeof option === 'object' && option !== null;
                const optionValue = isObject ? option.value : option;
                const optionLabel = isObject ? option.label : option;

                return (
                  <SelectItem key={optionValue || index} value={optionValue}>
                    {optionLabel}
                  </SelectItem>
                );
              })}
            </SelectContent>
          </Select>
        );

      case 'date':
        return (
          <Input
            id={field.name}
            type="date"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
          />
        );

      case 'number':
        return (
          <Input
            id={field.name}
            type="number"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={field.placeholder}
          />
        );

      case 'email':
        return (
          <Input
            id={field.name}
            type="email"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={field.placeholder}
          />
        );

      default: // text
        return (
          <Input
            id={field.name}
            type="text"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={field.placeholder}
          />
        );
    }
  };

  return (
    <div className="space-y-2">
      <Label htmlFor={field.name}>
        {field.label}
        {field.required && <span className="text-red-500 ml-1">*</span>}
      </Label>
      {renderField()}
      {field.help_text && (
        <div className="flex items-start gap-2 text-xs text-muted-foreground">
          <AlertCircle className="h-3 w-3 mt-0.5 flex-shrink-0" />
          <span>{field.help_text}</span>
        </div>
      )}
    </div>
  );
}

'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Sparkles } from 'lucide-react';

interface Field {
  id: string;
  type: string;
  label: string;
  required?: boolean;
  help_text?: string;
  placeholder?: string;
  ai_assist?: boolean;
  ai_prompt_types?: string[]; // Array de tipos de IA
}

interface FormPreviewProps {
  fields: Field[];
}

export function FormPreview({ fields }: FormPreviewProps) {
  const renderField = (field: Field) => {
    switch (field.type) {
      case 'textarea':
        return (
          <Textarea
            placeholder={field.placeholder}
            rows={4}
            disabled
          />
        );

      case 'select':
        return (
          <Select disabled>
            <SelectTrigger>
              <SelectValue placeholder={field.placeholder || 'Selecione...'} />
            </SelectTrigger>
          </Select>
        );

      case 'checkbox':
        return (
          <div className="flex items-center space-x-2">
            <Checkbox id={field.id} disabled />
            <label
              htmlFor={field.id}
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              {field.placeholder || 'Opção'}
            </label>
          </div>
        );

      case 'radio':
        return (
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <input type="radio" name={field.id} disabled className="h-4 w-4" />
              <label className="text-sm">Opção 1</label>
            </div>
            <div className="flex items-center space-x-2">
              <input type="radio" name={field.id} disabled className="h-4 w-4" />
              <label className="text-sm">Opção 2</label>
            </div>
          </div>
        );

      case 'number':
      case 'email':
      case 'date':
      case 'file':
      case 'text':
      default:
        return (
          <Input
            type={field.type}
            placeholder={field.placeholder}
            disabled
          />
        );
    }
  };

  return (
    <Card className="bg-slate-50 dark:bg-slate-900">
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          👁️ Preview do Formulário
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          Visualização de como o formulário aparecerá para o usuário
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        {fields.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <p>Nenhum campo adicionado ainda.</p>
            <p className="text-sm mt-2">Clique em "Adicionar Campo" para começar.</p>
          </div>
        ) : (
          fields.map((field, index) => (
            <div key={index} className="space-y-2">
              <Label className="flex items-center gap-2 flex-wrap">
                {field.label}
                {field.required && <span className="text-red-500">*</span>}
                {field.ai_assist && field.ai_prompt_types && field.ai_prompt_types.length > 0 && (
                  <div className="flex items-center gap-1 flex-wrap">
                    {field.ai_prompt_types.map((type, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1 text-xs bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded"
                        title={type}
                      >
                        <Sparkles className="h-3 w-3" />
                        {type}
                      </span>
                    ))}
                  </div>
                )}
              </Label>

              {field.help_text && (
                <p className="text-sm text-muted-foreground">
                  {field.help_text}
                </p>
              )}

              <div className="relative">
                {renderField(field)}
                {field.ai_assist && (
                  <div className="absolute top-2 right-2 opacity-50">
                    <Sparkles className="h-4 w-4 text-purple-500" />
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {fields.length > 0 && (
          <div className="pt-4 border-t text-sm text-muted-foreground">
            <p>Total de campos: {fields.length}</p>
            <p>Campos obrigatórios: {fields.filter(f => f.required).length}</p>
            <p>Campos com IA: {fields.filter(f => f.ai_assist).length}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Plus, Trash2, User, Users, Upload, Loader2, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Editor } from '@tinymce/tinymce-react';
import { useToast } from '@/hooks/use-toast';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import api from '@/lib/api';
import type { BlueprintSectionField } from '@/types';

interface SectionFieldsFormProps {
  fields: BlueprintSectionField[];
  values: Record<string, any>;
  onChange: (values: Record<string, any>) => void;
  disabled?: boolean;
  compact?: boolean;
  /** Nome do blueprint (usado no prompt da IA para preencher com documento) */
  blueprintName?: string;
  /** Mostra o botao de preencher com documento */
  showFillFromDocument?: boolean;
}

/**
 * Componente para renderizar campos estruturados de uma seção do Blueprint.
 * Suporta campos simples (text, email, tel, etc.) e campos de array (equipe).
 */
export function SectionFieldsForm({
  fields,
  values,
  onChange,
  disabled = false,
  compact = false,
  blueprintName = '',
  showFillFromDocument = false,
}: SectionFieldsFormProps) {
  const { toast } = useToast();
  const fillFileRef = useRef<HTMLInputElement>(null);
  const [isFilling, setIsFilling] = useState(false);
  const [fieldsNotFound, setFieldsNotFound] = useState<Set<string>>(new Set());
  // Pré-popular valores com `default_value` (e `default_html` pra richtext)
  // quando o campo ainda não tem valor no state. Executa quando a definição
  // de fields chega/muda; idempotente (só propaga se `values[name]` undefined).
  useEffect(() => {
    if (!fields || fields.length === 0) return;
    const updates: Record<string, any> = {};
    let changed = false;
    fields.forEach((field) => {
      if (values[field.name] !== undefined) return;
      let seed: any;
      if (field.default_value !== undefined) {
        seed = field.default_value;
      } else if (field.type === 'richtext' && field.default_html) {
        seed = field.default_html;
      }
      if (seed !== undefined) {
        updates[field.name] = seed;
        changed = true;
      }
    });
    if (changed) {
      onChange({ ...values, ...updates });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fields]);

  // Handler para atualizar valor de um campo simples
  const handleFieldChange = useCallback(
    (fieldName: string, value: any) => {
      onChange({
        ...values,
        [fieldName]: value,
      });
    },
    [values, onChange]
  );

  // Handler para atualizar item de um array
  const handleArrayItemChange = useCallback(
    (fieldName: string, index: number, itemFieldName: string, value: any) => {
      const currentArray = values[fieldName] || [];
      const newArray = [...currentArray];
      newArray[index] = {
        ...newArray[index],
        [itemFieldName]: value,
      };
      onChange({
        ...values,
        [fieldName]: newArray,
      });
    },
    [values, onChange]
  );

  // Handler para adicionar item ao array
  const handleAddArrayItem = useCallback(
    (fieldName: string, itemFields: BlueprintSectionField[]) => {
      const currentArray = values[fieldName] || [];
      const newItem: Record<string, any> = {};
      itemFields.forEach((field) => {
        newItem[field.name] = '';
      });
      onChange({
        ...values,
        [fieldName]: [...currentArray, newItem],
      });
    },
    [values, onChange]
  );

  // Handler para remover item do array
  const handleRemoveArrayItem = useCallback(
    (fieldName: string, index: number) => {
      const currentArray = values[fieldName] || [];
      const newArray = currentArray.filter((_: any, i: number) => i !== index);
      onChange({
        ...values,
        [fieldName]: newArray,
      });
    },
    [values, onChange]
  );

  // Handler para preencher com documento via IA
  const handleFillFromDoc = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      // Reset input para permitir re-selecionar mesmo arquivo
      if (fillFileRef.current) fillFileRef.current.value = '';

      setIsFilling(true);
      setFieldsNotFound(new Set());

      try {
        // Montar lista de campos para a IA
        const fieldsDef = fields
          .filter((f) => f.type !== 'array') // arrays sao complexos demais para auto-fill
          .map((f) => ({
            name: f.name,
            label: f.label,
            type: f.type,
            required: f.required,
            options: f.options,
          }));

        const formData = new FormData();
        formData.append('file', file);
        formData.append('fields', JSON.stringify(fieldsDef));
        formData.append('blueprint_name', blueprintName);

        const response = await api.post(
          '/api/v1/intelligent-assistant/fill-form-from-document/',
          formData,
          {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 120000, // 2 minutos para documentos grandes
          }
        );

        const { filled_fields, fields_found, fields_total, fields_not_found } = response.data;

        // Atualizar valores do formulario
        if (filled_fields && typeof filled_fields === 'object') {
          const newValues = { ...values };
          for (const [fieldName, fieldValue] of Object.entries(filled_fields)) {
            if (fieldValue !== null && fieldValue !== undefined) {
              newValues[fieldName] = fieldValue;
            }
          }
          onChange(newValues);
        }

        // Marcar campos nao encontrados
        if (fields_not_found && Array.isArray(fields_not_found)) {
          const notFoundNames = new Set<string>();
          for (const label of fields_not_found) {
            const field = fields.find((f) => f.label === label);
            if (field) notFoundNames.add(field.name);
          }
          setFieldsNotFound(notFoundNames);
        }

        toast({
          title: 'Formulario preenchido',
          description: `${fields_found} de ${fields_total} campos preenchidos automaticamente a partir do documento.`,
          variant: fields_found > 0 ? 'default' : 'destructive',
        });
      } catch (err: any) {
        const errorMsg =
          err?.response?.data?.error || 'Erro ao processar documento. Tente novamente.';
        toast({
          title: 'Erro ao preencher',
          description: errorMsg,
          variant: 'destructive',
        });
      } finally {
        setIsFilling(false);
      }
    },
    [fields, values, onChange, blueprintName, toast]
  );

  // Renderiza um campo simples
  const renderSimpleField = (field: BlueprintSectionField) => {
    const value = values[field.name] || '';

    switch (field.type) {
      case 'textarea':
        return (
          <Textarea
            id={field.name}
            value={value}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            placeholder={field.placeholder}
            disabled={disabled}
            rows={(field as any).rows ?? 3}
            className={(field as any).rows ? 'resize-y' : 'resize-none'}
          />
        );

      case 'richtext':
        return (
          <RichTextField
            field={field}
            value={value}
            onChange={(v) => handleFieldChange(field.name, v)}
            disabled={disabled}
          />
        );

      case 'select':
        return (
          <Select
            value={value}
            onValueChange={(val) => handleFieldChange(field.name, val)}
            disabled={disabled}
          >
            <SelectTrigger>
              <SelectValue placeholder={field.placeholder || 'Selecione...'} />
            </SelectTrigger>
            <SelectContent>
              {field.options?.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );

      default:
        return (
          <Input
            id={field.name}
            type={field.type === 'tel' ? 'tel' : field.type === 'email' ? 'email' : field.type === 'number' ? 'number' : field.type === 'date' ? 'date' : 'text'}
            value={value}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            placeholder={field.placeholder}
            disabled={disabled}
          />
        );
    }
  };

  // Renderiza um campo de array (como Equipe)
  const renderArrayField = (field: BlueprintSectionField) => {
    const arrayValue = values[field.name] || [];
    const itemFields = field.item_fields || [];
    const minItems = field.min_items || 0;
    const maxItems = field.max_items || 10;

    return (
      <div className="space-y-3">
        {/* Header do array */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">{field.label}</span>
            <Badge variant="secondary" className="text-xs">
              {arrayValue.length} / {maxItems}
            </Badge>
          </div>
          {!disabled && arrayValue.length < maxItems && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => handleAddArrayItem(field.name, itemFields)}
            >
              <Plus className="h-4 w-4 mr-1" />
              Adicionar
            </Button>
          )}
        </div>

        {/* Help text */}
        {field.help_text && (
          <p className="text-xs text-muted-foreground">{field.help_text}</p>
        )}

        {/* Lista de itens */}
        <div className="space-y-3">
          {arrayValue.map((item: Record<string, any>, index: number) => (
            <Card key={index} className="border-dashed">
              <CardHeader className="py-2 px-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <CardTitle className="text-sm font-medium">
                      {(field as any).item_label || 'Item'} {index + 1}
                    </CardTitle>
                  </div>
                  {!disabled && arrayValue.length > minItems && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 text-destructive hover:text-destructive"
                      onClick={() => handleRemoveArrayItem(field.name, index)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="py-2 px-3">
                <div className={compact ? 'grid grid-cols-1 md:grid-cols-2 gap-2' : 'grid grid-cols-1 md:grid-cols-2 gap-3'}>
                  {itemFields.map((itemField) => {
                    const isTextarea = itemField.type === 'textarea';
                    const inputId = `${field.name}-${index}-${itemField.name}`;
                    return (
                      <div
                        key={itemField.name}
                        className={cn(
                          'space-y-1',
                          // Textarea ocupa linha inteira do grid
                          isTextarea && 'md:col-span-2'
                        )}
                      >
                        <Label htmlFor={inputId} className="text-xs">
                          {itemField.label}
                          {itemField.required && <span className="text-destructive ml-1">*</span>}
                        </Label>
                        {isTextarea ? (
                          <Textarea
                            id={inputId}
                            value={item[itemField.name] || ''}
                            onChange={(e) =>
                              handleArrayItemChange(field.name, index, itemField.name, e.target.value)
                            }
                            placeholder={itemField.placeholder}
                            disabled={disabled}
                            rows={(itemField as any).rows || 4}
                            className="text-sm resize-y"
                          />
                        ) : (
                          <Input
                            id={inputId}
                            type={itemField.type === 'email' ? 'email' : itemField.type === 'tel' ? 'tel' : 'text'}
                            value={item[itemField.name] || ''}
                            onChange={(e) =>
                              handleArrayItemChange(field.name, index, itemField.name, e.target.value)
                            }
                            placeholder={itemField.placeholder}
                            disabled={disabled}
                            className="h-8 text-sm"
                          />
                        )}
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          ))}

          {/* Mensagem quando vazio */}
          {arrayValue.length === 0 && (
            <div className="flex flex-col items-center justify-center py-6 border-2 border-dashed rounded-lg text-muted-foreground">
              <Users className="h-8 w-8 mb-2 opacity-50" />
              <p className="text-sm">Nenhum {((field as any).item_label || 'item').toLowerCase()} adicionado</p>
              <p className="text-xs">Clique em "Adicionar" para incluir</p>
            </div>
          )}

          {/* Aviso de mínimo */}
          {arrayValue.length < minItems && (
            <p className="text-xs text-amber-600">
              Mínimo de {minItems} {((field as any).item_label || 'item').toLowerCase()}(s) necessário(s)
            </p>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className={compact ? 'space-y-3' : 'space-y-4'}>
      {/* Card de Preencher com Documento */}
      {showFillFromDocument && !disabled && (
        <Card className="border-dashed border-2 border-primary/20 p-3 mb-1">
          <div className="flex items-center gap-3">
            <Upload className="h-5 w-5 text-primary flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium">Preencher com Documento</p>
              <p className="text-xs text-muted-foreground">
                Anexe um PDF ou DOCX e a IA preenchera os campos automaticamente
              </p>
            </div>
            <input
              type="file"
              ref={fillFileRef}
              className="hidden"
              accept=".pdf,.docx,.doc,.odt,.txt"
              onChange={handleFillFromDoc}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={() => fillFileRef.current?.click()}
              disabled={isFilling}
              className="flex-shrink-0"
            >
              {isFilling ? (
                <Loader2 className="h-4 w-4 animate-spin mr-1" />
              ) : (
                <Upload className="h-4 w-4 mr-1" />
              )}
              {isFilling ? 'Analisando...' : 'Anexar'}
            </Button>
          </div>
        </Card>
      )}

      {fields.map((field) => (
        <div key={field.name}>
          {field.type === 'array' ? (
            renderArrayField(field)
          ) : (
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5">
                <Label htmlFor={field.name} className={compact ? 'text-xs' : 'text-sm'}>
                  {field.label}
                  {field.required && <span className="text-destructive ml-1">*</span>}
                </Label>
                {fieldsNotFound.has(field.name) && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <AlertTriangle className="h-3.5 w-3.5 text-amber-500 flex-shrink-0" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="text-xs">Nao encontrado no documento</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
              </div>
              <div className={fieldsNotFound.has(field.name) ? 'ring-1 ring-amber-400 rounded-md' : ''}>
                {renderSimpleField(field)}
              </div>
              {field.help_text && (
                <p className="text-xs text-muted-foreground">{field.help_text}</p>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export default SectionFieldsForm;


// ─────────────────────────────────────────────────────────────────────────────
// Componente do editor TinyMCE (richtext) extraido para suportar useEffect
// (default_html: pre-popular HTML quando o campo esta vazio na primeira carga).
// ─────────────────────────────────────────────────────────────────────────────
interface RichTextFieldProps {
  field: BlueprintSectionField;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

function RichTextField({ field, value, onChange, disabled }: RichTextFieldProps) {
  const defaultHtml = field.default_html || '';
  const initialValue = value || defaultHtml;

  // Se o campo esta vazio E ha default_html, propaga o default pro form_data
  // logo na primeira renderizacao - assim o Salvar persiste o seed.
  useEffect(() => {
    if (!value && defaultHtml) {
      onChange(defaultHtml);
    }
    // Roda apenas no mount; o usuario controla o valor depois disso.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="border border-input rounded-md bg-white">
      <Editor
        apiKey={process.env.NEXT_PUBLIC_TINYMCE_API_KEY}
        value={initialValue}
        onEditorChange={(content) => onChange(content)}
        disabled={disabled}
        init={{
                  // @ts-expect-error -- TinyMCE types want licenseKey prop instead of init.license_key
                  license_key: 'gpl',
          // Editor cresce automaticamente conforme conteudo.
          min_height: field.height ?? 300,
          max_height: 1200,
          autoresize_bottom_margin: 20,
          menubar: 'edit view insert format table',
          plugins:
            'autoresize advlist autolink lists link image charmap searchreplace visualblocks ' +
            'fullscreen media table wordcount code preview',
          toolbar:
            'undo redo | blocks fontfamily fontsize | ' +
            'bold italic underline strikethrough subscript superscript | ' +
            'forecolor backcolor | ' +
            'alignleft aligncenter alignright alignjustify | ' +
            'lineheight | bullist numlist outdent indent | ' +
            'hr blockquote | table | link image media | ' +
            'searchreplace | removeformat code preview fullscreen',
          line_height_formats: '1 1.15 1.3 1.5 1.75 2 2.5 3',
          paste_as_text: false,
          paste_data_images: true,
          language: 'pt_BR',
          content_style: 'body { font-family: Calibri, Arial, sans-serif; font-size: 11pt; }',
          placeholder: field.placeholder,
        }}
      />
    </div>
  );
}

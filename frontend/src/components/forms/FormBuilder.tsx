'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Plus, Settings, Trash2, Eye, EyeOff, Loader2, GripVertical, Sparkles } from 'lucide-react';
import { AddFieldDialog } from './AddFieldDialog';
import { FormPreview } from './FormPreview';
import { useForms } from '@/hooks/use-forms';
import { useToast } from '@/hooks/use-toast';

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

interface FormBuilderProps {
  formData: {
    name: string;
    description: string;
    blueprint?: string;
    fields: Field[];
  };
  onSave: () => void;
  onBack: () => void;
}

export function FormBuilder({ formData, onSave, onBack }: FormBuilderProps) {
  const [fields, setFields] = useState<Field[]>([]);
  const [showPreview, setShowPreview] = useState(false);
  const { createForm, isCreating } = useForms();
  const { toast } = useToast();

  const handleAddField = (field: Field) => {
    setFields([...fields, field]);
  };

  const handleRemoveField = (index: number) => {
    setFields(fields.filter((_, i) => i !== index));
  };

  const handleMoveUp = (index: number) => {
    if (index === 0) return;
    const newFields = [...fields];
    [newFields[index - 1], newFields[index]] = [newFields[index], newFields[index - 1]];
    setFields(newFields);
  };

  const handleMoveDown = (index: number) => {
    if (index === fields.length - 1) return;
    const newFields = [...fields];
    [newFields[index], newFields[index + 1]] = [newFields[index + 1], newFields[index]];
    setFields(newFields);
  };

  const handleSaveForm = async () => {
    if (fields.length === 0) {
      toast({
        title: "Nenhum campo adicionado",
        description: "Adicione pelo menos um campo antes de salvar o formulário.",
        variant: "destructive",
      });
      return;
    }

    const payload = {
      name: formData.name,
      description: formData.description,
      blueprint: formData.blueprint || null,
      fields,
      is_active: true,
    };

    try {
      await createForm(payload);
      toast({
        title: "Formulário criado!",
        description: `O formulário "${formData.name}" foi criado com sucesso.`,
      });
      onSave();
    } catch (error: any) {
      toast({
        title: "Erro ao criar formulário",
        description: error.response?.data?.detail || "Ocorreu um erro ao salvar o formulário.",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="space-y-4 py-4">
      {/* Header with Actions */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="font-semibold text-lg">Campos do Formulário</h3>
          <p className="text-sm text-muted-foreground">
            {formData.name} • {fields.length} campo{fields.length !== 1 ? 's' : ''}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowPreview(!showPreview)}
          >
            {showPreview ? (
              <>
                <EyeOff className="mr-2 h-4 w-4" />
                Ocultar Preview
              </>
            ) : (
              <>
                <Eye className="mr-2 h-4 w-4" />
                Mostrar Preview
              </>
            )}
          </Button>
          <AddFieldDialog onAdd={handleAddField} blueprintId={formData.blueprint}>
            <Button size="sm">
              <Plus className="mr-2 h-4 w-4" />
              Adicionar Campo
            </Button>
          </AddFieldDialog>
        </div>
      </div>

      {/* Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Fields List */}
        <div className="space-y-2">
          <h4 className="font-medium text-sm text-muted-foreground mb-3">
            CAMPOS CONFIGURADOS
          </h4>

          {fields.length === 0 ? (
            <Card className="p-12 text-center">
              <div className="flex flex-col items-center gap-3 text-muted-foreground">
                <Plus className="h-12 w-12 opacity-20" />
                <p>Nenhum campo adicionado</p>
                <p className="text-sm">
                  Clique em "Adicionar Campo" para começar a construir seu formulário
                </p>
              </div>
            </Card>
          ) : (
            <div className="space-y-2">
              {fields.map((field, index) => (
                <Card key={index} className="p-4 hover:bg-accent/50 transition-colors">
                  <div className="flex items-start justify-between gap-4">
                    {/* Field Info */}
                    <div className="flex items-start gap-3 flex-1 min-w-0">
                      <div className="mt-1">
                        <GripVertical className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-mono text-xs text-muted-foreground">
                            #{index + 1}
                          </span>
                          <h5 className="font-semibold truncate">{field.label}</h5>
                          {field.required && (
                            <span className="text-red-500 text-xs">*</span>
                          )}
                          {field.ai_assist && (
                            <span className="inline-flex items-center gap-1 text-xs bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300 px-1.5 py-0.5 rounded">
                              <Sparkles className="h-3 w-3" />
                            </span>
                          )}
                        </div>
                        <div className="text-sm text-muted-foreground space-y-1">
                          <p>ID: <span className="font-mono">{field.id}</span></p>
                          <p>Tipo: {field.type}</p>
                          {field.ai_assist && field.ai_prompt_types && field.ai_prompt_types.length > 0 && (
                            <div className="text-purple-600 dark:text-purple-400">
                              <p className="font-medium">IA ({field.ai_prompt_types.length}):</p>
                              <ul className="list-disc list-inside text-xs space-y-0.5 ml-2">
                                {field.ai_prompt_types.map((type, idx) => (
                                  <li key={idx}>{type}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-1">
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleMoveUp(index)}
                          disabled={index === 0}
                          title="Mover para cima"
                        >
                          ↑
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleMoveDown(index)}
                          disabled={index === fields.length - 1}
                          title="Mover para baixo"
                        >
                          ↓
                        </Button>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemoveField(index)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        title="Remover campo"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Preview */}
        {showPreview && (
          <div className="space-y-2">
            <h4 className="font-medium text-sm text-muted-foreground mb-3">
              PREVIEW EM TEMPO REAL
            </h4>
            <FormPreview fields={fields} />
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="flex justify-between pt-6 border-t">
        <Button variant="outline" onClick={onBack}>
          ← Voltar
        </Button>
        <Button
          onClick={handleSaveForm}
          disabled={fields.length === 0 || isCreating}
        >
          {isCreating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Salvando...
            </>
          ) : (
            <>
              Salvar Formulário ({fields.length} campo{fields.length !== 1 ? 's' : ''})
            </>
          )}
        </Button>
      </div>
    </div>
  );
}

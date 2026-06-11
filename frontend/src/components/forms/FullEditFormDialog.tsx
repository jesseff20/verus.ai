'use client';

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card } from '@/components/ui/card';
import { Loader2, Edit, Plus, Trash2, GripVertical, Sparkles, Settings, FileText } from 'lucide-react';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';
import { useForms } from '@/hooks/use-forms';
import { useToast } from '@/hooks/use-toast';
import { AddFieldDialog } from './AddFieldDialog';
import { EditFieldDialog } from './EditFieldDialog';
import { useBlueprints } from '@/hooks/use-blueprints';
import type { FormTemplate } from '@/types';

interface Field {
  id: string;
  type: string;
  label: string;
  required?: boolean;
  help_text?: string;
  placeholder?: string;
  ai_assist?: boolean;
  ai_prompt_types?: string[];
}

interface FullEditFormDialogProps {
  form: FormTemplate;
  onSuccess?: () => void;
  children?: React.ReactNode;
}

export function FullEditFormDialog({ form, onSuccess, children }: FullEditFormDialogProps) {
  const [open, setOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('info');
  const { updateForm, isUpdating } = useForms();
  const { toast } = useToast();

  // Buscar Blueprints ativos
  const { blueprints, isLoading: loadingBlueprints } = useBlueprints();

  const [formData, setFormData] = useState({
    name: form.name,
    description: form.description || '',
    blueprint: (form as any).blueprint || undefined,
    is_active: form.is_active,
  });

  const [fields, setFields] = useState<Field[]>(form.fields || []);
  const [editingField, setEditingField] = useState<{ index: number; field: Field } | null>(null);

  useEffect(() => {
    if (open) {
      setFormData({
        name: form.name,
        description: form.description || '',
        blueprint: (form as any).blueprint || undefined,
        is_active: form.is_active,
      });
      setFields(form.fields || []);
      setActiveTab('info');
    }
  }, [open, form]);

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

  const handleEditField = (index: number) => {
    setEditingField({ index, field: { ...fields[index] } });
  };

  const handleSaveEditedField = (field: Field) => {
    if (editingField !== null) {
      const newFields = [...fields];
      newFields[editingField.index] = field;
      setFields(newFields);
      setEditingField(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      toast({
        title: 'Campo obrigatório',
        description: 'O nome do formulário é obrigatório.',
        variant: 'destructive',
      });
      return;
    }

    if (fields.length === 0) {
      toast({
        title: 'Campos obrigatórios',
        description: 'O formulário deve ter pelo menos um campo.',
        variant: 'destructive',
      });
      return;
    }

    try {
      // Normalizar campos antes de enviar para garantir consistência
      const normalizedFields = fields.map(field => ({
        ...field,
        // Garantir que ai_prompt_types sempre seja um array
        ai_prompt_types: field.ai_prompt_types || [],
        // Garantir que ai_assist seja boolean
        ai_assist: field.ai_assist || false,
        // Remover propriedades undefined ou null
        help_text: field.help_text || '',
        placeholder: field.placeholder || '',
      }));

      console.log('Enviando campos normalizados:', normalizedFields);
      await updateForm({
        id: form.id,
        data: {
          name: formData.name,
          description: formData.description,
          blueprint: formData.blueprint || null,
          is_active: formData.is_active,
          fields: normalizedFields,
        },
      });

      toast({
        title: 'Formulário atualizado!',
        description: `O formulário "${formData.name}" foi atualizado com sucesso.`,
      });

      setOpen(false);
      onSuccess?.();
    } catch (error: any) {
      toast({
        title: 'Erro ao atualizar',
        description: error.response?.data?.detail || 'Não foi possível atualizar o formulário.',
        variant: 'destructive',
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      {children ? (
        <div onClick={() => setOpen(true)}>{children}</div>
      ) : (
        <Button variant="outline" onClick={() => setOpen(true)}>
          <Edit className="mr-2 h-4 w-4" />
          Editar
        </Button>
      )}

      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Editar Formulário: {form.name}</DialogTitle>
          <DialogDescription>
            Atualize as informações e campos do formulário.
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="info">Informações Básicas</TabsTrigger>
            <TabsTrigger value="fields">
              Campos ({fields.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="info" className="space-y-4">
            <div>
              <Label htmlFor="edit-name">
                Nome do Formulário <span className="text-red-500">*</span>
              </Label>
              <Input
                id="edit-name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Ex: Formulário de Petição Inicial"
                required
              />
            </div>

            <div>
              <Label htmlFor="edit-description">Descrição</Label>
              <div className="relative">
                <Textarea
                  id="edit-description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Descreva o propósito deste formulário"
                  rows={3}
                  className="pr-32"
                />
                <div className="absolute top-1 right-1">
                  <AIEnhanceButton
                    value={formData.description}
                    onEnhance={(text) => setFormData({ ...formData, description: text })}
                    context="descrição de formulário jurídico"
                  />
                </div>
              </div>
            </div>

            <div>
              <Label htmlFor="edit-blueprint">
                <FileText className="inline h-4 w-4 mr-1" />
                Blueprint (Opcional)
              </Label>
              <p className="text-xs text-muted-foreground mb-2">
                Selecione o blueprint que define a estrutura do documento e os agentes especialistas disponíveis
              </p>
              {loadingBlueprints ? (
                <div className="flex items-center justify-center py-4 border rounded-md">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                  <span className="ml-2 text-sm text-muted-foreground">Carregando blueprints...</span>
                </div>
              ) : (
                <Select
                  value={formData.blueprint || 'none'}
                  onValueChange={(v) => setFormData({ ...formData, blueprint: v === 'none' ? undefined : v })}
                >
                  <SelectTrigger id="edit-blueprint">
                    <SelectValue placeholder="Nenhum blueprint selecionado" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">
                      <span className="text-muted-foreground">Nenhum (remover vínculo)</span>
                    </SelectItem>
                    {blueprints.map((blueprint) => (
                      <SelectItem key={blueprint.id} value={blueprint.id}>
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4" />
                          <span>{blueprint.name}</span>
                          <span className="text-xs text-muted-foreground">
                            ({blueprint.section_count} seções)
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
              {blueprints.length === 0 && !loadingBlueprints && (
                <p className="text-xs text-amber-600 mt-1">
                  Nenhum blueprint ativo disponível. Configure em Assistente Inteligente.
                </p>
              )}
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="edit-is-active"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="h-4 w-4 rounded border-gray-300"
              />
              <Label htmlFor="edit-is-active" className="cursor-pointer">
                Formulário ativo
              </Label>
            </div>
          </TabsContent>

          <TabsContent value="fields" className="space-y-4">
            <div className="flex justify-between items-center">
              <h4 className="font-medium text-sm text-muted-foreground">
                CAMPOS CONFIGURADOS
              </h4>
              <AddFieldDialog onAdd={handleAddField} existingFields={fields} blueprintId={formData.blueprint}>
                <Button size="sm">
                  <Plus className="mr-2 h-4 w-4" />
                  Adicionar Campo
                </Button>
              </AddFieldDialog>
            </div>

            {fields.length === 0 ? (
              <Card className="p-12 text-center">
                <div className="flex flex-col items-center gap-3 text-muted-foreground">
                  <Plus className="h-12 w-12 opacity-20" />
                  <p>Nenhum campo adicionado</p>
                  <p className="text-sm">
                    Clique em "Adicionar Campo" para começar
                  </p>
                </div>
              </Card>
            ) : (
              <div className="space-y-2">
                {fields.map((field, index) => (
                  <Card key={index} className="p-4 hover:bg-accent/50 transition-colors">
                    <div className="flex items-start justify-between gap-4">
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
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEditField(index)}
                            title="Editar campo"
                          >
                            <Settings className="h-4 w-4" />
                          </Button>
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
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>

        <div className="flex justify-between pt-4 border-t">
          <Button type="button" variant="outline" onClick={() => setOpen(false)}>
            Cancelar
          </Button>
          <Button onClick={handleSubmit} disabled={isUpdating || fields.length === 0}>
            {isUpdating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Salvando...
              </>
            ) : (
              <>
                Salvar Alterações ({fields.length} campo{fields.length !== 1 ? 's' : ''})
              </>
            )}
          </Button>
        </div>
      </DialogContent>

      {/* Edit Field Dialog */}
      {editingField && (
        <EditFieldDialog
          field={editingField.field}
          open={!!editingField}
          onClose={() => setEditingField(null)}
          onSave={handleSaveEditedField}
          blueprintId={formData.blueprint}
        />
      )}
    </Dialog>
  );
}

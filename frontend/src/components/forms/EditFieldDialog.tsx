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
import { Switch } from '@/components/ui/switch';
import { Checkbox } from '@/components/ui/checkbox';
import { Sparkles, Loader2, Plus, Trash2, Wrench, Brain } from 'lucide-react';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';
import api from '@/lib/api';

// Interface para agentes de seção do Blueprint
interface SectionAgent {
  id: string;
  name: string;
  description: string;
  section_number: number;
  section_name: string;
  section_key: string;
  is_active: boolean;
}

const FIELD_TYPES = [
  { value: 'text', label: 'Texto Curto', icon: '📝' },
  { value: 'textarea', label: 'Texto Longo', icon: '📄' },
  { value: 'number', label: 'Número', icon: '🔢' },
  { value: 'email', label: 'E-mail', icon: '📧' },
  { value: 'date', label: 'Data', icon: '📅' },
  { value: 'select', label: 'Seleção (Dropdown)', icon: '▼' },
  { value: 'checkbox', label: 'Checkbox', icon: '☑' },
  { value: 'radio', label: 'Opções (Radio)', icon: '🔘' },
  { value: 'file', label: 'Arquivo', icon: '📎' },
];

// Mapeamento de ícones e descrições por tipo
const AI_TYPE_CONFIG: Record<string, { icon: string; description: string }> = {
  'corretor': { icon: '✍️', description: 'Corrige erros de português' },
  'exemplo': { icon: '💡', description: 'Fornece exemplos práticos' },
  'analise': { icon: '🔍', description: 'Analisa clareza e conformidade' },
  'sugestao': { icon: '🎯', description: 'Sugere melhorias e complementos' },
  'resumo': { icon: '📋', description: 'Gera resumos automáticos' },
};

interface Field {
  id: string;
  type: string;
  label: string;
  required?: boolean;
  help_text?: string;
  placeholder?: string;
  ai_assist?: boolean;
  ai_prompt_types?: string[];
  validation?: any;
  options?: Array<string | { value: string; label: string }>;
  min_length?: number;
  max_length?: number;
  pattern?: string;
  default_value?: string;
}

interface EditFieldDialogProps {
  field: Field;
  open: boolean;
  onClose: () => void;
  onSave: (field: Field) => void;
  blueprintId?: string;
}

export function EditFieldDialog({ field: initialField, open, onClose, onSave, blueprintId }: EditFieldDialogProps) {
  const [field, setField] = useState<Field>(initialField);
  const [aiAgentTypes, setAiAgentTypes] = useState<Array<{ value: string; label: string; description: string }>>([]);
  const [loadingAgents, setLoadingAgents] = useState(false);

  // Estado para agentes de seção do Blueprint
  const [sectionAgents, setSectionAgents] = useState<SectionAgent[]>([]);
  const [loadingSectionAgents, setLoadingSectionAgents] = useState(false);

  // Sincronizar com initialField quando mudar
  useEffect(() => {
    setField(initialField);
  }, [initialField]);

  // Sanitizar ID: apenas a-z, 0-9 e _
  const sanitizeId = (value: string): string => {
    return value
      .toLowerCase()
      .replace(/[^a-z0-9_]/g, '');
  };

  // Buscar FormAssistants do backend
  useEffect(() => {
    const fetchAgentTypes = async () => {
      setLoadingAgents(true);
      try {
        const response = await api.get('/api/v1/forms/assistants/', {
          params: { active_only: 'true' }
        });

        // Extrair tipos únicos dos FormAssistants
        const uniqueTypes = new Set<string>();
        const typesData: Array<{ value: string; label: string; description: string }> = [];

        const assistants = Array.isArray(response.data) ? response.data : (response.data.results || []);
        assistants.forEach((assistant: any) => {
          if (!uniqueTypes.has(assistant.assistant_type)) {
            uniqueTypes.add(assistant.assistant_type);
            const config = AI_TYPE_CONFIG[assistant.assistant_type] || { icon: '🤖', description: assistant.description || 'Assistente de formulário' };
            typesData.push({
              value: assistant.assistant_type,
              label: `${config.icon} ${assistant.name}`,
              description: config.description
            });
          }
        });

        setAiAgentTypes(typesData);
      } catch (error) {
        console.error('Erro ao buscar form assistants:', error);
        // Fallback para tipos hardcoded se falhar
        setAiAgentTypes([
          { value: 'corretor', label: '✍️ Corretor Ortográfico', description: 'Corrige erros de português' },
          { value: 'exemplo', label: '💡 Exemplos e Sugestões', description: 'Fornece exemplos práticos' },
          { value: 'analise', label: '🔍 Análise de Texto', description: 'Analisa clareza e conformidade' },
          { value: 'sugestao', label: '🎯 Sugestão de Conteúdo', description: 'Sugere melhorias e complementos' },
        ]);
      } finally {
        setLoadingAgents(false);
      }
    };

    if (open) {
      fetchAgentTypes();
    }
  }, [open]);

  // Buscar agentes de seção do Blueprint (quando blueprintId fornecido)
  useEffect(() => {
    const fetchSectionAgents = async () => {
      if (!blueprintId) {
        setSectionAgents([]);
        return;
      }

      setLoadingSectionAgents(true);
      try {
        const response = await api.get(`/api/v1/intelligent-assistant/blueprints/${blueprintId}/agents/`);
        const agents = response.data.agents || [];
        setSectionAgents(agents);
      } catch (error) {
        console.error('Erro ao buscar agentes de seção:', error);
        setSectionAgents([]);
      } finally {
        setLoadingSectionAgents(false);
      }
    };

    if (open) {
      fetchSectionAgents();
    }
  }, [open, blueprintId]);

  const handleSave = () => {
    if (!field.id || !field.label) {
      alert('ID e Label são obrigatórios');
      return;
    }

    // Validar campos que precisam de opções
    if ((field.type === 'select' || field.type === 'radio' || field.type === 'checkbox') &&
        (!field.options || field.options.length === 0)) {
      alert(`Campo do tipo ${field.type === 'select' ? 'Dropdown' : field.type === 'radio' ? 'Opções (Radio)' : 'Checkbox'} precisa ter pelo menos uma opção configurada`);
      return;
    }

    if (field.ai_assist && (!field.ai_prompt_types || field.ai_prompt_types.length === 0)) {
      alert('Selecione pelo menos um tipo de assistência de IA');
      return;
    }

    onSave(field);
    onClose();
  };

  const toggleAIPromptType = (type: string) => {
    const currentTypes = field.ai_prompt_types || [];
    if (currentTypes.includes(type)) {
      setField({
        ...field,
        ai_prompt_types: currentTypes.filter(t => t !== type),
      });
    } else {
      setField({
        ...field,
        ai_prompt_types: [...currentTypes, type],
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Editar Campo</DialogTitle>
          <DialogDescription className="sr-only">Editar configurações do campo do formulário</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Tipo do Campo */}
          <div>
            <Label htmlFor="field-type">
              Tipo do Campo <span className="text-red-500">*</span>
            </Label>
            <Select value={field.type} onValueChange={(v) => setField({ ...field, type: v })}>
              <SelectTrigger id="field-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {FIELD_TYPES.map((t) => (
                  <SelectItem key={t.value} value={t.value}>
                    {t.icon} {t.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Label */}
          <div>
            <Label htmlFor="field-label">
              Label (Título) <span className="text-red-500">*</span>
            </Label>
            <Input
              id="field-label"
              value={field.label}
              onChange={(e) => setField({ ...field, label: e.target.value })}
              placeholder="Ex: Descrição do Objeto da Contratação"
            />
          </div>

          {/* ID do Campo (placeholder) */}
          <div>
            <Label htmlFor="edit-field-id">
              ID do Campo <span className="text-red-500">*</span>
            </Label>
            <Input
              id="edit-field-id"
              value={field.id}
              onChange={(e) => {
                const sanitized = sanitizeId(e.target.value);
                setField({ ...field, id: sanitized });
              }}
              placeholder="Ex: integrante_1_name"
              className="font-mono"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Este ID corresponde ao placeholder <code className="bg-slate-200 dark:bg-slate-800 px-1 rounded">{`{{${field.id || '...'}}}`}</code> no template. Apenas letras minúsculas, números e underline.
            </p>
          </div>

          {/* Help Text */}
          <div>
            <Label htmlFor="field-help">Texto de Ajuda</Label>
            <div className="relative">
              <Textarea
                id="field-help"
                value={field.help_text || ''}
                onChange={(e) => setField({ ...field, help_text: e.target.value })}
                placeholder="Texto explicativo para auxiliar o preenchimento"
                rows={2}
                className="pr-32"
              />
              <div className="absolute top-1 right-1">
                <AIEnhanceButton
                  value={field.help_text || ''}
                  onEnhance={(text) => setField({ ...field, help_text: text })}
                  context="texto de ajuda de campo de formulário jurídico"
                />
              </div>
            </div>
          </div>

          {/* Placeholder */}
          <div>
            <Label htmlFor="field-placeholder">Placeholder</Label>
            <Input
              id="field-placeholder"
              value={field.placeholder || ''}
              onChange={(e) => setField({ ...field, placeholder: e.target.value })}
              placeholder="Ex: Digite aqui a descrição detalhada..."
            />
          </div>

          {/* Campos específicos por tipo */}
          {(field.type === 'select' || field.type === 'radio' || field.type === 'checkbox') && (
            <div className="space-y-3 p-4 border rounded-lg bg-slate-50 dark:bg-slate-900">
              <div className="flex items-center justify-between">
                <Label>Opções {field.type === 'select' ? '(Dropdown)' : field.type === 'radio' ? '(Seleção Única)' : '(Múltipla Escolha)'}</Label>
                <span className="text-xs text-muted-foreground">
                  {(field.options || []).length} opção(ões)
                </span>
              </div>

              <div className="space-y-2">
                {(field.options || []).map((option, index) => {
                  const optionValue = typeof option === 'string' ? option : option.label;
                  return (
                    <div key={index} className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground w-6">{index + 1}.</span>
                      <Input
                        value={optionValue}
                        onChange={(e) => {
                          const newOptions = [...(field.options || [])];
                          newOptions[index] = e.target.value;
                          setField({ ...field, options: newOptions });
                        }}
                        placeholder={`Opção ${index + 1}`}
                        className="flex-1"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          const newOptions = (field.options || []).filter((_, i) => i !== index);
                          setField({ ...field, options: newOptions });
                        }}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  );
                })}
              </div>

              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  const newOptions = [...(field.options || []), ''];
                  setField({ ...field, options: newOptions });
                }}
                className="w-full"
              >
                <Plus className="h-4 w-4 mr-2" />
                Adicionar Opção
              </Button>
            </div>
          )}

          {(field.type === 'text' || field.type === 'textarea' || field.type === 'email') && (
            <div className="grid grid-cols-2 gap-4 p-4 border rounded-lg bg-slate-50 dark:bg-slate-900">
              <div>
                <Label htmlFor="min-length">Tamanho Mínimo</Label>
                <Input
                  id="min-length"
                  type="number"
                  min={0}
                  value={field.min_length || ''}
                  onChange={(e) => setField({ ...field, min_length: e.target.value ? parseInt(e.target.value) : undefined })}
                  placeholder="Ex: 10"
                />
              </div>
              <div>
                <Label htmlFor="max-length">Tamanho Máximo</Label>
                <Input
                  id="max-length"
                  type="number"
                  min={0}
                  value={field.max_length || ''}
                  onChange={(e) => setField({ ...field, max_length: e.target.value ? parseInt(e.target.value) : undefined })}
                  placeholder="Ex: 500"
                />
              </div>
            </div>
          )}

          {field.type === 'number' && (
            <div className="grid grid-cols-2 gap-4 p-4 border rounded-lg bg-slate-50 dark:bg-slate-900">
              <div>
                <Label htmlFor="min-value">Valor Mínimo</Label>
                <Input
                  id="min-value"
                  type="number"
                  value={field.validation?.min || ''}
                  onChange={(e) => setField({
                    ...field,
                    validation: { ...field.validation, min: e.target.value ? parseFloat(e.target.value) : undefined }
                  })}
                  placeholder="Ex: 0"
                />
              </div>
              <div>
                <Label htmlFor="max-value">Valor Máximo</Label>
                <Input
                  id="max-value"
                  type="number"
                  value={field.validation?.max || ''}
                  onChange={(e) => setField({
                    ...field,
                    validation: { ...field.validation, max: e.target.value ? parseFloat(e.target.value) : undefined }
                  })}
                  placeholder="Ex: 100"
                />
              </div>
            </div>
          )}

          {field.type === 'file' && (
            <div className="p-4 border rounded-lg bg-slate-50 dark:bg-slate-900">
              <Label htmlFor="file-types">Tipos de Arquivo Aceitos</Label>
              <Input
                id="file-types"
                value={field.validation?.accept || ''}
                onChange={(e) => setField({
                  ...field,
                  validation: { ...field.validation, accept: e.target.value }
                })}
                placeholder="Ex: .pdf,.doc,.docx"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Use vírgula para separar múltiplos tipos (ex: .pdf,.doc,.docx)
              </p>
            </div>
          )}

          {/* Required Switch */}
          <div className="flex items-center space-x-2 py-2 border-t">
            <Switch
              id="field-required"
              checked={field.required}
              onCheckedChange={(checked) => setField({ ...field, required: checked })}
            />
            <Label htmlFor="field-required" className="cursor-pointer">
              Campo Obrigatório
            </Label>
          </div>

          {/* AI Assistance Section */}
          <div className="border-t pt-4 space-y-4">
            <div className="flex items-center space-x-2">
              <Switch
                id="field-ai"
                checked={field.ai_assist}
                onCheckedChange={(checked) => setField({ ...field, ai_assist: checked })}
              />
              <Label htmlFor="field-ai" className="cursor-pointer font-semibold flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-purple-500" />
                Habilitar Assistente IA
              </Label>
            </div>

            {field.ai_assist && (
              <div className="ml-6 space-y-4">
                {/* FERRAMENTAS - FormAssistants genéricos */}
                <div className="p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-800">
                  <div className="flex items-center gap-2 mb-3">
                    <Wrench className="h-4 w-4 text-blue-600" />
                    <Label className="text-blue-700 dark:text-blue-300 font-semibold">FERRAMENTAS</Label>
                    <span className="text-xs text-blue-500">(FormAssistant)</span>
                  </div>
                  <p className="text-xs text-muted-foreground mb-3">
                    Ferramentas genéricas de auxílio à escrita disponíveis para qualquer campo
                  </p>
                  {loadingAgents ? (
                    <div className="flex items-center justify-center py-4">
                      <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
                      <span className="ml-2 text-sm text-muted-foreground">Carregando ferramentas...</span>
                    </div>
                  ) : aiAgentTypes.length === 0 ? (
                    <p className="text-xs text-amber-600 py-2">Nenhuma ferramenta disponível</p>
                  ) : (
                    <div className="space-y-2">
                      {aiAgentTypes.map((type) => (
                        <div key={type.value} className="flex items-start space-x-3 p-2 rounded-md hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors">
                          <Checkbox
                            id={`edit-ai-type-${type.value}`}
                            checked={field.ai_prompt_types?.includes(type.value) || false}
                            onCheckedChange={() => toggleAIPromptType(type.value)}
                            className="mt-0.5"
                          />
                          <div className="flex-1">
                            <label
                              htmlFor={`edit-ai-type-${type.value}`}
                              className="text-sm font-medium leading-none cursor-pointer"
                            >
                              {type.label}
                            </label>
                            <p className="text-xs text-muted-foreground mt-0.5">
                              {type.description}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* AGENTES DE SEÇÃO - Do Blueprint selecionado */}
                {blueprintId && (
                  <div className="p-4 bg-purple-50 dark:bg-purple-950/20 rounded-lg border border-purple-200 dark:border-purple-800">
                    <div className="flex items-center gap-2 mb-3">
                      <Brain className="h-4 w-4 text-purple-600" />
                      <Label className="text-purple-700 dark:text-purple-300 font-semibold">AGENTES DE SEÇÃO</Label>
                      <span className="text-xs text-purple-500">(do Blueprint)</span>
                    </div>
                    <p className="text-xs text-muted-foreground mb-3">
                      Agentes especialistas configurados nas seções do Blueprint vinculado ao formulário
                    </p>
                    {loadingSectionAgents ? (
                      <div className="flex items-center justify-center py-4">
                        <Loader2 className="h-5 w-5 animate-spin text-purple-500" />
                        <span className="ml-2 text-sm text-muted-foreground">Carregando agentes de seção...</span>
                      </div>
                    ) : sectionAgents.length === 0 ? (
                      <p className="text-xs text-amber-600 py-2">Nenhum agente de seção configurado no Blueprint</p>
                    ) : (
                      <div className="space-y-2">
                        {sectionAgents.map((agent) => (
                          <div key={agent.id} className="flex items-start space-x-3 p-2 rounded-md hover:bg-purple-100 dark:hover:bg-purple-900/30 transition-colors">
                            <Checkbox
                              id={`edit-section-agent-${agent.id}`}
                              checked={field.ai_prompt_types?.includes(`section:${agent.section_key}`) || false}
                              onCheckedChange={() => toggleAIPromptType(`section:${agent.section_key}`)}
                              className="mt-0.5"
                            />
                            <div className="flex-1">
                              <label
                                htmlFor={`edit-section-agent-${agent.id}`}
                                className="text-sm font-medium leading-none cursor-pointer"
                              >
                                {agent.section_number}. {agent.name}
                              </label>
                              <p className="text-xs text-muted-foreground mt-0.5">
                                {agent.description || `Seção: ${agent.section_name}`}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Mensagem se não houver Blueprint selecionado */}
                {!blueprintId && (
                  <div className="p-3 bg-amber-50 dark:bg-amber-950/20 rounded-lg border border-amber-200 dark:border-amber-800">
                    <p className="text-xs text-amber-700 dark:text-amber-300">
                      <Brain className="h-3 w-3 inline mr-1" />
                      Selecione um Blueprint no formulário para ter acesso aos Agentes de Seção especializados
                    </p>
                  </div>
                )}

                {/* Resumo de seleções */}
                {field.ai_prompt_types && field.ai_prompt_types.length > 0 && (
                  <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-xs font-medium text-green-700 dark:text-green-300">
                      ✓ {field.ai_prompt_types.length} assistência{field.ai_prompt_types.length !== 1 ? 's' : ''} selecionada{field.ai_prompt_types.length !== 1 ? 's' : ''}
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="outline" onClick={onClose}>
              Cancelar
            </Button>
            <Button onClick={handleSave} disabled={!field.id || !field.label}>
              Salvar Alterações
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

'use client';

import { useState, useEffect } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Info, Bot, Loader2, Copy, Check, CheckCircle2, FileText } from 'lucide-react';
import { AIAssistantButton } from '@/components/forms/AIAssistantButton';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';
import api from '@/lib/api';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';

// Tipo para campo flat (fields)
interface FlatField {
  id: string;
  type: 'text' | 'textarea' | 'number' | 'email' | 'date' | 'select' | 'checkbox' | 'radio' | 'file' | 'array';
  label: string;
  required?: boolean;
  help_text?: string;
  placeholder?: string;
  options?: string[] | { value: string; label: string }[];
  ai_assist?: boolean;
  ai_prompt_types?: string[];
}

// Tipo para campo em seção (sections)
interface SectionField {
  field_id: string;
  field_type: 'text' | 'textarea' | 'number' | 'email' | 'date' | 'select' | 'checkbox' | 'radio' | 'file' | 'array';
  field_name: string;
  required?: boolean;
  help_text?: string;
  placeholder?: string;
  options?: string[] | { value: string; label: string }[];
  ai_assist?: boolean;
  ai_prompt_types?: string[];
}

interface Section {
  section_id: string;
  section_title: string;
  legal_basis?: string;
  fields: SectionField[];
}

// Agente do Blueprint
interface BlueprintAgent {
  id: string;
  name: string;
  type: 'generator' | 'validator';
  section_name: string;
  section_key: string;
  section_number: number;
}

interface DynamicFormProps {
  fields?: FlatField[];
  sections?: Section[];
  data: Record<string, any>;
  onChange: (data: Record<string, any>) => void;
  disabled?: boolean;
  documentTitle?: string;
  blueprintAgents?: BlueprintAgent[];
}

export function DynamicForm({ fields, sections, data, onChange, disabled = false, documentTitle = '', blueprintAgents = [] }: DynamicFormProps) {
  const [formData, setFormData] = useState<Record<string, any>>(data || {});
  const [agentDialogOpen, setAgentDialogOpen] = useState(false);
  const [agentResult, setAgentResult] = useState<string>('');
  const [agentLoading, setAgentLoading] = useState<string | null>(null);
  const [currentAgentInfo, setCurrentAgentInfo] = useState<{ name: string; type: string; sectionName: string } | null>(null);
  // Estados para os botões do dialog do agente
  const [currentFieldId, setCurrentFieldId] = useState<string>('');
  const [currentFieldValue, setCurrentFieldValue] = useState<string>('');
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  // Remove marcadores markdown e retorna texto limpo
  const stripMarkdown = (text: string): string => {
    if (!text || typeof text !== 'string') return text;
    return text
      .replace(/^#{1,6}\s+/gm, '')          // ## heading → heading
      .replace(/\*\*(.+?)\*\*/g, '$1')      // **bold** → bold
      .replace(/\*(.+?)\*/g, '$1')          // *italic* → italic
      .replace(/`(.+?)`/g, '$1')            // `code` → code
      .replace(/^\s*[-*]\s+/gm, '- ')       // Normaliza bullets
      .replace(/^\s*>\s+/gm, '')            // > blockquote → texto
      .replace(/\[(.+?)\]\(.+?\)/g, '$1')   // [link](url) → link
      .replace(/\n{3,}/g, '\n\n');           // Triplas quebras → dupla
  };

  // Mapear tipos de IA para ações
  const aiTypeToAction: Record<string, 'corrigir' | 'melhorar' | 'exemplo' | 'consultar' | 'resumir' | 'expandir' | 'simplificar'> = {
    'corretor': 'corrigir',
    'sugestao': 'melhorar',
    'exemplo': 'exemplo',
    'analise': 'consultar',
    'resumo': 'resumir',
    'expansao': 'expandir',
    'simplificacao': 'simplificar',
  };

  useEffect(() => {
    setFormData(data || {});
  }, [data]);

  const handleChange = (fieldId: string, value: any) => {
    const newData = { ...formData, [fieldId]: value };
    setFormData(newData);
    onChange(newData);
  };

  const renderField = (field: FlatField | SectionField, fieldId: string, fieldType: string, fieldName: string) => {
    const commonProps = {
      id: fieldId,
      disabled,
      required: field.required,
    };

    switch (fieldType) {
      case 'text':
        return (
          <Input
            {...commonProps}
            type="text"
            placeholder={field.placeholder || `Digite ${fieldName.toLowerCase()}`}
            value={formData[fieldId] || ''}
            onChange={(e) => handleChange(fieldId, e.target.value)}
          />
        );

      case 'email':
        return (
          <Input
            {...commonProps}
            type="email"
            placeholder={field.placeholder || 'usuario@verus.ai'}
            value={formData[fieldId] || ''}
            onChange={(e) => handleChange(fieldId, e.target.value)}
          />
        );

      case 'number':
        return (
          <Input
            {...commonProps}
            type="number"
            placeholder={field.placeholder || '0'}
            value={formData[fieldId] || ''}
            onChange={(e) => handleChange(fieldId, parseFloat(e.target.value) || 0)}
          />
        );

      case 'date':
        return (
          <Input
            {...commonProps}
            type="date"
            value={formData[fieldId] || ''}
            onChange={(e) => handleChange(fieldId, e.target.value)}
          />
        );

      case 'textarea':
        return (
          <Textarea
            {...commonProps}
            placeholder={field.placeholder || `Digite ${fieldName.toLowerCase()}`}
            value={formData[fieldId] || ''}
            onChange={(e) => handleChange(fieldId, e.target.value)}
            rows={5}
            className="resize-y"
          />
        );

      case 'select':
        const options = field.options || [];
        return (
          <Select
            value={formData[fieldId] || ''}
            onValueChange={(value) => handleChange(fieldId, value)}
            disabled={disabled}
          >
            <SelectTrigger {...commonProps}>
              <SelectValue placeholder={`Selecione ${fieldName.toLowerCase()}`} />
            </SelectTrigger>
            <SelectContent>
              {options.map((option, index) => {
                const optionValue = typeof option === 'string' ? option : option.value;
                const optionLabel = typeof option === 'string' ? option : option.label;
                return (
                  <SelectItem key={index} value={optionValue}>
                    {optionLabel}
                  </SelectItem>
                );
              })}
            </SelectContent>
          </Select>
        );

      case 'checkbox':
        return (
          <div className="flex items-center space-x-2">
            <Checkbox
              id={fieldId}
              checked={formData[fieldId] || false}
              onCheckedChange={(checked) => handleChange(fieldId, checked)}
              disabled={disabled}
            />
            <Label htmlFor={fieldId} className="text-sm font-normal cursor-pointer">
              {fieldName}
            </Label>
          </div>
        );

      case 'radio':
        const radioOptions = field.options || [];
        return (
          <div className="space-y-2">
            {radioOptions.map((option, index) => {
              const optionValue = typeof option === 'string' ? option : option.value;
              const optionLabel = typeof option === 'string' ? option : option.label;
              return (
                <div key={index} className="flex items-center space-x-2">
                  <input
                    type="radio"
                    id={`${fieldId}-${index}`}
                    name={fieldId}
                    value={optionValue}
                    checked={formData[fieldId] === optionValue}
                    onChange={(e) => handleChange(fieldId, e.target.value)}
                    disabled={disabled}
                    className="h-4 w-4"
                  />
                  <Label htmlFor={`${fieldId}-${index}`} className="text-sm font-normal cursor-pointer">
                    {optionLabel}
                  </Label>
                </div>
              );
            })}
          </div>
        );

      case 'file':
        return (
          <Input
            {...commonProps}
            type="file"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) {
                handleChange(fieldId, file.name);
              }
            }}
          />
        );

      case 'array':
        // Implementação simplificada de array como textarea com linhas separadas
        const arrayValue = Array.isArray(formData[fieldId])
          ? formData[fieldId].join('\n')
          : formData[fieldId] || '';

        return (
          <Textarea
            {...commonProps}
            placeholder="Digite cada item em uma linha separada"
            value={arrayValue}
            onChange={(e) => {
              const lines = e.target.value.split('\n').filter(line => line.trim());
              handleChange(fieldId, lines);
            }}
            rows={5}
            className="resize-y"
          />
        );

      default:
        return (
          <Input
            {...commonProps}
            type="text"
            value={formData[fieldId] || ''}
            onChange={(e) => handleChange(fieldId, e.target.value)}
          />
        );
    }
  };

  // Função para executar agente de seção do Blueprint
  const executeSectionAgent = async (sectionType: string, fieldId: string, fieldLabel: string) => {
    // Extrair o section_key do tipo (ex: "section:demanda" -> "demanda")
    const sectionKey = sectionType.replace('section:', '');

    // Encontrar o agente correspondente ao section_key nos blueprintAgents
    const agent = blueprintAgents.find(a => a.section_key === sectionKey);

    if (!agent) {
      toast({
        title: 'Agente não encontrado',
        description: `Não foi possível encontrar o agente para a seção "${sectionKey}". Verifique se o Blueprint está configurado corretamente.`,
        variant: 'destructive',
      });
      return;
    }

    setAgentLoading(agent.id);
    setCopied(false);
    setCurrentFieldId(fieldId);
    setCurrentFieldValue(formData[fieldId] || '');
    setCurrentAgentInfo({
      name: agent.name,
      type: agent.type,
      sectionName: agent.section_name,
    });

    try {
      // Construir contexto para o agente
      const contextSummary = Object.entries(formData)
        .filter(([_, value]) => value)
        .map(([key, value]) => `${key}: ${String(value).substring(0, 200)}`)
        .join('\n');

      // Timeout maior para agentes de seção (2 minutos) - eles processam RAG + LLM
      const response = await api.post(
        `/api/v1/intelligent-assistant/agents/${agent.id}/execute/`,
        {
          objective: documentTitle || 'Documento em elaboração',
          context: contextSummary,
          section_data: { [fieldLabel]: formData[fieldId] || '' },
          field_name: fieldLabel,
          field_value: formData[fieldId] || '',
        },
        { timeout: 120000 } // 2 minutos
      );

      setAgentResult(response.data.content || response.data.response || 'Sem conteúdo gerado.');
      setAgentDialogOpen(true);

    } catch (error: any) {
      if (error.response?.status === 404) {
        toast({
          title: 'Endpoint não disponível',
          description: `O agente "${agent.name}" está configurado mas o endpoint de execução não foi encontrado.`,
          variant: 'destructive',
        });
      } else {
        toast({
          title: 'Erro ao executar agente',
          description: error.response?.data?.detail || error.message || 'Ocorreu um erro.',
          variant: 'destructive',
        });
      }
    } finally {
      setAgentLoading(null);
    }
  };

  // Função para copiar resultado do agente
  const handleAgentCopy = async () => {
    try {
      await navigator.clipboard.writeText(agentResult);
      setCopied(true);
      toast({
        title: 'Copiado!',
        description: 'Texto copiado para a área de transferência.',
      });
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast({
        title: 'Erro',
        description: 'Não foi possível copiar o texto.',
        variant: 'destructive',
      });
    }
  };

  // Função para aplicar resultado do agente no campo (strip markdown)
  const handleAgentApply = () => {
    if (currentFieldId && agentResult) {
      handleChange(currentFieldId, stripMarkdown(agentResult));
      toast({
        title: 'Aplicado!',
        description: `Conteúdo do agente aplicado com sucesso no campo.`,
      });
    }
    setAgentDialogOpen(false);
  };

  // Função para renderizar botões de IA
  const renderAIButtons = (field: FlatField | SectionField, fieldId: string, fieldLabel: string) => {
    // Verificar se há assistentes de IA configurados
    if (!field.ai_assist || !field.ai_prompt_types || field.ai_prompt_types.length === 0 || disabled) {
      return null;
    }

    // Separar tipos normais (ferramentas) dos tipos de seção (section:xxx)
    const toolTypes = field.ai_prompt_types.filter(type => !type.startsWith('section:'));
    const sectionTypes = field.ai_prompt_types.filter(type => type.startsWith('section:'));

    // Mapear ferramentas para objetos com tipo original e ação
    const aiButtonsData = toolTypes
      .map(type => ({
        type,
        action: aiTypeToAction[type],
      }))
      .filter(item => item.action);

    const hasTools = aiButtonsData.length > 0;
    const hasSectionAgents = sectionTypes.length > 0 && blueprintAgents.length > 0;

    if (!hasTools && !hasSectionAgents) return null;

    return (
      <div className="flex flex-wrap gap-2 mt-2">
        {/* Ferramentas genéricas (FormAssistants) */}
        {aiButtonsData.map((item) => (
          <AIAssistantButton
            key={item.type}
            action={item.action}
            assistantType={item.type}
            fieldName={fieldId}
            fieldValue={formData[fieldId]}
            fieldLabel={fieldLabel}
            formContext={formData}
            documentTitle={documentTitle}
            onResult={(result) => handleChange(fieldId, result)}
          />
        ))}

        {/* Agentes de Seção do Blueprint */}
        {hasSectionAgents && (
          <TooltipProvider>
            {sectionTypes.map((sectionType) => {
              const sectionKey = sectionType.replace('section:', '');
              // Encontrar o agente correspondente pelo section_key
              const agent = blueprintAgents.find(a => a.section_key === sectionKey);

              if (!agent) return null;

              return (
                <Tooltip key={sectionType}>
                  <TooltipTrigger asChild>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => executeSectionAgent(sectionType, fieldId, fieldLabel)}
                      disabled={agentLoading === agent.id}
                      className="border-purple-300 hover:bg-purple-50 dark:hover:bg-purple-950"
                    >
                      {agentLoading === agent.id ? (
                        <Loader2 className="h-3 w-3 animate-spin mr-1" />
                      ) : (
                        <Bot className="h-3 w-3 mr-1 text-purple-600" />
                      )}
                      <span className="text-xs">{agent.name}</span>
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="text-xs">Agente especialista: {agent.section_name}</p>
                  </TooltipContent>
                </Tooltip>
              );
            })}
          </TooltipProvider>
        )}
      </div>
    );
  };

  // Renderizar Dialog para resultado do agente (compartilhado)
  const renderAgentDialog = () => (
    <Dialog open={agentDialogOpen} onOpenChange={setAgentDialogOpen}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-purple-600" />
            {currentAgentInfo?.name}
          </DialogTitle>
          <DialogDescription>
            Conteúdo gerado pelo agente especialista: {currentAgentInfo?.sectionName}. Você pode aplicar no campo ou copiar.
          </DialogDescription>
        </DialogHeader>

        {/* Texto original (se houver) */}
        {currentFieldValue && (
          <div className="space-y-2">
            <label className="text-sm font-medium text-muted-foreground">Texto Original:</label>
            <div className="p-3 bg-muted rounded-md text-sm max-h-32 overflow-y-auto">
              <p className="whitespace-pre-wrap">{currentFieldValue}</p>
            </div>
          </div>
        )}

        {/* Resultado */}
        <div className="space-y-2">
          <label className="text-sm font-medium flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Resultado:
          </label>
          <div className="p-4 bg-purple-50 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-800 rounded-md prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown
              rehypePlugins={[rehypeRaw]}
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                ul: ({ children }) => <ul className="list-disc ml-4 mb-2 space-y-1">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal ml-4 mb-2 space-y-1">{children}</ol>,
                li: ({ children }) => <li className="text-sm">{children}</li>,
                h1: ({ children }) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
                h2: ({ children }) => <h2 className="text-base font-bold mb-2">{children}</h2>,
                h3: ({ children }) => <h3 className="text-sm font-bold mb-1">{children}</h3>,
                code: ({ children }) => <code className="bg-muted px-1 py-0.5 rounded text-xs">{children}</code>,
              }}
            >
              {agentResult}
            </ReactMarkdown>
          </div>
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button
            variant="outline"
            onClick={handleAgentCopy}
            className="w-full sm:w-auto"
          >
            {copied ? (
              <Check className="h-4 w-4 mr-2 text-green-600" />
            ) : (
              <Copy className="h-4 w-4 mr-2" />
            )}
            {copied ? 'Copiado!' : 'Copiar'}
          </Button>

          <div className="flex gap-2 w-full sm:w-auto">
            <Button
              variant="ghost"
              onClick={() => setAgentDialogOpen(false)}
              className="flex-1 sm:flex-initial"
            >
              Fechar
            </Button>

            <Button
              onClick={handleAgentApply}
              className="flex-1 sm:flex-initial"
            >
              <CheckCircle2 className="h-4 w-4 mr-2" />
              Aplicar no Campo
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );

  // Renderizar formato FLAT (fields)
  if (fields && fields.length > 0) {
    return (
      <>
        <div className="space-y-6">
          {fields.map((field) => (
            <div key={field.id} className="space-y-2">
              <Label htmlFor={field.id}>
                {field.label}
                {field.required && <span className="text-red-500 ml-1">*</span>}
              </Label>
              {renderField(field, field.id, field.type, field.label)}
              {field.help_text && (
                <p className="text-sm text-muted-foreground flex items-start gap-1">
                  <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <span>{field.help_text}</span>
                </p>
              )}
              {/* Botões de Assistente IA */}
              {renderAIButtons(field, field.id, field.label)}
            </div>
          ))}
        </div>
        {renderAgentDialog()}
      </>
    );
  }

  // Renderizar formato SECTIONS
  if (sections && sections.length > 0) {
    return (
      <>
        <div className="space-y-6">
          {sections.map((section) => (
            <Card key={section.section_id}>
              <CardHeader>
                <CardTitle>{section.section_title}</CardTitle>
                {section.legal_basis && (
                  <CardDescription className="text-xs">
                    <strong>Base Legal:</strong> {section.legal_basis}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent className="space-y-6">
                {section.fields.map((field) => (
                  <div key={field.field_id} className="space-y-2">
                    {field.field_type !== 'checkbox' && (
                      <Label htmlFor={field.field_id}>
                        {field.field_name}
                        {field.required && <span className="text-red-500 ml-1">*</span>}
                      </Label>
                    )}
                    {renderField(field, field.field_id, field.field_type, field.field_name)}
                    {field.help_text && (
                      <p className="text-sm text-muted-foreground flex items-start gap-1">
                        <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
                        <span>{field.help_text}</span>
                      </p>
                    )}
                    {/* Botões de Assistente IA */}
                    {renderAIButtons(field, field.field_id, field.field_name)}
                  </div>
                ))}
              </CardContent>
            </Card>
          ))}
        </div>
        {renderAgentDialog()}
      </>
    );
  }

  // Fallback se não houver campos
  return (
    <div className="text-center text-muted-foreground py-8">
      Nenhum campo configurado para este formulário.
    </div>
  );
}

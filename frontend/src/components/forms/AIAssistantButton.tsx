'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
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
import { Wand2, CheckCircle2, Lightbulb, BookOpen, Loader2, Copy, Check, FileText, Minimize2, Maximize2, FileSearch } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import api from '@/lib/api';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';

type AIAction = 'corrigir' | 'melhorar' | 'exemplo' | 'consultar' | 'resumir' | 'expandir' | 'simplificar';

interface AIAssistantButtonProps {
  action: AIAction;
  assistantType: string; // Tipo original do assistente (corretor, exemplo, analise, etc)
  fieldName: string;
  fieldValue?: string;
  fieldLabel?: string;
  formContext?: Record<string, any>;
  documentTitle?: string;
  onResult?: (result: string) => void;
}

const actionConfig = {
  corrigir: {
    icon: CheckCircle2,
    label: 'Corrigir Texto',
    tooltip: 'Corrigir gramática e ortografia',
    color: 'text-green-600',
    modalTitle: 'Texto Corrigido',
    modalDescription: 'Revise o texto corrigido abaixo. Você pode aplicar no campo ou copiar.',
  },
  melhorar: {
    icon: Wand2,
    label: 'Melhorar Redacao',
    tooltip: 'Melhorar clareza e fluidez do texto',
    color: 'text-blue-600',
    modalTitle: 'Texto Melhorado',
    modalDescription: 'Revise o texto melhorado abaixo. Voce pode aplicar no campo ou copiar.',
  },
  exemplo: {
    icon: Lightbulb,
    label: 'Gerar Exemplo',
    tooltip: 'Gerar exemplo baseado na base de conhecimento',
    color: 'text-yellow-600',
    modalTitle: 'Exemplo Gerado',
    modalDescription: 'Veja o exemplo gerado abaixo. Você pode aplicar no campo ou copiar.',
  },
  consultar: {
    icon: BookOpen,
    label: 'Consultar',
    tooltip: 'Buscar informações na base de conhecimento',
    color: 'text-purple-600',
    modalTitle: 'Resultado da Consulta',
    modalDescription: 'Informações encontradas na base de conhecimento.',
  },
  resumir: {
    icon: Minimize2,
    label: 'Resumir',
    tooltip: 'Criar um resumo do texto',
    color: 'text-orange-600',
    modalTitle: 'Texto Resumido',
    modalDescription: 'Revise o resumo abaixo. Voce pode aplicar no campo ou copiar.',
  },
  expandir: {
    icon: Maximize2,
    label: 'Expandir',
    tooltip: 'Expandir e detalhar o texto',
    color: 'text-teal-600',
    modalTitle: 'Texto Expandido',
    modalDescription: 'Revise o texto expandido abaixo. Voce pode aplicar no campo ou copiar.',
  },
  simplificar: {
    icon: FileSearch,
    label: 'Simplificar',
    tooltip: 'Simplificar a linguagem do texto',
    color: 'text-cyan-600',
    modalTitle: 'Texto Simplificado',
    modalDescription: 'Revise o texto simplificado abaixo. Voce pode aplicar no campo ou copiar.',
  },
};

// Mapeamento de assistantType para labels mais amigaveis
const assistantTypeLabels: Record<string, string> = {
  'corretor': 'Corrigir',
  'sugestao': 'Melhorar',
  'exemplo': 'Exemplo',
  'analise': 'Analisar',
  'resumo': 'Resumir',
  'expansao': 'Expandir',
  'simplificacao': 'Simplificar',
};

export function AIAssistantButton({
  action,
  assistantType,
  fieldName,
  fieldValue,
  fieldLabel,
  formContext = {},
  documentTitle = '',
  onResult,
}: AIAssistantButtonProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [result, setResult] = useState<string>('');
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  const config = actionConfig[action];
  const Icon = config.icon;

  // Label customizado baseado no tipo do assistente
  const buttonLabel = assistantTypeLabels[assistantType] || config.label;

  const handleAction = async () => {
    setIsLoading(true);
    setCopied(false);

    try {
      // 1. Buscar FormAssistant por tipo especifico
      const assistantsResponse = await api.get('/api/v1/forms/assistants/', {
        params: {
          assistant_type: assistantType,
          active_only: 'true',
        },
      });

      // A API pode retornar array direto ou objeto paginado {results: [...]}
      const assistants = Array.isArray(assistantsResponse.data)
        ? assistantsResponse.data
        : (assistantsResponse.data.results || []);

      if (!assistants || assistants.length === 0) {
        throw new Error(`Nenhum assistente do tipo "${assistantType}" encontrado. Configure assistentes em /dashboard/form-assistants`);
      }

      // Usar o primeiro assistente ativo encontrado (ou o marcado como default)
      const assistant = assistants.find((a: any) => a.is_default) || assistants[0];

      // 2. Preparar contexto do formulario
      // Criar resumo das respostas ja preenchidas
      const contextSummary = Object.entries(formContext)
        .filter(([key, value]) => value && key !== fieldName) // Excluir campo atual e vazios
        .map(([key, value]) => `${key}: ${String(value).substring(0, 100)}`) // Limitar tamanho
        .join('\n');

      const context = `Documento: ${documentTitle || 'Sem título'}
Campos ja preenchidos:
${contextSummary || 'Nenhum campo preenchido ainda'}`;

      // 3. Preparar variaveis para o agente
      let variables: Record<string, any> = {};
      let user_input = '';

      switch (action) {
        case 'corrigir':
        case 'melhorar':
        case 'resumir':
        case 'expandir':
        case 'simplificar':
          variables = {
            texto: fieldValue || '',
            context: context
          };
          break;

        case 'exemplo':
          // Exemplo tambem recebe o texto atual para contextualizar melhor
          variables = {
            texto: fieldValue || '',
            campo_nome: fieldName,
            campo_label: fieldLabel || fieldName,
            context: context
          };
          break;

        case 'consultar':
          user_input = `Informações sobre: ${fieldLabel || fieldName}`;
          variables = { context: context };
          break;
      }

      // 3. Executar assistente
      const response = await api.post(`/api/v1/forms/assistants/${assistant.id}/execute/`, {
        variables,
        user_input,
      });

      const responseText = response.data.response;

      // Sempre mostrar em modal para o usuario decidir
      setResult(responseText);
      setDialogOpen(true);

    } catch (error: any) {
      toast({
        title: 'Erro',
        description: error.response?.data?.detail || error.message || `Erro ao executar ${config.label}.`,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

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

  const handleApply = () => {
    if (onResult && result) {
      onResult(stripMarkdown(result));
      toast({
        title: 'Aplicado!',
        description: `${buttonLabel} aplicado com sucesso no campo.`,
      });
    }
    setDialogOpen(false);
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(result);
      setCopied(true);
      toast({
        title: 'Copiado!',
        description: 'Texto copiado para a area de transferencia.',
      });
      // Reset do icone apos 2 segundos
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast({
        title: 'Erro',
        description: 'Não foi possível copiar o texto.',
        variant: 'destructive',
      });
    }
  };

  // Para consultar e exemplo, nao precisa de valor no campo
  // Para outros (corrigir, melhorar, resumir, expandir, simplificar), precisa de valor
  const actionsWithoutValue: AIAction[] = ['exemplo', 'consultar'];
  const isDisabled = isLoading || (!actionsWithoutValue.includes(action) && !fieldValue);

  return (
    <>
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleAction}
              disabled={isDisabled}
            >
              {isLoading ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Icon className={`h-3 w-3 ${config.color}`} />
              )}
              <span className="ml-1 text-xs">{buttonLabel}</span>
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>{config.tooltip}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      {/* Dialog para mostrar resultado com opcoes */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Icon className={`h-5 w-5 ${config.color}`} />
              {config.modalTitle}
            </DialogTitle>
            <DialogDescription>
              {config.modalDescription}
            </DialogDescription>
          </DialogHeader>

          {/* Campo original (se houver) */}
          {fieldValue && action !== 'consultar' && (
            <div className="space-y-2">
              <label className="text-sm font-medium text-muted-foreground">Texto Original:</label>
              <div className="p-3 bg-muted rounded-md text-sm max-h-32 overflow-y-auto">
                <p className="whitespace-pre-wrap">{fieldValue}</p>
              </div>
            </div>
          )}

          {/* Resultado */}
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2">
              <FileText className="h-4 w-4" />
              {action === 'consultar' ? 'Informações Encontradas:' : 'Resultado:'}
            </label>
            <div className="p-4 bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-md prose prose-sm dark:prose-invert max-w-none">
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
                {result}
              </ReactMarkdown>
            </div>
          </div>

          <DialogFooter className="flex-col sm:flex-row gap-2">
            <Button
              variant="outline"
              onClick={handleCopy}
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
                onClick={() => setDialogOpen(false)}
                className="flex-1 sm:flex-initial"
              >
                Fechar
              </Button>

              {/* Botao Aplicar - so mostra se nao for consulta (consulta e apenas informativa) */}
              {action !== 'consultar' && onResult && (
                <Button
                  onClick={handleApply}
                  className="flex-1 sm:flex-initial"
                >
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  Aplicar no Campo
                </Button>
              )}
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import {
  FileText,
  Plus,
  Copy,
  Check,
  ChevronDown,
  Search,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';

export interface ClauseTemplate {
  id: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  usage_count?: number;
}

interface ClauseSuggesterProps {
  /** Templates disponíveis */
  templates?: ClauseTemplate[];
  /** Callback ao inserir cláusula */
  onInsert?: (clause: ClauseTemplate) => void;
  /** Callback ao buscar mais templates */
  onSearch?: (query: string) => void;
  /** Loading state */
  isLoading?: boolean;
  /** Indica que os templates vieram do fallback local (API offline) */
  isOffline?: boolean;
}

/**
 * Sugestor de Cláusulas Contextuais
 *
 * Sugere cláusulas baseadas no contexto do documento sendo editado.
 */
export function ClauseSuggester({
  templates = [],
  onInsert,
  onSearch,
  isLoading = false,
  isOffline = false,
}: ClauseSuggesterProps) {
  const [searchQuery, setSearchQuery] = React.useState('');
  const [selectedCategory, setSelectedCategory] = React.useState<string | null>(null);

  // Filtrar templates
  const filteredTemplates = React.useMemo(() => {
    let filtered = templates;

    // Filtro por categoria
    if (selectedCategory) {
      filtered = filtered.filter(t => t.category === selectedCategory);
    }

    // Filtro por busca
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(t =>
        t.title.toLowerCase().includes(query) ||
        t.content.toLowerCase().includes(query) ||
        t.tags.some(tag => tag.toLowerCase().includes(query))
      );
    }

    return filtered;
  }, [templates, selectedCategory, searchQuery]);

  // Categorias únicas
  const categories = React.useMemo(() => {
    const cats = new Set(templates.map(t => t.category));
    return Array.from(cats);
  }, [templates]);

  return (
    <div className="w-full">
      {/* Header com busca */}
      <div className="flex items-center gap-2 mb-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar cláusula..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        {searchQuery && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSearchQuery('')}
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Filtros por categoria */}
      {categories.length > 0 && (
        <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
          <Badge
            variant={selectedCategory === null ? 'default' : 'outline'}
            className="cursor-pointer shrink-0"
            onClick={() => setSelectedCategory(null)}
          >
            Todas
          </Badge>
          {categories.map(cat => (
            <Badge
              key={cat}
              variant={selectedCategory === cat ? 'default' : 'outline'}
              className="cursor-pointer shrink-0"
              onClick={() => setSelectedCategory(cat)}
            >
              {cat}
            </Badge>
          ))}
        </div>
      )}

      {/* Lista de templates */}
      <ScrollArea className="h-[400px] pr-4">
        {isLoading ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="h-8 w-8 mx-auto mb-2 opacity-30 animate-pulse" />
            <p className="text-sm">Carregando cláusulas...</p>
          </div>
        ) : filteredTemplates.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="h-8 w-8 mx-auto mb-2 opacity-30" />
            <p className="text-sm">Nenhuma cláusula encontrada</p>
            <p className="text-xs mt-1">
              Tente buscar por outro termo ou categoria
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredTemplates.map((template) => (
              <ClauseCard
                key={template.id}
                template={template}
                onInsert={onInsert}
              />
            ))}
          </div>
        )}
      </ScrollArea>

      {/* Footer */}
      <div className="border-t pt-3 mt-4 flex items-center justify-between text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <span>{filteredTemplates.length} cláusula(s)</span>
          {isOffline && (
            <span className="inline-flex items-center gap-1 text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded text-[10px] font-medium">
              offline
            </span>
          )}
        </div>
        <span>
          {templates.reduce((acc, t) => acc + (t.usage_count || 0), 0)} usos totais
        </span>
      </div>
    </div>
  );
}

interface ClauseCardProps {
  template: ClauseTemplate;
  onInsert?: (clause: ClauseTemplate) => void;
}

function ClauseCard({ template, onInsert }: ClauseCardProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);
  const [isInserted, setIsInserted] = React.useState(false);

  const handleInsert = () => {
    onInsert?.(template);
    setIsInserted(true);
    setTimeout(() => setIsInserted(false), 2000);
  };

  return (
    <div className="border rounded-lg p-4 hover:border-primary/50 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <FileText className="h-4 w-4 text-primary shrink-0" />
            <h4 className="font-medium text-sm truncate">{template.title}</h4>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="outline" className="text-xs">
              {template.category}
            </Badge>
            {template.tags.slice(0, 3).map(tag => (
              <span
                key={tag}
                className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded"
              >
                #{tag}
              </span>
            ))}
          </div>
        </div>
        <Button
          variant={isInserted ? 'default' : 'outline'}
          size="sm"
          className="shrink-0"
          onClick={handleInsert}
          disabled={isInserted}
        >
          {isInserted ? (
            <>
              <Check className="h-3 w-3 mr-1" />
              Inserida
            </>
          ) : (
            <>
              <Plus className="h-3 w-3 mr-1" />
              Inserir
            </>
          )}
        </Button>
      </div>

      {/* Preview do conteúdo */}
      <div className="relative">
        <div
          className={cn(
            'text-xs text-muted-foreground whitespace-pre-wrap bg-muted/50 rounded p-3 font-mono',
            !isExpanded && 'line-clamp-3'
          )}
        >
          {template.content}
        </div>
        {template.content.length > 200 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-xs text-primary hover:underline mt-1 flex items-center gap-1"
          >
            {isExpanded ? (
              <>
                Ver menos <ChevronDown className="h-3 w-3 rotate-180" />
              </>
            ) : (
              <>
                Ver mais <ChevronDown className="h-3 w-3" />
              </>
            )}
          </button>
        )}
      </div>

      {/* Usage count */}
      {template.usage_count !== undefined && (
        <div className="text-[10px] text-muted-foreground mt-2">
          {template.usage_count} uso(s)
        </div>
      )}
    </div>
  );
}

/**
 * Dialog para selecionar cláusulas
 */
interface ClauseSelectorDialogProps {
  /** Templates disponíveis */
  templates: ClauseTemplate[];
  /** Aberto? */
  open?: boolean;
  /** Callback open change */
  onOpenChange?: (open: boolean) => void;
  /** Callback ao inserir cláusula */
  onInsert?: (clause: ClauseTemplate) => void;
  /** Trigger customizado */
  trigger?: React.ReactNode;
}

export function ClauseSelectorDialog({
  templates,
  open,
  onOpenChange,
  onInsert,
  trigger,
}: ClauseSelectorDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline" size="sm">
            <FileText className="h-4 w-4 mr-2" />
            Inserir Cláusula
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>Inserir Cláusula</DialogTitle>
          <DialogDescription>
            Selecione uma cláusula do modelo para inserir no documento
          </DialogDescription>
        </DialogHeader>
        <div className="flex-1 overflow-hidden mt-4">
          <ClauseSuggester
            templates={templates}
            onInsert={(clause) => {
              onInsert?.(clause);
              onOpenChange?.(false);
            }}
          />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange?.(false)}>
            Cancelar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

/**
 * Hook para gerenciar biblioteca de cláusulas
 */
export function useClauseLibrary() {
  const [templates, setTemplates] = React.useState<ClauseTemplate[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [isOffline, setIsOffline] = React.useState(false);

  // Fallback templates — usados apenas quando a API falha
  const fallbackTemplates: ClauseTemplate[] = [
    {
      id: 'fallback-1',
      title: 'Cláusula de Confidencialidade',
      category: 'Contratos',
      tags: ['sigilo', 'confidencialidade'],
      content: 'CLÁUSULA X - DA CONFIDENCIALIDADE\n\nAs partes comprometem-se a manter sigilo...',
      usage_count: 42,
    },
    {
      id: 'fallback-2',
      title: 'Cláusula de Rescisão',
      category: 'Contratos',
      tags: ['rescisão', 'término'],
      content: 'CLÁUSULA Y - DA RESCISÃO\n\nO presente contrato poderá ser rescindido...',
      usage_count: 38,
    },
  ];

  // Carregar templates via API (POST /api/v1/copilot/suggest/)
  const loadTemplates = React.useCallback(async (documentType?: string) => {
    setIsLoading(true);
    setIsOffline(false);
    try {
      const { default: api } = await import('@/lib/api');
      const response = await api.post('/api/v1/intelligent-assistant/copilot/suggest/', {
        current_text: '',
        current_fragment: documentType || 'cláusula contratual',
        document_type: documentType,
        enabled_types: ['clause'],
        max_suggestions: 20,
      });

      const suggestions = response.data?.suggestions ?? [];
      if (suggestions.length > 0) {
        const mapped: ClauseTemplate[] = suggestions.map((s: Record<string, unknown>) => ({
          id: (s.id as string) || crypto.randomUUID(),
          title: (s.title as string) || 'Cláusula',
          content: (s.content as string) || '',
          category: (s.metadata as Record<string, unknown>)?.category as string || (s.type as string) || 'Geral',
          tags: Array.isArray((s.metadata as Record<string, unknown>)?.tags)
            ? (s.metadata as Record<string, unknown>)?.tags as string[]
            : [(s.source as string) || 'ia'].filter(Boolean),
          usage_count: typeof s.relevance_score === 'number'
            ? Math.round((s.relevance_score as number) * 100)
            : 0,
        }));
        setTemplates(mapped);
      } else {
        // API returned empty — use fallback
        setTemplates(fallbackTemplates);
        setIsOffline(true);
      }
    } catch {
      // API unreachable — fallback to local templates
      setTemplates(fallbackTemplates);
      setIsOffline(true);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Salvar novo template
  const saveTemplate = React.useCallback(async (template: Omit<ClauseTemplate, 'id'>) => {
    try {
      const { default: api } = await import('@/lib/api');
      await api.post('/api/v1/intelligent-assistant/copilot/suggest/', {
        current_text: template.content,
        current_fragment: template.title,
        document_type: template.category,
        enabled_types: ['clause'],
      });
    } catch {
      console.warn('Falha ao salvar template via API');
    }
  }, []);

  // Deletar template
  const deleteTemplate = React.useCallback(async (id: string) => {
    setTemplates(prev => prev.filter(t => t.id !== id));
  }, []);

  return {
    templates,
    isLoading,
    isOffline,
    loadTemplates,
    saveTemplate,
    deleteTemplate,
  };
}

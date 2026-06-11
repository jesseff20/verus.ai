'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import {
  BookOpen,
  FileText,
  MessageSquare,
  Scale,
  Clock,
  Sparkles,
  Check,
  X,
  ChevronRight,
  Lightbulb,
  BookOpenCheck,
  Gavel,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import type { CopilotSuggestion, CopilotSuggestionType } from '@/hooks/use-legal-copilot';
import { SLASH_COMMANDS } from '@/hooks/use-legal-copilot';

interface LegalCopilotPopupProps {
  /** Sugestões atuais */
  suggestions: CopilotSuggestion[];
  /** Loading state */
  isLoading?: boolean;
  /** Posição do popup (x, y) */
  position?: { x: number; y: number };
  /** Callback ao aceitar sugestão */
  onAccept?: (suggestion: CopilotSuggestion) => void;
  /** Callback ao descartar sugestão */
  onDismiss?: (suggestionId: string) => void;
  /** Callback ao fechar popup */
  onClose?: () => void;
  /** Sugestão selecionada (índice) */
  selectedIndex?: number;
  /** Mostrar comandos slash */
  showSlashCommands?: boolean;
}

/**
 * Ícone por tipo de sugestão
 */
function getSuggestionIcon(type: CopilotSuggestionType) {
  switch (type) {
    case 'citation':
      return <BookOpen className="h-4 w-4" />;
    case 'jurisprudence':
      return <Gavel className="h-4 w-4" />;
    case 'clause':
      return <FileText className="h-4 w-4" />;
    case 'deadline':
      return <Clock className="h-4 w-4" />;
    case 'argument':
      return <MessageSquare className="h-4 w-4" />;
    case 'definition':
      return <Lightbulb className="h-4 w-4" />;
    case 'statute':
      return <Scale className="h-4 w-4" />;
    case 'correction':
      return <Sparkles className="h-4 w-4" />;
    default:
      return <Sparkles className="h-4 w-4" />;
  }
}

/**
 * Cor do badge por tipo
 */
function getSuggestionBadgeColor(type: CopilotSuggestionType) {
  switch (type) {
    case 'citation':
      return 'bg-blue-100 text-blue-700 border-blue-300';
    case 'jurisprudence':
      return 'bg-purple-100 text-purple-700 border-purple-300';
    case 'clause':
      return 'bg-green-100 text-green-700 border-green-300';
    case 'deadline':
      return 'bg-orange-100 text-orange-700 border-orange-300';
    case 'argument':
      return 'bg-indigo-100 text-indigo-700 border-indigo-300';
    case 'definition':
      return 'bg-yellow-100 text-yellow-700 border-yellow-300';
    case 'statute':
      return 'bg-red-100 text-red-700 border-red-300';
    case 'correction':
      return 'bg-pink-100 text-pink-700 border-pink-300';
    default:
      return 'bg-gray-100 text-gray-700 border-gray-300';
  }
}

/**
 * Popup do Copilot Jurídico
 */
export function LegalCopilotPopup({
  suggestions,
  isLoading = false,
  position,
  onAccept,
  onDismiss,
  onClose,
  selectedIndex = -1,
  showSlashCommands = false,
}: LegalCopilotPopupProps) {
  const scrollRef = React.useRef<HTMLDivElement>(null);

  // Scroll para sugestão selecionada
  React.useEffect(() => {
    if (selectedIndex >= 0 && scrollRef.current) {
      const selectedElement = scrollRef.current.children[selectedIndex] as HTMLElement;
      if (selectedElement) {
        selectedElement.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }
    }
  }, [selectedIndex]);

  // Fechar ao clicar fora
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (scrollRef.current && !scrollRef.current.contains(event.target as Node)) {
        onClose?.();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  // Renderizar comandos slash
  if (showSlashCommands) {
    return (
      <div
        className="fixed z-50 w-80 rounded-lg border bg-popover p-2 shadow-lg animate-in fade-in zoom-in-95"
        style={{
          left: position?.x,
          top: position?.y,
        }}
        role="menu"
      >
        <div className="mb-2 px-2 text-xs font-medium text-muted-foreground">
          Comandos
        </div>
        <ScrollArea className="h-[300px]">
          <div ref={scrollRef} className="space-y-1">
            {Object.values(SLASH_COMMANDS).map((cmd, index) => (
              <button
                key={cmd.command}
                className={cn(
                  'w-full flex items-center justify-between rounded-md px-3 py-2 text-left text-sm hover:bg-accent transition-colors',
                  index === selectedIndex && 'bg-accent'
                )}
                onClick={() => onAccept?.({
                  id: cmd.command,
                  type: cmd.type,
                  title: cmd.command,
                  content: cmd.description,
                  relevanceScore: 1,
                })}
                role="menuitem"
              >
                <div className="flex items-center gap-2">
                  <span className="text-primary font-mono text-xs">/{cmd.command}</span>
                  <span className="text-muted-foreground">{cmd.description}</span>
                </div>
                {cmd.shortcut && (
                  <Badge variant="outline" className="text-xs">
                    {cmd.shortcut}
                  </Badge>
                )}
              </button>
            ))}
          </div>
        </ScrollArea>
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div
        className="fixed z-50 w-96 rounded-lg border bg-popover p-4 shadow-lg"
        style={{
          left: position?.x,
          top: position?.y,
        }}
      >
        <div className="flex items-center gap-2 text-muted-foreground">
          <Sparkles className="h-4 w-4 animate-spin" />
          <span className="text-sm">Copilot buscando sugestões...</span>
        </div>
      </div>
    );
  }

  // Sem sugestões
  if (suggestions.length === 0) {
    return null;
  }

  // Renderizar sugestões
  return (
    <div
      className="fixed z-50 w-96 rounded-lg border bg-popover shadow-lg animate-in fade-in zoom-in-95"
      style={{
        left: position?.x,
        top: position?.y,
        maxHeight: '400px',
      }}
      role="menu"
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-2">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium">Sugestões do Copilot</span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0"
          onClick={onClose}
        >
          <X className="h-3 w-3" />
        </Button>
      </div>

      {/* Lista de sugestões */}
      <ScrollArea className="max-h-[340px]">
        <div ref={scrollRef} className="p-2">
          {suggestions.map((suggestion, index) => (
            <div
              key={suggestion.id}
              className={cn(
                'group relative rounded-md p-3 hover:bg-accent transition-colors cursor-pointer',
                index === selectedIndex && 'bg-accent'
              )}
              onClick={() => onAccept?.(suggestion)}
              role="menuitem"
            >
              {/* Tipo e título */}
              <div className="flex items-start justify-between gap-2 mb-1">
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      'flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium',
                      getSuggestionBadgeColor(suggestion.type)
                    )}
                  >
                    {getSuggestionIcon(suggestion.type)}
                    {suggestion.type}
                  </span>
                </div>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDismiss?.(suggestion.id);
                    }}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 text-primary"
                    onClick={(e) => {
                      e.stopPropagation();
                      onAccept?.(suggestion);
                    }}
                  >
                    <Check className="h-3 w-3" />
                  </Button>
                </div>
              </div>

              {/* Conteúdo */}
              <h4 className="text-sm font-medium text-foreground mb-1">
                {suggestion.title}
              </h4>
              <p className="text-xs text-muted-foreground line-clamp-2">
                {suggestion.content}
              </p>

              {/* Fonte e relevância */}
              <div className="flex items-center justify-between mt-2">
                {suggestion.source && (
                  <span className="text-[10px] text-muted-foreground">
                    Fonte: {suggestion.source}
                  </span>
                )}
                <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
                  <span>Relevância:</span>
                  <div className="flex items-center gap-1">
                    <div className="w-16 h-1.5 rounded-full bg-muted overflow-hidden">
                      <div
                        className="h-full bg-primary rounded-full"
                        style={{ width: `${suggestion.relevanceScore * 100}%` }}
                      />
                    </div>
                    <span>{Math.round(suggestion.relevanceScore * 100)}%</span>
                  </div>
                </div>
              </div>

              {/* Indicador de seleção */}
              {index === selectedIndex && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-primary rounded-r" />
              )}
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* Footer com atalhos */}
      <div className="border-t px-4 py-2 flex items-center justify-between text-[10px] text-muted-foreground">
        <div className="flex items-center gap-2">
          <kbd className="rounded border bg-muted px-1.5 py-0.5">↑↓</kbd>
          <span>Navegar</span>
          <kbd className="rounded border bg-muted px-1.5 py-0.5">Enter</kbd>
          <span>Selecionar</span>
          <kbd className="rounded border bg-muted px-1.5 py-0.5">Esc</kbd>
          <span>Fechar</span>
        </div>
        <span>{suggestions.length} sugestão(ões)</span>
      </div>
    </div>
  );
}

/**
 * Painel lateral do Copilot (para sugestões persistentes)
 */
export function LegalCopilotPanel({
  suggestions,
  onAccept,
  onDismiss,
}: {
  suggestions: CopilotSuggestion[];
  onAccept?: (suggestion: CopilotSuggestion) => void;
  onDismiss?: (suggestionId: string) => void;
}) {
  return (
    <div className="w-80 border-l bg-background h-full overflow-hidden flex flex-col">
      {/* Header */}
      <div className="border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          <h3 className="font-semibold">Copilot Jurídico</h3>
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          Sugestões inteligentes enquanto você digita
        </p>
      </div>

      {/* Lista de sugestões */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-3">
          {suggestions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Sparkles className="h-8 w-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">
                Digite para receber sugestões do Copilot
              </p>
            </div>
          ) : (
            suggestions.map((suggestion) => (
              <div
                key={suggestion.id}
                className="rounded-lg border p-3 hover:border-primary/50 transition-colors"
              >
                <div className="flex items-center justify-between mb-2">
                  <Badge
                    variant="outline"
                    className={cn(
                      'text-xs',
                      getSuggestionBadgeColor(suggestion.type)
                    )}
                  >
                    {getSuggestionIcon(suggestion.type)}
                    <span className="ml-1">{suggestion.type}</span>
                  </Badge>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0"
                      onClick={() => onDismiss?.(suggestion.id)}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                    <Button
                      variant="default"
                      size="sm"
                      className="h-7 w-7 p-0"
                      onClick={() => onAccept?.(suggestion)}
                    >
                      <Check className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
                <h4 className="text-sm font-medium mb-1">
                  {suggestion.title}
                </h4>
                <p className="text-xs text-muted-foreground line-clamp-3">
                  {suggestion.content}
                </p>
                {suggestion.source && (
                  <p className="text-[10px] text-muted-foreground mt-2">
                    Fonte: {suggestion.source}
                  </p>
                )}
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

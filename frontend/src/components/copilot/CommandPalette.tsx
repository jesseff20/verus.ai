'use client';

import * as React from 'react';
import {
  Gavel,
  FileText,
  Lightbulb,
  Users,
  Building2,
  Send,
  Calendar,
  FileBox,
  Search,
  ChevronRight,
  X,
  Scale,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';

interface CommandInfo {
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  examples: string[];
}

const COMMANDS: CommandInfo[] = [
  {
    name: 'jurisprudencia',
    description: 'Pesquisa jurisprudência e precedentes',
    icon: Gavel,
    color: 'text-blue-500',
    examples: [
      '@jurisprudencia dano moral transporte público',
      '@jurisprudencia prescrição penal',
    ],
  },
  {
    name: 'documento',
    description: 'Gerencia versões de documentos',
    icon: FileText,
    color: 'text-green-500',
    examples: [
      '@documento abc123 versoes',
      '@documento abc123 diff 1.0.0 1.1.0',
    ],
  },
  {
    name: 'argumentos',
    description: 'Busca argumentos na biblioteca viva',
    icon: Lightbulb,
    color: 'text-yellow-500',
    examples: [
      '@argumentos prescrição',
      '@argumentos legítima defesa',
    ],
  },
  {
    name: 'colaboracao',
    description: 'Gerencia sessões colaborativas',
    icon: Users,
    color: 'text-purple-500',
    examples: [
      '@colaboracao listar',
      '@colaboracao criar abc123 legal',
    ],
  },
  {
    name: 'tribunal',
    description: 'Integração com tribunais',
    icon: Building2,
    color: 'text-orange-500',
    examples: [
      '@tribunal listar',
      '@tribunal sincronizar 0000000-00.2024.8.26.0000',
    ],
  },
  {
    name: 'caso',
    description: 'Gerencia casos e processos',
    icon: FileBox,
    color: 'text-cyan-500',
    examples: [
      '@caso listar',
      '@caso detalhes abc123',
    ],
  },
  {
    name: 'prazo',
    description: 'Consulta prazos processuais',
    icon: Calendar,
    color: 'text-pink-500',
    examples: [
      '@prazo listar',
      '@prazo proximos',
    ],
  },
  {
    name: 'modelo',
    description: 'Busca modelos de peças',
    icon: FileText,
    color: 'text-indigo-500',
    examples: [
      '@modelo petição inicial',
      '@modelo contestação',
    ],
  },
  {
    name: 'resumo',
    description: 'Gera resumo de documentos com IA',
    icon: FileText,
    color: 'text-emerald-500',
    examples: [
      '@resumo [cole o texto aqui]',
    ],
  },
  {
    name: 'traduzir',
    description: 'Traduzir textos jurídicos',
    icon: Send,
    color: 'text-violet-500',
    examples: [
      '@traduzir [texto] para inglês',
      '@traduzir [texto] para espanhol',
    ],
  },
  {
    name: 'revisar',
    description: 'Revisar peças jurídicas',
    icon: FileText,
    color: 'text-rose-500',
    examples: [
      '@revisar [cole a petição]',
    ],
  },
  {
    name: 'citar',
    description: 'Gerar citações e referências',
    icon: Gavel,
    color: 'text-amber-500',
    examples: [
      '@citar dano moral',
      '@citar prescrição penal',
    ],
  },
  {
    name: 'expandir',
    description: 'Expandir tópicos em texto completo',
    icon: FileText,
    color: 'text-teal-500',
    examples: [
      '@expandir 1. Introdução 2. Fundamentos 3. Pedidos',
    ],
  },
  {
    name: 'peticao',
    description: 'Gera ou analisa petições e peças processuais',
    icon: FileText,
    color: 'text-sky-500',
    examples: [
      '@peticao inicial trabalhista',
      '@peticao contestação cível',
    ],
  },
  {
    name: 'blueprint',
    description: 'Lista e gera documentos jurídicos via gerador inteligente',
    icon: FileText,
    color: 'text-lime-500',
    examples: [
      '@blueprint listar',
      '@blueprint petição inicial',
    ],
  },
  {
    name: 'legislacao',
    description: 'Pesquisa legislação e normas vigentes',
    icon: Scale,
    color: 'text-red-500',
    examples: [
      '@legislacao CDC artigo 14',
      '@legislacao CLT férias',
    ],
  },
  {
    name: 'simulacao',
    description: 'Informações sobre simulações jurídicas disponíveis',
    icon: Scale,
    color: 'text-fuchsia-500',
    examples: [
      '@simulação júri',
      '@simulação sentença',
    ],
  },
];

interface CommandPaletteProps {
  /** Query atual após @ */
  query: string;
  /** Callback quando comando é selecionado */
  onSelect: (command: string, fullQuery: string) => void;
  /** Callback para fechar o palette */
  onClose: () => void;
  /** Posição do palette */
  position?: { x: number; y: number };
}

/**
 * CommandPalette - Seletor de comandos @
 *
 * Mostra lista de comandos disponíveis quando usuário digita @
 */
export function CommandPalette({
  query,
  onSelect,
  onClose,
  position,
}: CommandPaletteProps) {
  const [selectedIndex, setSelectedIndex] = React.useState(0);
  const containerRef = React.useRef<HTMLDivElement>(null);

  // Filtrar comandos baseado na query
  const filteredCommands = React.useMemo(() => {
    if (!query) return COMMANDS;
    const q = query.toLowerCase();
    return COMMANDS.filter(
      (cmd) =>
        cmd.name.includes(q) ||
        cmd.description.toLowerCase().includes(q)
    );
  }, [query]);

  // Resetar seleção quando query mudar
  React.useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Navegação com teclado
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < filteredCommands.length - 1 ? prev + 1 : 0
        );
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev > 0 ? prev - 1 : filteredCommands.length - 1
        );
      } else if (e.key === 'Enter' && filteredCommands.length > 0) {
        e.preventDefault();
        const selected = filteredCommands[selectedIndex];
        if (selected) {
          onSelect(selected.name, '');
        }
      } else if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [filteredCommands.length, selectedIndex, onSelect, onClose]);

  // Ajustar posição para caber na tela
  const style = position
    ? {
        position: 'fixed' as const,
        left: Math.min(position.x, window.innerWidth - 320),
        top: Math.min(position.y, window.innerHeight - 400),
      }
    : undefined;

  return (
    <div
      ref={containerRef}
      style={style}
      className={cn(
        'z-50 w-80 rounded-lg border bg-popover shadow-lg',
        'animate-in fade-in-0 zoom-in-95'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b px-3 py-2">
        <div className="flex items-center gap-2">
          <Search className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Comandos</span>
        </div>
        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onClose}>
          <X className="h-3 w-3" />
        </Button>
      </div>

      {/* Lista de comandos */}
      <ScrollArea className="h-[320px]">
        <div className="p-2">
          {filteredCommands.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground text-sm">
              Nenhum comando encontrado
            </div>
          ) : (
            filteredCommands.map((cmd, index) => (
              <button
                key={cmd.name}
                className={cn(
                  'w-full text-left p-3 rounded-md transition-colors',
                  index === selectedIndex
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-muted'
                )}
                onClick={() => onSelect(cmd.name, '')}
                onMouseEnter={() => setSelectedIndex(index)}
              >
                <div className="flex items-start gap-3">
                  <cmd.icon
                    className={cn('h-5 w-5 shrink-0 mt-0.5', cmd.color)}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">@{cmd.name}</span>
                      <ChevronRight className="h-3 w-3 text-muted-foreground" />
                    </div>
                    <p
                      className={cn(
                        'text-xs mt-0.5',
                        index === selectedIndex
                          ? 'text-primary-foreground/80'
                          : 'text-muted-foreground'
                      )}
                    >
                      {cmd.description}
                    </p>
                    {cmd.examples.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {cmd.examples.slice(0, 2).map((ex, i) => (
                          <Badge
                            key={i}
                            variant={index === selectedIndex ? 'secondary' : 'outline'}
                            className="text-[10px] px-1.5 py-0 h-auto font-mono"
                          >
                            {ex}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Footer */}
      <div className="border-t px-3 py-2 text-xs text-muted-foreground">
        <span className="flex items-center gap-2">
          <kbd className="px-1.5 py-0.5 rounded bg-muted font-mono">↑↓</kbd>
          navegar
          <kbd className="px-1.5 py-0.5 rounded bg-muted font-mono ml-2">Enter</kbd>
          selecionar
          <kbd className="px-1.5 py-0.5 rounded bg-muted font-mono ml-2">Esc</kbd>
          fechar
        </span>
      </div>
    </div>
  );
}

// Componente Button local para evitar import circular
function Button({
  variant,
  size,
  className,
  onClick,
  children,
}: {
  variant: string;
  size: string;
  className?: string;
  onClick?: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center rounded-md',
        variant === 'ghost' && 'hover:bg-muted',
        size === 'icon' && 'h-8 w-8',
        className
      )}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

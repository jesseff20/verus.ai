'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import {
  Home,
  Gavel,
  FileText,
  Scale,
  Search,
  BookMarked,
  Bot,
  Settings,
  Users,
  LayoutTemplate,
  Brain,
  BarChart2,
  Library,
} from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogTitle } from '@/components/ui/dialog';
import { VisuallyHidden } from '@radix-ui/react-visually-hidden';
import { Input } from '@/components/ui/input';

interface SearchItem {
  title: string;
  href: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  keywords: string[];
}

const NAV_ITEMS: SearchItem[] = [
  {
    title: 'Dashboard',
    href: '/dashboard',
    description: 'Visão geral e estatísticas',
    icon: Home,
    keywords: ['inicio', 'home', 'dashboard', 'resumo', 'stats'],
  },
  {
    title: 'Gerador de Peças',
    href: '/dashboard/intelligent-assistant',
    description: 'Gerar peças processuais com IA',
    icon: Gavel,
    keywords: ['peça', 'gerador', 'ia', 'assistente', 'gerar', 'documento'],
  },
  {
    title: 'Peças Processuais',
    href: '/dashboard/documents',
    description: 'Gerenciar documentos jurídicos',
    icon: FileText,
    keywords: ['documento', 'peça', 'processual', 'arquivo'],
  },
  {
    title: 'Casos Jurídicos',
    href: '/dashboard/processos',
    description: 'Gestão de processos e casos',
    icon: Scale,
    keywords: ['caso', 'processo', 'juridico', 'cliente'],
  },
  {
    title: 'Prazos',
    href: '/dashboard/processos/prazos',
    description: 'Controle de prazos processuais',
    icon: Scale,
    keywords: ['prazo', 'deadline', 'data', 'vencimento'],
  },
  {
    title: 'Jurisprudência',
    href: '/dashboard/jurisprudencia',
    description: 'Pesquisa de precedentes e jurisprudência',
    icon: Search,
    keywords: ['jurisprudencia', 'precedente', 'stj', 'stf', 'tribunal'],
  },
  {
    title: 'Base Jurídica',
    href: '/dashboard/knowledge-base',
    description: 'Documentos indexados para consulta',
    icon: BookMarked,
    keywords: ['base', 'conhecimento', 'kb', 'indexado', 'juridica'],
  },
  {
    title: 'Biblioteca de Argumentos',
    href: '/dashboard/legal-library',
    description: 'Argumentos jurídicos reutilizáveis',
    icon: Library,
    keywords: ['argumento', 'biblioteca', 'tese', 'fundamento'],
  },
  {
    title: 'Copilot',
    href: '/dashboard/copilot',
    description: 'Assistente de procuradoria conversacional',
    icon: Bot,
    keywords: ['copilot', 'chat', 'ia', 'conversa', 'assistente'],
  },
  {
    title: 'Agentes IA',
    href: '/dashboard/agents',
    description: 'Gerenciar agentes de IA',
    icon: Brain,
    keywords: ['agente', 'ia', 'prompt', 'llm'],
  },
  {
    title: 'Analytics',
    href: '/dashboard/analytics',
    description: 'Relatórios e métricas de uso',
    icon: BarChart2,
    keywords: ['analytics', 'relatorio', 'metrica', 'estatistica'],
  },
  {
    title: 'Usuários',
    href: '/dashboard/users',
    description: 'Gerenciar usuários do sistema',
    icon: Users,
    keywords: ['usuario', 'equipe', 'membro', 'acesso'],
  },
  {
    title: 'Templates',
    href: '/dashboard/templates',
    description: 'Templates de documentos',
    icon: LayoutTemplate,
    keywords: ['template', 'modelo', 'formulario'],
  },
  {
    title: 'Configurações',
    href: '/dashboard/settings',
    description: 'Configurações do sistema',
    icon: Settings,
    keywords: ['config', 'configuracao', 'preferencia', 'ajuste'],
  },
];

function normalize(str: string): string {
  return str
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');
}

function scoreItem(item: SearchItem, query: string): number {
  const q = normalize(query);
  const title = normalize(item.title);
  const desc = normalize(item.description);
  const kws = item.keywords.map(normalize).join(' ');

  if (title.startsWith(q)) return 3;
  if (title.includes(q)) return 2;
  if (kws.includes(q) || desc.includes(q)) return 1;
  return 0;
}

export function GlobalSearch() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(0);
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);

  const filtered = query.trim()
    ? NAV_ITEMS.filter((item) => scoreItem(item, query) > 0).sort(
        (a, b) => scoreItem(b, query) - scoreItem(a, query)
      )
    : NAV_ITEMS.slice(0, 6);

  const navigate = useCallback(
    (href: string) => {
      setOpen(false);
      setQuery('');
      router.push(href);
    },
    [router]
  );

  // Global Ctrl+K / Cmd+K listener
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  // Arrow key navigation + Enter inside dialog
  useEffect(() => {
    if (!open) return;

    const handler = (e: KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelected((prev) => Math.min(prev + 1, filtered.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelected((prev) => Math.max(prev - 1, 0));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filtered[selected]) navigate(filtered[selected].href);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open, filtered, selected, navigate]);

  // Reset selection on query change
  useEffect(() => {
    setSelected(0);
  }, [query]);

  // Focus input when opened
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setQuery('');
    }
  }, [open]);

  return (
    <>
      {/* Trigger button */}
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 px-3 h-9 rounded-md border border-input bg-background text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
        title="Busca global (Ctrl+K)"
      >
        <Search className="h-3.5 w-3.5" />
        <span className="hidden sm:inline">Buscar...</span>
        <kbd className="hidden sm:inline pointer-events-none select-none rounded border border-border bg-muted px-1 font-mono text-[10px] font-medium text-muted-foreground">
          ⌘K
        </kbd>
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="p-0 overflow-hidden max-w-[calc(100vw-2rem)] sm:max-w-lg gap-0">
          <VisuallyHidden>
            <DialogTitle>Busca global</DialogTitle>
          </VisuallyHidden>
          <DialogDescription className="sr-only">Buscar páginas e funcionalidades do sistema</DialogDescription>
          {/* Search input */}
          <div className="flex items-center border-b px-3">
            <Search className="h-4 w-4 mr-2 text-muted-foreground shrink-0" />
            <Input
              ref={inputRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Buscar páginas e funcionalidades..."
              className="border-0 shadow-none focus-visible:ring-0 h-12 text-sm"
            />
          </div>

          {/* Results */}
          <div className="overflow-y-auto max-h-[60vh] p-2">
            {filtered.length === 0 ? (
              <p className="text-center text-sm text-muted-foreground py-8">
                Nenhum resultado encontrado para &quot;{query}&quot;
              </p>
            ) : (
              <>
                {!query.trim() && (
                  <p className="text-xs text-muted-foreground px-2 pb-1">
                    Páginas frequentes
                  </p>
                )}
                {filtered.map((item, i) => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={item.href}
                      onClick={() => navigate(item.href)}
                      onMouseEnter={() => setSelected(i)}
                      className={`w-full flex items-center gap-3 rounded-md px-3 py-2 text-left transition-colors ${
                        selected === i
                          ? 'bg-accent text-accent-foreground'
                          : 'hover:bg-accent/50'
                      }`}
                    >
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border bg-background">
                        <Icon className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium leading-none truncate">
                          {item.title}
                        </p>
                        <p className="text-xs text-muted-foreground mt-0.5 truncate">
                          {item.description}
                        </p>
                      </div>
                    </button>
                  );
                })}
              </>
            )}
          </div>

          {/* Footer hint */}
          <div className="border-t px-3 py-2 flex items-center gap-4 text-xs text-muted-foreground">
            <span><kbd className="font-mono">↑↓</kbd> navegar</span>
            <span><kbd className="font-mono">↵</kbd> abrir</span>
            <span><kbd className="font-mono">Esc</kbd> fechar</span>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

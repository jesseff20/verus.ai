'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import Image from 'next/image';
import { cn } from '@/lib/utils';
import { useBrandSettings } from '@/hooks/use-brand-settings';
import { usePermissions, Permission } from '@/hooks/use-permissions';
import { useAuth } from '@/hooks/use-auth';
import {
  FileText,
  Home,
  Settings,
  Users,
  LayoutTemplate,
  Palette,
  Shield,
  UserCog,
  Calendar,
  Clock,
  Bot,
  Scale,
  Gavel,
  Vote,
  Search,
  BookMarked,
  BarChart3,
  FlaskConical,
  Bell,
  Landmark,
  Building,
  Swords,
  ShieldCheck,
  DollarSign,
  Calculator,
  FileCheck,
  PenTool,
  Receipt,
  ClipboardList,
  Database,
  Brain,
  Eye,
  UsersRound,
  Upload,
  Download,
  GitBranch,
  Mail,
  MessageSquare,
  FolderOpen,
  Kanban,
  Timer,
  TrendingUp,
  FileEdit,
  ScanLine,
  Briefcase,
  AlertTriangle,
  Workflow,
  Activity,
} from 'lucide-react';
import { Separator } from '@/components/ui/separator';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
  children?: NavItem[];
  /** Permissão necessária para ver este item (ANY) */
  requiredPermissions?: Permission[];
  /** Abre em nova aba (links externos) */
  external?: boolean;
}

// Função para gerar os itens de navegação baseado na role
const getNavItems = (isAnalyst: boolean): NavItem[] => {
  const items: NavItem[] = [
    // ── Dashboard (direct link, no submenu) ──
    {
      title: 'Dashboard',
      href: '/dashboard',
      icon: Home,
      requiredPermissions: ['dashboard.view'],
    },

    // ── Fluxos de Trabalho ──
    {
      title: 'Fluxos de Trabalho',
      href: '/dashboard/fluxos',
      icon: Workflow,
      requiredPermissions: ['dashboard.view'],
      children: [
        {
          title: 'Templates',
          href: '/dashboard/fluxos',
          icon: Workflow,
          requiredPermissions: ['dashboard.view'],
        },
        {
          title: 'Execuções',
          href: '/dashboard/execucoes',
          icon: Activity,
          requiredPermissions: ['dashboard.view'],
        },
        {
          title: 'Minhas Tarefas',
          href: '/dashboard/minhas-tarefas',
          icon: Briefcase,
          requiredPermissions: ['dashboard.view'],
        },
        {
          title: 'Solicitações',
          href: '/dashboard/solicitacoes',
          icon: ClipboardList,
          requiredPermissions: ['dashboard.view'],
        },
      ],
    },

    // ── Processos ──
    {
      title: 'Processos',
      href: '/dashboard/processos',
      icon: Scale,
      requiredPermissions: ['documents.view_own', 'documents.view_all'],
      children: [
        {
          title: 'Meus Processos',
          href: '/dashboard/processos',
          icon: Briefcase,
          requiredPermissions: ['documents.view_own', 'documents.view_all'],
        },
        {
          title: 'Prazos',
          href: '/dashboard/processos/prazos',
          icon: Clock,
          requiredPermissions: ['documents.view_own', 'documents.view_all'],
        },
        {
          title: 'Calendário',
          href: '/dashboard/processos/calendario',
          icon: Calendar,
          requiredPermissions: ['documents.view_own', 'documents.view_all'],
        },
        {
          title: 'Kanban de Tarefas',
          href: '/dashboard/kanban',
          icon: Kanban,
          requiredPermissions: ['documents.view_own', 'documents.view_all'],
        },
        {
          title: 'Workflows',
          href: '/dashboard/workflows',
          icon: GitBranch,
          requiredPermissions: ['documents.view_own', 'documents.view_all'],
        },
        {
          title: 'Prazos Inteligentes',
          href: '/dashboard/prazos-inteligentes',
          icon: Brain,
          badge: 'IA',
          requiredPermissions: ['documents.view_own', 'documents.view_all'],
        },
      ],
    },

    // Módulo Clientes & CRM removido — não aplicável a procuradorias

    // ── Documentos ──
    {
      title: 'Documentos',
      href: '/dashboard/documents',
      icon: FolderOpen,
      requiredPermissions: ['documents.view_own', 'documents.view_all'],
      children: [
        {
          title: 'Gerador de Peças',
          href: '/dashboard/intelligent-assistant',
          icon: Gavel,
          badge: 'IA',
          requiredPermissions: ['assistant.use'],
        },
        {
          title: 'Peças Processuais',
          href: '/dashboard/documents',
          icon: FileText,
          requiredPermissions: ['documents.view_own', 'documents.view_all'],
        },
        {
          title: 'Protocolo Eletrônico',
          href: '/dashboard/protocolo',
          icon: FileCheck,
          requiredPermissions: ['documents.view_own', 'documents.view_all'],
        },
        {
          title: 'Contratos Administrativos',
          href: '/dashboard/contratos',
          icon: ClipboardList,
          requiredPermissions: ['documents.view_own', 'documents.view_all'],
        },
        {
          title: 'Assinatura Digital',
          href: '/dashboard/assinatura-digital',
          icon: PenTool,
          requiredPermissions: ['documents.view_own', 'documents.view_all'],
        },
        {
          title: 'Templates E-mail',
          href: '/dashboard/email-templates',
          icon: Mail,
          requiredPermissions: ['documents.view_own', 'documents.view_all'],
        },
        {
          title: 'OCR de Documentos',
          href: '/dashboard/ocr',
          icon: ScanLine,
          requiredPermissions: ['documents.view_own', 'documents.view_all'],
        },
      ],
    },

    // ── Inteligência Jurídica ──
    {
      title: 'Inteligência Jurídica',
      href: '/dashboard/copilot',
      icon: Bot,
      requiredPermissions: ['assistant.use'],
      children: [
        {
          title: 'Copilot',
          href: '/dashboard/copilot',
          icon: Bot,
          badge: 'IA',
          requiredPermissions: ['assistant.use'],
        },
        {
          title: 'Análise de Decisão Judicial',
          href: '/dashboard/simulations',
          icon: FlaskConical,
          badge: 'IA',
          requiredPermissions: ['assistant.use'],
          children: [
            {
              title: 'Histórico',
              href: '/dashboard/simulations',
              icon: Clock,
              requiredPermissions: ['assistant.use'],
            },
            {
              title: 'Previsão de Sentença',
              href: '/dashboard/simulations/judge',
              icon: Scale,
              requiredPermissions: ['assistant.use'],
            },
            {
              title: '2ª Instância / Acórdão',
              href: '/dashboard/simulations/acordao',
              icon: Landmark,
              requiredPermissions: ['assistant.use'],
            },
            {
              title: 'STJ',
              href: '/dashboard/simulations/stj',
              icon: Building,
              requiredPermissions: ['assistant.use'],
            },
            {
              title: 'STF',
              href: '/dashboard/simulations/stf',
              icon: Landmark,
              requiredPermissions: ['assistant.use'],
            },
            {
              title: 'Turma Recursal / JEC',
              href: '/dashboard/simulations/jec',
              icon: Gavel,
              requiredPermissions: ['assistant.use'],
            },
          ],
        },
        {
          title: 'Jurisprudência',
          href: '/dashboard/jurisprudencia',
          icon: Search,
          requiredPermissions: ['dashboard.view'],
        },
        {
          title: 'Consulta CNJ / DataJud',
          href: '/dashboard/datajud',
          icon: Database,
          requiredPermissions: ['documents.view_own', 'documents.view_all'],
        },
        {
          title: 'Acompanhamento Tribunal',
          href: '/dashboard/tribunal-push',
          icon: Bell,
          requiredPermissions: ['documents.view_own', 'documents.view_all'],
        },
        {
          title: 'Agentes Jurídicos',
          href: '/dashboard/agents',
          icon: Bot,
          badge: 'IA',
          requiredPermissions: ['agents.view'],
        },
      ],
    },

    // Módulo Financeiro removido — não aplicável a procuradorias

    // ── Base de Conhecimento ──
    {
      title: 'Base de Conhecimento',
      href: '/dashboard/knowledge-base',
      icon: BookMarked,
      requiredPermissions: ['knowledge_base.view'],
      children: [
        {
          title: 'Base Jurídica',
          href: '/dashboard/knowledge-base',
          icon: BookMarked,
          requiredPermissions: ['knowledge_base.view'],
        },
        {
          title: 'Blueprints',
          href: '/dashboard/blueprints',
          icon: LayoutTemplate,
          requiredPermissions: ['agents.view'],
        },
        ...(isAnalyst
          ? [
              {
                title: 'Geradores de Documento',
                href: '/dashboard/document-generators',
                icon: FileText,
                requiredPermissions: ['document_generators.use'] as Permission[],
              },
            ]
          : []),
        {
          title: 'Minuta por IA',
          href: '/dashboard/peticao-ia',
          icon: FileEdit,
          badge: 'IA',
          requiredPermissions: ['assistant.use'],
        },
      ],
    },

    // ── Relatórios & Analytics ──
    {
      title: 'Relatórios & Analytics',
      href: '/dashboard/relatorios',
      icon: BarChart3,
      requiredPermissions: ['dashboard.view'],
      children: [
        {
          title: 'Relatórios',
          href: '/dashboard/relatorios',
          icon: BarChart3,
          requiredPermissions: ['dashboard.view'],
        },
        {
          title: 'Analytics',
          href: '/dashboard/analytics',
          icon: BarChart3,
          requiredPermissions: ['analytics.view'],
        },
        {
          title: 'Auditoria',
          href: '/dashboard/auditoria',
          icon: Eye,
          requiredPermissions: ['analytics.view'],
        },
      ],
    },

    // ── Administração ──
    {
      title: 'Administração',
      href: '/dashboard/users',
      icon: Settings,
      requiredPermissions: ['dashboard.view'],
      children: [
        {
          title: 'Usuários',
          href: '/dashboard/users',
          icon: Users,
          requiredPermissions: ['users.view'],
        },
        {
          title: 'Equipe',
          href: '/dashboard/equipe',
          icon: UsersRound,
          requiredPermissions: ['dashboard.view'],
        },
        {
          title: 'Importar Dados',
          href: '/dashboard/importar',
          icon: Upload,
          requiredPermissions: ['dashboard.view'],
        },
        {
          title: 'Exportar Dados',
          href: '/dashboard/exportar',
          icon: Download,
          requiredPermissions: ['dashboard.view'],
        },
        {
          title: 'Lembretes',
          href: '/dashboard/reminders',
          icon: Bell,
          requiredPermissions: ['dashboard.view'],
        },
        {
          title: 'Configurações',
          href: '/dashboard/settings',
          icon: Settings,
          requiredPermissions: ['dashboard.view'],
          children: [
            {
              title: 'Perfil',
              href: '/dashboard/settings/profile',
              icon: UserCog,
              requiredPermissions: ['dashboard.view'],
            },
            {
              title: 'Identidade Visual',
              href: '/dashboard/settings/brand',
              icon: Palette,
              requiredPermissions: ['settings.edit'],
            },
            {
              title: 'Perfis e Permissões',
              href: '/dashboard/settings/roles',
              icon: Shield,
              requiredPermissions: ['users.view'],
            },
            {
              title: 'LGPD',
              href: '/dashboard/settings/lgpd',
              icon: ShieldCheck,
              requiredPermissions: ['settings.edit'],
            },
          ],
        },
      ],
    },
  ];

  return items;
};

interface SidebarProps {
  onNavigate?: () => void;
}

export function Sidebar({ onNavigate }: SidebarProps = {}) {
  const pathname = usePathname();
  const { brandSettings } = useBrandSettings();
  const { hasAnyPermission, isLoadingPermissions } = usePermissions();
  const { user } = useAuth();

  const operatorRoles = [
    'procurador', 'assessor_gerencial', 'assessor_gabinete', 'servidor', 'distribuidor',
  ];
  const isAnalyst = operatorRoles.includes(user?.role || '');

  // Função para verificar se o usuário pode ver um item
  const canSeeItem = (item: NavItem): boolean => {
    if (!item.requiredPermissions || item.requiredPermissions.length === 0) {
      return true;
    }
    return hasAnyPermission(item.requiredPermissions);
  };

  // Função para filtrar itens visíveis (recursiva para suportar 3+ níveis)
  const filterVisibleItems = (items: NavItem[]): NavItem[] => {
    return items
      .filter(canSeeItem)
      .map((item) => {
        if (item.children) {
          return {
            ...item,
            children: filterVisibleItems(item.children),
          };
        }
        return item;
      })
      .filter((item) => {
        // Remove itens pai que não têm filhos visíveis
        if (item.children && item.children.length === 0) {
          return false;
        }
        return true;
      });
  };

  const navItems = getNavItems(isAnalyst);
  const visibleItems = isLoadingPermissions ? [] : filterVisibleItems(navItems);

  return (
    <div className="flex h-full w-full flex-col gap-2 bg-card border-r overflow-hidden">
      <div className="flex h-16 items-center border-b px-6">
        <Link href="/dashboard" className="flex items-center gap-3 font-semibold">
          <Image
            src={brandSettings?.logo || '/logo.png'}
            alt={brandSettings?.system_name || 'Verus.AI'}
            width={36}
            height={36}
            className="h-8 w-8 object-contain shrink-0"
            unoptimized
          />
          <div className="flex flex-col">
            <span className="text-sm font-bold tracking-tight text-foreground leading-tight">
              {brandSettings?.system_name || 'Verus.AI'}
            </span>
            <span className="text-[10px] text-muted-foreground font-mono leading-tight">
              {brandSettings?.system_tagline || 'Assistente Jurídico'}
            </span>
          </div>
        </Link>
      </div>

      <div className="flex-1 overflow-y-auto overflow-x-hidden py-2" style={{ WebkitOverflowScrolling: 'touch' }}>
        <nav className="grid gap-1 px-2">
          {visibleItems.map((item) => {
            const Icon = item.icon;
            // Exact match for root items, startsWith only for non-root
            const isActive = item.href === '/dashboard'
              ? pathname === '/dashboard'
              : (pathname === item.href || pathname?.startsWith(item.href + '/'));
            const hasChildren = item.children && item.children.length > 0;

            // Se tem filhos, renderiza com Accordion
            if (hasChildren) {
              // Parent is "active" if ANY child (or grandchild) route matches
              const isAnyChildActive = (children: NavItem[]): boolean =>
                children.some(
                  (child) =>
                    pathname === child.href ||
                    pathname?.startsWith(child.href + '/') ||
                    (child.children ? isAnyChildActive(child.children) : false)
                );
              const isParentActive = item.children ? isAnyChildActive(item.children) : false;
              return (
                <Accordion key={item.href} type="single" collapsible defaultValue={isParentActive ? item.href : undefined} className="border-none">
                  <AccordionItem value={item.href} className="border-none">
                    <AccordionTrigger
                      className={cn(
                        'flex items-center gap-3 rounded-lg px-3 py-2.5 min-h-[44px] text-sm font-medium transition-colors hover:no-underline',
                        isParentActive
                          ? 'bg-primary/10 text-primary'
                          : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                      )}
                    >
                      <div className="flex items-center gap-3 flex-1">
                        <Icon className="h-4 w-4" />
                        {item.title}
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="pb-0 pt-1">
                      <div className="ml-6 grid gap-1">
                        {item.children?.map((child) => {
                          const ChildIcon = child.icon;
                          const isChildActive = pathname === child.href || pathname?.startsWith(child.href + '/');
                          const childHasChildren = child.children && child.children.length > 0;

                          // Nested submenu (e.g. Simulações inside Inteligência Jurídica)
                          if (childHasChildren) {
                            const isNestedActive = child.children ? isAnyChildActive(child.children) : false;
                            return (
                              <Accordion key={child.href} type="single" collapsible defaultValue={isNestedActive ? child.href : undefined} className="border-none">
                                <AccordionItem value={child.href} className="border-none">
                                  <AccordionTrigger
                                    className={cn(
                                      'flex items-center gap-3 rounded-lg px-3 py-2 min-h-[40px] text-sm font-medium transition-colors hover:no-underline',
                                      isNestedActive
                                        ? 'bg-primary/10 text-primary'
                                        : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                                    )}
                                  >
                                    <div className="flex items-center gap-3 flex-1">
                                      <ChildIcon className="h-4 w-4" />
                                      {child.title}
                                      {child.badge && (
                                        <span className="ml-auto flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[10px]">
                                          {child.badge}
                                        </span>
                                      )}
                                    </div>
                                  </AccordionTrigger>
                                  <AccordionContent className="pb-0 pt-1">
                                    <div className="ml-5 grid gap-1">
                                      {child.children?.map((grandchild) => {
                                        const GrandchildIcon = grandchild.icon;
                                        const isGrandchildActive = pathname === grandchild.href || pathname?.startsWith(grandchild.href + '/');
                                        return (
                                          <Link
                                            key={grandchild.href}
                                            href={grandchild.href}
                                            onClick={onNavigate}
                                            className={cn(
                                              'flex items-center gap-3 rounded-lg px-3 py-2 min-h-[36px] text-xs font-medium transition-colors',
                                              isGrandchildActive
                                                ? 'bg-primary text-primary-foreground'
                                                : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                                            )}
                                          >
                                            <GrandchildIcon className="h-3.5 w-3.5" />
                                            {grandchild.title}
                                          </Link>
                                        );
                                      })}
                                    </div>
                                  </AccordionContent>
                                </AccordionItem>
                              </Accordion>
                            );
                          }

                          return (
                            <Link
                              key={child.href}
                              href={child.href}
                              onClick={onNavigate}
                              className={cn(
                                'flex items-center gap-3 rounded-lg px-3 py-2.5 min-h-[44px] text-sm font-medium transition-colors',
                                isChildActive
                                  ? 'bg-primary text-primary-foreground'
                                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                              )}
                            >
                              <ChildIcon className="h-4 w-4" />
                              {child.title}
                              {child.badge && (
                                <span className="ml-auto flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs">
                                  {child.badge}
                                </span>
                              )}
                            </Link>
                          );
                        })}
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
              );
            }

            // Link externo - abre em nova aba
            if (item.external) {
              return (
                <a
                  key={item.href}
                  href={item.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={cn(
                    'flex items-center gap-3 rounded-lg px-3 py-2.5 min-h-[44px] text-sm font-medium transition-colors',
                    'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.title}
                </a>
              );
            }

            // Se não tem filhos, renderiza normalmente
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onNavigate}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 min-h-[44px] text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )}
              >
                <Icon className="h-4 w-4" />
                {item.title}
                {item.badge && (
                  <span className="ml-auto flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="mt-auto p-3 lg:p-4 shrink-0">
        <Separator className="mb-3 lg:mb-4" />
        <div className="text-[11px] lg:text-xs text-muted-foreground truncate">
          <p className="font-semibold truncate">
            {process.env.NEXT_PUBLIC_APP_NAME || 'Verus.AI'} v{process.env.NEXT_PUBLIC_APP_VERSION || '0.0.0'}
          </p>
          <p className="truncate">Assistente Jurídico com IA</p>
        </div>
      </div>
    </div>
  );
}

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ChevronRight, Home } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface BreadcrumbItem {
  label: string;
  href?: string;
  icon?: React.ReactNode;
}

interface BreadcrumbsProps {
  items?: BreadcrumbItem[];
  className?: string;
  separator?: React.ReactNode;
  showHome?: boolean;
}

/**
 * Mapeamento de rotas para labels amigáveis
 */
const ROUTE_LABELS: Record<string, string> = {
  'dashboard': 'Painel',
  'intelligent-assistant': 'Assistente Jurídico',
  'jurisprudencia': 'Jurisprudência',
  'casos': 'Casos',
  'clientes': 'Clientes',
  'calendario': 'Calendário',
  'documentos': 'Documentos',
  'agentes': 'Agentes',
  'configuracoes': 'Configurações',
  'perfil': 'Perfil',
  'gerador': 'Gerador de Documentos',
  'etp': 'Documento Jurídico',
  'termo-referencia': 'Termo de Referência',
  'contrato': 'Contrato',
  'ata-execucao': 'Ata de Execução',
  'parecer': 'Parecer',
  'peticao': 'Petição',
  'contato': 'Contato',
  'settings': 'Configurações',
  // Fluxos de trabalho
  'fluxos': 'Fluxos de Trabalho',
  'execucoes': 'Execuções',
  'minhas-tarefas': 'Minhas Tarefas',
  'solicitacoes': 'Solicitações',
  // Processos
  'processos': 'Processos',
  'prazos': 'Prazos',
  'relatorios': 'Relatórios',
  'auditoria': 'Auditoria',
  'analytics': 'Analytics',
  'usuarios': 'Usuários',
  'users': 'Usuários',
  'equipe': 'Equipe',
  'importar': 'Importar Dados',
  'exportar': 'Exportar Dados',
  'knowledge-base': 'Base de Conhecimento',
  'blueprints': 'Blueprints',
  'protocolo': 'Protocolo Eletrônico',
  'contratos': 'Contratos',
  'assinatura-digital': 'Assinatura Digital',
  'email-templates': 'Templates de E-mail',
  'ocr': 'OCR de Documentos',
  'copilot': 'Copilot',
  'simulations': 'Simulações',
  'datajud': 'Consulta CNJ / DataJud',
  'tribunal-push': 'Acompanhamento Tribunal',
  'kanban': 'Kanban de Tarefas',
  'workflows': 'Workflows',
  'prazos-inteligentes': 'Prazos Inteligentes',
  'kpis': 'KPIs',
  'reminders': 'Lembretes',
  'documents': 'Documentos',
  'peticao-ia': 'Petição por IA',
  'agents': 'Agentes Jurídicos',
};

/**
 * Componente de Breadcrumbs para navegação hierárquica
 *
 * @example
 * <Breadcrumbs />
 * // Auto-detecta rota atual e gera breadcrumbs
 *
 * @example
 * <Breadcrumbs items={[
 *   { label: 'Início', href: '/dashboard' },
 *   { label: 'Casos', href: '/dashboard/casos' },
 *   { label: 'Novo Caso' },
 * ]} />
 */
export function Breadcrumbs({
  items,
  className,
  separator = <ChevronRight className="h-4 w-4 text-muted-foreground" />,
  showHome = true,
}: BreadcrumbsProps) {
  const pathname = usePathname();

  // Gerar breadcrumbs automaticamente da rota
  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    if (!pathname) return [];

    const segments = pathname.split('/').filter(Boolean);
    const breadcrumbs: BreadcrumbItem[] = [];

    // Adicionar home
    if (showHome) {
      breadcrumbs.push({
        label: 'Início',
        href: '/dashboard',
        icon: <Home className="h-4 w-4" />,
      });
    }

    // Construir breadcrumbs para cada segmento
    let accumulatedPath = '';
    for (const segment of segments) {
      accumulatedPath += `/${segment}`;

      // Ignorar segmentos que são IDs (números ou UUIDs)
      const isId = /^\d+$|^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(segment);

      if (isId) {
        continue;
      }

      const label = ROUTE_LABELS[segment] || formatLabel(segment);
      const isLast = accumulatedPath === pathname;

      breadcrumbs.push({
        label,
        href: isLast ? undefined : accumulatedPath,
      });
    }

    return breadcrumbs;
  };

  const breadcrumbs = items || generateBreadcrumbs();

  if (breadcrumbs.length === 0) return null;

  return (
    <nav
      aria-label="Breadcrumb"
      className={cn('flex items-center gap-1 text-sm text-muted-foreground', className)}
    >
      {breadcrumbs.map((item, index) => {
        const isLast = index === breadcrumbs.length - 1;

        return (
          <div key={item.href || item.label} className="flex items-center gap-1">
            {/* Separador (exceto no primeiro item) */}
            {index > 0 && separator}

            {/* Link ou texto */}
            {item.href && !isLast ? (
              <Link
                href={item.href}
                className={cn(
                  'flex items-center gap-1 hover:text-foreground transition-colors',
                  item.icon && 'text-muted-foreground'
                )}
              >
                {item.icon}
                {item.label}
              </Link>
            ) : (
              <span
                className={cn(
                  'flex items-center gap-1 font-medium text-foreground',
                  !isLast && 'hover:text-foreground cursor-pointer'
                )}
                aria-current={isLast ? 'page' : undefined}
              >
                {item.icon}
                {item.label}
              </span>
            )}
          </div>
        );
      })}
    </nav>
  );
}

/**
 * Formata um slug para label legível
 */
function formatLabel(slug: string): string {
  return slug
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Hook para usar breadcrumbs programaticamente
 */
export function useBreadcrumbs() {
  const pathname = usePathname();

  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    if (!pathname) return [];

    const segments = pathname.split('/').filter(Boolean);
    const breadcrumbs: BreadcrumbItem[] = [];

    breadcrumbs.push({
      label: 'Início',
      href: '/dashboard',
      icon: <Home className="h-4 w-4" />,
    });

    let accumulatedPath = '';
    for (const segment of segments) {
      accumulatedPath += `/${segment}`;

      const isId = /^\d+$|^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(segment);

      if (isId) continue;

      const label = ROUTE_LABELS[segment] || formatLabel(segment);
      const isLast = accumulatedPath === pathname;

      breadcrumbs.push({
        label,
        href: isLast ? undefined : accumulatedPath,
      });
    }

    return breadcrumbs;
  };

  return {
    breadcrumbs: generateBreadcrumbs(),
    pathname,
  };
}

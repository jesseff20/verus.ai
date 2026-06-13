'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import {
  Scale,
  LogOut,
  Briefcase,
  FileText,
  ClipboardList,
  MessageSquare,
  Calendar,
  Bell,
  User,
  ShieldCheck,
  Menu,
  X,
  ChevronRight,
  Bot,
} from 'lucide-react';
import { useClientPortalAuth } from '@/hooks/use-client-portal';
import { useBrandSettings } from '@/hooks/use-brand-settings';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

const SIDEBAR_ITEMS = [
  { href: '/portal', label: 'Meus Processos', icon: Briefcase, exact: true },
  { href: '/portal/copilot', label: 'Assistente IA', icon: Bot, badge: 'IA' },
  { href: '/portal/documentos', label: 'Documentos', icon: FileText },
  { href: '/portal/contratos', label: 'Contratos', icon: ClipboardList },
  { href: '/portal/mensagens', label: 'Mensagens', icon: MessageSquare },
  { href: '/portal/audiencias', label: 'Audiências', icon: Calendar },
  { href: '/portal/notificacoes', label: 'Notificações', icon: Bell },
  { href: '/portal/meus-dados', label: 'Meus Dados', icon: User },
  { href: '/portal/privacidade', label: 'Privacidade', icon: ShieldCheck },
];

export default function ClientLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { client, loading, isAuthenticated, logout } = useClientPortalAuth();
  const { brandSettings } = useBrandSettings();
  const appName = brandSettings?.system_name || process.env.NEXT_PUBLIC_APP_NAME || 'Verus.AI';
  const router = useRouter();
  const pathname = usePathname();
  // Lazy initializer lê localStorage imediatamente — sem race condition entre os dois effects
  const [hasToken, setHasToken] = useState(() => {
    if (typeof window === 'undefined') return false;
    return !!localStorage.getItem('client_portal_access_token');
  });
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const isLoginPage = pathname === '/portal/login';

  // Mantém o estado de token sincronizado quando o estado de autenticação muda
  useEffect(() => {
    setHasToken(!!localStorage.getItem('client_portal_access_token'));
  }, [isAuthenticated]);

  // Redireciona só quando a query terminou E não há token E não está autenticado
  useEffect(() => {
    if (!loading && !isAuthenticated && !isLoginPage && !hasToken) {
      router.push('/portal/login');
    }
  }, [loading, isAuthenticated, hasToken, isLoginPage, router]);

  // Close sidebar on route change
  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  if (loading && !isLoginPage) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-[3px] border-primary/20 border-t-primary" />
          <p className="text-sm text-muted-foreground font-mono tracking-wide">
            Carregando...
          </p>
        </div>
      </div>
    );
  }

  // Login page renders without chrome
  if (isLoginPage) {
    return <>{children}</>;
  }

  if (!isAuthenticated && !hasToken) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-[3px] border-primary/20 border-t-primary" />
          <p className="text-sm text-muted-foreground font-mono tracking-wide">
            Redirecionando...
          </p>
        </div>
      </div>
    );
  }

  function isActive(href: string, exact?: boolean) {
    if (exact) return pathname === href;
    return pathname === href || pathname.startsWith(href + '/');
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* ── Header ─────────────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b bg-card">
        <div className="flex h-14 items-center justify-between px-4">
          <div className="flex items-center gap-3">
            {/* Mobile hamburger */}
            <button
              type="button"
              className="lg:hidden flex items-center justify-center h-9 w-9 rounded-md hover:bg-accent transition-colors"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              aria-label="Menu"
            >
              {sidebarOpen ? (
                <X className="h-5 w-5" />
              ) : (
                <Menu className="h-5 w-5" />
              )}
            </button>

            <Link href="/portal" className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
                <Scale className="h-4 w-4 text-primary-foreground" />
              </div>
              <div>
                <span className="text-sm font-semibold">{appName}</span>
                <span className="hidden sm:inline text-xs text-muted-foreground ml-2">
                  Portal de Acompanhamento
                </span>
              </div>
            </Link>
          </div>

          <div className="flex items-center gap-3">
            {client && (
              <span className="hidden sm:inline text-sm text-muted-foreground">
                {client.name}
              </span>
            )}
            <Button variant="ghost" size="sm" onClick={logout}>
              <LogOut className="h-4 w-4 mr-1" />
              <span className="hidden sm:inline">Sair</span>
            </Button>
          </div>
        </div>
      </header>

      <div className="flex flex-1">
        {/* ── Mobile overlay ──────────────────────────── */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-30 bg-black/40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* ── Sidebar ─────────────────────────────────── */}
        <aside
          className={`
            fixed top-14 left-0 z-40 h-[calc(100vh-3.5rem)] w-64 border-r bg-card
            transition-transform duration-200 ease-in-out
            lg:sticky lg:translate-x-0 lg:block
            ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          `}
        >
          <nav className="flex flex-col h-full py-4">
            <div className="flex-1 space-y-1 px-3">
              {SIDEBAR_ITEMS.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href, item.exact);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`
                      flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium
                      transition-colors duration-150
                      ${
                        active
                          ? 'bg-primary/10 text-primary'
                          : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                      }
                    `}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span className="truncate">{item.label}</span>
                    {'badge' in item && item.badge && (
                      <Badge variant="secondary" className="ml-1 px-1.5 py-0 text-[10px] bg-primary/15 text-primary font-semibold">
                        {item.badge}
                      </Badge>
                    )}
                    {active && (
                      <ChevronRight className="ml-auto h-4 w-4 opacity-50" />
                    )}
                  </Link>
                );
              })}
            </div>

            {/* Sidebar logout */}
            <div className="border-t px-3 pt-3 mt-2">
              <button
                type="button"
                onClick={logout}
                className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
              >
                <LogOut className="h-4 w-4 shrink-0" />
                <span>Sair</span>
              </button>
            </div>
          </nav>
        </aside>

        {/* ── Content ─────────────────────────────────── */}
        <main className="flex-1 min-w-0">
          <div className="max-w-5xl mx-auto px-4 py-6">
            {children}
          </div>
        </main>
      </div>

      {/* ── Footer ────────────────────────────────────── */}
      <footer className="border-t bg-background px-4 py-2 shrink-0">
        <p className="text-center text-[10px] sm:text-[11px] text-muted-foreground">
          {appName} - Portal de Acompanhamento.{' '}
          <strong className="font-medium text-foreground/60">
            As informações exibidas são apenas para acompanhamento e não constituem aconselhamento jurídico.
          </strong>
        </p>
      </footer>
    </div>
  );
}

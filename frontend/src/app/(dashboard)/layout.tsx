'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/use-auth';
import { Sidebar } from '@/components/layouts/sidebar';
import { Header } from '@/components/layouts/header';
import { Breadcrumbs } from '@/components/navigation/Breadcrumbs';
import { TourProvider } from '@/components/tour/TourProvider';
import { TourHelpButton } from '@/components/tour/TourHelpButton';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();
  // Lazy initializer lê localStorage imediatamente — sem race condition entre os dois effects
  const [hasToken, setHasToken] = useState(() => {
    if (typeof window === 'undefined') return false;
    return !!localStorage.getItem('access_token');
  });

  // Mantém o estado de token sincronizado quando o estado de autenticação muda
  useEffect(() => {
    setHasToken(!!localStorage.getItem('access_token'));
  }, [isAuthenticated]);

  // Redireciona só quando a query terminou E não há token E não está autenticado
  useEffect(() => {
    if (!loading && !isAuthenticated && !hasToken) {
      router.push('/login');
    }
  }, [loading, isAuthenticated, hasToken, router]);

  if (loading) {
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

  // Renderiza o layout mesmo com isAuthenticated=false se houver token —
  // pode ser erro de rede temporário; o backend protege as rotas de API.
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

  return (
    <div className="flex h-screen overflow-hidden bg-background max-w-full">

      {/* ── Sidebar (desktop) ──────────────────────── */}
      <aside className="hidden w-64 shrink-0 lg:flex flex-col border-r bg-card overflow-hidden">
        <Sidebar />
      </aside>

      {/* ── Conteúdo principal ─────────────────────── */}
      <div className="flex flex-1 flex-col overflow-hidden min-w-0 w-full">
        <Header />

        <main className="flex-1 overflow-y-auto overflow-x-hidden bg-muted/30" style={{ WebkitOverflowScrolling: 'touch' }}>
          <TourProvider>
            <div className="max-w-[1800px] mx-auto px-3 py-4 sm:px-4 md:px-6 md:py-6">
              {/* Breadcrumbs */}
              <div className="mb-4">
                <Breadcrumbs />
              </div>
              {children}
            </div>

            {/* Botão de ajuda flutuante */}
            <TourHelpButton />
          </TourProvider>

          {/* ── Aviso Legal ───────────────────────── */}
            <footer className="border-t bg-background px-3 sm:px-4 md:px-6 py-2 sm:py-2.5 shrink-0">
            <p className="text-center text-[10px] sm:text-[11px] text-muted-foreground leading-relaxed">
              <span className="hidden sm:inline">Verus.AI é um assistente de procuradoria com inteligência artificial.{' '}</span>
              <strong className="font-medium text-foreground/60">
                Não substitui a orientação de um procurador habilitado.
              </strong>{' '}
              <span className="hidden sm:inline">Verifique sempre as informações com um profissional do Direito antes de tomar decisões jurídicas.</span>
            </p>
          </footer>
        </main>
      </div>
    </div>
  );
}

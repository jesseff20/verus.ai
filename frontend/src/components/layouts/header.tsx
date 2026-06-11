'use client';

import { useState, useEffect } from 'react';
import { useTheme } from 'next-themes';
import { useAuth } from '@/hooks/use-auth';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Sheet,
  SheetContent,
  SheetTrigger,
  SheetTitle,
} from '@/components/ui/sheet';
import { VisuallyHidden } from '@radix-ui/react-visually-hidden';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import {
  LogOut,
  Settings,
  User,
  Menu,
  Sun,
  Moon,
} from 'lucide-react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { Sidebar } from './sidebar';
import { GlobalSearch } from '@/components/navigation/GlobalSearch';
import { NotificationBell } from '@/components/notifications/NotificationBell';

const roleLabels: Record<string, string> = {
  // Roles de procuradoria (verus.ai)
  superadmin:           'Super Admin',
  admin:                'Administrador',
  procurador_geral:     'Procurador(a) Geral',
  subprocurador_geral:  'Subprocurador(a) Geral',
  gerente:              'Gerente',
  procurador:           'Procurador(a)',
  assessor_gerencial:   'Assessor(a) Gerencial',
  assessor_gabinete:    'Assessor(a) Gabinete',
  distribuidor:         'Distribuidor(a)',
  servidor:             'Servidor(a)',
  visualizador:         'Visualizador',
  // Aliases legados BravoJus
  manager:              'Gestor',
  analyst:              'Analista',
  reviewer:             'Revisor',
  viewer:               'Visualizador',
};

const roleColors: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  superadmin:           'destructive',
  admin:                'destructive',
  procurador_geral:     'default',
  subprocurador_geral:  'default',
  gerente:              'default',
  procurador:           'secondary',
  assessor_gerencial:   'secondary',
  assessor_gabinete:    'outline',
  distribuidor:         'outline',
  servidor:             'outline',
  visualizador:         'outline',
  manager:              'default',
  analyst:              'secondary',
  reviewer:             'default',
  viewer:               'outline',
};

export function Header() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Evita hydration mismatch no toggle de tema
  useEffect(() => { setMounted(true); }, []);

  const getInitials = (name: string) => {
    const parts = name.split(' ');
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  const displayName =
    user?.first_name && user?.last_name
      ? `${user.first_name} ${user.last_name}`
      : user?.username || 'Usuário';

  const isDark = theme === 'dark';

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60" style={{ paddingTop: 'env(safe-area-inset-top)' }}>
      <div className="flex h-12 sm:h-14 items-center justify-between px-3 sm:px-4 md:px-6">

        {/* ── Esquerda ──────────────────────────────── */}
        <div className="flex items-center gap-3">
          {/* Mobile: hamburger */}
          <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="lg:hidden h-11 w-11">
                <Menu className="h-5 w-5" />
                <span className="sr-only">Abrir menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="p-0 w-[85vw] max-w-[320px] transition-transform duration-300 ease-out">
              <VisuallyHidden>
                <SheetTitle>Menu de Navegação</SheetTitle>
              </VisuallyHidden>
              <Sidebar onNavigate={() => setMobileMenuOpen(false)} />
            </SheetContent>
          </Sheet>

          {/* Título (logo está no sidebar) */}
          <div className="flex items-center gap-2 lg:hidden">
            <Image
              src="/logo.png"
              alt="Verus.AI"
              width={28}
              height={28}
              className="h-7 w-7 object-contain"
              unoptimized
            />
            <span className="text-sm font-semibold tracking-tight text-foreground">
              Verus.AI
            </span>
          </div>
        </div>

        {/* ── Direita ───────────────────────────────── */}
        <div className="flex items-center gap-1 sm:gap-2">

          {/* Busca global Ctrl+K */}
          <GlobalSearch />

          {/* Notificações */}
          {user && <NotificationBell />}

          {/* Toggle de tema */}
          {mounted && (
            <Button
              variant="ghost"
              size="icon"
              className="h-10 w-10 sm:h-9 sm:w-9 text-muted-foreground hover:text-foreground"
              onClick={() => setTheme(isDark ? 'light' : 'dark')}
              title={isDark ? 'Mudar para modo claro' : 'Mudar para modo escuro'}
            >
              {isDark
                ? <Sun className="h-4 w-4" />
                : <Moon className="h-4 w-4" />
              }
              <span className="sr-only">
                {isDark ? 'Modo claro' : 'Modo escuro'}
              </span>
            </Button>
          )}

          {user && (
            <>
              {/* Badge de perfil */}
              <Badge
                variant={roleColors[user.role] || 'default'}
                className="hidden sm:flex text-[11px] font-mono tracking-wide"
              >
                {roleLabels[user.role] || user.role}
              </Badge>

              {/* Menu do usuário */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className="relative h-10 w-10 sm:h-9 sm:w-9 rounded-full p-0"
                  >
                    <Avatar className="h-9 w-9 sm:h-8 sm:w-8">
                      <AvatarFallback className="bg-primary text-primary-foreground text-xs font-semibold">
                        {getInitials(displayName)}
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56" align="end" forceMount>
                  <DropdownMenuLabel className="font-normal">
                    <div className="flex flex-col gap-0.5">
                      <p className="text-sm font-semibold leading-none">
                        {displayName}
                      </p>
                      <p className="text-xs leading-none text-muted-foreground">
                        {user.email || user.username}
                      </p>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={() => router.push('/dashboard/settings/profile')}
                  >
                    <User className="mr-2 h-4 w-4" />
                    Perfil
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => router.push('/dashboard/settings')}
                  >
                    <Settings className="mr-2 h-4 w-4" />
                    Configurações
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={logout}
                    className="text-destructive focus:text-destructive"
                  >
                    <LogOut className="mr-2 h-4 w-4" />
                    Sair
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

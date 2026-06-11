'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import {
  FileText,
  Clock,
  CheckCircle,
  Calendar,
  MessageSquare,
  Bell,
  Loader2,
  AlertTriangle,
  CheckCheck,
} from 'lucide-react';

// ─── Types ──────────────────────────────────────────────────────────────────

interface PortalNotification {
  id: string;
  tipo: 'document' | 'deadline' | 'phase' | 'hearing' | 'message';
  titulo: string;
  descricao: string;
  caso_titulo: string | null;
  caso_id: string | null;
  lida: boolean;
  created_at: string;
}

// ─── API ────────────────────────────────────────────────────────────────────

const portalApi = axios.create({
  baseURL: '',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

portalApi.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('client_portal_access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// ─── Helpers ────────────────────────────────────────────────────────────────

const ICON_MAP: Record<string, React.ElementType> = {
  document: FileText,
  deadline: Clock,
  phase: CheckCircle,
  hearing: Calendar,
  message: MessageSquare,
};

const DOT_COLOR: Record<string, string> = {
  document: 'bg-blue-500',
  deadline: 'bg-amber-500',
  phase: 'bg-green-500',
  hearing: 'bg-purple-500',
  message: 'bg-sky-500',
};

const ICON_COLOR: Record<string, string> = {
  document: 'text-blue-500',
  deadline: 'text-amber-500',
  phase: 'text-green-500',
  hearing: 'text-purple-500',
  message: 'text-sky-500',
};

function formatTimestamp(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMin / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMin < 1) return 'agora';
  if (diffMin < 60) return `${diffMin}min atrás`;
  if (diffHours < 24) return `${diffHours}h atrás`;
  if (diffDays < 7) return `${diffDays}d atrás`;
  return date.toLocaleDateString('pt-BR');
}

// ─── Component ──────────────────────────────────────────────────────────────

export default function NotificacoesPage() {
  const queryClient = useQueryClient();

  const { data: notifications, isLoading, error } = useQuery<PortalNotification[]>({
    queryKey: ['client-portal-notificacoes'],
    queryFn: async () => {
      const res = await portalApi.get('/api/v1/auth/client-portal/notificacoes/');
      return res.data;
    },
    staleTime: 60 * 1000,
    retry: false,
  });

  const markAllRead = useMutation({
    mutationFn: async () => {
      await portalApi.post('/api/v1/auth/client-portal/notificacoes/mark-all-read/');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['client-portal-notificacoes'] });
    },
  });

  const hasUnread = notifications?.some((n) => !n.lida);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight flex items-center gap-2">
            <Bell className="h-7 w-7 sm:h-8 sm:w-8" />
            Atualizações
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Fique por dentro das novidades dos seus processos
          </p>
        </div>
        {hasUnread && (
          <Button
            variant="outline"
            size="sm"
            className="text-xs shrink-0"
            onClick={() => markAllRead.mutate()}
            disabled={markAllRead.isPending}
          >
            <CheckCheck className="h-3.5 w-3.5 mr-1" />
            Marcar todas como lidas
          </Button>
        )}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <div className="flex items-center justify-center py-16 text-destructive gap-2">
          <AlertTriangle className="h-5 w-5" />
          <span>Erro ao carregar atualizações</span>
        </div>
      ) : !notifications || notifications.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground gap-3">
          <Bell className="h-12 w-12 opacity-30" />
          <p className="text-sm">Nenhuma atualização recente</p>
        </div>
      ) : (
        <div className="space-y-1">
          {notifications.map((notif) => {
            const Icon = ICON_MAP[notif.tipo] || Bell;
            const dotColor = DOT_COLOR[notif.tipo] || 'bg-gray-400';
            const iconColor = ICON_COLOR[notif.tipo] || 'text-gray-400';

            return (
              <div
                key={notif.id}
                className={`flex gap-3 p-3 sm:p-4 rounded-lg ${
                  notif.lida
                    ? 'bg-background'
                    : 'bg-primary/5 dark:bg-primary/10'
                } transition-colors`}
              >
                <div className="flex flex-col items-center gap-1 shrink-0">
                  <div className={`w-1.5 h-1.5 rounded-full mt-1.5 ${dotColor}`} />
                </div>
                <div className={`mt-0.5 shrink-0 ${iconColor}`}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0 space-y-1">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className={`text-sm ${notif.lida ? 'font-normal' : 'font-semibold'}`}>
                      {notif.titulo}
                    </h3>
                    <span className="text-[10px] text-muted-foreground whitespace-nowrap shrink-0">
                      {formatTimestamp(notif.created_at)}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">{notif.descricao}</p>
                  {notif.caso_titulo && (
                    <p className="text-[10px] text-muted-foreground/70">
                      Caso: {notif.caso_titulo}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

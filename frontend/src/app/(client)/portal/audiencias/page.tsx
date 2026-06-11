'use client';

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Gavel,
  Loader2,
  AlertTriangle,
  MapPin,
  CalendarPlus,
  ChevronDown,
  Clock,
} from 'lucide-react';

// ─── Types ──────────────────────────────────────────────────────────────────

interface Hearing {
  id: string;
  data_hora: string;
  local: string;
  tipo: string;
  tipo_display: string;
  caso_titulo: string;
  observacoes: string;
  resultado: string | null;
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

function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('pt-BR', {
    weekday: 'long',
    day: '2-digit',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

const TYPE_COLORS: Record<string, string> = {
  conciliacao: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
  instrucao: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300',
  julgamento: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300',
  pericia: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
};

// ─── Component ──────────────────────────────────────────────────────────────

function HearingCard({ hearing, isPast }: { hearing: Hearing; isPast: boolean }) {
  return (
    <Card className={isPast ? 'opacity-60' : ''}>
      <CardContent className="p-4 sm:p-5 space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-2">
              <Badge className={`text-[10px] px-1.5 py-0 ${TYPE_COLORS[hearing.tipo] || 'bg-gray-100 text-gray-800 dark:bg-gray-800/40 dark:text-gray-300'}`}>
                {hearing.tipo_display}
              </Badge>
            </div>
            <h3 className="font-medium text-sm sm:text-base">{hearing.caso_titulo}</h3>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {formatDateTime(hearing.data_hora)}
          </span>
          <span className="flex items-center gap-1">
            <MapPin className="h-3 w-3" />
            {hearing.local}
          </span>
        </div>

        {hearing.observacoes && (
          <p className="text-xs text-muted-foreground border-l-2 border-primary/20 pl-3">
            {hearing.observacoes}
          </p>
        )}

        {isPast && hearing.resultado && (
          <p className="text-xs font-medium text-muted-foreground">
            Resultado: {hearing.resultado}
          </p>
        )}

        {!isPast && (
          <Button variant="outline" size="sm" className="text-xs" disabled>
            <CalendarPlus className="h-3 w-3 mr-1" />
            Adicionar ao Calendário
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

export default function AudienciasPage() {
  const { data: hearings, isLoading, error } = useQuery<Hearing[]>({
    queryKey: ['client-portal-audiencias'],
    queryFn: async () => {
      const res = await portalApi.get('/api/v1/auth/client-portal/audiencias/');
      return res.data;
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  const { upcoming, past } = useMemo(() => {
    if (!hearings) return { upcoming: [], past: [] };
    const now = new Date();
    const up: Hearing[] = [];
    const pa: Hearing[] = [];
    for (const h of hearings) {
      if (new Date(h.data_hora) >= now) up.push(h);
      else pa.push(h);
    }
    up.sort((a, b) => new Date(a.data_hora).getTime() - new Date(b.data_hora).getTime());
    pa.sort((a, b) => new Date(b.data_hora).getTime() - new Date(a.data_hora).getTime());
    return { upcoming: up, past: pa };
  }, [hearings]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight flex items-center gap-2">
          <Gavel className="h-7 w-7 sm:h-8 sm:w-8" />
          Audiências
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Acompanhe suas audiências agendadas e realizadas
        </p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <div className="flex items-center justify-center py-16 text-destructive gap-2">
          <AlertTriangle className="h-5 w-5" />
          <span>Erro ao carregar audiências</span>
        </div>
      ) : !hearings || hearings.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground gap-3">
          <Gavel className="h-12 w-12 opacity-30" />
          <p className="text-sm">Nenhuma audiência agendada</p>
        </div>
      ) : (
        <>
          {/* Upcoming */}
          {upcoming.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-lg font-semibold">Próximas Audiências</h2>
              <div className="grid gap-3">
                {upcoming.map((h) => (
                  <HearingCard key={h.id} hearing={h} isPast={false} />
                ))}
              </div>
            </div>
          )}

          {/* Past */}
          {past.length > 0 && (
            <Collapsible>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" className="w-full justify-between text-muted-foreground">
                  <span className="text-sm font-semibold">
                    Audiências Anteriores ({past.length})
                  </span>
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent className="space-y-3 mt-3">
                {past.map((h) => (
                  <HearingCard key={h.id} hearing={h} isPast />
                ))}
              </CollapsibleContent>
            </Collapsible>
          )}
        </>
      )}
    </div>
  );
}

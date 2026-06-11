'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import {
  Calendar,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Loader2,
  ChevronRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import api from '@/lib/api';

interface LegalDeadline {
  id: string;
  caso: string;
  titulo: string;
  descricao: string;
  tipo: string;
  tipo_display: string;
  prioridade: string;
  prioridade_display: string;
  status: string;
  status_display: string;
  data_prazo: string;
  responsavel_nome: string | null;
  dias_restantes: number | null;
}

const prioridadeConfig: Record<string, { color: string }> = {
  baixa: { color: 'bg-gray-100 text-gray-700' },
  media: { color: 'bg-blue-100 text-blue-700' },
  alta: { color: 'bg-orange-100 text-orange-700' },
  urgente: { color: 'bg-red-100 text-red-700' },
};

function formatDate(dateStr: string): string {
  return new Date(dateStr + 'T12:00:00').toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

function DaysRemaining({ dias }: { dias: number | null }) {
  if (dias === null) return null;

  if (dias < 0) {
    return (
      <span className="flex items-center gap-1 text-red-600 text-xs font-medium">
        <AlertTriangle className="h-3 w-3" />
        {Math.abs(dias)} dias atrasado
      </span>
    );
  }
  if (dias === 0) {
    return (
      <span className="flex items-center gap-1 text-orange-600 text-xs font-medium">
        <Clock className="h-3 w-3" />
        Vence hoje
      </span>
    );
  }
  if (dias <= 3) {
    return (
      <span className="flex items-center gap-1 text-orange-500 text-xs">
        <Clock className="h-3 w-3" />
        {dias} dias
      </span>
    );
  }
  return (
    <span className="text-xs text-muted-foreground">{dias} dias</span>
  );
}

export default function PrazosPage() {
  const [statusFilter, setStatusFilter] = useState<string>('pendente');

  const { data: prazos = [], isLoading, error } = useQuery({
    queryKey: ['prazos-global', statusFilter],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (statusFilter && statusFilter !== 'all') params.status = statusFilter;
      const response = await api.get('/api/v1/processos/prazos/', { params });
      const data = response.data;
      // Handle paginated response ({count, next, results}) or flat array
      const items: LegalDeadline[] = data?.results || (Array.isArray(data) ? data : []);
      return items;
    },
  });

  // Agrupar por data
  const hoje = new Date();
  const prazosAtrasados = prazos.filter(p => p.dias_restantes !== null && p.dias_restantes < 0);
  const prazosHoje = prazos.filter(p => p.dias_restantes === 0);
  const prazosSemana = prazos.filter(p => p.dias_restantes !== null && p.dias_restantes > 0 && p.dias_restantes <= 7);
  const prazosFuturos = prazos.filter(p => p.dias_restantes !== null && p.dias_restantes > 7);
  const prazosConcluídos = prazos.filter(p => p.status === 'concluido');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Calendar className="h-8 w-8" />
            Prazos Processuais
          </h1>
          <p className="text-muted-foreground">
            Controle os prazos de todos os seus casos jurídicos
          </p>
        </div>
        <div className="flex gap-2">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              <SelectItem value="pendente">Pendentes</SelectItem>
              <SelectItem value="em_andamento">Em Andamento</SelectItem>
              <SelectItem value="concluido">Concluídos</SelectItem>
              <SelectItem value="atrasado">Atrasados</SelectItem>
            </SelectContent>
          </Select>
          <Button asChild variant="outline">
            <Link href="/dashboard/processos">
              Ver Casos
            </Link>
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <Card>
          <CardContent className="flex items-center justify-center py-12 text-destructive gap-2">
            <AlertTriangle className="h-5 w-5" />
            <span>Erro ao carregar prazos</span>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {/* Atrasados */}
          {prazosAtrasados.length > 0 && (
            <Card className="border-red-200 dark:border-red-900">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-red-600">
                  <AlertTriangle className="h-5 w-5" />
                  Atrasados ({prazosAtrasados.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {prazosAtrasados.map(prazo => (
                  <PrazoItem key={prazo.id} prazo={prazo} />
                ))}
              </CardContent>
            </Card>
          )}

          {/* Vence Hoje */}
          {prazosHoje.length > 0 && (
            <Card className="border-orange-200 dark:border-orange-900">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-orange-600">
                  <Clock className="h-5 w-5" />
                  Vencem Hoje ({prazosHoje.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {prazosHoje.map(prazo => (
                  <PrazoItem key={prazo.id} prazo={prazo} />
                ))}
              </CardContent>
            </Card>
          )}

          {/* Próximos 7 dias */}
          {prazosSemana.length > 0 && (
            <Card className="border-yellow-200 dark:border-yellow-900">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-yellow-700 dark:text-yellow-500">
                  <Calendar className="h-5 w-5" />
                  Próximos 7 dias ({prazosSemana.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {prazosSemana.map(prazo => (
                  <PrazoItem key={prazo.id} prazo={prazo} />
                ))}
              </CardContent>
            </Card>
          )}

          {/* Futuros */}
          {prazosFuturos.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-5 w-5 text-muted-foreground" />
                  Futuros ({prazosFuturos.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {prazosFuturos.map(prazo => (
                  <PrazoItem key={prazo.id} prazo={prazo} />
                ))}
              </CardContent>
            </Card>
          )}

          {/* Concluídos */}
          {prazosConcluídos.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-green-600">
                  <CheckCircle2 className="h-5 w-5" />
                  Concluídos ({prazosConcluídos.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {prazosConcluídos.map(prazo => (
                  <PrazoItem key={prazo.id} prazo={prazo} />
                ))}
              </CardContent>
            </Card>
          )}

          {prazos.length === 0 && (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12 text-muted-foreground gap-3">
                <Calendar className="h-12 w-12 opacity-30" />
                <p className="text-sm">Nenhum prazo encontrado</p>
                <Button asChild size="sm" variant="outline">
                  <Link href="/dashboard/processos">Ir para casos</Link>
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

function PrazoItem({ prazo }: { prazo: LegalDeadline }) {
  const prio = prioridadeConfig[prazo.prioridade] || prioridadeConfig.media;

  return (
    <Link
      href={`/dashboard/processos/${prazo.caso}`}
      className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent/50 transition-colors"
    >
      <div className="space-y-1 flex-1 min-w-0">
        <p className="font-medium text-sm">{prazo.titulo}</p>
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant="outline" className={`text-xs ${prio.color}`}>
            {prazo.prioridade_display}
          </Badge>
          <span className="text-xs text-muted-foreground">{prazo.tipo_display}</span>
          {prazo.responsavel_nome && (
            <span className="text-xs text-muted-foreground">• {prazo.responsavel_nome}</span>
          )}
        </div>
      </div>
      <div className="flex items-center gap-3 ml-3 shrink-0">
        <div className="text-right">
          <p className="text-xs font-medium">{new Date(prazo.data_prazo + 'T12:00:00').toLocaleDateString('pt-BR')}</p>
          <DaysRemaining dias={prazo.dias_restantes} />
        </div>
        <ChevronRight className="h-4 w-4 text-muted-foreground" />
      </div>
    </Link>
  );
}

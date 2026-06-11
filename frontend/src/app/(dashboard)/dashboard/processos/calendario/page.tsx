'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import {
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  Clock,
  CheckCircle2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import api from '@/lib/api';

interface LegalDeadline {
  id: string;
  caso: string;
  titulo: string;
  tipo_display: string;
  prioridade: string;
  status: string;
  data_prazo: string;
  dias_restantes: number | null;
}

const prioridadeColor: Record<string, string> = {
  baixa: 'bg-gray-400',
  media: 'bg-blue-400',
  alta: 'bg-orange-400',
  urgente: 'bg-red-500',
};

const statusIcon = (status: string, diasRestantes: number | null) => {
  if (status === 'concluido') return <CheckCircle2 className="h-3 w-3 text-green-600" />;
  if (diasRestantes !== null && diasRestantes < 0) return <AlertTriangle className="h-3 w-3 text-red-600" />;
  if (diasRestantes !== null && diasRestantes <= 3) return <AlertTriangle className="h-3 w-3 text-orange-500" />;
  return <Clock className="h-3 w-3 text-blue-600" />;
};

function getDaysInMonth(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate();
}

function getFirstDayOfMonth(year: number, month: number): number {
  return new Date(year, month, 1).getDay();
}

const MONTHS_PT = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
];
const WEEKDAYS = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];

export default function CalendarioPage() {
  const today = new Date();
  const [viewYear, setViewYear] = useState(today.getFullYear());
  const [viewMonth, setViewMonth] = useState(today.getMonth());

  const { data: deadlines = [], isLoading } = useQuery<LegalDeadline[]>({
    queryKey: ['all-prazos'],
    queryFn: async () => {
      const res = await api.get('/api/v1/processos/prazos/');
      return res.data.results || res.data || [];
    },
  });

  const deadlinesByDay = deadlines.reduce<Record<number, LegalDeadline[]>>((acc, d) => {
    const date = new Date(d.data_prazo + 'T12:00:00');
    if (date.getFullYear() === viewYear && date.getMonth() === viewMonth) {
      const day = date.getDate();
      if (!acc[day]) acc[day] = [];
      acc[day].push(d);
    }
    return acc;
  }, {});

  const daysInMonth = getDaysInMonth(viewYear, viewMonth);
  const firstDay = getFirstDayOfMonth(viewYear, viewMonth);

  const prevMonth = () => {
    if (viewMonth === 0) { setViewMonth(11); setViewYear(y => y - 1); }
    else setViewMonth(m => m - 1);
  };

  const nextMonth = () => {
    if (viewMonth === 11) { setViewMonth(0); setViewYear(y => y + 1); }
    else setViewMonth(m => m + 1);
  };

  const cells: (number | null)[] = [
    ...Array.from<null>({ length: firstDay }).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ];

  const weeks: (number | null)[][] = [];
  for (let i = 0; i < cells.length; i += 7) {
    const week = cells.slice(i, i + 7);
    while (week.length < 7) week.push(null);
    weeks.push(week);
  }

  const isToday = (day: number) =>
    day === today.getDate() && viewMonth === today.getMonth() && viewYear === today.getFullYear();

  const upcomingDeadlines = deadlines
    .filter(d => {
      if (d.status === 'concluido') return false;
      const date = new Date(d.data_prazo + 'T12:00:00');
      const now = new Date();
      const diff = Math.ceil((date.getTime() - now.getTime()) / 86400000);
      return diff >= 0 && diff <= 7;
    })
    .sort((a, b) => new Date(a.data_prazo).getTime() - new Date(b.data_prazo).getTime());

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Calendário Jurídico</h1>
        <p className="text-muted-foreground">Visualize seus prazos processuais no calendário</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        {/* Calendar */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-xl">
                {MONTHS_PT[viewMonth]} {viewYear}
              </CardTitle>
              <div className="flex gap-2">
                <Button variant="outline" size="icon" onClick={prevMonth} aria-label="Mês anterior">
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => { setViewMonth(today.getMonth()); setViewYear(today.getFullYear()); }}
                >
                  Hoje
                </Button>
                <Button variant="outline" size="icon" onClick={nextMonth} aria-label="Próximo mês">
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="h-96 flex items-center justify-center text-muted-foreground">
                Carregando prazos...
              </div>
            ) : (
              <div className="overflow-hidden rounded-lg border">
                {/* Weekday headers */}
                <div className="grid grid-cols-7 bg-muted/50">
                  {WEEKDAYS.map(d => (
                    <div key={d} className="py-2 text-center text-xs font-medium text-muted-foreground">
                      {d}
                    </div>
                  ))}
                </div>

                {/* Weeks */}
                {weeks.map((week, wi) => (
                  <div key={wi} className="grid grid-cols-7 divide-x border-t">
                    {week.map((day, di) => {
                      const dayDeadlines = day ? (deadlinesByDay[day] || []) : [];
                      const hasUrgent = dayDeadlines.some(d => d.prioridade === 'urgente' || d.prioridade === 'alta');
                      return (
                        <div
                          key={di}
                          className={`min-h-[80px] p-1.5 ${!day ? 'bg-muted/20' : ''} ${isToday(day!) ? 'bg-primary/5' : ''}`}
                        >
                          {day && (
                            <>
                              <div className={`mb-1 flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium
                                ${isToday(day) ? 'bg-primary text-primary-foreground' : 'text-foreground'}`}>
                                {day}
                              </div>
                              <div className="space-y-0.5">
                                {dayDeadlines.slice(0, 2).map(d => (
                                  <div
                                    key={d.id}
                                    className={`flex items-center gap-1 rounded px-1 py-0.5 text-[10px] leading-tight
                                      ${d.status === 'concluido' ? 'bg-green-50 text-green-700' :
                                        (d.dias_restantes !== null && d.dias_restantes < 0) ? 'bg-red-50 text-red-700' :
                                        (d.dias_restantes !== null && d.dias_restantes <= 3) ? 'bg-orange-50 text-orange-700' :
                                        'bg-blue-50 text-blue-700'}`}
                                    title={d.titulo}
                                  >
                                    <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${prioridadeColor[d.prioridade] || 'bg-gray-400'}`} />
                                    <span className="truncate">{d.titulo}</span>
                                  </div>
                                ))}
                                {dayDeadlines.length > 2 && (
                                  <div className="text-[10px] text-muted-foreground px-1">
                                    +{dayDeadlines.length - 2} mais
                                  </div>
                                )}
                              </div>
                            </>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Sidebar: próximos 7 dias */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Próximos 7 dias</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {upcomingDeadlines.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">
                  Nenhum prazo nos próximos 7 dias
                </p>
              ) : (
                upcomingDeadlines.map(d => (
                  <div key={d.id} className="space-y-1">
                    <div className="flex items-start gap-2">
                      {statusIcon(d.status, d.dias_restantes)}
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium leading-tight truncate">{d.titulo}</p>
                        <p className="text-[10px] text-muted-foreground">
                          {new Date(d.data_prazo + 'T12:00:00').toLocaleDateString('pt-BR')}
                          {d.dias_restantes === 0 ? ' · Hoje' : d.dias_restantes === 1 ? ' · Amanhã' : ` · ${d.dias_restantes}d`}
                        </p>
                      </div>
                      <Badge className={`text-[10px] shrink-0 ${prioridadeColor[d.prioridade] || 'bg-gray-400'} text-white border-0`}>
                        {d.prioridade}
                      </Badge>
                    </div>
                  </div>
                ))
              )}
              <Link href="/dashboard/processos/prazos">
                <Button variant="outline" size="sm" className="w-full mt-2 text-xs">
                  Ver todos os prazos
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* Legend */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Legenda</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {[
                { color: 'bg-red-500', label: 'Urgente' },
                { color: 'bg-orange-400', label: 'Alta prioridade' },
                { color: 'bg-blue-400', label: 'Média prioridade' },
                { color: 'bg-gray-400', label: 'Baixa prioridade' },
              ].map(item => (
                <div key={item.label} className="flex items-center gap-2 text-xs">
                  <div className={`w-3 h-3 rounded-full ${item.color}`} />
                  <span>{item.label}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

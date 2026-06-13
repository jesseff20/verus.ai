'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Leaderboard, Badge as BadgeType } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Trophy, Medal, Star, Zap, Target, Clock, FileText, DollarSign, RefreshCw, Crown, Award } from 'lucide-react';
import { toast } from 'sonner';

const rankIcons = [Crown, Medal, Award];
const rankColors = ['text-yellow-500', 'text-gray-400', 'text-amber-600'];

export default function KPIsPage() {
  const queryClient = useQueryClient();
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);

  const { data, isLoading } = useQuery({
    queryKey: ['kpi-leaderboard', year, month],
    queryFn: async () => {
      const res = await api.get('/api/v1/processos/kpis/leaderboard/', { params: { year, month } });
      return res.data;
    },
    staleTime: 5 * 60 * 1000,
  });

  const recalculate = useMutation({
    mutationFn: async () => {
      const res = await api.post('/api/v1/processos/kpis/recalcular/', { year, month });
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['kpi-leaderboard'] });
      toast.success(data.message);
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || 'Erro ao processar');
    },
  });

  const leaderboard: Leaderboard[] = data?.leaderboard || [];
  const badges: BadgeType[] = data?.badges_available || [];
  const maxScore = leaderboard[0]?.total_score || 1;

  const monthNames = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2"><Trophy className="h-6 w-6 text-yellow-500" /> KPIs Gamificados</h1>
          <p className="text-muted-foreground">Ranking de produtividade — estilo Taskscore</p>
        </div>
        <div className="flex gap-2 items-center">
          <Select value={String(month)} onValueChange={(v) => setMonth(Number(v))}>
            <SelectTrigger className="w-[120px]"><SelectValue /></SelectTrigger>
            <SelectContent>{monthNames.map((m, i) => <SelectItem key={i} value={String(i+1)}>{m}</SelectItem>)}</SelectContent>
          </Select>
          <Select value={String(year)} onValueChange={(v) => setYear(Number(v))}>
            <SelectTrigger className="w-[100px]"><SelectValue /></SelectTrigger>
            <SelectContent>{[2024,2025,2026].map(y => <SelectItem key={y} value={String(y)}>{y}</SelectItem>)}</SelectContent>
          </Select>
          <Button variant="outline" onClick={() => recalculate.mutate()} disabled={recalculate.isPending}>
            <RefreshCw className={`h-4 w-4 mr-2 ${recalculate.isPending ? 'animate-spin' : ''}`} /> Recalcular
          </Button>
        </div>
      </div>

      {/* Podium - Top 3 */}
      {leaderboard.length >= 3 && (
        <div className="grid grid-cols-3 gap-4">
          {[1, 0, 2].map(idx => {
            const entry = leaderboard[idx];
            if (!entry) return null;
            const RankIcon = rankIcons[idx] || Award;
            return (
              <Card key={entry.lawyer_id} className={`${idx === 0 ? 'md:col-start-2 md:row-start-1 ring-2 ring-yellow-400' : ''}`}>
                <CardContent className="pt-6 text-center">
                  <RankIcon className={`h-10 w-10 mx-auto mb-2 ${rankColors[idx]}`} />
                  <Avatar className="h-14 w-14 mx-auto mb-2"><AvatarFallback className="text-lg">{entry.lawyer_name.split(' ').map((n: string) => n[0]).join('').slice(0,2)}</AvatarFallback></Avatar>
                  <p className="font-bold">{entry.lawyer_name}</p>
                  <p className="text-3xl font-bold text-primary mt-1">{entry.total_score}</p>
                  <p className="text-xs text-muted-foreground">pontos</p>
                  <div className="flex flex-wrap gap-1 justify-center mt-3">
                    {entry.badges?.map((b: BadgeType) => (
                      <span key={b.id} title={b.description} className="text-lg cursor-help">{b.icon}</span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Full Leaderboard */}
      <Card>
        <CardHeader><CardTitle>Ranking Completo</CardTitle><CardDescription>{monthNames[month-1]} {year}</CardDescription></CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Carregando ranking...</div>
          ) : leaderboard.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Trophy className="h-12 w-12 mx-auto mb-4 opacity-30" />
              <p>Nenhum score calculado para este período</p>
              <Button className="mt-4" onClick={() => recalculate.mutate()}>Calcular Agora</Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">#</TableHead><TableHead>Procurador</TableHead><TableHead className="text-center">Pontos</TableHead>
                  <TableHead className="text-center"><Target className="h-4 w-4 inline" /> Casos</TableHead>
                  <TableHead className="text-center"><Zap className="h-4 w-4 inline" /> Prazos</TableHead>
                  <TableHead className="text-center"><Clock className="h-4 w-4 inline" /> Horas</TableHead>
                  <TableHead className="text-center"><FileText className="h-4 w-4 inline" /> Docs</TableHead>
                  <TableHead className="text-center"><DollarSign className="h-4 w-4 inline" /> Receita</TableHead>
                  <TableHead>Badges</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {leaderboard.map((entry: Leaderboard) => (
                  <TableRow key={entry.lawyer_id}>
                    <TableCell className="font-bold text-lg">{entry.rank <= 3 ? <span className={rankColors[entry.rank - 1]}>{entry.rank}</span> : entry.rank}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Avatar className="h-8 w-8"><AvatarFallback className="text-xs">{entry.lawyer_name.split(' ').map((n: string) => n[0]).join('').slice(0,2)}</AvatarFallback></Avatar>
                        <span className="font-medium">{entry.lawyer_name}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <div className="space-y-1"><span className="font-bold text-lg">{entry.total_score}</span><Progress value={(entry.total_score / maxScore) * 100} className="h-1.5" /></div>
                    </TableCell>
                    <TableCell className="text-center"><Badge variant="outline">{entry.cases_won}W</Badge></TableCell>
                    <TableCell className="text-center">
                      <span className="text-green-600">{entry.deadlines_met}</span>/<span className="text-red-500">{entry.deadlines_missed}</span>
                    </TableCell>
                    <TableCell className="text-center">{entry.hours_logged.toFixed(0)}h</TableCell>
                    <TableCell className="text-center">{entry.tasks_completed}</TableCell>
                    <TableCell className="text-center">R$ {entry.revenue_generated.toLocaleString('pt-BR')}</TableCell>
                    <TableCell>
                      <div className="flex gap-1">{entry.badges?.map((b: BadgeType) => <span key={b.id} title={`${b.name}: ${b.description}`} className="cursor-help">{b.icon}</span>)}</div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Available Badges */}
      <Card>
        <CardHeader><CardTitle>Conquistas Disponíveis</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
            {badges.map((b: BadgeType) => (
              <div key={b.id} className="text-center p-3 rounded-lg border hover:bg-accent transition-colors">
                <span className="text-3xl block mb-2">{b.icon}</span>
                <p className="font-semibold text-sm">{b.name}</p>
                <p className="text-xs text-muted-foreground mt-1">{b.description}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

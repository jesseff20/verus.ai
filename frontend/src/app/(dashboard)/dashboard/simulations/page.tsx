'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useSimulations, useDeleteSimulation, useDuplicateSimulation } from '@/hooks/use-simulations';
import { useToast } from '@/hooks/use-toast';
import type { Simulation } from '@/types';
import {
  Users, Scale, Clock, ArrowRight, FlaskConical, CheckCircle2,
  Loader2, AlertCircle, Trash2, Copy, Filter, Eye, Landmark, Building,
  Gavel, Vote, Swords, ShieldCheck,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

const STATUS_MAP: Record<string, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
  draft: { label: 'Rascunho', variant: 'outline' },
  configuring: { label: 'Configurando', variant: 'outline' },
  running: { label: 'Em andamento', variant: 'secondary' },
  deliberating: { label: 'Deliberando', variant: 'secondary' },
  completed: { label: 'Concluída', variant: 'default' },
  failed: { label: 'Falhou', variant: 'destructive' },
};

function getResultBadge(sim: Simulation) {
  const summary = sim.result_summary;
  if (!summary) return null;

  // Judge simulation
  if (summary.dispositivo) {
    const labels: Record<string, { text: string; className: string }> = {
      procedente: { text: 'Procedente', className: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' },
      improcedente: { text: 'Improcedente', className: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' },
      parcialmente_procedente: { text: 'Parcial', className: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200' },
    };
    const item = labels[summary.dispositivo];
    if (item) {
      return <Badge className={`${item.className} border-0 text-xs`}>{item.text}</Badge>;
    }
  }

  // Jury simulation
  if (summary.verdict) {
    const isCondenacao = summary.verdict === 'condenacao';
    return (
      <Badge
        className={`border-0 text-xs ${
          isCondenacao
            ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
            : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
        }`}
      >
        {isCondenacao ? 'Condenação' : 'Absolvição'}
      </Badge>
    );
  }

  return null;
}

export default function SimulationsPage() {
  const router = useRouter();
  const { toast } = useToast();

  // Filters
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const filters: Record<string, string> = {};
  if (typeFilter !== 'all') filters.simulation_type = typeFilter;
  if (statusFilter !== 'all') filters.status = statusFilter;

  const { data: simulations, isLoading } = useSimulations(
    Object.keys(filters).length > 0 ? (filters as any) : undefined,
  );

  // Delete
  const deleteMutation = useDeleteSimulation();
  const [deleteTarget, setDeleteTarget] = useState<Simulation | null>(null);

  const handleDelete = useCallback(async () => {
    if (!deleteTarget) return;
    try {
      await deleteMutation.mutateAsync(deleteTarget.id);
      toast({ title: 'Simulação excluída', description: `"${deleteTarget.title}" foi removida do histórico.` });
    } catch {
      toast({ title: 'Erro', description: 'Não foi possível excluir a simulação.', variant: 'destructive' });
    } finally {
      setDeleteTarget(null);
    }
  }, [deleteTarget, deleteMutation, toast]);

  // Duplicate
  const duplicateMutation = useDuplicateSimulation();

  const handleDuplicate = useCallback(async (sim: Simulation) => {
    try {
      const newSim = await duplicateMutation.mutateAsync(sim.id);
      toast({ title: 'Simulação duplicada', description: `"${newSim.title}" criada como cópia.` });
      // Navigate to the appropriate simulation page
      const typeRouteMap: Record<string, string> = {
        jury: '/dashboard/simulations/jury',
        judge: '/dashboard/simulations/judge',
        stf: '/dashboard/simulations/stf',
        acordao_2inst: '/dashboard/simulations/acordao',
        stj: '/dashboard/simulations/stj',
        jec: '/dashboard/simulations/jec',
        jecrim: '/dashboard/simulations/jecrim',
        trabalho: '/dashboard/simulations/trabalho',
        trt: '/dashboard/simulations/trt',
        tst: '/dashboard/simulations/tst-trabalho',
        eleitoral: '/dashboard/simulations/eleitoral',
        tre: '/dashboard/simulations/eleitoral',
        tse: '/dashboard/simulations/eleitoral',
        turma_recursal: '/dashboard/simulations/turma-recursal',
        militar: '/dashboard/simulations/militar',
        stm: '/dashboard/simulations/stm',
      };
      router.push(typeRouteMap[sim.simulation_type] || '/dashboard/simulations/judge');
    } catch {
      toast({ title: 'Erro', description: 'Não foi possível duplicar a simulação.', variant: 'destructive' });
    }
  }, [duplicateMutation, toast, router]);

  const handleViewSimulation = useCallback((sim: Simulation) => {
    // Navigate to the appropriate detail/result page with simulation ID
    const typeRouteMap: Record<string, string> = {
      jury: '/dashboard/simulations/jury',
      judge: '/dashboard/simulations/judge',
      stf: '/dashboard/simulations/stf',
      acordao_2inst: '/dashboard/simulations/acordao',
      stj: '/dashboard/simulations/stj',
      jec: '/dashboard/simulations/jec',
      jecrim: '/dashboard/simulations/jecrim',
      trabalho: '/dashboard/simulations/trabalho',
      trt: '/dashboard/simulations/trt',
      tst: '/dashboard/simulations/tst-trabalho',
      eleitoral: '/dashboard/simulations/eleitoral',
      tre: '/dashboard/simulations/eleitoral',
      tse: '/dashboard/simulations/eleitoral',
      turma_recursal: '/dashboard/simulations/turma-recursal',
      militar: '/dashboard/simulations/militar',
      stm: '/dashboard/simulations/stm',
    };
    const base = typeRouteMap[sim.simulation_type] || '/dashboard/simulations/judge';
    router.push(`${base}?id=${sim.id}`);
  }, [router]);

  const formatDate = (d: string) =>
    new Date(d).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-2">
          <FlaskConical className="h-8 w-8 text-primary" />
          <h1 className="text-3xl font-bold tracking-tight">Simulações Jurídicas</h1>
        </div>
        <p className="text-muted-foreground text-lg">
          Simule julgamentos e sentenças com IA para análise estratégica
        </p>
      </div>

      {/* Data quality warning */}
      <Card className="border-amber-200 bg-amber-50/50 dark:border-amber-900 dark:bg-amber-950/20">
        <CardContent className="flex gap-4 py-4">
          <AlertCircle className="h-6 w-6 text-amber-500 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-amber-800 dark:text-amber-200">
              A qualidade da simulação depende diretamente da qualidade dos dados fornecidos
            </p>
            <p className="text-sm text-amber-700 dark:text-amber-300 mt-1 leading-relaxed">
              Quanto mais documentos do processo, detalhes dos fatos, provas, perícias e contexto você fornecer,
              mais precisa e realista será a simulação. Anexe a denúncia completa, laudos periciais, depoimentos
              de testemunhas e todas as peças relevantes para obter uma previsão confiável do resultado.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Module Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-3">
        {/* Jury */}
        <Card className="relative overflow-hidden border-2 hover:border-primary/50 transition-colors cursor-pointer group">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-500/10 text-blue-600">
                <Users className="h-6 w-6" />
              </div>
              <div>
                <CardTitle className="text-xl">Simulação de Júri</CardTitle>
                <Badge variant="secondary" className="mt-1">IA</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <CardDescription className="text-sm leading-relaxed">
              Simule uma sessão completa do Tribunal do Júri com jurados virtuais dotados de personalidades
              distintas. Acompanhe debates entre acusação e defesa, réplicas, tréplicas e a deliberação
              final com votação dos quesitos conforme o CPP.
            </CardDescription>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                7 jurados com perfis customizáveis
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Debates com streaming em tempo real
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Votação de quesitos conforme CPP art. 483
              </li>
            </ul>
            <Button
              className="w-full group-hover:bg-primary"
              onClick={() => router.push('/dashboard/simulations/jury')}
            >
              Iniciar Simulação
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        {/* Judge */}
        <Card className="relative overflow-hidden border-2 hover:border-primary/50 transition-colors cursor-pointer group">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-500/10 text-amber-600">
                <Scale className="h-6 w-6" />
              </div>
              <div>
                <CardTitle className="text-xl">Simulação de Sentença</CardTitle>
                <Badge variant="secondary" className="mt-1">IA</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <CardDescription className="text-sm leading-relaxed">
              Simule como um juiz específico decidiria seu caso. A IA analisa o perfil do magistrado,
              suas decisões anteriores e padrões de fundamentação para gerar uma sentença simulada
              com alto grau de fidelidade.
            </CardDescription>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Perfil do juiz baseado em decisões reais
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Sentença completa com fundamentação
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Exportação em PDF e DOCX
              </li>
            </ul>
            <Button
              className="w-full group-hover:bg-primary"
              onClick={() => router.push('/dashboard/simulations/judge')}
            >
              Iniciar Simulação
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        {/* STF */}
        <Card className="relative overflow-hidden border-2 hover:border-primary/50 transition-colors cursor-pointer group">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600">
                <Landmark className="h-6 w-6" />
              </div>
              <div>
                <CardTitle className="text-xl">Simulação STF</CardTitle>
                <Badge variant="secondary" className="mt-1">IA</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <CardDescription className="text-sm leading-relaxed">
              Simule um julgamento no Supremo Tribunal Federal com os 11 ministros reais.
              Cada ministro vota individualmente com base em sua filosofia judicial,
              posições anteriores e estilo de fundamentação.
            </CardDescription>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                11 ministros com perfis reais
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Votos individuais com fundamentação
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Plenário, 1a ou 2a Turma
              </li>
            </ul>
            <Button
              className="w-full group-hover:bg-primary"
              onClick={() => router.push('/dashboard/simulations/stf')}
            >
              Iniciar Simulação
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        {/* 2a Instancia */}
        <Card className="relative overflow-hidden border-2 hover:border-primary/50 transition-colors cursor-pointer group">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-500/10 text-amber-600">
                <Landmark className="h-6 w-6" />
              </div>
              <div>
                <CardTitle className="text-xl">2a Instancia (TJ/TRF)</CardTitle>
                <Badge variant="secondary" className="mt-1">IA</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <CardDescription className="text-sm leading-relaxed">
              Simule um acordao de 2a instancia com 3 desembargadores (Relator, Revisor e Vogal).
              A IA gera o relatorio, votos individuais, ementa e proclamacao do resultado.
            </CardDescription>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                3 desembargadores (Relator, Revisor, Vogal)
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Ementa e acordao completo
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                TJs estaduais e TRFs
              </li>
            </ul>
            <Button
              className="w-full group-hover:bg-primary"
              onClick={() => router.push('/dashboard/simulations/acordao')}
            >
              Iniciar Simulação
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        {/* STJ */}
        <Card className="relative overflow-hidden border-2 hover:border-primary/50 transition-colors cursor-pointer group">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-600">
                <Building className="h-6 w-6" />
              </div>
              <div>
                <CardTitle className="text-xl">Simulação STJ</CardTitle>
                <Badge variant="secondary" className="mt-1">IA</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <CardDescription className="text-sm leading-relaxed">
              Simule um julgamento no Superior Tribunal de Justiça com 5 ministros por Turma
              ou 10 por Secao. Foco em legislacao infraconstitucional (REsp, HC, CC).
            </CardDescription>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                5 ministros por Turma / 10 por Secao
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                REsp, HC, conflitos de competencia
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                6 Turmas e 3 Secoes
              </li>
            </ul>
            <Button
              className="w-full group-hover:bg-primary"
              onClick={() => router.push('/dashboard/simulations/stj')}
            >
              Iniciar Simulação
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        {/* Vara do Trabalho */}
        <Card className="relative overflow-hidden border-2 hover:border-primary/50 transition-colors cursor-pointer group">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-orange-500/10 text-orange-600">
                <Scale className="h-6 w-6" />
              </div>
              <div>
                <CardTitle className="text-xl">Vara do Trabalho</CardTitle>
                <Badge variant="secondary" className="mt-1">IA</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <CardDescription className="text-sm leading-relaxed">
              Simule uma sentenca da Vara do Trabalho (1a instancia). Conciliacao obrigatoria
              (CLT art. 846), instrucao e sentenca com calculos de verbas rescisorias.
            </CardDescription>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-green-500" />Conciliacao obrigatoria (CLT art. 846)</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-green-500" />Analise por pedido (verbas, horas extras, FGTS)</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-green-500" />Sentenca com calculos trabalhistas</li>
            </ul>
            <Button className="w-full group-hover:bg-primary" onClick={() => router.push('/dashboard/simulations/trabalho')}>
              Iniciar Simulação
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        {/* TRT */}
        <Card className="relative overflow-hidden border-2 hover:border-primary/50 transition-colors cursor-pointer group">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-orange-500/10 text-orange-600">
                <Landmark className="h-6 w-6" />
              </div>
              <div>
                <CardTitle className="text-xl">TRT - 2a Instancia</CardTitle>
                <Badge variant="secondary" className="mt-1">IA</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <CardDescription className="text-sm leading-relaxed">
              Simule um acordao do TRT com 3 desembargadores (Relator, Revisor, Vogal).
              Recurso Ordinario contra sentenca trabalhista (CLT/sumulas TST).
            </CardDescription>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-green-500" />3 desembargadores trabalhistas</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-green-500" />Recurso Ordinario (CLT/sumulas TST)</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-green-500" />Ementa e acordao completo</li>
            </ul>
            <Button className="w-full group-hover:bg-primary" onClick={() => router.push('/dashboard/simulations/trt')}>
              Iniciar Simulação
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        {/* TST */}
        <Card className="relative overflow-hidden border-2 hover:border-primary/50 transition-colors cursor-pointer group">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-orange-500/10 text-orange-600">
                <Building className="h-6 w-6" />
              </div>
              <div>
                <CardTitle className="text-xl">TST</CardTitle>
                <Badge variant="secondary" className="mt-1">IA</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <CardDescription className="text-sm leading-relaxed">
              Simule um julgamento no TST com 5 ministros por Turma.
              Recurso de Revista, Embargos, CLT, sumulas e OJs. 8 Turmas + SDI-1/2 + SDC.
            </CardDescription>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-green-500" />5 ministros por Turma</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-green-500" />RR, Embargos, CLT e sumulas</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-green-500" />8 Turmas + SDI-1 + SDI-2 + SDC</li>
            </ul>
            <Button className="w-full group-hover:bg-primary" onClick={() => router.push('/dashboard/simulations/tst-trabalho')}>
              Iniciar Simulação
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        {/* JEC */}
        <Card className="relative overflow-hidden border-2 hover:border-primary/50 transition-colors cursor-pointer group">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-teal-500/10 text-teal-600">
                <Gavel className="h-6 w-6" />
              </div>
              <div>
                <CardTitle className="text-xl">JEC - Juizado Especial Cível</CardTitle>
                <Badge variant="secondary" className="mt-1">IA</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <CardDescription className="text-sm leading-relaxed">
              Simule um procedimento completo no Juizado Especial Cível (Lei 9.099/95).
              Inclui triagem de competência, audiência de conciliação obrigatória,
              instrução e sentença simplificada.
            </CardDescription>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Conciliação obrigatória (50% chance de acordo)
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Sentença simplificada (art. 38)
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Causas até 40 salários mínimos
              </li>
            </ul>
            <Button
              className="w-full group-hover:bg-primary"
              onClick={() => router.push('/dashboard/simulations/jec')}
            >
              Iniciar Simulação
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        {/* JECRIM */}
        <Card className="relative overflow-hidden border-2 hover:border-primary/50 transition-colors cursor-pointer group">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-rose-500/10 text-rose-600">
                <Gavel className="h-6 w-6" />
              </div>
              <div>
                <CardTitle className="text-xl">JECRIM - Juizado Especial Criminal</CardTitle>
                <Badge variant="secondary" className="mt-1">IA</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <CardDescription className="text-sm leading-relaxed">
              Simule o procedimento do Juizado Especial Criminal (Lei 9.099/95).
              Inclui transação penal (art. 76), suspensão condicional (art. 89)
              e instrução criminal simplificada.
            </CardDescription>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Transação penal (art. 76)
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Suspensão condicional (art. 89)
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Infrações de menor potencial ofensivo
              </li>
            </ul>
            <Button
              className="w-full group-hover:bg-primary"
              onClick={() => router.push('/dashboard/simulations/jecrim')}
            >
              Iniciar Simulação
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        {/* Eleitoral */}
        <Card className="relative overflow-hidden border-2 hover:border-primary/50 transition-colors cursor-pointer group">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-500/10 text-purple-600">
                <Vote className="h-6 w-6" />
              </div>
              <div>
                <CardTitle className="text-xl">Justica Eleitoral</CardTitle>
                <Badge variant="secondary" className="mt-1">IA</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <CardDescription className="text-sm leading-relaxed">
              Simule julgamentos na Justica Eleitoral: sentenca de Juiz Eleitoral (1a instancia),
              acordao do TRE (7 membros) ou julgamento do TSE (7 ministros).
            </CardDescription>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Juiz Eleitoral, TRE e TSE
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Propaganda, registro, cassacao
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                TRE: 7 membros / TSE: 7 ministros
              </li>
            </ul>
            <Button
              className="w-full group-hover:bg-primary"
              onClick={() => router.push('/dashboard/simulations/eleitoral')}
            >
              Iniciar Simulação
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        {/* Turma Recursal */}
        <Card className="relative overflow-hidden border-2 hover:border-primary/50 transition-colors cursor-pointer group">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-600">
                <Scale className="h-6 w-6" />
              </div>
              <div>
                <CardTitle className="text-xl">Turma Recursal</CardTitle>
                <Badge variant="secondary" className="mt-1">IA</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <CardDescription className="text-sm leading-relaxed">
              Simule o julgamento de Recurso Inominado pela Turma Recursal dos Juizados Especiais.
              3 juizes de primeiro grau (nao desembargadores) analisam a sentenca do JEC/JECRIM.
            </CardDescription>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                3 juizes de 1o grau (Relator + 2 vogais)
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Acordao simplificado (Lei 9.099/95)
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Reforma / mantem / reforma parcial
              </li>
            </ul>
            <Button
              className="w-full group-hover:bg-primary"
              onClick={() => router.push('/dashboard/simulations/turma-recursal')}
            >
              Iniciar Simulação
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        {/* Justica Militar */}
        <Card className="relative overflow-hidden border-2 hover:border-primary/50 transition-colors cursor-pointer group">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-stone-500/10 text-stone-600">
                <Swords className="h-6 w-6" />
              </div>
              <div>
                <CardTitle className="text-xl">Justica Militar</CardTitle>
                <Badge variant="secondary" className="mt-1">IA</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <CardDescription className="text-sm leading-relaxed">
              Simule um julgamento na Auditoria de Justica Militar com Conselho de Justica:
              1 Juiz Auditor + 4 Oficiais Militares. Inclui interrogatorio, debates e votacao.
            </CardDescription>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Conselho de 5 membros (1 togado + 4 oficiais)
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Interrogatorio e debates completos
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                CPM e CPPM (desercao, insubordinacao, etc.)
              </li>
            </ul>
            <Button
              className="w-full group-hover:bg-primary"
              onClick={() => router.push('/dashboard/simulations/militar')}
            >
              Iniciar Simulação
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        {/* STM */}
        <Card className="relative overflow-hidden border-2 hover:border-primary/50 transition-colors cursor-pointer group">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-stone-500/10 text-stone-700">
                <ShieldCheck className="h-6 w-6" />
              </div>
              <div>
                <CardTitle className="text-xl">Simulação STM</CardTitle>
                <Badge variant="secondary" className="mt-1">IA</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <CardDescription className="text-sm leading-relaxed">
              Simule um julgamento no Superior Tribunal Militar com 15 ministros:
              5 civis (advogados, juiz, MPM) e 10 militares (Exercito, Marinha, Aeronautica).
            </CardDescription>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                15 ministros (5 civis + 10 militares)
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Votos individuais com fundamentacao
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Apelacao militar, HC, revisao criminal
              </li>
            </ul>
            <Button
              className="w-full group-hover:bg-primary"
              onClick={() => router.push('/dashboard/simulations/stm')}
            >
              Iniciar Simulação
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* History Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Histórico de Simulações</h2>
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-[150px] h-8 text-xs">
                <SelectValue placeholder="Tipo" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos os tipos</SelectItem>
                <SelectItem value="jury">Júri</SelectItem>
                <SelectItem value="judge">Sentença</SelectItem>
                <SelectItem value="stf">STF</SelectItem>
                <SelectItem value="acordao_2inst">2a Instância</SelectItem>
                <SelectItem value="stj">STJ</SelectItem>
                <SelectItem value="trabalho">Vara do Trabalho</SelectItem>
                <SelectItem value="trt">TRT</SelectItem>
                <SelectItem value="tst">TST</SelectItem>
                <SelectItem value="jec">JEC</SelectItem>
                <SelectItem value="jecrim">JECRIM</SelectItem>
                <SelectItem value="eleitoral">Eleitoral</SelectItem>
                <SelectItem value="tre">TRE</SelectItem>
                <SelectItem value="tse">TSE</SelectItem>
                <SelectItem value="turma_recursal">Turma Recursal</SelectItem>
                <SelectItem value="militar">Militar</SelectItem>
                <SelectItem value="stm">STM</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[150px] h-8 text-xs">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos os status</SelectItem>
                <SelectItem value="completed">Concluídas</SelectItem>
                <SelectItem value="running">Em andamento</SelectItem>
                <SelectItem value="draft">Rascunho</SelectItem>
                <SelectItem value="failed">Falhou</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <Separator className="mb-4" />

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : !simulations || simulations.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12 text-center">
              <FlaskConical className="h-12 w-12 text-muted-foreground/40 mb-4" />
              <p className="text-muted-foreground font-medium">Nenhuma simulação encontrada</p>
              <p className="text-sm text-muted-foreground mt-1">
                {typeFilter !== 'all' || statusFilter !== 'all'
                  ? 'Tente ajustar os filtros acima.'
                  : 'Inicie uma simulação de júri ou sentença acima para começar.'}
              </p>
            </CardContent>
          </Card>
        ) : (
          <ScrollArea className="h-[500px]">
            <div className="space-y-3">
              {simulations.map((sim) => {
                const statusInfo = STATUS_MAP[sim.status] || { label: sim.status, variant: 'outline' as const };
                const resultBadge = getResultBadge(sim);

                return (
                  <Card
                    key={sim.id}
                    className="hover:bg-accent/50 transition-colors cursor-pointer group/card"
                    onClick={() => handleViewSimulation(sim)}
                  >
                    <CardContent className="flex items-center justify-between p-4">
                      <div className="flex items-center gap-4 flex-1 min-w-0">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted shrink-0">
                          {sim.simulation_type === 'jury' ? (
                            <Users className="h-5 w-5 text-blue-600" />
                          ) : sim.simulation_type === 'stf' ? (
                            <Landmark className="h-5 w-5 text-emerald-600" />
                          ) : sim.simulation_type === 'acordao_2inst' ? (
                            <Landmark className="h-5 w-5 text-amber-600" />
                          ) : sim.simulation_type === 'stj' ? (
                            <Building className="h-5 w-5 text-indigo-600" />
                          ) : sim.simulation_type === 'trabalho' ? (
                            <Scale className="h-5 w-5 text-orange-600" />
                          ) : sim.simulation_type === 'trt' ? (
                            <Landmark className="h-5 w-5 text-orange-600" />
                          ) : sim.simulation_type === 'tst' ? (
                            <Building className="h-5 w-5 text-orange-600" />
                          ) : sim.simulation_type === 'jec' ? (
                            <Gavel className="h-5 w-5 text-teal-600" />
                          ) : sim.simulation_type === 'jecrim' ? (
                            <Gavel className="h-5 w-5 text-rose-600" />
                          ) : sim.simulation_type === 'eleitoral' || sim.simulation_type === 'tre' || sim.simulation_type === 'tse' ? (
                            <Vote className="h-5 w-5 text-purple-600" />
                          ) : sim.simulation_type === 'turma_recursal' ? (
                            <Scale className="h-5 w-5 text-cyan-600" />
                          ) : sim.simulation_type === 'militar' ? (
                            <Swords className="h-5 w-5 text-stone-600" />
                          ) : sim.simulation_type === 'stm' ? (
                            <ShieldCheck className="h-5 w-5 text-stone-600" />
                          ) : (
                            <Scale className="h-5 w-5 text-amber-600" />
                          )}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="font-medium text-sm truncate">{sim.title}</p>
                          <div className="flex items-center gap-2 mt-1 flex-wrap">
                            <Badge variant="outline" className="text-xs">
                              {{ jury: 'Júri', judge: 'Sentença', stf: 'STF', acordao_2inst: '2a Instância', stj: 'STJ', trabalho: 'Vara do Trabalho', trt: 'TRT', tst: 'TST', jec: 'JEC', jecrim: 'JECRIM', eleitoral: 'Eleitoral', tre: 'TRE', tse: 'TSE', turma_recursal: 'Turma Recursal', militar: 'Militar', stm: 'STM' }[sim.simulation_type] || sim.simulation_type}
                            </Badge>
                            <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
                            {resultBadge}
                            {sim.case_title && (
                              <span className="text-xs text-muted-foreground truncate max-w-[200px]">
                                {sim.case_title}
                              </span>
                            )}
                            <span className="text-xs text-muted-foreground flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {formatDate(sim.created_at)}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Action buttons */}
                      <div className="flex items-center gap-1 shrink-0 ml-2 opacity-0 group-hover/card:opacity-100 transition-opacity">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          title="Ver detalhes"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleViewSimulation(sim);
                          }}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          title="Refazer simulação"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDuplicate(sim);
                          }}
                          disabled={duplicateMutation.isPending}
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-destructive hover:text-destructive"
                          title="Excluir simulação"
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeleteTarget(sim);
                          }}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>

                      <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0 ml-2 group-hover/card:hidden" />
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </ScrollArea>
        )}
      </div>

      {/* Delete confirmation dialog */}
      <AlertDialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir simulação?</AlertDialogTitle>
            <AlertDialogDescription>
              A simulação &quot;{deleteTarget?.title}&quot; será removida do histórico.
              Esta ação pode ser desfeita pelo administrador.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Trash2 className="h-4 w-4 mr-2" />
              )}
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

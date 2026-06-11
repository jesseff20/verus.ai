'use client';

import { useState } from 'react';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Database,
  Search,
  RefreshCw,
  Scale,
  Users,
  Clock,
  CheckCircle2,
  ArrowRight,
} from 'lucide-react';
import {
  useDataJudSearch,
  useDataJudSync,
  type DataJudResult,
} from '@/hooks/use-datajud';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

function formatProcessoMask(value: string): string {
  const digits = value.replace(/\D/g, '').slice(0, 20);
  let formatted = '';
  if (digits.length > 0) formatted += digits.slice(0, 7);
  if (digits.length > 7) formatted += '-' + digits.slice(7, 9);
  if (digits.length > 9) formatted += '.' + digits.slice(9, 13);
  if (digits.length > 13) formatted += '.' + digits.slice(13, 14);
  if (digits.length > 14) formatted += '.' + digits.slice(14, 16);
  if (digits.length > 16) formatted += '.' + digits.slice(16, 20);
  return formatted;
}

function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  } catch {
    return dateStr;
  }
}

function formatDateTime(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
}

export default function DataJudPage() {
  const [numeroProcesso, setNumeroProcesso] = useState('');
  const [result, setResult] = useState<DataJudResult | null>(null);
  const [selectedCaseId, setSelectedCaseId] = useState('');

  const searchMutation = useDataJudSearch();
  const syncMutation = useDataJudSync();

  // Buscar casos para dropdown de sincronização
  const { data: casesData } = useQuery({
    queryKey: ['cases-list-simple'],
    queryFn: async () => {
      const res = await api.get('/api/v1/processos/', { params: { page_size: 100 } });
      return res.data?.results || [];
    },
  });

  const handleSearch = async () => {
    const clean = numeroProcesso.replace(/\D/g, '');
    if (clean.length < 13) {
      toast.error('Informe um número de processo válido.');
      return;
    }

    try {
      const data = await searchMutation.mutateAsync(numeroProcesso);
      setResult(data);
      toast.success('Processo encontrado no DataJud.');
    } catch {
      toast.error('Erro ao buscar processo no DataJud.');
    }
  };

  const handleSync = async () => {
    if (!selectedCaseId) {
      toast.error('Selecione um caso para sincronizar.');
      return;
    }

    try {
      const data = await syncMutation.mutateAsync(selectedCaseId);
      toast.success(data.message || 'Sincronizado com sucesso.');
    } catch {
      toast.error('Erro ao sincronizar com o caso.');
    }
  };

  return (
    <div className="flex flex-col gap-6 p-4 md:p-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Database className="h-8 w-8 text-primary" />
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Consulta DataJud / CNJ</h1>
          <p className="text-sm text-muted-foreground">
            Busque processos na base de dados do Conselho Nacional de Justiça
          </p>
        </div>
      </div>

      {/* Search Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Buscar Processo
          </CardTitle>
          <CardDescription>
            Informe o número do processo no formato CNJ (NNNNNNN-NN.NNNN.N.NN.NNNN)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3 items-end">
            <div className="flex-1">
              <Label htmlFor="numero_processo">Número do Processo</Label>
              <Input
                id="numero_processo"
                placeholder="0000000-00.0000.0.00.0000"
                value={numeroProcesso}
                onChange={(e) => setNumeroProcesso(formatProcessoMask(e.target.value))}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              />
            </div>
            <Button onClick={handleSearch} disabled={searchMutation.isPending}>
              {searchMutation.isPending ? (
                <RefreshCw className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Search className="h-4 w-4 mr-2" />
              )}
              Buscar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Loading */}
      {searchMutation.isPending && (
        <Card>
          <CardContent className="pt-6 space-y-3">
            <Skeleton className="h-6 w-1/3" />
            <Skeleton className="h-4 w-2/3" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-4 w-3/4" />
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {result && !searchMutation.isPending && (
        <>
          {/* Process Info Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Scale className="h-5 w-5" />
                Dados do Processo
              </CardTitle>
              <CardDescription>{result.numero}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Tribunal</p>
                  <p className="font-medium">{result.tribunal}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Vara</p>
                  <p className="font-medium">{result.vara}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Classe</p>
                  <p className="font-medium">{result.classe}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Status</p>
                  <Badge variant={result.status === 'Em andamento' ? 'default' : 'secondary'}>
                    {result.status}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Valor da Causa</p>
                  <p className="font-medium">{formatCurrency(result.valor_causa)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Data de Distribuição</p>
                  <p className="font-medium">{formatDate(result.data_distribuicao)}</p>
                </div>
                <div className="col-span-full">
                  <p className="text-sm text-muted-foreground">Assuntos</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {result.assuntos.map((a, i) => (
                      <Badge key={i} variant="outline">{a}</Badge>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Partes Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Partes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Badge>Autor</Badge>
                  <p className="font-medium">{result.partes.autor.nome}</p>
                  {result.partes.autor.advogados.map((adv, i) => (
                    <p key={i} className="text-sm text-muted-foreground">{adv}</p>
                  ))}
                </div>
                <div className="space-y-2">
                  <Badge variant="secondary">Réu</Badge>
                  <p className="font-medium">{result.partes.reu.nome}</p>
                  {result.partes.reu.advogados.map((adv, i) => (
                    <p key={i} className="text-sm text-muted-foreground">{adv}</p>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Movimentações Timeline */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Movimentações
              </CardTitle>
              <CardDescription>Últimas movimentações processuais</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {result.movimentacoes.map((mov, i) => (
                  <div key={mov.id} className="flex gap-4">
                    <div className="flex flex-col items-center">
                      <div className="w-3 h-3 rounded-full bg-primary mt-1" />
                      {i < result.movimentacoes.length - 1 && (
                        <div className="w-0.5 flex-1 bg-border mt-1" />
                      )}
                    </div>
                    <div className="flex-1 pb-4">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline" className="text-xs">{mov.tipo}</Badge>
                        <span className="text-xs text-muted-foreground">
                          {formatDateTime(mov.data)}
                        </span>
                      </div>
                      <p className="text-sm">{mov.descricao}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Sync Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <RefreshCw className="h-5 w-5" />
                Sincronizar com Caso
              </CardTitle>
              <CardDescription>
                Atualize um caso existente com os dados obtidos do DataJud
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-3 items-end">
                <div className="flex-1">
                  <Label>Selecione o Caso</Label>
                  <Select value={selectedCaseId} onValueChange={setSelectedCaseId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione um caso..." />
                    </SelectTrigger>
                    <SelectContent>
                      {(casesData || []).map((c: { id: string; titulo: string; numero_processo?: string }) => (
                        <SelectItem key={c.id} value={c.id}>
                          {c.titulo} {c.numero_processo ? `(${c.numero_processo})` : ''}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={handleSync} disabled={syncMutation.isPending || !selectedCaseId}>
                  {syncMutation.isPending ? (
                    <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <ArrowRight className="h-4 w-4 mr-2" />
                  )}
                  Sincronizar
                </Button>
              </div>
              {syncMutation.isSuccess && syncMutation.data && (
                <div className="mt-4 p-3 bg-green-50 dark:bg-green-950/20 rounded-lg flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <span className="text-sm text-green-700 dark:text-green-400">
                    {syncMutation.data.message}
                  </span>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

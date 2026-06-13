'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { ConflictCheckResult, ConflictDetail } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { Shield, Search, AlertTriangle, CheckCircle, XCircle, Scale, FileSearch, Users, Database, BookOpen, Clock } from 'lucide-react';
import { toast } from 'sonner';

export default function ConflictCheckPage() {
  const [name, setName] = useState('');
  const [cpfCnpj, setCpfCnpj] = useState('');
  const [result, setResult] = useState<ConflictCheckResult | null>(null);

  const check = useMutation({
    mutationFn: async () => {
      const res = await api.post('/api/v1/processos/conflito-interesses/', { name, cpf_cnpj: cpfCnpj });
      return res.data as ConflictCheckResult;
    },
    onSuccess: (data) => {
      setResult(data);
      if (data.has_conflicts) toast.warning(`${data.total_conflicts} conflito(s) encontrado(s)!`);
      else toast.success('Nenhum conflito identificado');
    },
    onError: () => toast.error('Erro na verificação'),
  });

  const severityColors: Record<string, string> = { critical: 'destructive', warning: 'default', none: 'secondary' };
  const severityIcons: Record<string, any> = { critical: XCircle, warning: AlertTriangle, none: CheckCircle };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2"><Shield className="h-6 w-6" /> Verificação de Conflito de Interesses</h1>
        <p className="text-muted-foreground">OAB Art. 19 — Obrigatório antes de cadastrar novo cliente</p>
      </div>

      <Card>
        <CardHeader><CardTitle>Dados para Verificação</CardTitle><CardDescription>Informe os dados da potencial parte para cruzar com partes adversas</CardDescription></CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div><Label>Nome Completo *</Label><Input value={name} onChange={e => setName(e.target.value)} placeholder="Nome da potencial parte" /></div>
            <div><Label>CPF/CNPJ</Label><Input value={cpfCnpj} onChange={e => setCpfCnpj(e.target.value)} placeholder="000.000.000-00" /></div>
          </div>
          <Button onClick={() => check.mutate()} disabled={!name || check.isPending} className="w-full">
            {check.isPending ? 'Verificando...' : <><Search className="h-4 w-4 mr-2" /> Verificar Conflitos</>}
          </Button>
        </CardContent>
      </Card>

      {result && (
        <div className="space-y-4">
          <Alert variant={result.severity === 'critical' ? 'destructive' : 'default'}>
            {result.severity === 'none' ? <CheckCircle className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
            <AlertTitle>{result.has_conflicts ? `${result.total_conflicts} conflito(s) encontrado(s)` : 'Verificação concluída com sucesso'}</AlertTitle>
            <AlertDescription>{result.has_conflicts ? result.oab_reference : 'Nenhum conflito de interesses identificado. A potencial parte pode ser registrada.'}</AlertDescription>
          </Alert>

          {/* Análise Realizada */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg"><FileSearch className="h-5 w-5" /> Análise Realizada</CardTitle>
              <CardDescription>Detalhes da verificação de conflito de interesses</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="flex items-center gap-3 rounded-lg border p-3">
                  <Database className="h-8 w-8 text-blue-500 flex-shrink-0" />
                  <div>
                    <p className="text-xs text-muted-foreground">Casos verificados</p>
                    <p className="text-xl font-bold">{result.total_cases_checked ?? '—'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 rounded-lg border p-3">
                  <Scale className="h-8 w-8 text-amber-500 flex-shrink-0" />
                  <div>
                    <p className="text-xs text-muted-foreground">Partes adversas cruzadas</p>
                    <p className="text-xl font-bold">{result.total_adverse_parties_checked ?? '—'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 rounded-lg border p-3">
                  <Users className="h-8 w-8 text-green-500 flex-shrink-0" />
                  <div>
                    <p className="text-xs text-muted-foreground">Clientes ativos analisados</p>
                    <p className="text-xl font-bold">{result.total_clients_checked ?? '—'}</p>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Critérios e Bases */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-semibold mb-2">Critérios utilizados</p>
                  <ul className="space-y-1 text-sm text-muted-foreground">
                    {(result.criteria_used || ['CPF/CNPJ exato', 'Similaridade de nome (threshold 60%)', 'Conflito reverso']).map((c, i) => (
                      <li key={i} className="flex items-center gap-2"><CheckCircle className="h-3.5 w-3.5 text-green-500 flex-shrink-0" /> {c}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="text-sm font-semibold mb-2">Bases consultadas</p>
                  <ul className="space-y-1 text-sm text-muted-foreground">
                    {(result.search_scope || ['Casos ativos', 'Casos arquivados', 'Clientes cadastrados']).map((s, i) => (
                      <li key={i} className="flex items-center gap-2"><Database className="h-3.5 w-3.5 text-blue-500 flex-shrink-0" /> {s}</li>
                    ))}
                  </ul>
                </div>
              </div>

              <Separator />

              {/* Timeline visual */}
              <div>
                <p className="text-sm font-semibold mb-3">Etapas da verificação</p>
                <div className="flex flex-col gap-0">
                  {[
                    { step: 1, label: 'Correspondência exata de CPF/CNPJ', desc: 'Busca por documento idêntico nas partes contrárias de todos os casos' },
                    { step: 2, label: 'Similaridade de nome', desc: 'Comparação de tokens do nome com threshold de 60% (Jaccard)' },
                    { step: 3, label: 'Verificação reversa', desc: 'Confere se o nome já está cadastrada como parte representada em caso oposto' },
                  ].map((item, i) => (
                    <div key={i} className="flex gap-3">
                      <div className="flex flex-col items-center">
                        <div className="flex items-center justify-center h-8 w-8 rounded-full bg-primary text-primary-foreground text-sm font-bold flex-shrink-0">{item.step}</div>
                        {i < 2 && <div className="w-0.5 h-6 bg-border" />}
                      </div>
                      <div className="pb-4">
                        <p className="text-sm font-medium">{item.label}</p>
                        <p className="text-xs text-muted-foreground">{item.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/50 rounded-md p-2">
                <BookOpen className="h-3.5 w-3.5 flex-shrink-0" />
                <span>Referência legal: {result.oab_reference || 'Art. 19 do Código de Ética e Disciplina da OAB'}</span>
              </div>
            </CardContent>
          </Card>

          {/* Conflitos encontrados */}
          {result.conflicts.map((conflict: ConflictDetail, i: number) => {
            const SevIcon = severityIcons[conflict.severity] || AlertTriangle;
            return (
              <Card key={i} className={conflict.severity === 'critical' ? 'border-red-500' : 'border-yellow-500'}>
                <CardContent className="pt-6">
                  <div className="flex items-start gap-3">
                    <SevIcon className={`h-5 w-5 mt-0.5 ${conflict.severity === 'critical' ? 'text-red-500' : 'text-yellow-500'}`} />
                    <div className="space-y-2 flex-1">
                      <div className="flex items-center gap-2">
                        <Badge variant={severityColors[conflict.severity] as any}>{conflict.severity === 'critical' ? 'CRÍTICO' : 'ATENÇÃO'}</Badge>
                        <Badge variant="outline">{conflict.type.replace('_', ' ')}</Badge>
                        {conflict.similarity && <Badge variant="secondary">{(conflict.similarity * 100).toFixed(0)}% similar</Badge>}
                      </div>
                      <p className="text-sm">{conflict.message}</p>
                      <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                        {conflict.case_titulo && <div><Scale className="h-3 w-3 inline mr-1" />Caso: {conflict.case_titulo}</div>}
                        {conflict.numero_processo && <div>Processo: {conflict.numero_processo}</div>}
                        {conflict.advogado && <div>Procurador: {conflict.advogado}</div>}
                        {conflict.parte_contraria && <div>Parte Contrária: {conflict.parte_contraria}</div>}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { InvoiceNFSe } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { FileText, Plus, Send, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

const statusColors: Record<string, string> = { draft: 'secondary', pending: 'outline', processing: 'default', authorized: 'default', cancelled: 'destructive', error: 'destructive' };
const statusLabels: Record<string, string> = { draft: 'Rascunho', pending: 'Pendente', processing: 'Processando', authorized: 'Autorizada', cancelled: 'Cancelada', error: 'Erro' };

export default function NFSePage() {
  const queryClient = useQueryClient();

  const { data: invoices = [], isLoading } = useQuery({
    queryKey: ['nfse-list'],
    queryFn: async () => {
      const res = await api.get('/api/v1/processos/nfse/');
      return (res.data?.results || res.data) as InvoiceNFSe[];
    },
    staleTime: 2 * 60 * 1000,
  });

  const emitNFSe = useMutation({
    mutationFn: async (id: string) => {
      const res = await api.post(`/api/v1/processos/nfse/${id}/emitir/`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nfse-list'] });
      toast.success('NFS-e emitida com sucesso!');
    },
    onError: (err: any) => {
      const data = err.response?.data;
      if (data?.setup_required) {
        toast.error(`NFS-e não configurada. Variáveis necessárias: ${data.env_vars?.join(', ')}`);
      } else {
        toast.error(data?.error || 'Erro ao emitir NFS-e');
      }
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2"><FileText className="h-6 w-6" /> Notas Fiscais de Serviço</h1>
          <p className="text-muted-foreground">Emissão de NFS-e para serviços prestados</p>
        </div>
      </div>

      <Card>
        <CardHeader><CardTitle>Notas Fiscais</CardTitle><CardDescription>{invoices.length} notas cadastradas</CardDescription></CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Carregando...</div>
          ) : invoices.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-30" />
              <p>Nenhuma nota fiscal cadastrada</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Número</TableHead><TableHead>Cliente</TableHead><TableHead>Serviço</TableHead>
                  <TableHead className="text-right">Valor</TableHead><TableHead className="text-right">ISS</TableHead>
                  <TableHead className="text-right">Líquido</TableHead><TableHead>Status</TableHead><TableHead>Competência</TableHead><TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {invoices.map((nf: InvoiceNFSe) => (
                  <TableRow key={nf.id}>
                    <TableCell className="font-mono">{nf.numero_nfse || '—'}</TableCell>
                    <TableCell>{nf.client_name || '—'}</TableCell>
                    <TableCell className="max-w-[200px] truncate">{nf.descricao_servico}</TableCell>
                    <TableCell className="text-right">R$ {Number(nf.valor_servico).toLocaleString('pt-BR')}</TableCell>
                    <TableCell className="text-right">R$ {Number(nf.valor_iss || 0).toLocaleString('pt-BR')}</TableCell>
                    <TableCell className="text-right font-semibold">R$ {Number(nf.valor_liquido || 0).toLocaleString('pt-BR')}</TableCell>
                    <TableCell>
                      <Badge variant={statusColors[nf.status] as any || 'outline'}>
                        {statusLabels[nf.status] || nf.status}
                      </Badge>
                    </TableCell>
                    <TableCell>{nf.data_competencia}</TableCell>
                    <TableCell>
                      {nf.status === 'draft' && (
                        <Button size="sm" variant="outline" onClick={() => emitNFSe.mutate(nf.id)} disabled={emitNFSe.isPending}>
                          <Send className="h-3 w-3 mr-1" /> Emitir
                        </Button>
                      )}
                      {nf.status === 'error' && (
                        <span className="text-xs text-red-500 flex items-center gap-1"><AlertCircle className="h-3 w-3" /> {nf.error_message?.slice(0, 30)}</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

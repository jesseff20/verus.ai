'use client';

import { useState } from 'react';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import {
  Download,
  Scale,
  Users,
  Calendar,
  Loader2,
} from 'lucide-react';

const BASE = '/api/v1/processos/exportar';

interface ExportCardConfig {
  title: string;
  description: string;
  endpoint: string;
  icon: React.ComponentType<{ className?: string }>;
}

const EXPORT_CONFIGS: ExportCardConfig[] = [
  {
    title: 'Casos Jurídicos',
    description: 'Exporte todos os casos com dados de processo, partes, tribunal e valores.',
    endpoint: 'casos',
    icon: Scale,
  },
  {
    title: 'Clientes',
    description: 'Exporte a base de clientes com dados de contato, endereço e tipo.',
    endpoint: 'clientes',
    icon: Users,
  },
  {
    title: 'Prazos Processuais',
    description: 'Exporte prazos com caso vinculado, tipo, prioridade e responsável.',
    endpoint: 'prazos',
    icon: Calendar,
  },
];

function ExportCard({ config }: { config: ExportCardConfig }) {
  const [format, setFormat] = useState('csv');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [isExporting, setIsExporting] = useState(false);
  const Icon = config.icon;

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const params: Record<string, string> = { format };
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      if (format === 'json') {
        const res = await api.get(`${BASE}/${config.endpoint}/`, { params });
        const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `${config.endpoint}.json`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } else {
        const res = await api.get(`${BASE}/${config.endpoint}/`, {
          params,
          responseType: 'blob',
        });
        const url = window.URL.createObjectURL(new Blob([res.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `${config.endpoint}.csv`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      }

      toast.success(`${config.title} exportados com sucesso!`);
    } catch {
      toast.error(`Erro ao exportar ${config.title.toLowerCase()}.`);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-primary/10 p-2">
            <Icon className="h-5 w-5 text-primary" />
          </div>
          <div>
            <CardTitle className="text-lg">{config.title}</CardTitle>
            <CardDescription>{config.description}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <Label>Formato</Label>
            <Select value={format} onValueChange={setFormat}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="csv">CSV</SelectItem>
                <SelectItem value="json">JSON</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Data Inicial</Label>
            <Input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>
          <div>
            <Label>Data Final</Label>
            <Input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>
        </div>
        <Button onClick={handleExport} disabled={isExporting} className="w-full sm:w-auto">
          {isExporting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Exportando...
            </>
          ) : (
            <>
              <Download className="mr-2 h-4 w-4" />
              Exportar
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}

export default function ExportarPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Exportação de Dados</h1>
        <p className="text-muted-foreground">
          Exporte dados do sistema em formato CSV ou JSON.
        </p>
      </div>

      <div className="grid gap-6">
        {EXPORT_CONFIGS.map((config) => (
          <ExportCard key={config.endpoint} config={config} />
        ))}
      </div>
    </div>
  );
}

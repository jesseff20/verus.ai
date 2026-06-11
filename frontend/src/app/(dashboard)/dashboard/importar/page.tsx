'use client';

import { useState, useRef, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import {
  Upload,
  Download,
  FileSpreadsheet,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
} from 'lucide-react';

const BASE = '/api/v1/processos/importar';

interface ImportResult {
  importados: number;
  erros_count: number;
  erros: Array<{ linha: number; erro: string }>;
}

function FileDropZone({
  onFileSelect,
  file,
  accept = '.csv',
}: {
  onFileSelect: (f: File) => void;
  file: File | null;
  accept?: string;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const f = e.dataTransfer.files[0];
      if (f) onFileSelect(f);
    },
    [onFileSelect]
  );

  return (
    <div
      className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors cursor-pointer ${
        isDragging ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50'
      }`}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFileSelect(f);
        }}
      />
      <Upload className="h-10 w-10 text-muted-foreground mb-3" />
      {file ? (
        <div className="text-center">
          <p className="font-medium text-foreground">{file.name}</p>
          <p className="text-sm text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</p>
        </div>
      ) : (
        <div className="text-center">
          <p className="font-medium">Arraste o arquivo CSV aqui</p>
          <p className="text-sm text-muted-foreground">ou clique para selecionar</p>
        </div>
      )}
    </div>
  );
}

function ImportTab({ tipo }: { tipo: 'casos' | 'clientes' }) {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);

  const importMutation = useMutation({
    mutationFn: async (f: File) => {
      const formData = new FormData();
      formData.append('file', f);
      const res = await api.post<ImportResult>(
        `${BASE}/${tipo}/`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      return res.data;
    },
    onSuccess: (data) => {
      setResult(data);
      if (data.erros_count === 0) {
        toast.success(`${data.importados} registros importados com sucesso!`);
      } else {
        toast.warning(`${data.importados} importados, ${data.erros_count} erros.`);
      }
    },
    onError: () => {
      toast.error('Erro ao importar arquivo.');
    },
  });

  const handleDownloadTemplate = async () => {
    try {
      const res = await api.get(`${BASE}/template/`, {
        params: { tipo },
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `template_${tipo}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      toast.error('Erro ao baixar template.');
    }
  };

  const handleImport = () => {
    if (!file) {
      toast.error('Selecione um arquivo primeiro.');
      return;
    }
    setResult(null);
    importMutation.mutate(file);
  };

  const label = tipo === 'casos' ? 'Casos' : 'Clientes';

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Importe {label.toLowerCase()} a partir de um arquivo CSV (separador: ponto e vírgula).
        </p>
        <Button variant="outline" size="sm" onClick={handleDownloadTemplate}>
          <Download className="mr-2 h-4 w-4" />
          Download Template
        </Button>
      </div>

      <FileDropZone file={file} onFileSelect={setFile} />

      {file && (
        <div className="flex items-center gap-3">
          <FileSpreadsheet className="h-5 w-5 text-green-600" />
          <span className="text-sm font-medium">{file.name}</span>
          <Button
            onClick={handleImport}
            disabled={importMutation.isPending}
          >
            {importMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Importando...
              </>
            ) : (
              `Importar ${label}`
            )}
          </Button>
        </div>
      )}

      {result && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Resultado da Importação</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex gap-4">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                <span className="font-medium">{result.importados} importados</span>
              </div>
              {result.erros_count > 0 && (
                <div className="flex items-center gap-2">
                  <XCircle className="h-5 w-5 text-destructive" />
                  <span className="font-medium">{result.erros_count} erros</span>
                </div>
              )}
            </div>

            {result.erros.length > 0 && (
              <div className="space-y-1">
                <p className="text-sm font-medium flex items-center gap-1">
                  <AlertTriangle className="h-4 w-4 text-yellow-500" />
                  Detalhes dos erros:
                </p>
                <ul className="max-h-48 overflow-y-auto space-y-1">
                  {result.erros.map((err, idx) => (
                    <li key={idx} className="text-sm rounded bg-destructive/10 px-3 py-1.5">
                      <Badge variant="outline" className="mr-2">Linha {err.linha}</Badge>
                      {err.erro}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function ImportarPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Importação em Massa</h1>
        <p className="text-muted-foreground">
          Importe casos e clientes a partir de arquivos CSV.
        </p>
      </div>

      <Tabs defaultValue="casos">
        <TabsList>
          <TabsTrigger value="casos">Casos</TabsTrigger>
          <TabsTrigger value="clientes">Clientes</TabsTrigger>
        </TabsList>
        <TabsContent value="casos" className="mt-4">
          <ImportTab tipo="casos" />
        </TabsContent>
        <TabsContent value="clientes" className="mt-4">
          <ImportTab tipo="clientes" />
        </TabsContent>
      </Tabs>
    </div>
  );
}

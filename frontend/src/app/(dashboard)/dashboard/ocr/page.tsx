'use client';

import { useState, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { OCRResult } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import {
  ScanLine, Upload, FileText, Copy, Download, CheckCircle, AlertCircle, Loader2,
  Sparkles, BriefcaseBusiness, FormInput, Link2, ListTodo, Users, ChevronRight,
} from 'lucide-react';
import { toast } from 'sonner';

// ── AI Actions Section ──

interface CopilotSuggestion {
  answer: string;
  tokens_used: number;
  context_type: string;
}

interface ActionCard {
  id: string;
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  href: string;
}

function AIActionsSection({ extractedText, filename }: { extractedText: string; filename: string }) {
  const router = useRouter();
  const [copilotResult, setCopilotResult] = useState<CopilotSuggestion | null>(null);
  const [showActions, setShowActions] = useState(false);

  const analyzeMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post('/api/v1/processos/copilot/analisar/', {
        context_type: 'ocr',
        context_data: { text: extractedText, filename },
        question: 'Analise o texto extraído por OCR deste documento jurídico. Identifique: 1) Tipo de documento, 2) Partes envolvidas (autor/réu/requerente/requerido), 3) Informações-chave (números de processo, datas, valores), 4) Sugira as melhores ações a tomar com esses dados.',
      });
      return res.data as CopilotSuggestion;
    },
    onSuccess: (data) => {
      setCopilotResult(data);
      setShowActions(true);
      toast.success('Analise do Copilot concluída!');
    },
    onError: () => toast.error('Erro ao analisar com Copilot'),
  });

  const encodedText = encodeURIComponent(extractedText.slice(0, 2000));
  const encodedFilename = encodeURIComponent(filename);

  const actionCards: ActionCard[] = [
    {
      id: 'new-case',
      title: 'Criar Novo Caso',
      description: 'Cria um novo caso jurídico pré-preenchido com os dados extraídos do documento.',
      icon: BriefcaseBusiness,
      href: `/dashboard/cases/new?ocr_text=${encodedText}&ocr_file=${encodedFilename}`,
    },
    {
      id: 'fill-form',
      title: 'Preencher Formulário',
      description: 'Abre o formulário de petição com dados extraídos automaticamente.',
      icon: FormInput,
      href: `/dashboard/documents/new?ocr_text=${encodedText}&ocr_file=${encodedFilename}`,
    },
    {
      id: 'link-case',
      title: 'Vincular a Caso Existente',
      description: 'Selecione um caso existente para vincular este documento extraído.',
      icon: Link2,
      href: `/dashboard/cases?ocr_link=true&ocr_text=${encodedText}&ocr_file=${encodedFilename}`,
    },
    {
      id: 'create-task',
      title: 'Criar Tarefa',
      description: 'Cria uma tarefa com a descrição baseada no conteúdo extraído.',
      icon: ListTodo,
      href: `/dashboard/tasks?ocr_task=true&ocr_text=${encodedText}&ocr_file=${encodedFilename}`,
    },
    {
      id: 'extract-parties',
      title: 'Extrair Partes',
      description: 'Identifica automaticamente nomes de autor, réu e demais partes no documento.',
      icon: Users,
      href: `/dashboard/cases?ocr_parties=true&ocr_text=${encodedText}&ocr_file=${encodedFilename}`,
    },
  ];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Sparkles className="h-5 w-5 text-amber-500" /> Ações com IA
          </CardTitle>
          {!showActions && (
            <Button
              onClick={() => analyzeMutation.mutate()}
              disabled={analyzeMutation.isPending}
              className="gap-2"
            >
              {analyzeMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              Analisar com Copilot
            </Button>
          )}
        </div>
        {!showActions && !analyzeMutation.isPending && (
          <CardDescription>
            Use a IA para analisar o texto extraído e sugerir ações automáticas.
          </CardDescription>
        )}
      </CardHeader>
      {showActions && copilotResult && (
        <CardContent className="space-y-4">
          {/* Copilot Analysis */}
          <div className="rounded-lg border bg-muted/30 p-4 space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold flex items-center gap-1.5">
                <Sparkles className="h-4 w-4 text-amber-500" /> Análise do Copilot
              </h4>
              <Badge variant="secondary" className="text-[10px]">
                {copilotResult.tokens_used} tokens
              </Badge>
            </div>
            <ScrollArea className="max-h-[200px]">
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">{copilotResult.answer}</p>
            </ScrollArea>
          </div>

          <Separator />

          {/* Action Cards */}
          <div>
            <h4 className="text-sm font-semibold mb-3">Ações Sugeridas</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {actionCards.map((action) => {
                const Icon = action.icon;
                return (
                  <Card
                    key={action.id}
                    className="cursor-pointer hover:shadow-md hover:border-primary/30 transition-all group"
                    onClick={() => router.push(action.href)}
                  >
                    <CardContent className="p-4 flex items-start gap-3">
                      <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 group-hover:bg-primary/20 transition-colors">
                        <Icon className="h-5 w-5 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium flex items-center gap-1">
                          {action.title}
                          <ChevronRight className="h-3 w-3 text-muted-foreground group-hover:translate-x-0.5 transition-transform" />
                        </p>
                        <p className="text-xs text-muted-foreground mt-0.5">{action.description}</p>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  );
}

export default function OCRPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<OCRResult | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const extract = useMutation({
    mutationFn: async (f: File) => {
      const formData = new FormData();
      formData.append('file', f);
      formData.append('language', 'por');
      const res = await api.post('/api/v1/processos/ocr/extrair/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return res.data as OCRResult;
    },
    onSuccess: (data) => {
      setResult(data);
      if (data.success) toast.success(`Texto extraído: ${data.pages} página(s)`);
      else toast.error(data.error || 'Erro na extração');
    },
    onError: () => toast.error('Erro ao processar arquivo'),
  });

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) { setFile(f); extract.mutate(f); }
  }, [extract]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) { setFile(f); extract.mutate(f); }
  };

  const copyText = () => {
    if (result?.text) {
      navigator.clipboard.writeText(result.text);
      toast.success('Texto copiado!');
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <ScanLine className="h-6 w-6" /> OCR de Documentos
        </h1>
        <p className="text-muted-foreground">
          Extraia texto de PDFs escaneados e imagens de documentos
        </p>
      </div>

      {/* Upload Area */}
      <Card>
        <CardContent className="pt-6">
          <div
            className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors cursor-pointer
              ${dragOver ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50'}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => document.getElementById('ocr-file-input')?.click()}
          >
            {extract.isPending ? (
              <div className="space-y-4">
                <Loader2 className="h-12 w-12 mx-auto animate-spin text-primary" />
                <p className="font-medium">Processando OCR...</p>
                <p className="text-sm text-muted-foreground">Extraindo texto de {file?.name}</p>
              </div>
            ) : (
              <>
                <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="font-medium mb-1">Arraste um arquivo ou clique para selecionar</p>
                <p className="text-sm text-muted-foreground">
                  Suporta: PDF, PNG, JPG, JPEG, TIFF, BMP
                </p>
              </>
            )}
            <input
              id="ocr-file-input"
              type="file"
              className="hidden"
              accept=".pdf,.png,.jpg,.jpeg,.tiff,.bmp"
              onChange={handleFileChange}
            />
          </div>
        </CardContent>
      </Card>

      {/* Result */}
      {result && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  {result.success ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-500" />
                  )}
                  Resultado da Extração
                </CardTitle>
                <CardDescription>
                  {result.filename} — {result.pages} página(s)
                </CardDescription>
              </div>
              {result.success && (
                <Button variant="outline" size="sm" onClick={copyText}>
                  <Copy className="h-4 w-4 mr-2" /> Copiar Texto
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Metadata */}
            <div className="flex gap-4 flex-wrap">
              <Badge variant="outline">
                Método: {result.method === 'text_extraction' ? 'Extração Direta' : 'OCR Tesseract'}
              </Badge>
              {result.confidence !== undefined && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">Confiança:</span>
                  <Progress value={result.confidence * 100} className="w-24 h-2" />
                  <span className="text-sm font-medium">{(result.confidence * 100).toFixed(0)}%</span>
                </div>
              )}
              {result.file_size && (
                <Badge variant="secondary">
                  {(result.file_size / 1024).toFixed(0)} KB
                </Badge>
              )}
            </div>

            <Separator />

            {/* Text Content */}
            {result.success ? (
              <ScrollArea className="h-[400px] rounded-md border p-4">
                <pre className="whitespace-pre-wrap text-sm font-mono">{result.text}</pre>
              </ScrollArea>
            ) : (
              <div className="text-center py-8 text-red-500">
                <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                <p>{result.error}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* AI Actions - shown after successful extraction */}
      {result?.success && result.text && (
        <AIActionsSection extractedText={result.text} filename={result.filename || file?.name || 'documento'} />
      )}
    </div>
  );
}

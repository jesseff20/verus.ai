'use client';

import { useState, useRef, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  useClientPortalCaseDetail,
  useClientPortalUploadDocument,
} from '@/hooks/use-client-portal';
import type {
  ClientCasePhase,
  ClientCaseDeadline,
  ClientCaseDocument,
  ClientCaseHearing,
} from '@/hooks/use-client-portal';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  ArrowLeft,
  Loader2,
  AlertTriangle,
  Calendar,
  Building2,
  CheckCircle2,
  Clock,
  Circle,
  AlertCircle,
  FileText,
  Download,
  Upload,
  User,
  DollarSign,
  MapPin,
  Gavel,
} from 'lucide-react';

// ─── Helpers ────────────────────────────────────────────────────────────────

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '\u2014';
  return new Date(dateStr).toLocaleDateString('pt-BR');
}

function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '\u2014';
  return new Date(dateStr).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

const STATUS_COLORS: Record<string, string> = {
  ativo: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300',
  aguardando: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300',
  suspenso: 'bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300',
  encerrado: 'bg-gray-100 text-gray-600 dark:bg-gray-800/40 dark:text-gray-400',
  ganho: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
  perdido: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300',
  acordo: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300',
};

const PHASE_ICONS: Record<string, React.ReactNode> = {
  completed: <CheckCircle2 className="h-5 w-5 text-green-600" />,
  in_progress: <Clock className="h-5 w-5 text-blue-600 animate-pulse" />,
  pending: <Circle className="h-5 w-5 text-gray-400" />,
  skipped: <Circle className="h-5 w-5 text-gray-300" />,
  overdue: <AlertCircle className="h-5 w-5 text-red-600" />,
};

const DEADLINE_PRIORITY_DOT: Record<string, string> = {
  urgente: 'bg-red-500',
  alta: 'bg-orange-500',
  media: 'bg-yellow-500',
  baixa: 'bg-green-500',
};

const ACCEPTED_TYPES = '.pdf,.jpg,.jpeg,.png,.docx';

// ─── Component ──────────────────────────────────────────────────────────────

export default function ClientCaseDetailPage() {
  const params = useParams();
  const caseId = params.id as string;
  const { data: caso, isLoading, error } = useClientPortalCaseDetail(caseId);

  const [uploadOpen, setUploadOpen] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const uploadMutation = useClientPortalUploadDocument();

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) setSelectedFile(e.dataTransfer.files[0]);
  }, []);

  const handleUpload = async () => {
    if (!selectedFile) return;
    try {
      await uploadMutation.mutateAsync({
        file: selectedFile,
        case_id: caseId,
        titulo: uploadTitle || undefined,
      });
      setUploadOpen(false);
      setSelectedFile(null);
      setUploadTitle('');
    } catch {
      // error handled by mutation
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !caso) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/portal">
            <ArrowLeft className="h-4 w-4 mr-1" />
            Voltar
          </Link>
        </Button>
        <div className="flex items-center justify-center py-16 text-destructive gap-2">
          <AlertTriangle className="h-5 w-5" />
          <span>Erro ao carregar processo</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back + title */}
      <div>
        <Button variant="ghost" size="sm" asChild className="mb-3">
          <Link href="/portal">
            <ArrowLeft className="h-4 w-4 mr-1" />
            Voltar
          </Link>
        </Button>

        <div className="flex items-start gap-3 flex-wrap">
          <div className="flex-1 min-w-0">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight">
              {caso.titulo}
            </h1>
            <div className="mt-2 flex items-center gap-2 flex-wrap">
              <Badge className={`text-xs ${STATUS_COLORS[caso.status] || STATUS_COLORS.encerrado}`}>
                {caso.status_display}
              </Badge>
              {caso.numero_processo && (
                <Badge variant="outline" className="text-xs font-mono">
                  {caso.numero_processo}
                </Badge>
              )}
              {caso.tribunal && (
                <Badge variant="outline" className="text-xs">
                  <Building2 className="h-3 w-3 mr-1" />
                  {caso.tribunal}
                </Badge>
              )}
              {caso.vara_juizo && (
                <Badge variant="outline" className="text-xs">
                  {caso.vara_juizo}
                </Badge>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="visao-geral" className="w-full">
        <TabsList className="w-full grid grid-cols-2 sm:grid-cols-4">
          <TabsTrigger value="visao-geral" className="text-xs sm:text-sm">
            Visão Geral
          </TabsTrigger>
          <TabsTrigger value="documentos" className="text-xs sm:text-sm">
            Documentos
          </TabsTrigger>
          <TabsTrigger value="prazos" className="text-xs sm:text-sm">
            Prazos
          </TabsTrigger>
          <TabsTrigger value="audiencias" className="text-xs sm:text-sm">
            Audiências
          </TabsTrigger>
        </TabsList>

        {/* ── Tab: Visão Geral ──────────────────────────── */}
        <TabsContent value="visao-geral" className="space-y-4 mt-4">
          {/* Info cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {caso.advogado_responsavel && (
              <Card>
                <CardContent className="p-4 flex items-center gap-3">
                  <User className="h-5 w-5 text-muted-foreground shrink-0" />
                  <div>
                    <p className="text-xs text-muted-foreground">Advogado Responsável</p>
                    <p className="text-sm font-medium">{caso.advogado_responsavel}</p>
                  </div>
                </CardContent>
              </Card>
            )}
            {caso.data_distribuicao && (
              <Card>
                <CardContent className="p-4 flex items-center gap-3">
                  <Calendar className="h-5 w-5 text-muted-foreground shrink-0" />
                  <div>
                    <p className="text-xs text-muted-foreground">Data Distribuição</p>
                    <p className="text-sm font-medium">{formatDate(caso.data_distribuicao)}</p>
                  </div>
                </CardContent>
              </Card>
            )}
            {caso.valor_causa && (
              <Card>
                <CardContent className="p-4 flex items-center gap-3">
                  <DollarSign className="h-5 w-5 text-muted-foreground shrink-0" />
                  <div>
                    <p className="text-xs text-muted-foreground">Valor da Causa</p>
                    <p className="text-sm font-medium">
                      {Number(caso.valor_causa).toLocaleString('pt-BR', {
                        style: 'currency',
                        currency: 'BRL',
                      })}
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Case info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Dados do Processo</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 text-sm">
                {caso.parte_contraria && (
                  <div>
                    <dt className="text-muted-foreground text-xs">Parte Contrária</dt>
                    <dd>{caso.parte_contraria}</dd>
                  </div>
                )}
                {caso.comarca && (
                  <div>
                    <dt className="text-muted-foreground text-xs">Comarca</dt>
                    <dd>{caso.comarca}</dd>
                  </div>
                )}
                {caso.especialidade_display && (
                  <div>
                    <dt className="text-muted-foreground text-xs">Especialidade</dt>
                    <dd>{caso.especialidade_display}</dd>
                  </div>
                )}
                {caso.fase_display && (
                  <div>
                    <dt className="text-muted-foreground text-xs">Fase Atual</dt>
                    <dd>{caso.fase_display}</dd>
                  </div>
                )}
              </dl>
              {caso.descricao && (
                <div className="mt-4 pt-4 border-t">
                  <h4 className="text-xs text-muted-foreground mb-1">Descrição</h4>
                  <p className="text-sm whitespace-pre-wrap">{caso.descricao}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Phases timeline */}
          {caso.phases && caso.phases.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Fases do Processo</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-0">
                  {caso.phases
                    .sort((a: ClientCasePhase, b: ClientCasePhase) => a.order - b.order)
                    .map((phase: ClientCasePhase, idx: number) => (
                    <div key={phase.id} className="flex gap-3">
                      <div className="flex flex-col items-center">
                        {PHASE_ICONS[phase.status] || PHASE_ICONS.pending}
                        {idx < caso.phases.length - 1 && (
                          <div className={`w-0.5 flex-1 my-1 ${
                            phase.status === 'completed' ? 'bg-green-300' :
                            phase.status === 'in_progress' ? 'bg-blue-300' : 'bg-gray-200'
                          }`} />
                        )}
                      </div>
                      <div className="pb-5 flex-1">
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium text-sm">{phase.name}</h4>
                          <Badge variant="outline" className="text-[10px]">
                            {phase.status_display}
                          </Badge>
                        </div>
                        {phase.description && (
                          <p className="text-xs text-muted-foreground mt-0.5">{phase.description}</p>
                        )}
                        <div className="flex gap-3 mt-1 text-[11px] text-muted-foreground">
                          {phase.estimated_date && (
                            <span>Previsto: {formatDate(phase.estimated_date)}</span>
                          )}
                          {phase.actual_date && (
                            <span>Realizado: {formatDate(phase.actual_date)}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* ── Tab: Documentos ───────────────────────────── */}
        <TabsContent value="documentos" className="space-y-4 mt-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-medium">Documentos do Caso</h3>
            <Button size="sm" onClick={() => setUploadOpen(true)}>
              <Upload className="h-4 w-4 mr-1" />
              Enviar Documento
            </Button>
          </div>

          {caso.documentos && caso.documentos.length > 0 ? (
            <div className="space-y-2">
              {caso.documentos.map((doc: ClientCaseDocument) => (
                <div
                  key={doc.id}
                  className="flex items-center gap-3 p-3 rounded-lg border bg-background hover:bg-accent/30 transition-colors"
                >
                  <FileText className="h-5 w-5 text-muted-foreground shrink-0" />
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-sm truncate">{doc.titulo}</h4>
                    <div className="flex items-center gap-2 mt-0.5 text-[11px] text-muted-foreground">
                      <Badge variant="outline" className="text-[10px]">
                        {doc.tipo_display}
                      </Badge>
                      {doc.data_documento && (
                        <span>{formatDate(doc.data_documento)}</span>
                      )}
                    </div>
                    {doc.descricao && (
                      <p className="text-xs text-muted-foreground mt-0.5 truncate">{doc.descricao}</p>
                    )}
                  </div>
                  <Button variant="ghost" size="sm">
                    <Download className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground gap-3">
              <FileText className="h-10 w-10 opacity-30" />
              <p className="text-sm">Nenhum documento encontrado</p>
            </div>
          )}

          {/* Upload Dialog */}
          <Dialog open={uploadOpen} onOpenChange={setUploadOpen}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Enviar Documento</DialogTitle>
                <DialogDescription>
                  Selecione ou arraste um arquivo para enviar. Formatos aceitos: PDF, JPG, PNG, DOCX.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="upload-title">Título (opcional)</Label>
                  <Input
                    id="upload-title"
                    value={uploadTitle}
                    onChange={(e) => setUploadTitle(e.target.value)}
                    placeholder="Ex: Comprovante de residência"
                  />
                </div>
                <div
                  className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                    dragActive
                      ? 'border-primary bg-primary/5'
                      : 'border-muted-foreground/25 hover:border-primary/50'
                  }`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                  {selectedFile ? (
                    <p className="text-sm font-medium">{selectedFile.name}</p>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      Arraste um arquivo aqui ou clique para selecionar
                    </p>
                  )}
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept={ACCEPTED_TYPES}
                    className="hidden"
                    onChange={(e) => {
                      if (e.target.files?.[0]) setSelectedFile(e.target.files[0]);
                    }}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setUploadOpen(false)}>
                  Cancelar
                </Button>
                <Button
                  onClick={handleUpload}
                  disabled={!selectedFile || uploadMutation.isPending}
                >
                  {uploadMutation.isPending && <Loader2 className="h-4 w-4 mr-1 animate-spin" />}
                  Enviar
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </TabsContent>

        {/* ── Tab: Prazos ───────────────────────────────── */}
        <TabsContent value="prazos" className="space-y-4 mt-4">
          {caso.prazos && caso.prazos.length > 0 ? (
            <div className="space-y-2">
              {caso.prazos.map((prazo: ClientCaseDeadline) => (
                <div
                  key={prazo.id}
                  className="flex gap-3 rounded-lg border bg-background p-3"
                >
                  <div className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${
                    DEADLINE_PRIORITY_DOT[prazo.prioridade] || 'bg-gray-300'
                  }`} />
                  <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-sm">{prazo.titulo}</h4>
                      {prazo.descricao && (
                        <p className="text-xs text-muted-foreground mt-0.5">{prazo.descricao}</p>
                      )}
                    </div>
                    <Badge
                      variant="outline"
                      className={`text-[10px] shrink-0 ${
                        prazo.status === 'concluido' ? 'text-green-600' :
                        prazo.status === 'atrasado' ? 'text-red-600' : ''
                      }`}
                    >
                      {prazo.status_display}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-3 mt-2 text-[11px] text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {formatDate(prazo.data_prazo)}
                    </span>
                    <span>{prazo.tipo_display}</span>
                    <Badge variant="outline" className="text-[10px]">
                      {prazo.prioridade_display}
                    </Badge>
                  </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground gap-3">
              <Calendar className="h-10 w-10 opacity-30" />
              <p className="text-sm">Nenhum prazo registrado</p>
            </div>
          )}
        </TabsContent>

        {/* ── Tab: Audiências ───────────────────────────── */}
        <TabsContent value="audiencias" className="space-y-4 mt-4">
          {caso.audiencias && caso.audiencias.length > 0 ? (
            <div className="space-y-2">
              {caso.audiencias.map((aud: ClientCaseHearing) => {
                const isPast = new Date(aud.data_audiencia) < new Date();
                return (
                  <Card key={aud.id} className={isPast ? 'opacity-60' : ''}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge variant="outline" className="text-[10px]">
                              {aud.tipo_display}
                            </Badge>
                            <Badge
                              variant="outline"
                              className={`text-[10px] ${isPast ? 'text-gray-500' : 'text-blue-600'}`}
                            >
                              {aud.status_display}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-3 text-sm">
                            <span className="flex items-center gap-1">
                              <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                              {formatDate(aud.data_audiencia)}
                            </span>
                            {aud.hora_audiencia && (
                              <span className="flex items-center gap-1">
                                <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                                {aud.hora_audiencia}
                              </span>
                            )}
                          </div>
                          {aud.local && (
                            <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                              <MapPin className="h-3 w-3" />
                              {aud.local}
                            </p>
                          )}
                          {aud.observacoes && (
                            <p className="text-xs text-muted-foreground mt-1">{aud.observacoes}</p>
                          )}
                        </div>
                        <Gavel className={`h-5 w-5 shrink-0 ${isPast ? 'text-gray-400' : 'text-primary'}`} />
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground gap-3">
              <Gavel className="h-10 w-10 opacity-30" />
              <p className="text-sm">Nenhuma audiência registrada</p>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

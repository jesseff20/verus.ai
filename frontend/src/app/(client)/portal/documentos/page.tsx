'use client';

import { useState, useRef, useCallback } from 'react';
import {
  useClientPortalDocuments,
  useClientPortalUploadDocument,
  useClientPortalCases,
} from '@/hooks/use-client-portal';
import type { ClientDocumentAll } from '@/hooks/use-client-portal';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  FileText,
  Loader2,
  AlertTriangle,
  Download,
  Upload,
  FolderOpen,
} from 'lucide-react';

// ─── Helpers ────────────────────────────────────────────────────────────────

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '\u2014';
  return new Date(dateStr).toLocaleDateString('pt-BR');
}

const ACCEPTED_TYPES = '.pdf,.jpg,.jpeg,.png,.docx';

// ─── Component ──────────────────────────────────────────────────────────────

export default function DocumentosPage() {
  const { data: documents, isLoading, error } = useClientPortalDocuments();
  const { data: cases } = useClientPortalCases();
  const uploadMutation = useClientPortalUploadDocument();

  const [caseFilter, setCaseFilter] = useState<string>('all');
  const [uploadOpen, setUploadOpen] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadCaseId, setUploadCaseId] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const filteredDocuments = documents?.filter((doc) =>
    caseFilter === 'all' ? true : doc.case_id === caseFilter
  );

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
    if (!selectedFile || !uploadCaseId) return;
    try {
      await uploadMutation.mutateAsync({
        file: selectedFile,
        case_id: uploadCaseId,
        titulo: uploadTitle || undefined,
      });
      setUploadOpen(false);
      setSelectedFile(null);
      setUploadTitle('');
      setUploadCaseId('');
    } catch {
      // error handled by mutation
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight flex items-center gap-2">
            <FolderOpen className="h-7 w-7 sm:h-8 sm:w-8" />
            Meus Documentos
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Todos os documentos dos seus processos
          </p>
        </div>
        <Button onClick={() => setUploadOpen(true)}>
          <Upload className="h-4 w-4 mr-1" />
          Enviar Documento
        </Button>
      </div>

      {/* Case filter */}
      {cases && cases.length > 0 && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Filtrar por caso:</span>
          <Select value={caseFilter} onValueChange={setCaseFilter}>
            <SelectTrigger className="w-[260px]">
              <SelectValue placeholder="Todos os casos" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos os casos</SelectItem>
              {cases.map((c) => (
                <SelectItem key={c.id} value={c.id}>
                  {c.titulo}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Documents list */}
      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <div className="flex items-center justify-center py-16 text-destructive gap-2">
          <AlertTriangle className="h-5 w-5" />
          <span>Erro ao carregar documentos</span>
        </div>
      ) : !filteredDocuments || filteredDocuments.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground gap-3">
          <FileText className="h-12 w-12 opacity-30" />
          <p className="text-sm">Nenhum documento encontrado</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filteredDocuments.map((doc: ClientDocumentAll) => (
            <Card key={doc.id}>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-muted-foreground shrink-0" />
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-sm truncate">{doc.titulo}</h4>
                    <div className="flex items-center gap-2 mt-0.5 flex-wrap text-[11px] text-muted-foreground">
                      <Badge variant="outline" className="text-[10px]">
                        {doc.tipo_display}
                      </Badge>
                      <span className="hidden sm:inline">|</span>
                      <span className="text-[10px] text-muted-foreground truncate">
                        {doc.case_titulo}
                      </span>
                      {doc.data_documento && (
                        <>
                          <span className="hidden sm:inline">|</span>
                          <span>{formatDate(doc.data_documento)}</span>
                        </>
                      )}
                    </div>
                    {doc.descricao && (
                      <p className="text-xs text-muted-foreground mt-0.5 truncate">{doc.descricao}</p>
                    )}
                  </div>
                  {doc.download_url && (
                    <Button
                      variant="ghost"
                      size="sm"
                      asChild
                    >
                      <a href={doc.download_url} target="_blank" rel="noopener noreferrer">
                        <Download className="h-4 w-4" />
                      </a>
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Upload Dialog */}
      <Dialog open={uploadOpen} onOpenChange={setUploadOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Enviar Documento</DialogTitle>
            <DialogDescription>
              Selecione o caso e arraste um arquivo para enviar. Formatos aceitos: PDF, JPG, PNG, DOCX.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Caso</Label>
              <Select value={uploadCaseId} onValueChange={setUploadCaseId}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecione o caso" />
                </SelectTrigger>
                <SelectContent>
                  {cases?.map((c) => (
                    <SelectItem key={c.id} value={c.id}>
                      {c.titulo}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="upload-title-global">Título (opcional)</Label>
              <Input
                id="upload-title-global"
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
              disabled={!selectedFile || !uploadCaseId || uploadMutation.isPending}
            >
              {uploadMutation.isPending && <Loader2 className="h-4 w-4 mr-1 animate-spin" />}
              Enviar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

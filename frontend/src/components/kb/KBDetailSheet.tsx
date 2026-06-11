'use client';

import { useState, useRef } from 'react';
import { useKBSources } from '@/hooks/use-knowledge-base';
import { useToast } from '@/hooks/use-toast';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Upload,
  FileText,
  Loader2,
  Trash2,
  Database,
  Brain,
} from 'lucide-react';
import { AgentLinksTab } from './AgentLinksTab';
import type { ManagedKnowledgeBase } from '@/types';

interface KBDetailSheetProps {
  kb: ManagedKnowledgeBase | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpload: (kbId: string, formData: FormData, callbacks: {
    onSuccess: (data: any) => void;
    onError: (error: any) => void;
  }) => void;
  isUploading: boolean;
  onDeleteSource: (kbId: string, sourceName: string, callbacks: {
    onSuccess: (data: any) => void;
    onError: () => void;
  }) => void;
  isDeletingSource: boolean;
}

export function KBDetailSheet({
  kb,
  open,
  onOpenChange,
  onUpload,
  isUploading,
  onDeleteSource,
  isDeletingSource,
}: KBDetailSheetProps) {
  const { toast } = useToast();
  const { data: sourcesData, isLoading: isLoadingSources } = useKBSources(
    open && kb ? kb.id : null
  );

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [sourceName, setSourceName] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const formatChars = (chars: number) => {
    if (chars < 1000) return chars + '';
    if (chars < 1000000) return (chars / 1000).toFixed(1) + 'K';
    return (chars / 1000000).toFixed(1) + 'M';
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      if (!sourceName) setSourceName(file.name);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      const validTypes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.oasis.opendocument.text',
        'text/plain',
      ];
      const validExtensions = ['.pdf', '.docx', '.odt', '.txt'];
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!validTypes.includes(file.type) && !validExtensions.includes(ext)) {
        toast({ title: 'Tipo invalido', description: 'Formatos aceitos: PDF, DOCX, ODT, TXT', variant: 'destructive' });
        return;
      }
      setSelectedFile(file);
      if (!sourceName) setSourceName(file.name);
    }
  };

  const handleUpload = () => {
    if (!selectedFile || !kb) return;
    const formData = new FormData();
    formData.append('file', selectedFile);
    if (sourceName.trim()) {
      formData.append('source_name', sourceName.trim());
    }
    onUpload(kb.id, formData, {
      onSuccess: (data: any) => {
        toast({
          title: 'Documento processado',
          description: `${data.chunks_created} chunks criados (${formatChars(data.char_count)} caracteres)`,
        });
        setSelectedFile(null);
        setSourceName('');
        if (fileInputRef.current) fileInputRef.current.value = '';
      },
      onError: (error: any) => {
        toast({
          title: 'Erro no upload',
          description: error.response?.data?.error || 'Erro ao processar documento',
          variant: 'destructive',
        });
      },
    });
  };

  const handleDeleteSource = (sName: string) => {
    if (!kb) return;
    onDeleteSource(kb.id, sName, {
      onSuccess: (data: any) => {
        toast({ title: `${data.deleted_count} embeddings removidos` });
      },
      onError: () => {
        toast({ title: 'Erro ao deletar fonte', variant: 'destructive' });
      },
    });
  };

  if (!kb) return null;

  return (
    <Sheet open={open} onOpenChange={(v) => {
      onOpenChange(v);
      if (!v) {
        setSelectedFile(null);
        setSourceName('');
      }
    }}>
      <SheetContent className="w-full sm:max-w-2xl overflow-y-auto">
        <SheetHeader className="pb-4">
          <div className="flex items-center gap-2">
            <SheetTitle className="text-lg">{kb.name}</SheetTitle>
            <Badge variant={kb.is_active ? 'default' : 'secondary'}>
              {kb.is_active ? 'Ativo' : 'Inativo'}
            </Badge>
          </div>
          <SheetDescription>
            {kb.blueprint_name && (
              <span className="inline-flex items-center gap-1">
                <Database className="h-3 w-3" /> {kb.blueprint_name}
                {kb.document_type_name && ` - ${kb.document_type_name}`}
              </span>
            )}
            {kb.description && <span className="block mt-1">{kb.description}</span>}
          </SheetDescription>
        </SheetHeader>

        <Tabs defaultValue="sources" className="mt-2">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="sources" className="flex items-center gap-1">
              <FileText className="h-3 w-3" />
              Fontes ({sourcesData?.total_sources || 0})
            </TabsTrigger>
            <TabsTrigger value="agents" className="flex items-center gap-1">
              <Brain className="h-3 w-3" />
              Agentes ({kb.agent_links_count || 0})
            </TabsTrigger>
            <TabsTrigger value="upload" className="flex items-center gap-1">
              <Upload className="h-3 w-3" />
              Upload
            </TabsTrigger>
          </TabsList>

          {/* ── Tab: Fontes ── */}
          <TabsContent value="sources" className="mt-4">
            {isLoadingSources ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : (sourcesData?.sources?.length || 0) === 0 ? (
              <p className="text-center text-muted-foreground py-8">
                Nenhuma fonte encontrada. Use a aba Upload para adicionar documentos.
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Fonte</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Chunks</TableHead>
                    <TableHead>Caracteres</TableHead>
                    <TableHead>Data</TableHead>
                    <TableHead className="text-right">Ação</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sourcesData?.sources?.map((source) => (
                    <TableRow key={source.source_name}>
                      <TableCell className="font-medium max-w-[180px] truncate">
                        {source.source_name}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{source.source_type}</Badge>
                      </TableCell>
                      <TableCell>{source.chunks_count}</TableCell>
                      <TableCell>{formatChars(source.total_characters)}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(source.created_at).toLocaleDateString('pt-BR')}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          onClick={() => handleDeleteSource(source.source_name)}
                          disabled={isDeletingSource}
                        >
                          {isDeletingSource ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </TabsContent>

          {/* ── Tab: Agentes ── */}
          <TabsContent value="agents" className="mt-4">
            <AgentLinksTab kbId={kb.id} kbName={kb.name} />
          </TabsContent>

          {/* ── Tab: Upload ── */}
          <TabsContent value="upload" className="mt-4 space-y-4">
            <div
              className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                isDragging
                  ? 'border-primary bg-primary/5'
                  : selectedFile
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}
              onDrop={handleDrop}
            >
              <Input
                type="file"
                ref={fileInputRef}
                onChange={handleFileSelect}
                accept=".pdf,.docx,.odt,.txt"
                className="hidden"
              />
              {selectedFile ? (
                <div className="space-y-2">
                  <FileText className="h-10 w-10 mx-auto text-green-600" />
                  <p className="text-sm font-medium text-green-700">{selectedFile.name}</p>
                  <p className="text-xs text-muted-foreground">{formatFileSize(selectedFile.size)}</p>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedFile(null);
                      setSourceName('');
                      if (fileInputRef.current) fileInputRef.current.value = '';
                    }}
                  >
                    Trocar arquivo
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  <Upload className="h-10 w-10 mx-auto text-gray-400" />
                  <p className="text-sm">
                    Arraste um arquivo ou{' '}
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="text-primary hover:underline"
                    >
                      clique para selecionar
                    </button>
                  </p>
                  <p className="text-xs text-muted-foreground">PDF, DOCX, ODT, TXT</p>
                </div>
              )}
            </div>

            <div className="space-y-2">
              <Label>Nome da fonte (opcional)</Label>
              <Input
                value={sourceName}
                onChange={(e) => setSourceName(e.target.value)}
                placeholder="Auto-preenchido com nome do arquivo"
              />
            </div>

            <Button
              onClick={handleUpload}
              disabled={isUploading || !selectedFile}
              className="w-full"
            >
              {isUploading ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Processando...</>
              ) : (
                <><Upload className="mr-2 h-4 w-4" />Enviar Documento</>
              )}
            </Button>
          </TabsContent>
        </Tabs>
      </SheetContent>
    </Sheet>
  );
}

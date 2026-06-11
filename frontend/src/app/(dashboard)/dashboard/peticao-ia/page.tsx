'use client';

import { useState, useRef, useCallback } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { PetitionType, PetitionResult } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Bot, FileText, Loader2, Copy, Download, PenLine, Save, Check } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { toast } from 'sonner';

export default function PeticaoIAPage() {
  const [caseId, setCaseId] = useState('');
  const [petitionType, setPetitionType] = useState('');
  const [extraInstructions, setExtraInstructions] = useState('');
  const [result, setResult] = useState<PetitionResult | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const editorRef = useRef<HTMLTextAreaElement>(null);

  const { data: types = [] } = useQuery({
    queryKey: ['petition-types'],
    queryFn: async () => {
      const res = await api.get('/api/v1/processos/peticao-ia/tipos/');
      return res.data as PetitionType[];
    },
    staleTime: 10 * 60 * 1000,
  });

  const { data: cases = [] } = useQuery({
    queryKey: ['cases-list-simple'],
    queryFn: async () => {
      const res = await api.get('/api/v1/processos/', { params: { page_size: 100 } });
      return res.data?.results || res.data || [];
    },
  });

  const generate = useMutation({
    mutationFn: async () => {
      const res = await api.post('/api/v1/processos/peticao-ia/gerar/', {
        case_id: caseId,
        petition_type: petitionType,
        extra_instructions: extraInstructions,
      });
      return res.data as PetitionResult;
    },
    onSuccess: (data) => {
      setResult(data);
      setEditedContent(data.content);
      setIsEditing(false);
      toast.success(`${data.petition_name} gerada com sucesso!`);
    },
    onError: (err: any) => {
      const msg = err.response?.data?.error || err.response?.data?.detail || 'Erro ao gerar petição';
      toast.error(msg);
    },
  });

  const currentContent = isEditing ? editedContent : (result?.content || '');

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(currentContent);
    toast.success('Copiado para a área de transferência!');
  }, [currentContent]);

  const handleToggleEdit = useCallback(() => {
    if (!isEditing && result) {
      setEditedContent(result.content);
    }
    setIsEditing((prev) => !prev);
  }, [isEditing, result]);

  const handleSaveEdit = useCallback(() => {
    if (result) {
      setResult({ ...result, content: editedContent });
      setIsEditing(false);
      toast.success('Alterações salvas na petição.');
    }
  }, [result, editedContent]);

  const handleSaveAsDocument = useCallback(async () => {
    if (!result) return;
    setIsSaving(true);
    try {
      await api.post(`/api/v1/processos/${result.case_id}/documentos/`, {
        titulo: result.petition_name + ' - ' + result.case_titulo,
        tipo: 'peticao',
        descricao: `Petição gerada por IA: ${result.petition_name}`,
        observacoes: currentContent,
      });
      toast.success('Petição salva como documento do caso!');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Erro ao salvar documento.');
    } finally {
      setIsSaving(false);
    }
  }, [result, currentContent]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2"><Bot className="h-6 w-6" /> Petição por IA</h1>
        <p className="text-muted-foreground">Gere petições completas baseadas nos dados do caso</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1">
          <CardHeader><CardTitle>Configuração</CardTitle><CardDescription>Selecione o caso e tipo de petição</CardDescription></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Caso *</Label>
              <Select value={caseId} onValueChange={setCaseId}>
                <SelectTrigger><SelectValue placeholder="Selecione o caso" /></SelectTrigger>
                <SelectContent>{cases.map((c: any) => <SelectItem key={c.id} value={String(c.id)}>{c.titulo}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div>
              <Label>Tipo de Petição *</Label>
              <Select value={petitionType} onValueChange={setPetitionType}>
                <SelectTrigger><SelectValue placeholder="Selecione o tipo" /></SelectTrigger>
                <SelectContent>{types.map((t: PetitionType) => <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div>
              <Label>Instruções Adicionais</Label>
              <Textarea value={extraInstructions} onChange={e => setExtraInstructions(e.target.value)} placeholder="Instruções específicas para o advogado IA..." rows={4} />
            </div>
            <Button className="w-full" onClick={() => generate.mutate()} disabled={!caseId || !petitionType || generate.isPending}>
              {generate.isPending ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Gerando...</> : <><Bot className="h-4 w-4 mr-2" /> Gerar Petição</>}
            </Button>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>{result ? result.petition_name : 'Resultado'}</CardTitle>
              {result && (
                <div className="flex items-center gap-2">
                  <Button size="sm" variant="outline" onClick={handleCopy}>
                    <Copy className="h-4 w-4 mr-1" /> Copiar
                  </Button>
                  {isEditing ? (
                    <>
                      <Button size="sm" variant="default" onClick={handleSaveEdit}>
                        <Check className="h-4 w-4 mr-1" /> Salvar Edição
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setIsEditing(false)}>
                        Cancelar
                      </Button>
                    </>
                  ) : (
                    <Button size="sm" variant="outline" onClick={handleToggleEdit}>
                      <PenLine className="h-4 w-4 mr-1" /> Editar
                    </Button>
                  )}
                  <Button size="sm" variant="outline" onClick={handleSaveAsDocument} disabled={isSaving}>
                    {isSaving ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Save className="h-4 w-4 mr-1" />}
                    Salvar como Documento
                  </Button>
                </div>
              )}
            </div>
            {result && (
              <p className="text-xs text-muted-foreground mt-1">
                Caso: {result.case_titulo} | Tokens: {result.tokens_used}
              </p>
            )}
          </CardHeader>
          <CardContent>
            {result ? (
              isEditing ? (
                <Textarea
                  ref={editorRef}
                  value={editedContent}
                  onChange={(e) => setEditedContent(e.target.value)}
                  className="min-h-[600px] font-mono text-sm"
                  placeholder="Edite o conteúdo da petição..."
                />
              ) : (
                <ScrollArea className="h-[600px] pr-4">
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <ReactMarkdown>{currentContent}</ReactMarkdown>
                  </div>
                </ScrollArea>
              )
            ) : (
              <div className="text-center py-20 text-muted-foreground">
                <FileText className="h-16 w-16 mx-auto mb-4 opacity-20" />
                <p>Selecione um caso e tipo de petição para gerar</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

'use client';

import { useState, useEffect, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Search,
  Loader2,
  AlertTriangle,
  ExternalLink,
  BookOpen,
  Clock,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Trash2,
  Brain,
  Send,
  X,
  Bot,
  User,
  MessageSquare,
  Gavel,
  Building2,
  CalendarDays,
  FileText,
  Tag,
  BarChart3,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import api from '@/lib/api';
import { useCopilot } from '@/hooks/use-copilot';

interface JurisprudenceResult {
  id: string;
  tribunal: string;
  case_number: string;
  relator: string;
  judgment_date: string | null;
  organ: string;
  summary: string;
  full_text: string;
  source_url: string | null;
  is_verified: boolean;
  relevance_score: number;
  // campos enriquecidos do DataJud
  classe?: string;
  grau?: string;
  assuntos?: string[];
  title?: string;
}

interface JurisprudenceSearch {
  id: string;
  query: string;
  specialty: string | null;
  status: string;
  results: JurisprudenceResult[];
  created_at: string;
}

interface Specialty {
  id: string;
  code: string;
  name: string;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '';
  try {
    return new Date(dateStr).toLocaleDateString('pt-BR');
  } catch {
    return dateStr;
  }
}

function grauLabel(grau: string): string {
  const map: Record<string, string> = {
    SUP: 'Superior', G1: '1º Grau', G2: '2º Grau', JE: 'Juizado Especial',
  };
  return map[grau] || grau;
}

// ─── Dialog de Detalhes do Processo ─────────────────────────────────────────

interface DetailDialogProps {
  result: JurisprudenceResult | null;
  open: boolean;
  onClose: () => void;
  onAskCopilot: (result: JurisprudenceResult) => void;
}

function DetailDialog({ result, open, onClose, onAskCopilot }: DetailDialogProps) {
  if (!result) return null;

  const hasDetails = result.case_number || result.organ || result.judgment_date ||
    result.classe || result.grau || (result.assuntos && result.assuntos.length > 0);

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
      <DialogContent className="max-w-2xl w-full max-h-[85vh] flex flex-col p-0 gap-0">
        <DialogDescription className="sr-only">Detalhes do precedente jurisprudencial selecionado</DialogDescription>
        <DialogHeader className="px-5 py-4 border-b shrink-0">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <DialogTitle className="text-base font-semibold flex items-center gap-2">
                <Gavel className="h-4 w-4 text-primary shrink-0" />
                {result.title || `${result.tribunal} – ${result.case_number || 'Processo'}`}
              </DialogTitle>
              <div className="flex items-center gap-2 mt-1 flex-wrap">
                <Badge variant="outline" className="font-mono text-xs">{result.tribunal}</Badge>
                {result.is_verified ? (
                  <Badge className="bg-green-100 text-green-700 text-xs">
                    <CheckCircle2 className="h-3 w-3 mr-1" />Verificado
                  </Badge>
                ) : (
                  <Badge variant="outline" className="text-xs text-yellow-600 border-yellow-300">
                    <AlertTriangle className="h-3 w-3 mr-1" />Não verificado
                  </Badge>
                )}
              </div>
            </div>
            <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </DialogHeader>

        <ScrollArea className="flex-1">
          <div className="px-5 py-4 space-y-5">
            {/* Informações principais */}
            {hasDetails && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {result.case_number && (
                  <InfoRow icon={<FileText className="h-3.5 w-3.5" />} label="Número do Processo" value={result.case_number} mono />
                )}
                {result.tribunal && (
                  <InfoRow icon={<Building2 className="h-3.5 w-3.5" />} label="Tribunal" value={result.tribunal} />
                )}
                {result.organ && (
                  <InfoRow icon={<Building2 className="h-3.5 w-3.5" />} label="Órgão Julgador" value={result.organ} className="sm:col-span-2" />
                )}
                {result.relator && (
                  <InfoRow icon={<User className="h-3.5 w-3.5" />} label="Relator" value={result.relator} className="sm:col-span-2" />
                )}
                {result.judgment_date && (
                  <InfoRow icon={<CalendarDays className="h-3.5 w-3.5" />} label="Data de Ajuizamento" value={formatDate(result.judgment_date)} />
                )}
                {result.classe && (
                  <InfoRow icon={<Gavel className="h-3.5 w-3.5" />} label="Classe Processual" value={result.classe} />
                )}
                {result.grau && (
                  <InfoRow icon={<BarChart3 className="h-3.5 w-3.5" />} label="Grau" value={grauLabel(result.grau)} />
                )}
              </div>
            )}

            {/* Assuntos */}
            {result.assuntos && result.assuntos.length > 0 && (
              <div>
                <p className="text-xs font-medium text-muted-foreground flex items-center gap-1 mb-2">
                  <Tag className="h-3 w-3" /> Assuntos
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {result.assuntos.map((a, i) => (
                    <Badge key={i} variant="secondary" className="text-xs">{a}</Badge>
                  ))}
                </div>
              </div>
            )}

            <Separator />

            {/* Ementa / Resumo */}
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-2">Ementa / Resumo</p>
              <p className="text-sm leading-relaxed text-foreground whitespace-pre-wrap">
                {result.summary || result.full_text || 'Sem resumo disponível.'}
              </p>
            </div>

            {/* Link para fonte */}
            {result.source_url && (
              <>
                <Separator />
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-2">Fonte Oficial</p>
                  <a
                    href={result.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-sm text-primary hover:underline break-all"
                  >
                    <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                    {result.source_url}
                  </a>
                </div>
              </>
            )}
          </div>
        </ScrollArea>

        {/* Ações */}
        <div className="px-5 py-3 border-t shrink-0 flex items-center gap-2">
          <Button
            className="gap-2"
            onClick={() => { onClose(); onAskCopilot(result); }}
          >
            <MessageSquare className="h-4 w-4" />
            Perguntar ao Copilot
          </Button>
          <Button variant="outline" className="gap-2" onClick={() => { onClose(); }}>
            <Brain className="h-4 w-4" />
            Analisar com IA
          </Button>
          {result.source_url && (
            <a href={result.source_url} target="_blank" rel="noopener noreferrer" className="ml-auto">
              <Button variant="ghost" size="sm" className="gap-1 text-xs">
                <ExternalLink className="h-3 w-3" />
                Ver no tribunal
              </Button>
            </a>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

function InfoRow({
  icon,
  label,
  value,
  mono,
  className,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  mono?: boolean;
  className?: string;
}) {
  return (
    <div className={className}>
      <p className="text-xs font-medium text-muted-foreground flex items-center gap-1 mb-0.5">
        {icon} {label}
      </p>
      <p className={`text-sm ${mono ? 'font-mono' : ''}`}>{value}</p>
    </div>
  );
}

// ─── Dialog de análise com IA (Perguntar ao Copilot) ─────────────────────────

interface CopilotDialogProps {
  result: JurisprudenceResult | null;
  open: boolean;
  onClose: () => void;
}

function CopilotDialog({ result, open, onClose }: CopilotDialogProps) {
  const { messages, isStreaming, sendMessage, clearConversation } = useCopilot();
  const [inputText, setInputText] = useState('');
  const [isScraping, setIsScraping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const hasSentInitial = useRef(false);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (!open || !result) {
      hasSentInitial.current = false;
      return;
    }
    if (hasSentInitial.current) return;
    hasSentInitial.current = true;

    const buildContext = (extraText?: string) => {
      const lines: string[] = [
        `Analise este processo judicial do ${result.tribunal}:`,
        '',
        result.title ? `Título: ${result.title}` : '',
        result.case_number ? `Processo: ${result.case_number}` : '',
        `Tribunal: ${result.tribunal}`,
        result.organ ? `Órgão Julgador: ${result.organ}` : '',
        result.relator ? `Relator: ${result.relator}` : '',
        result.judgment_date ? `Data de Ajuizamento: ${formatDate(result.judgment_date)}` : '',
        result.classe ? `Classe Processual: ${result.classe}` : '',
        result.grau ? `Grau: ${grauLabel(result.grau)}` : '',
        result.assuntos && result.assuntos.length > 0
          ? `Assuntos: ${result.assuntos.join(', ')}`
          : '',
        '',
        'Ementa/Resumo:',
        result.summary || result.full_text || '',
      ].filter((l) => l !== undefined);

      if (extraText) {
        lines.push('', '--- Conteúdo adicional da página do tribunal ---', extraText.slice(0, 3000));
      }

      lines.push(
        '',
        'Com base nessas informações, por favor:',
        '1. Faça um resumo jurídico estruturado do processo',
        '2. Identifique os principais fundamentos e teses jurídicas',
        '3. Aponte a relevância prática para advogados',
        '4. Indique precedentes relacionados se souber',
      );

      return lines.filter(Boolean).join('\n');
    };

    // Tenta scrape da fonte, então envia ao Copilot com ou sem conteúdo adicional
    if (result.source_url) {
      setIsScraping(true);
      api.post('/api/v1/jurisprudence/scrape/', { url: result.source_url })
        .then((resp) => {
          const extraText = resp.data?.text || '';
          sendMessage(buildContext(extraText || undefined));
        })
        .catch(() => {
          sendMessage(buildContext());
        })
        .finally(() => setIsScraping(false));
    } else {
      sendMessage(buildContext());
    }
  }, [open, result]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleClose = () => {
    clearConversation();
    setInputText('');
    onClose();
  };

  const handleSend = () => {
    if (!inputText.trim() || isStreaming) return;
    sendMessage(inputText.trim());
    setInputText('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!result) return null;

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) handleClose(); }}>
      <DialogContent className="max-w-2xl w-full h-[80vh] flex flex-col p-0 gap-0">
        <DialogDescription className="sr-only">Consultar o Copilot jurídico com base neste precedente</DialogDescription>
        <DialogHeader className="px-4 py-3 border-b shrink-0">
          <div className="flex items-center justify-between gap-2">
            <DialogTitle className="flex items-center gap-2 text-base font-semibold">
              <MessageSquare className="h-5 w-5 text-primary" />
              Perguntar ao Copilot
              <span className="text-sm font-normal text-muted-foreground">{result.tribunal}</span>
            </DialogTitle>
            <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0" onClick={handleClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
          {(result.case_number || result.classe) && (
            <p className="text-xs text-muted-foreground px-0 mt-0.5">
              {[result.classe, result.case_number].filter(Boolean).join(' · ')}
            </p>
          )}
        </DialogHeader>

        <ScrollArea className="flex-1 px-4 py-3">
          <div className="space-y-4">
            {(messages.length === 0 || isScraping) && (
              <div className="flex items-center justify-center h-20 text-muted-foreground text-sm gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                {isScraping ? 'Buscando conteúdo da fonte...' : 'Iniciando análise...'}
              </div>
            )}
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="shrink-0 h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center">
                    <Bot className="h-4 w-4 text-primary" />
                  </div>
                )}
                <div
                  className={`max-w-[85%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
                    msg.role === 'user'
                      ? 'bg-primary/10 text-foreground'
                      : 'bg-muted text-foreground'
                  }`}
                >
                  {msg.content}
                  {msg.isStreaming && (
                    <span className="inline-block ml-1 animate-pulse">▋</span>
                  )}
                </div>
                {msg.role === 'user' && (
                  <div className="shrink-0 h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center">
                    <User className="h-4 w-4 text-primary" />
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        <div className="px-4 py-3 border-t shrink-0">
          <div className="flex gap-2">
            <Textarea
              placeholder="Faça uma pergunta sobre este processo..."
              className="min-h-[40px] max-h-[120px] resize-none text-sm"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isStreaming || isScraping}
            />
            <Button
              size="icon"
              className="shrink-0 self-end"
              onClick={handleSend}
              disabled={!inputText.trim() || isStreaming || isScraping}
            >
              {isStreaming ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-1">Enter para enviar · Shift+Enter para nova linha</p>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ─── ResultCard ──────────────────────────────────────────────────────────────

function ResultCard({
  result,
  onDetail,
  onAskCopilot,
}: {
  result: JurisprudenceResult;
  onDetail: (r: JurisprudenceResult) => void;
  onAskCopilot: (r: JurisprudenceResult) => void;
}) {
  return (
    <div
      className="border rounded-lg p-4 space-y-2 hover:bg-accent/30 cursor-pointer transition-colors"
      onClick={() => onDetail(result)}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="outline" className="text-xs font-mono">{result.tribunal}</Badge>
            {result.case_number && (
              <span className="text-xs font-mono text-muted-foreground truncate max-w-[180px]">
                {result.case_number}
              </span>
            )}
            {result.classe && (
              <Badge variant="secondary" className="text-xs">{result.classe}</Badge>
            )}
            {result.is_verified ? (
              <Badge className="bg-green-100 text-green-700 text-xs">
                <CheckCircle2 className="h-3 w-3 mr-1" />Verificado
              </Badge>
            ) : (
              <Badge variant="outline" className="text-xs text-yellow-600 border-yellow-300">
                <AlertTriangle className="h-3 w-3 mr-1" />Não verificado
              </Badge>
            )}
          </div>
          <div className="mt-1 text-xs text-muted-foreground flex items-center gap-2 flex-wrap">
            {result.organ && <span>{result.organ}</span>}
            {result.judgment_date && (
              <span>• Ajuizado: {formatDate(result.judgment_date)}</span>
            )}
            {result.grau && <span>• {grauLabel(result.grau)}</span>}
          </div>
        </div>
        <div className="flex items-center gap-1 shrink-0" onClick={(e) => e.stopPropagation()}>
          <Button
            size="sm"
            variant="outline"
            className="h-7 gap-1 text-xs"
            onClick={() => onAskCopilot(result)}
          >
            <MessageSquare className="h-3 w-3" />
            Perguntar
          </Button>
          {result.source_url && (
            <a href={result.source_url} target="_blank" rel="noopener noreferrer">
              <Button size="sm" variant="ghost" className="h-7 gap-1 text-xs">
                <ExternalLink className="h-3 w-3" />
                Fonte
              </Button>
            </a>
          )}
        </div>
      </div>

      <p className="text-sm text-muted-foreground line-clamp-3">{result.summary}</p>

      {result.assuntos && result.assuntos.length > 0 && (
        <div className="flex gap-1 flex-wrap">
          {result.assuntos.slice(0, 3).map((a, i) => (
            <Badge key={i} variant="secondary" className="text-xs">{a}</Badge>
          ))}
          {result.assuntos.length > 3 && (
            <Badge variant="secondary" className="text-xs">+{result.assuntos.length - 3}</Badge>
          )}
        </div>
      )}

      <p className="text-xs text-primary/70">Clique para ver detalhes completos</p>
    </div>
  );
}

// ─── JurisprudenciaPage ──────────────────────────────────────────────────────

export default function JurisprudenciaPage() {
  const [query, setQuery] = useState('');
  const [specialty, setSpecialty] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [latestSearchData, setLatestSearchData] = useState<JurisprudenceSearch | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [detailTarget, setDetailTarget] = useState<JurisprudenceResult | null>(null);
  const [copilotTarget, setCopilotTarget] = useState<JurisprudenceResult | null>(null);
  const [confirmClearHistory, setConfirmClearHistory] = useState(false);
  const queryClient = useQueryClient();

  const { data: specialties = [] } = useQuery({
    queryKey: ['specialties'],
    queryFn: async () => {
      const response = await api.get<Specialty[]>('/api/v1/jurisprudence/specialties/');
      return response.data;
    },
  });

  const { data: searches = [], isLoading: loadingHistory } = useQuery({
    queryKey: ['jurisprudence-searches'],
    queryFn: async () => {
      const response = await api.get<{ results: JurisprudenceSearch[] }>('/api/v1/jurisprudence/searches/');
      return response.data.results || [];
    },
  });

  const handleSearch = async () => {
    if (!query.trim() || query.trim().length < 3) return;
    setIsSearching(true);
    setSearchError(null);
    setLatestSearchData(null);

    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const response = await fetch('/api/v1/jurisprudence/searches/stream/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ query, specialty: specialty || undefined }),
      });

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(errText || `HTTP ${response.status}`);
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let doneSearchId: string | null = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value);
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          let event: Record<string, any>;
          try {
            event = JSON.parse(line.slice(6));
          } catch {
            continue;
          }

          if (event.event === 'error') {
            throw new Error(event.error);
          } else if (event.event === 'done') {
            doneSearchId = event.search_id;
          }
        }
      }

      queryClient.invalidateQueries({ queryKey: ['jurisprudence-searches'] });

      if (doneSearchId) {
        const historyResp = await api.get<{ results: JurisprudenceSearch[] }>('/api/v1/jurisprudence/searches/');
        const allSearches = historyResp.data.results || [];
        const latest = allSearches.find(s => s.id === doneSearchId) || allSearches[0] || null;
        setLatestSearchData(latest);
        queryClient.setQueryData(['jurisprudence-searches'], allSearches);
      }
    } catch (err: any) {
      setSearchError(err.message || 'Erro desconhecido');
    } finally {
      setIsSearching(false);
    }
  };

  const handleClearHistory = async () => {
    setConfirmClearHistory(false);
    try {
      await api.delete('/api/v1/jurisprudence/searches/clear/');
      queryClient.invalidateQueries({ queryKey: ['jurisprudence-searches'] });
      setLatestSearchData(null);
    } catch {
      // toast já exibido pelo interceptor do axios
    }
  };

  const handleDeleteSearch = async (searchId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.delete(`/api/v1/jurisprudence/searches/${searchId}/`);
      queryClient.invalidateQueries({ queryKey: ['jurisprudence-searches'] });
      if (latestSearchData?.id === searchId) setLatestSearchData(null);
    } catch {
      // toast já exibido pelo interceptor do axios
    }
  };

  const latestSearch = latestSearchData || (searches.length > 0 ? searches[0] : null);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Search className="h-8 w-8" />
          Pesquisa Jurisprudencial
        </h1>
        <p className="text-muted-foreground">
          Pesquise jurisprudência dos principais tribunais brasileiros via DataJud (CNJ)
        </p>
      </div>

      {/* Formulário de Pesquisa */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Nova Pesquisa</CardTitle>
          <CardDescription>
            Digite um tema, tese jurídica ou assunto para pesquisar nos tribunais
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Termo de Pesquisa *</Label>
            <div className="relative">
              <Textarea
                placeholder="Ex: responsabilidade civil, dano moral, rescisão contratual, homicídio qualificado..."
                className="min-h-[80px] resize-none pr-32"
                value={query}
                onChange={e => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSearch();
                }
              }}
              />
              <div className="absolute top-1 right-1">
                <AIEnhanceButton
                  value={query}
                  onEnhance={setQuery}
                  context="termo de pesquisa de jurisprudência"
                  objective="Melhore a precisão terminológica jurídica do termo de pesquisa"
                />
              </div>
            </div>
          </div>

          {specialties.length > 0 && (
            <div className="space-y-2">
              <Label>Especialidade (opcional)</Label>
              <Select value={specialty || 'all'} onValueChange={v => setSpecialty(v === 'all' ? '' : v)}>
                <SelectTrigger className="w-[220px]">
                  <SelectValue placeholder="Todas as especialidades" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas</SelectItem>
                  {specialties.map(s => (
                    <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          <div className="flex items-center gap-3">
            <Button
              onClick={handleSearch}
              disabled={!query.trim() || query.trim().length < 3 || isSearching}
              className="gap-2"
            >
              {isSearching ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Search className="h-4 w-4" />
              )}
              {isSearching ? 'Pesquisando...' : 'Pesquisar'}
            </Button>
          </div>

          {searchError && !isSearching && (
            <div className="flex items-center gap-2 text-destructive text-sm">
              <AlertTriangle className="h-4 w-4" />
              Erro ao realizar pesquisa: {searchError}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Resultados */}
      {latestSearch && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              Resultados: &ldquo;{latestSearch.query}&rdquo;
            </CardTitle>
            <CardDescription>
              {latestSearch.results.length} resultado(s) encontrado(s) · Clique em um card para ver detalhes
            </CardDescription>
          </CardHeader>
          <CardContent>
            {latestSearch.results.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <BookOpen className="h-10 w-10 mx-auto mb-2 opacity-30" />
                <p className="text-sm">Nenhum resultado encontrado para esta pesquisa.</p>
                <p className="text-xs mt-1">Tente termos mais específicos ou consulte diretamente os tribunais:</p>
                <div className="flex gap-3 justify-center mt-3 flex-wrap">
                  <a href="https://jurisprudencia.stf.jus.br" target="_blank" rel="noopener noreferrer"
                    className="text-xs text-primary underline">STF</a>
                  <a href="https://scon.stj.jus.br" target="_blank" rel="noopener noreferrer"
                    className="text-xs text-primary underline">STJ</a>
                  <a href="https://jurisprudencia.tst.jus.br" target="_blank" rel="noopener noreferrer"
                    className="text-xs text-primary underline">TST</a>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                {latestSearch.results.map(result => (
                  <ResultCard
                    key={result.id}
                    result={result}
                    onDetail={setDetailTarget}
                    onAskCopilot={setCopilotTarget}
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Histórico */}
      {searches.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Pesquisas Anteriores
              </CardTitle>
              {confirmClearHistory ? (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">Apagar tudo?</span>
                  <Button variant="destructive" size="sm" onClick={handleClearHistory}>Sim</Button>
                  <Button variant="ghost" size="sm" onClick={() => setConfirmClearHistory(false)}>Não</Button>
                </div>
              ) : (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setConfirmClearHistory(true)}
                  className="text-destructive hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4 mr-1" />
                  Limpar histórico
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {searches.slice(0, 10).map((search: JurisprudenceSearch) => (
                <div
                  key={search.id}
                  className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent/50 cursor-pointer transition-colors"
                  onClick={() => setQuery(search.query)}
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{search.query}</p>
                    <p className="text-xs text-muted-foreground">
                      {search.results.length} resultado(s) •{' '}
                      {new Date(search.created_at).toLocaleDateString('pt-BR')}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 ml-3 shrink-0">
                    <Badge variant="outline" className="text-xs">
                      {search.status === 'completed' ? 'Concluída' : search.status}
                    </Badge>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive"
                      onClick={(e) => handleDeleteSearch(search.id, e)}
                      title="Excluir esta pesquisa"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Fontes Oficiais */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Fontes Oficiais de Consulta</CardTitle>
          <CardDescription>Acesse diretamente os portais dos tribunais</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {[
              { name: 'STF — Supremo Tribunal Federal', url: 'https://jurisprudencia.stf.jus.br', tribunal: 'STF' },
              { name: 'STJ — Superior Tribunal de Justiça', url: 'https://scon.stj.jus.br', tribunal: 'STJ' },
              { name: 'TST — Tribunal Superior do Trabalho', url: 'https://jurisprudencia.tst.jus.br', tribunal: 'TST' },
              { name: 'TRF-2 — Rio de Janeiro e ES', url: 'https://jurisprudencia.trf2.jus.br', tribunal: 'TRF-2' },
              { name: 'TJRJ — Tribunal de Justiça do RJ', url: 'https://www4.tjrj.jus.br/EJURIS', tribunal: 'TJRJ' },
              { name: 'Planalto — Legislação Federal', url: 'https://www.planalto.gov.br', tribunal: 'LEG' },
            ].map(source => (
              <a
                key={source.tribunal}
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-3 p-3 rounded-lg border hover:bg-accent/50 transition-colors"
              >
                <Badge variant="outline" className="font-mono shrink-0">{source.tribunal}</Badge>
                <span className="text-sm">{source.name}</span>
                <ExternalLink className="h-3 w-3 text-muted-foreground ml-auto shrink-0" />
              </a>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Dialogs */}
      <DetailDialog
        result={detailTarget}
        open={!!detailTarget}
        onClose={() => setDetailTarget(null)}
        onAskCopilot={(r) => { setDetailTarget(null); setCopilotTarget(r); }}
      />
      <CopilotDialog
        result={copilotTarget}
        open={!!copilotTarget}
        onClose={() => setCopilotTarget(null)}
      />
    </div>
  );
}

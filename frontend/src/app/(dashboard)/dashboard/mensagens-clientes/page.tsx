'use client';

import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import {
  MessageSquare,
  Send,
  Loader2,
  AlertTriangle,
  CheckCheck,
  Check,
  User,
  Search,
  Paperclip,
  FileText,
  Image as ImageIcon,
  X,
  Sparkles,
  ChevronDown,
  Phone,
  Mail,
  ExternalLink,
  Calendar,
  DollarSign,
  ClipboardList,
  Gavel,
  Bot,
  Briefcase,
  ArrowLeft,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { AITextarea } from '@/components/ui/ai-textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from '@/components/ui/dropdown-menu';
import { toast } from 'sonner';
import api from '@/lib/api';
import {
  useClientMessages,
  useClientMessageReply,
  useClientMessagesMarkRead,
  useClientMessagesUnread,
  ClientMessageItem,
} from '@/hooks/use-client-messages';

// ── Helpers ──

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMin = Math.floor(diffMs / 60000);

  if (diffMin < 1) return 'agora';
  if (diffMin < 60) return `${diffMin}min`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `${diffH}h`;
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
}

function formatFullDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ── Types ──

interface ClientThread {
  clientId: string;
  clientName: string;
  clientEmail?: string;
  clientPhone?: string;
  lastMessage: string;
  lastMessageAt: string;
  unreadCount: number;
  caseId: string | null;
  caseTitulo: string | null;
}

interface FileAttachment {
  file: File;
  preview?: string;
}

interface AtCommandOption {
  key: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  template: string;
}

interface AISuggestion {
  label: string;
  tone: string;
  prompt: string;
}

// ── Constants ──

const AT_COMMANDS: AtCommandOption[] = [
  {
    key: 'prazo',
    label: '@prazo',
    description: 'Criar prazo para este cliente',
    icon: <Calendar className="h-4 w-4 text-orange-500" />,
    template: '\n\n📅 **PRAZO CRIADO**\n> Prazo: [descreva o prazo]\n> Vencimento: [data]\n> Caso: {case}\n',
  },
  {
    key: 'tarefa',
    label: '@tarefa',
    description: 'Criar tarefa para este caso',
    icon: <ClipboardList className="h-4 w-4 text-blue-500" />,
    template: '\n\n✅ **TAREFA CRIADA**\n> Tarefa: [descreva a tarefa]\n> Responsável: [nome]\n> Caso: {case}\n',
  },
  {
    key: 'documento',
    label: '@documento',
    description: 'Anexar documento do caso',
    icon: <FileText className="h-4 w-4 text-green-500" />,
    template: '\n\n📎 **DOCUMENTO ANEXADO**\n> Documento: [nome do documento]\n> Tipo: [petição/contrato/procuração/outro]\n> Caso: {case}\n',
  },
  {
    key: 'audiencia',
    label: '@audiencia',
    description: 'Informar sobre audiência',
    icon: <Gavel className="h-4 w-4 text-purple-500" />,
    template: '\n\n⚖️ **AUDIÊNCIA AGENDADA**\n> Data: [data e hora]\n> Local: [vara/tribunal]\n> Tipo: [instrução/conciliação/julgamento]\n> Caso: {case}\n',
  },
  {
    key: 'financeiro',
    label: '@financeiro',
    description: 'Enviar resumo financeiro',
    icon: <DollarSign className="h-4 w-4 text-emerald-500" />,
    template: '\n\n💰 **RESUMO FINANCEIRO**\n> Honorários: R$ [valor]\n> Status: [em dia/pendente]\n> Próximo vencimento: [data]\n',
  },
  {
    key: 'caso',
    label: '@caso',
    description: 'Vincular/abrir caso do cliente',
    icon: <Briefcase className="h-4 w-4 text-indigo-500" />,
    template: '\n\n📋 **CASO VINCULADO**\n> Processo: [número]\n> Título: {case}\n> Status: [ativo/concluído/arquivado]\n',
  },
];

const AI_SUGGESTIONS: AISuggestion[] = [
  { label: 'Resposta formal', tone: 'formal', prompt: 'Responda de forma formal e profissional, usando linguagem jurídica adequada.' },
  { label: 'Resposta cordial', tone: 'cordial', prompt: 'Responda de forma cordial e acolhedora, mantendo o profissionalismo.' },
  { label: 'Explicar juridicamente', tone: 'legal_explanation', prompt: 'Explique a situação jurídica de forma clara e acessível para o cliente leigo.' },
  { label: 'Resumir situação', tone: 'summary', prompt: 'Resuma o estado atual do caso e próximos passos de forma clara e objetiva.' },
];

// ── Message Status Component ──

function MessageStatus({ msg }: { msg: ClientMessageItem }) {
  if (msg.sender_type !== 'lawyer') return null;

  // Simulated status based on is_read and time
  const now = new Date();
  const msgTime = new Date(msg.created_at);
  const diffMin = (now.getTime() - msgTime.getTime()) / 60000;

  if (msg.is_read) {
    return (
      <span className="inline-flex items-center gap-0.5 text-blue-300" title="Lida">
        <CheckCheck className="h-3 w-3" />
      </span>
    );
  }
  if (diffMin > 2) {
    return (
      <span className="inline-flex items-center gap-0.5 text-purple-300" title="Entregue">
        <CheckCheck className="h-3 w-3" />
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-0.5 text-purple-300/60" title="Enviada">
      <Check className="h-3 w-3" />
    </span>
  );
}

// ── File Attachment in Message ──

function MessageAttachment({ filename, size }: { filename: string; size?: number }) {
  const isImage = /\.(jpg|jpeg|png|gif|webp)$/i.test(filename);
  return (
    <div className="mt-2 flex items-center gap-2 rounded-lg bg-white/10 px-3 py-2 text-xs">
      {isImage ? (
        <ImageIcon className="h-4 w-4 shrink-0" />
      ) : (
        <FileText className="h-4 w-4 shrink-0" />
      )}
      <span className="truncate">{filename}</span>
      {size && <span className="shrink-0 opacity-70">{formatFileSize(size)}</span>}
    </div>
  );
}

// ── Client Context Sidebar ──

function ClientContextSidebar({
  thread,
  messages,
}: {
  thread: ClientThread;
  messages: ClientMessageItem[];
}) {
  // Derive basic context from available data
  const caseInfo = thread.caseTitulo
    ? [{ id: thread.caseId || '', titulo: thread.caseTitulo, status: 'Ativo' }]
    : [];

  const totalMessages = messages.length;
  const clientMessages = messages.filter((m) => m.sender_type === 'client').length;
  const lawyerMessages = messages.filter((m) => m.sender_type === 'lawyer').length;

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b">
        <div className="flex items-center gap-3 mb-3">
          <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
            <User className="h-6 w-6 text-primary" />
          </div>
          <div className="min-w-0">
            <p className="font-semibold text-sm truncate">{thread.clientName}</p>
            <p className="text-xs text-muted-foreground">Cliente</p>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="flex-1 text-xs h-8"
            title={thread.clientPhone || 'Sem telefone'}
            disabled={!thread.clientPhone}
            onClick={() => {
              if (thread.clientPhone) {
                window.open(`tel:${thread.clientPhone}`, '_self');
              }
            }}
          >
            <Phone className="h-3 w-3 mr-1" />
            Ligar
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="flex-1 text-xs h-8"
            title={thread.clientEmail || 'Sem e-mail'}
            disabled={!thread.clientEmail}
            onClick={() => {
              if (thread.clientEmail) {
                window.open(`mailto:${thread.clientEmail}`, '_self');
              }
            }}
          >
            <Mail className="h-3 w-3 mr-1" />
            E-mail
          </Button>
          {thread.caseId && (
            <Button
              variant="outline"
              size="sm"
              className="flex-1 text-xs h-8"
              title="Abrir caso"
              asChild
            >
              <a href={`/dashboard/processos/${thread.caseId}`}>
                <ExternalLink className="h-3 w-3 mr-1" />
                Caso
              </a>
            </Button>
          )}
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-4">
          {/* Stats */}
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              Estatísticas
            </h4>
            <div className="grid grid-cols-2 gap-2">
              <div className="rounded-lg bg-muted/50 p-2 text-center">
                <p className="text-lg font-bold">{totalMessages}</p>
                <p className="text-[10px] text-muted-foreground">Mensagens</p>
              </div>
              <div className="rounded-lg bg-muted/50 p-2 text-center">
                <p className="text-lg font-bold">{thread.unreadCount}</p>
                <p className="text-[10px] text-muted-foreground">Nao lidas</p>
              </div>
            </div>
          </div>

          <Separator />

          {/* Active Cases */}
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              Casos Ativos
            </h4>
            {caseInfo.length > 0 ? (
              <div className="space-y-2">
                {caseInfo.map((c) => (
                  <div key={c.id} className="rounded-lg border p-2.5">
                    <p className="text-xs font-medium truncate">{c.titulo}</p>
                    <div className="flex items-center gap-1.5 mt-1">
                      <Badge variant="secondary" className="text-[10px] h-4">
                        {c.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">Nenhum caso vinculado</p>
            )}
          </div>

          <Separator />

          {/* Timeline Summary */}
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              Atividade
            </h4>
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Msgs do cliente</span>
                <span className="font-medium">{clientMessages}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Suas respostas</span>
                <span className="font-medium">{lawyerMessages}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Ultima msg</span>
                <span className="font-medium">{formatDate(thread.lastMessageAt)}</span>
              </div>
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}

// ── Component ──

export default function MensagensClientesPage() {
  const [selectedClientId, setSelectedClientId] = useState<string | null>(null);
  const [replyContent, setReplyContent] = useState('');
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [mobileShowConversation, setMobileShowConversation] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // File attachments
  const [attachments, setAttachments] = useState<FileAttachment[]>([]);

  // AI suggestions
  const [aiLoading, setAiLoading] = useState(false);
  const [aiSuggestion, setAiSuggestion] = useState<string | null>(null);

  // @ commands
  const [showAtMenu, setShowAtMenu] = useState(false);
  const [atFilter, setAtFilter] = useState('');

  // Filters
  const filters: Record<string, string> = {};
  if (unreadOnly) filters.unread = 'true';

  const { data, isLoading, error } = useClientMessages(filters);
  const { data: unreadData } = useClientMessagesUnread();
  const replyMutation = useClientMessageReply();
  const markReadMutation = useClientMessagesMarkRead();

  const messages = data?.results || [];
  const unreadCount = unreadData?.unread_count ?? data?.unread_count ?? 0;

  // Build threads from messages
  const threads = useMemo<ClientThread[]>(() => {
    const map = new Map<string, ClientThread>();
    for (const msg of messages) {
      const key = msg.client;
      if (!map.has(key)) {
        map.set(key, {
          clientId: msg.client,
          clientName: msg.client_name || 'Cliente',
          clientEmail: msg.client_email || undefined,
          clientPhone: msg.client_phone || undefined,
          lastMessage: msg.content,
          lastMessageAt: msg.created_at,
          unreadCount: 0,
          caseId: msg.case,
          caseTitulo: msg.case_titulo,
        });
      }
      if (msg.sender_type === 'client' && !msg.is_read) {
        const t = map.get(key)!;
        t.unreadCount += 1;
      }
    }
    let result = Array.from(map.values());
    result.sort((a, b) => {
      if (a.unreadCount > 0 && b.unreadCount === 0) return -1;
      if (a.unreadCount === 0 && b.unreadCount > 0) return 1;
      return new Date(b.lastMessageAt).getTime() - new Date(a.lastMessageAt).getTime();
    });
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(
        (t) =>
          t.clientName.toLowerCase().includes(term) ||
          (t.caseTitulo && t.caseTitulo.toLowerCase().includes(term))
      );
    }
    return result;
  }, [messages, searchTerm]);

  // Conversation for selected client
  const conversation = useMemo(() => {
    if (!selectedClientId) return [];
    return messages
      .filter((m) => m.client === selectedClientId)
      .slice()
      .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
  }, [messages, selectedClientId]);

  const selectedThread = threads.find((t) => t.clientId === selectedClientId);

  // Filtered @ commands
  const filteredAtCommands = useMemo(() => {
    if (!atFilter) return AT_COMMANDS;
    const f = atFilter.toLowerCase();
    return AT_COMMANDS.filter(
      (cmd) =>
        cmd.key.includes(f) ||
        cmd.label.toLowerCase().includes(f) ||
        cmd.description.toLowerCase().includes(f)
    );
  }, [atFilter]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation]);

  // ── Handlers ──

  const handleSelectClient = (clientId: string) => {
    setSelectedClientId(clientId);
    setMobileShowConversation(true);
    setAttachments([]);
    setAiSuggestion(null);
  };

  const handleBackToList = () => {
    setMobileShowConversation(false);
  };

  const handleMarkRead = () => {
    if (!selectedClientId) return;
    markReadMutation.mutate(
      { client: selectedClientId, case: selectedThread?.caseId || undefined },
      {
        onSuccess: () => {
          toast.success('Mensagens marcadas como lidas');
        },
      }
    );
  };

  const handleSendReply = () => {
    if (!selectedClientId || (!replyContent.trim() && attachments.length === 0)) return;

    let content = replyContent.trim();

    // Append attachment info to message content
    if (attachments.length > 0) {
      const attachInfo = attachments
        .map((a) => `📎 ${a.file.name} (${formatFileSize(a.file.size)})`)
        .join('\n');
      content = content ? `${content}\n\n${attachInfo}` : attachInfo;
    }

    replyMutation.mutate(
      {
        client: selectedClientId,
        case: selectedThread?.caseId || undefined,
        content,
      },
      {
        onSuccess: () => {
          setReplyContent('');
          setAttachments([]);
          setAiSuggestion(null);
          toast.success('Mensagem enviada');
        },
        onError: () => {
          toast.error('Erro ao enviar mensagem');
        },
      }
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendReply();
    }
  };

  // ── File Handling ──

  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const newAttachments: FileAttachment[] = (Array.from(files) as File[]).map((file) => ({
      file,
      preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined,
    }));

    setAttachments((prev) => [...prev, ...newAttachments]);
    // Reset input
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeAttachment = (index: number) => {
    setAttachments((prev) => {
      const updated = [...prev];
      if (updated[index].preview) URL.revokeObjectURL(updated[index].preview!);
      updated.splice(index, 1);
      return updated;
    });
  };

  // ── AI Suggestion ──

  const handleAISuggest = useCallback(
    async (suggestion: AISuggestion) => {
      if (!selectedClientId || !conversation.length) return;

      setAiLoading(true);
      setAiSuggestion(null);

      // Build context from recent messages
      const recentMessages = conversation.slice(-5).map((m) => ({
        role: m.sender_type === 'client' ? 'user' : 'assistant',
        content: m.content,
      }));

      try {
        const res = await api.post('/api/v1/copilot/suggest/', {
          context: {
            messages: recentMessages,
            client_name: selectedThread?.clientName,
            case_titulo: selectedThread?.caseTitulo,
          },
          tone: suggestion.tone,
          prompt: suggestion.prompt,
        });

        const suggestedText = res.data?.suggestion || res.data?.content || res.data?.text || '';
        if (suggestedText) {
          setAiSuggestion(suggestedText);
          setReplyContent(suggestedText);
          toast.success('Sugestao de IA gerada');
        } else {
          toast.error('Nenhuma sugestao recebida');
        }
      } catch {
        toast.error('Erro ao gerar sugestao com IA');
      } finally {
        setAiLoading(false);
      }
    },
    [selectedClientId, conversation, selectedThread]
  );

  // ── @ Commands ──

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setReplyContent(value);

    // Check for @ trigger
    const cursorPos = e.target.selectionStart || 0;
    const textBefore = value.substring(0, cursorPos);
    const lastAtIndex = textBefore.lastIndexOf('@');

    if (lastAtIndex >= 0) {
      const textAfterAt = textBefore.substring(lastAtIndex + 1);
      // Only show menu if @ is at start of line or after whitespace, and no space in the filter
      const charBeforeAt = lastAtIndex > 0 ? textBefore[lastAtIndex - 1] : '\n';
      if ((charBeforeAt === '\n' || charBeforeAt === ' ' || lastAtIndex === 0) && !/\s/.test(textAfterAt)) {
        setShowAtMenu(true);
        setAtFilter(textAfterAt);
        return;
      }
    }
    setShowAtMenu(false);
    setAtFilter('');
  };

  const handleAtCommandSelect = (cmd: AtCommandOption) => {
    const caseName = selectedThread?.caseTitulo || '[caso]';
    const template = cmd.template.replace(/{case}/g, caseName);

    // Replace @xxx typed so far with the template
    const cursorPos = textareaRef.current?.selectionStart || replyContent.length;
    const textBefore = replyContent.substring(0, cursorPos);
    const lastAtIndex = textBefore.lastIndexOf('@');
    const textAfterCursor = replyContent.substring(cursorPos);

    const newContent =
      textBefore.substring(0, lastAtIndex) + template + textAfterCursor;
    setReplyContent(newContent);
    setShowAtMenu(false);
    setAtFilter('');

    // Focus back
    setTimeout(() => textareaRef.current?.focus(), 50);
  };

  // ── Render ──

  return (
    <div className="space-y-4 pb-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight flex items-center gap-2">
            <MessageSquare className="h-7 w-7 sm:h-8 sm:w-8" />
            Mensagens de Clientes
            {unreadCount > 0 && (
              <Badge variant="destructive" className="text-xs ml-1">
                {unreadCount}
              </Badge>
            )}
          </h1>
          <p className="text-muted-foreground text-sm sm:text-base">
            Visualize e responda mensagens recebidas pelo portal
          </p>
        </div>
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        className="hidden"
        onChange={handleFileChange}
        accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.gif,.webp,.xls,.xlsx,.txt,.odt"
      />

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <div className="flex items-center justify-center py-20 text-destructive gap-2">
          <AlertTriangle className="h-5 w-5" />
          <span>Erro ao carregar mensagens</span>
        </div>
      ) : messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground gap-3">
          <MessageSquare className="h-12 w-12 opacity-30" />
          <p className="text-sm">Nenhuma mensagem de clientes</p>
          <p className="text-xs">
            Quando clientes enviarem mensagens pelo portal, elas aparecerão aqui.
          </p>
        </div>
      ) : (
        <div className="flex gap-4 h-[calc(100vh-220px)] min-h-[500px]">
          {/* Left panel: client list */}
          <Card
            className={`w-full lg:w-80 lg:min-w-[320px] shrink-0 flex flex-col overflow-hidden ${
              mobileShowConversation ? 'hidden lg:flex' : 'flex'
            }`}
          >
            <CardHeader className="pb-3 shrink-0">
              <CardTitle className="text-sm font-medium">Conversas</CardTitle>
              <div className="space-y-2 mt-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Buscar parte..."
                    className="pl-9 text-sm h-9"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
                <div className="flex items-center gap-2">
                  <Switch
                    id="unread-filter"
                    checked={unreadOnly}
                    onCheckedChange={setUnreadOnly}
                  />
                  <Label
                    htmlFor="unread-filter"
                    className="text-xs text-muted-foreground cursor-pointer"
                  >
                    Apenas nao lidas
                  </Label>
                </div>
              </div>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto p-0">
              {threads.length === 0 ? (
                <div className="p-4 text-center text-sm text-muted-foreground">
                  Nenhuma conversa encontrada
                </div>
              ) : (
                <div className="divide-y">
                  {threads.map((thread) => (
                    <button
                      key={thread.clientId}
                      type="button"
                      onClick={() => handleSelectClient(thread.clientId)}
                      className={`w-full text-left p-3 hover:bg-accent/50 transition-colors ${
                        selectedClientId === thread.clientId ? 'bg-accent/70' : ''
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-2 min-w-0">
                          <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                            <User className="h-4 w-4 text-primary" />
                          </div>
                          <div className="min-w-0">
                            <p className="font-medium text-sm truncate">
                              {thread.clientName}
                            </p>
                            {thread.caseTitulo && (
                              <p className="text-[11px] text-muted-foreground truncate">
                                {thread.caseTitulo}
                              </p>
                            )}
                            <p className="text-xs text-muted-foreground truncate mt-0.5">
                              {thread.lastMessage.length > 50
                                ? thread.lastMessage.substring(0, 50) + '...'
                                : thread.lastMessage}
                            </p>
                          </div>
                        </div>
                        <div className="flex flex-col items-end gap-1 shrink-0">
                          <span className="text-[10px] text-muted-foreground">
                            {formatDate(thread.lastMessageAt)}
                          </span>
                          {thread.unreadCount > 0 && (
                            <Badge
                              variant="destructive"
                              className="text-[10px] h-5 min-w-5 flex items-center justify-center"
                            >
                              {thread.unreadCount}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Center panel: conversation */}
          <Card
            className={`flex-1 flex flex-col overflow-hidden ${
              !mobileShowConversation ? 'hidden lg:flex' : 'flex'
            }`}
          >
            {!selectedClientId ? (
              <div className="flex-1 flex items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <MessageSquare className="h-12 w-12 mx-auto mb-3 opacity-30" />
                  <p className="text-sm">Selecione uma conversa para visualizar</p>
                </div>
              </div>
            ) : (
              <>
                {/* Conversation header */}
                <CardHeader className="pb-3 shrink-0 border-b">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-3">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="lg:hidden"
                        onClick={handleBackToList}
                        aria-label="Voltar para lista de conversas"
                      >
                        <ArrowLeft className="h-4 w-4" />
                      </Button>
                      <div className="h-9 w-9 rounded-full bg-primary/10 flex items-center justify-center">
                        <User className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <p className="font-semibold text-sm">
                          {selectedThread?.clientName || 'Cliente'}
                        </p>
                        {selectedThread?.caseTitulo && (
                          <p className="text-xs text-muted-foreground">
                            {selectedThread.caseTitulo}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {selectedThread && selectedThread.unreadCount > 0 && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleMarkRead}
                          disabled={markReadMutation.isPending}
                          className="text-xs"
                        >
                          {markReadMutation.isPending ? (
                            <Loader2 className="h-3 w-3 animate-spin mr-1" />
                          ) : (
                            <CheckCheck className="h-3 w-3 mr-1" />
                          )}
                          Marcar como Lidas
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowSidebar(!showSidebar)}
                        className="hidden xl:flex text-xs"
                        title={showSidebar ? 'Ocultar detalhes' : 'Mostrar detalhes'}
                        aria-label={showSidebar ? 'Ocultar detalhes do cliente' : 'Mostrar detalhes do cliente'}
                      >
                        <User className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>

                {/* Messages */}
                <CardContent className="flex-1 overflow-y-auto p-4 space-y-3">
                  {conversation.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex ${
                        msg.sender_type === 'lawyer' ? 'justify-end' : 'justify-start'
                      }`}
                    >
                      <div
                        className={`max-w-[80%] rounded-2xl px-4 py-2.5 ${
                          msg.sender_type === 'lawyer'
                            ? 'bg-purple-600 text-white rounded-br-md'
                            : 'bg-gray-100 dark:bg-gray-800 text-foreground rounded-bl-md'
                        }`}
                      >
                        <p
                          className={`text-xs font-medium mb-1 ${
                            msg.sender_type === 'lawyer'
                              ? 'text-purple-200'
                              : 'text-muted-foreground'
                          }`}
                        >
                          {msg.sender_name}
                        </p>
                        <p className="text-sm whitespace-pre-wrap break-words">
                          {msg.content}
                        </p>
                        {/* Show file attachments if message contains file markers */}
                        {msg.content.includes('\uD83D\uDCCE') &&
                          msg.content
                            .split('\n')
                            .filter((line) => line.startsWith('\uD83D\uDCCE'))
                            .map((line, i) => {
                              const match = line.match(/📎\s*(.+?)\s*\((.+?)\)/);
                              return match ? (
                                <MessageAttachment
                                  key={i}
                                  filename={match[1]}
                                  size={undefined}
                                />
                              ) : null;
                            })}
                        <div
                          className={`flex items-center justify-end gap-1 mt-1 ${
                            msg.sender_type === 'lawyer'
                              ? 'text-purple-300'
                              : 'text-muted-foreground'
                          }`}
                        >
                          <span className="text-[10px]">
                            {formatFullDate(msg.created_at)}
                          </span>
                          <MessageStatus msg={msg} />
                        </div>
                      </div>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </CardContent>

                {/* AI Suggestion Preview */}
                {aiSuggestion && (
                  <div className="mx-3 mb-1 rounded-lg border border-purple-200 dark:border-purple-800 bg-purple-50 dark:bg-purple-950/30 p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-purple-700 dark:text-purple-300 flex items-center gap-1">
                        <Sparkles className="h-3 w-3" />
                        Sugestao da IA
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-5 w-5 p-0"
                        onClick={() => setAiSuggestion(null)}
                        aria-label="Fechar sugestão da IA"
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    </div>
                    <p className="text-xs text-purple-600 dark:text-purple-400 line-clamp-2">
                      Texto inserido no campo de resposta. Edite antes de enviar.
                    </p>
                  </div>
                )}

                {/* Attachment Preview Bar */}
                {attachments.length > 0 && (
                  <div className="mx-3 mb-1 flex gap-2 overflow-x-auto py-2">
                    {attachments.map((att, idx) => (
                      <div
                        key={idx}
                        className="relative shrink-0 flex items-center gap-2 rounded-lg border bg-muted/50 px-3 py-2"
                      >
                        {att.preview ? (
                          <img
                            src={att.preview}
                            alt={att.file.name}
                            className="h-8 w-8 rounded object-cover"
                          />
                        ) : (
                          <FileText className="h-5 w-5 text-muted-foreground" />
                        )}
                        <div className="min-w-0">
                          <p className="text-xs font-medium truncate max-w-[120px]">
                            {att.file.name}
                          </p>
                          <p className="text-[10px] text-muted-foreground">
                            {formatFileSize(att.file.size)}
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => removeAttachment(idx)}
                          className="absolute -top-1.5 -right-1.5 rounded-full bg-destructive text-destructive-foreground h-4 w-4 flex items-center justify-center"
                        >
                          <X className="h-2.5 w-2.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {/* Reply input with tools */}
                <div className="shrink-0 border-t p-3">
                  {/* @ Commands Popup */}
                  {showAtMenu && (
                    <div className="mb-2 rounded-lg border bg-popover shadow-lg max-h-52 overflow-y-auto">
                      <div className="p-1.5">
                        <p className="text-[10px] text-muted-foreground px-2 py-1 uppercase tracking-wider font-semibold">
                          Comandos rapidos
                        </p>
                        {filteredAtCommands.length === 0 ? (
                          <p className="text-xs text-muted-foreground px-2 py-2">
                            Nenhum comando encontrado
                          </p>
                        ) : (
                          filteredAtCommands.map((cmd) => (
                            <button
                              key={cmd.key}
                              type="button"
                              onClick={() => handleAtCommandSelect(cmd)}
                              className="w-full flex items-center gap-3 px-2 py-2 rounded-md hover:bg-accent/50 transition-colors text-left"
                            >
                              {cmd.icon}
                              <div>
                                <p className="text-sm font-medium">{cmd.label}</p>
                                <p className="text-[11px] text-muted-foreground">
                                  {cmd.description}
                                </p>
                              </div>
                            </button>
                          ))
                        )}
                      </div>
                    </div>
                  )}

                  {/* Toolbar */}
                  <div className="flex items-center gap-1 mb-2">
                    {/* File Upload */}
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0"
                      onClick={handleFileSelect}
                      title="Anexar arquivo"
                      aria-label="Anexar arquivo"
                    >
                      <Paperclip className="h-4 w-4" />
                    </Button>

                    {/* AI Suggestions */}
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 gap-1 text-xs text-purple-600 dark:text-purple-400"
                          disabled={aiLoading || conversation.length === 0}
                        >
                          {aiLoading ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <Sparkles className="h-3.5 w-3.5" />
                          )}
                          Responder com IA
                          <ChevronDown className="h-3 w-3" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="start" className="w-56">
                        <DropdownMenuLabel className="text-xs flex items-center gap-1.5">
                          <Bot className="h-3.5 w-3.5" />
                          Sugestoes de resposta
                        </DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        {AI_SUGGESTIONS.map((s) => (
                          <DropdownMenuItem
                            key={s.tone}
                            onClick={() => handleAISuggest(s)}
                            className="cursor-pointer"
                          >
                            <span className="text-sm">{s.label}</span>
                          </DropdownMenuItem>
                        ))}
                      </DropdownMenuContent>
                    </DropdownMenu>

                    {/* @ Command hint */}
                    <span className="text-[10px] text-muted-foreground ml-auto hidden sm:inline">
                      Digite <kbd className="px-1 py-0.5 rounded bg-muted text-[10px] font-mono">@</kbd> para comandos rapidos
                    </span>
                  </div>

                  {/* Text input + Send */}
                  <div className="flex items-end gap-2">
                    <AITextarea
                      ref={textareaRef}
                      placeholder="Digite sua resposta... (@ para comandos)"
                      className="min-h-[44px] max-h-32 resize-none text-sm"
                      value={replyContent}
                      onChange={handleTextareaChange}
                      onKeyDown={handleKeyDown}
                      rows={1}
                      aiContext={`Resposta a mensagem de cliente no contexto de mensagens a clientes de procuradoria${selectedThread?.clientName ? ` — cliente: ${selectedThread.clientName}` : ''}${selectedThread?.caseTitulo ? ` — caso: ${selectedThread.caseTitulo}` : ''}`}
                      aiObjective="Redigir uma resposta profissional, clara e juridicamente adequada para o cliente"
                      setValue={setReplyContent}
                    />
                    <Button
                      size="icon"
                      className="h-10 w-10 shrink-0"
                      disabled={
                        (!replyContent.trim() && attachments.length === 0) ||
                        replyMutation.isPending
                      }
                      onClick={handleSendReply}
                      aria-label="Enviar mensagem"
                    >
                      {replyMutation.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Send className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              </>
            )}
          </Card>

          {/* Right panel: Client Context Sidebar */}
          {selectedClientId && selectedThread && showSidebar && (
            <Card className="hidden xl:flex w-72 min-w-[288px] shrink-0 flex-col overflow-hidden">
              <ClientContextSidebar
                thread={selectedThread}
                messages={conversation}
              />
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

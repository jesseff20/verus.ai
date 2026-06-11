'use client';

import * as React from 'react';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import {
  MessageSquare,
  Plus,
  Trash2,
  RotateCcw,
  Clock,
  ChevronRight,
  Search,
  X,
  Share2,
  Download,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { useCopilotSessions } from '@/hooks/use-copilot-sessions';
import { ShareSessionDialog } from './ShareSessionDialog';
import api from '@/lib/api';

interface CopilotSessionHistoryProps {
  /** Callback quando sessão é selecionada */
  onSessionSelect?: (sessionId: string) => void;
  /** Callback quando nova sessão é criada */
  onNewSession?: () => void;
}

/**
 * Histórico de Sessões do Copilot
 *
 * Permite:
 * - Visualizar conversas anteriores
 * - Retomar sessões antigas
 * - Criar nova sessão
 * - Excluir sessões
 */
export function CopilotSessionHistory({
  onSessionSelect,
  onNewSession,
}: CopilotSessionHistoryProps) {
  const { sessions, loading, createSession, loadSession, deleteSession, currentSessionId, searchQuery, setSearchQuery } =
    useCopilotSessions();
  const [open, setOpen] = React.useState(false);

  const handleNewSession = () => {
    createSession();
    onNewSession?.();
    setOpen(false);
  };

  const handleSelectSession = (sessionId: string) => {
    loadSession(sessionId);
    onSessionSelect?.(sessionId);
    setOpen(false);
  };

  const handleDeleteSession = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    deleteSession(sessionId);
  };

  const handleExportSession = async (e: React.MouseEvent, sessionId: string, format: 'docx' | 'pdf' | 'odt') => {
    e.stopPropagation();
    try {
      const response = await api.post('/api/v1/copilot/export-session/', {
        session_id: sessionId,
        format: format,
      }, { responseType: 'blob' });

      const url = window.URL.createObjectURL(response.data);
      const link = document.createElement('a');
      link.href = url;
      link.download = `copilot_conversa_${sessionId.slice(0, 8)}.${format}`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Erro ao exportar:', error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          <Clock className="h-4 w-4" />
          Histórico
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Histórico de Conversas
          </DialogTitle>
          <DialogDescription>
            Retome conversas anteriores ou inicie uma nova sessão
          </DialogDescription>
        </DialogHeader>

        <div className="flex items-center justify-between mt-4 gap-2">
          <Button onClick={handleNewSession} className="gap-2">
            <Plus className="h-4 w-4" />
            Nova Sessão
          </Button>
          <Badge variant="secondary">
            {sessions.length} sessão{sessions.length !== 1 ? 'ões' : ''}
          </Badge>
        </div>

        {/* Busca */}
        <div className="relative mt-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar nas conversas..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
          {searchQuery && (
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7"
              onClick={() => setSearchQuery('')}
            >
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>

        <ScrollArea className="h-[400px] mt-4">
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">
              Carregando histórico...
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <MessageSquare className="h-12 w-12 mx-auto mb-3 opacity-20" />
              <p>Nenhuma conversa anterior</p>
              <p className="text-sm">Inicie uma nova sessão para começar</p>
            </div>
          ) : (
            <div className="space-y-2">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className={cn(
                    'flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-colors',
                    session.id === currentSessionId
                      ? 'border-primary bg-primary/5'
                      : 'hover:bg-muted'
                  )}
                  onClick={() => handleSelectSession(session.id)}
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <div
                      className={cn(
                        'flex h-10 w-10 items-center justify-center rounded-full',
                        session.id === currentSessionId
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted'
                      )}
                    >
                      <MessageSquare className="h-5 w-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium truncate">
                          {session.preview || 'Nova conversa'}
                        </span>
                        {session.id === currentSessionId && (
                          <Badge variant="default" className="text-xs">
                            Atual
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-3 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {formatDistanceToNow(new Date(session.last_message_at || session.created_at), {
                            addSuffix: true,
                            locale: ptBR,
                          })}
                        </span>
                        <span>{session.message_count} mensagens</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    {/* Exportar */}
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-primary"
                          onClick={(e) => e.stopPropagation()}
                          title="Exportar"
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleExportSession(e, session.id, 'docx'); }}>
                          Word (.docx)
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleExportSession(e, session.id, 'pdf'); }}>
                          PDF (.pdf)
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleExportSession(e, session.id, 'odt'); }}>
                          OpenDoc (.odt)
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>

                    {/* Compartilhar */}
                    <ShareSessionDialog
                      sessionId={session.id}
                      trigger={
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-primary"
                          onClick={(e) => e.stopPropagation()}
                          title="Compartilhar"
                        >
                          <Share2 className="h-4 w-4" />
                        </Button>
                      }
                    />
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-muted-foreground hover:text-destructive"
                      onClick={(e) => handleDeleteSession(e, session.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}

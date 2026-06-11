'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import {
  Users,
  UserPlus,
  UserMinus,
  MessageSquare,
  Lightbulb,
  Send,
  CheckCircle,
  XCircle,
  Clock,
  Edit,
  Eye,
  MessageSquarePlus,
  ThumbsUp,
  ThumbsDown,
  X,
  Activity,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  useCollaboration,
  type Collaborator,
  type Comment,
  type Suggestion,
} from '@/hooks/use-collaboration';

interface CollaborationPanelProps {
  /** ID da sessão de colaboração */
  sessionId: string;
  /** Callback quando comentário é adicionado */
  onCommentAdd?: () => void;
  /** Callback quando sugestão é criada */
  onSuggestionCreate?: () => void;
}

/**
 * Painel de Colaboração em Tempo Real
 *
 * Mostra:
 * - Colaboradores ativos
 * - Comentários
 * - Sugestões
 * - Status de conexão
 */
export function CollaborationPanel({
  sessionId,
  onCommentAdd,
  onSuggestionCreate,
}: CollaborationPanelProps) {
  const {
    session,
    collaborators,
    comments,
    suggestions,
    isConnected,
    isLoading,
    joinSession,
    leaveSession,
    createComment,
    resolveComment,
    createSuggestion,
    reviewSuggestion,
  } = useCollaboration(sessionId);

  const [activeTab, setActiveTab] = React.useState<'collaborators' | 'comments' | 'suggestions'>('collaborators');
  const [newComment, setNewComment] = React.useState('');
  const [showSuggestionForm, setShowSuggestionForm] = React.useState(false);
  const [suggestionText, setSuggestionText] = React.useState('');

  // Entrar na sessão ao montar
  React.useEffect(() => {
    if (sessionId && !isConnected) {
      joinSession(sessionId);
    }
  }, [sessionId]);

  // Lidar com envio de comentário
  const handleSendComment = () => {
    if (!newComment.trim()) return;
    createComment({ content: newComment });
    setNewComment('');
    onCommentAdd?.();
  };

  // Lidar com criação de sugestão
  const handleCreateSuggestion = () => {
    if (!suggestionText.trim()) return;
    createSuggestion({
      original_text: '',
      suggested_text: suggestionText,
      comment: 'Sugestão de melhoria',
    });
    setSuggestionText('');
    setShowSuggestionForm(false);
    onSuggestionCreate?.();
  };

  return (
    <div className="flex flex-col h-full space-y-4">
      {/* Header com Status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4" />
          <span className="font-medium">Colaboração</span>
        </div>
        <Badge variant={isConnected ? 'default' : 'secondary'} className="gap-1">
          {isConnected ? (
            <>
              <Wifi className="h-3 w-3" />
              Conectado
            </>
          ) : (
            <>
              <WifiOff className="h-3 w-3" />
              Desconectado
            </>
          )}
        </Badge>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setActiveTab('collaborators')}
          className={cn(
            'rounded-none border-b-2 border-transparent',
            activeTab === 'collaborators' && 'border-primary bg-muted'
          )}
        >
          <Users className="h-4 w-4 mr-1" />
          Colaboradores
          {collaborators.length > 0 && (
            <Badge variant="secondary" className="ml-1 text-xs">
              {collaborators.length}
            </Badge>
          )}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setActiveTab('comments')}
          className={cn(
            'rounded-none border-b-2 border-transparent',
            activeTab === 'comments' && 'border-primary bg-muted'
          )}
        >
          <MessageSquare className="h-4 w-4 mr-1" />
          Comentários
          {comments.filter((c) => !c.is_resolved).length > 0 && (
            <Badge variant="secondary" className="ml-1 text-xs">
              {comments.filter((c) => !c.is_resolved).length}
            </Badge>
          )}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setActiveTab('suggestions')}
          className={cn(
            'rounded-none border-b-2 border-transparent',
            activeTab === 'suggestions' && 'border-primary bg-muted'
          )}
        >
          <Lightbulb className="h-4 w-4 mr-1" />
          Sugestões
          {suggestions.filter((s) => s.status === 'pending').length > 0 && (
            <Badge variant="secondary" className="ml-1 text-xs">
              {suggestions.filter((s) => s.status === 'pending').length}
            </Badge>
          )}
        </Button>
      </div>

      {/* Conteúdo */}
      <ScrollArea className="flex-1">
        {activeTab === 'collaborators' && (
          <CollaboratorsList collaborators={collaborators} />
        )}
        {activeTab === 'comments' && (
          <CommentsList
            comments={comments}
            onResolve={resolveComment}
            onSend={handleSendComment}
            newComment={newComment}
            setNewComment={setNewComment}
          />
        )}
        {activeTab === 'suggestions' && (
          <SuggestionsList
            suggestions={suggestions}
            onReview={reviewSuggestion}
            onCreate={() => setShowSuggestionForm(true)}
            showForm={showSuggestionForm}
            suggestionText={suggestionText}
            setSuggestionText={setSuggestionText}
            handleCreate={handleCreateSuggestion}
          />
        )}
      </ScrollArea>
    </div>
  );
}

interface CollaboratorsListProps {
  collaborators: Collaborator[];
}

function CollaboratorsList({ collaborators }: CollaboratorsListProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'editing':
        return <Edit className="h-3 w-3 text-blue-600" />;
      case 'viewing':
        return <Eye className="h-3 w-3 text-gray-600" />;
      case 'commenting':
        return <MessageSquare className="h-3 w-3 text-green-600" />;
      default:
        return <Clock className="h-3 w-3 text-yellow-600" />;
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'editing':
        return 'Editando';
      case 'viewing':
        return 'Visualizando';
      case 'commenting':
        return 'Comentando';
      default:
        return 'Ausente';
    }
  };

  if (collaborators.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Users className="h-8 w-8 mx-auto mb-2 opacity-30" />
        <p>Nenhum colaborador ativo</p>
      </div>
    );
  }

  return (
    <div className="space-y-3 p-2">
      {collaborators.map((collab) => (
        <div
          key={collab.id}
          className="flex items-center justify-between p-2 rounded-lg border"
        >
          <div className="flex items-center gap-3">
            <Avatar className="h-8 w-8">
              <AvatarImage src={collab.user_avatar} />
              <AvatarFallback>
                {collab.user_name?.charAt(0) || 'U'}
              </AvatarFallback>
            </Avatar>
            <div>
              <p className="text-sm font-medium">{collab.user_name}</p>
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                {getStatusIcon(collab.status)}
                {getStatusLabel(collab.status)}
              </p>
            </div>
          </div>
          {collab.is_active && (
            <Badge variant="default" className="text-xs bg-green-600">
              Ativo
            </Badge>
          )}
        </div>
      ))}
    </div>
  );
}

interface CommentsListProps {
  comments: Comment[];
  onResolve: (commentId: string) => void;
  onSend: () => void;
  newComment: string;
  setNewComment: (value: string) => void;
}

function CommentsList({
  comments,
  onResolve,
  onSend,
  newComment,
  setNewComment,
}: CommentsListProps) {
  const pendingComments = comments.filter((c) => !c.is_resolved);
  const resolvedComments = comments.filter((c) => c.is_resolved);

  return (
    <div className="space-y-4 p-2">
      {/* Lista de comentários */}
      {pendingComments.length === 0 && resolvedComments.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-30" />
          <p>Nenhum comentário ainda</p>
          <p className="text-xs mt-1">
            Seja o primeiro a comentar
          </p>
        </div>
      ) : (
        <>
          {/* Pendentes */}
          {pendingComments.length > 0 && (
            <div className="space-y-3">
              {pendingComments.map((comment) => (
                <CommentItem
                  key={comment.id}
                  comment={comment}
                  onResolve={() => onResolve(comment.id)}
                />
              ))}
            </div>
          )}

          {/* Resolvidos */}
          {resolvedComments.length > 0 && (
            <div className="space-y-3 opacity-60">
              <div className="text-xs text-muted-foreground font-medium">
                Resolvidos ({resolvedComments.length})
              </div>
              {resolvedComments.map((comment) => (
                <CommentItem
                  key={comment.id}
                  comment={comment}
                  onResolve={() => onResolve(comment.id)}
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* Input de comentário */}
      <div className="flex gap-2 pt-2 border-t">
        <div className="relative flex-1">
          <Textarea
            placeholder="Adicionar comentário..."
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            className="min-h-[60px] pr-32"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              onSend();
            }
          }}
          />
          <div className="absolute top-1 right-1">
            <AIEnhanceButton
              value={newComment}
              onEnhance={setNewComment}
              context="comentário de revisão de documento jurídico"
            />
          </div>
        </div>
        <Button
          onClick={onSend}
          disabled={!newComment.trim()}
          className="self-end"
          size="icon"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

interface CommentItemProps {
  comment: Comment;
  onResolve: () => void;
}

function CommentItem({ comment, onResolve }: CommentItemProps) {
  return (
    <div
      className={cn(
        'p-3 rounded-lg border',
        comment.is_resolved && 'bg-muted'
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <Avatar className="h-6 w-6">
            <AvatarFallback className="text-xs">
              {comment.author_name?.charAt(0) || 'A'}
            </AvatarFallback>
          </Avatar>
          <div>
            <p className="text-xs font-medium">{comment.author_name}</p>
            <p className="text-xs text-muted-foreground">
              {new Date(comment.created_at).toLocaleDateString('pt-BR')}
            </p>
          </div>
        </div>
        {!comment.is_resolved && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onResolve}
            className="h-6 text-xs"
          >
            <CheckCircle className="h-3 w-3 mr-1" />
            Resolver
          </Button>
        )}
      </div>
      {comment.quoted_text && (
        <blockquote className="text-xs text-muted-foreground italic mt-2 pl-2 border-l-2 border-muted">
          {comment.quoted_text}
        </blockquote>
      )}
      <p className="text-sm mt-2">{comment.content}</p>
    </div>
  );
}

interface SuggestionsListProps {
  suggestions: Suggestion[];
  onReview: (params: { suggestionId: string; status: string; comment?: string }) => void;
  onCreate: () => void;
  showForm: boolean;
  suggestionText: string;
  setSuggestionText: (value: string) => void;
  handleCreate: () => void;
}

function SuggestionsList({
  suggestions,
  onReview,
  onCreate,
  showForm,
  suggestionText,
  setSuggestionText,
  handleCreate,
}: SuggestionsListProps) {
  const pendingSuggestions = suggestions.filter((s) => s.status === 'pending');

  return (
    <div className="space-y-4 p-2">
      {/* Botão nova sugestão */}
      {!showForm && (
        <Button
          variant="outline"
          onClick={onCreate}
          className="w-full gap-2"
        >
          <MessageSquarePlus className="h-4 w-4" />
          Nova Sugestão
        </Button>
      )}

      {/* Formulário */}
      {showForm && (
        <Card>
          <CardContent className="pt-4 space-y-3">
            <div className="relative">
              <Textarea
                placeholder="Digite sua sugestão..."
                value={suggestionText}
                onChange={(e) => setSuggestionText(e.target.value)}
                className="min-h-[100px] pr-32"
              />
              <div className="absolute top-1 right-1">
                <AIEnhanceButton
                  value={suggestionText}
                  onEnhance={setSuggestionText}
                  context="sugestão de melhoria em documento jurídico"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Button onClick={handleCreate} disabled={!suggestionText.trim()}>
                <Send className="h-4 w-4" />
                Enviar
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setShowForm(false);
                  setSuggestionText('');
                }}
              >
                <X className="h-4 w-4" />
                Cancelar
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Lista de sugestões */}
      {suggestions.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          <Lightbulb className="h-8 w-8 mx-auto mb-2 opacity-30" />
          <p>Nenhuma sugestão</p>
        </div>
      ) : (
        <div className="space-y-3">
          {suggestions.map((suggestion) => (
            <SuggestionItem
              key={suggestion.id}
              suggestion={suggestion}
              onReview={onReview}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface SuggestionItemProps {
  suggestion: Suggestion;
  onReview: (params: { suggestionId: string; status: string }) => void;
}

function SuggestionItem({ suggestion, onReview }: SuggestionItemProps) {
  const isPending = suggestion.status === 'pending';

  return (
    <div
      className={cn(
        'p-3 rounded-lg border',
        suggestion.status === 'accepted' && 'border-green-300 bg-green-50',
        suggestion.status === 'rejected' && 'border-red-300 bg-red-50'
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-xs font-medium">{suggestion.author_name}</p>
          <p className="text-xs text-muted-foreground">
            {new Date(suggestion.created_at).toLocaleDateString('pt-BR')}
          </p>
        </div>
        <Badge
          className={cn(
            'text-xs',
            suggestion.status === 'accepted' && 'bg-green-100 text-green-700',
            suggestion.status === 'rejected' && 'bg-red-100 text-red-700',
            suggestion.status === 'pending' && 'bg-yellow-100 text-yellow-700'
          )}
        >
          {suggestion.status_display}
        </Badge>
      </div>

      {suggestion.suggested_text && (
        <div className="mt-2 space-y-1">
          {suggestion.original_text && (
            <p className="text-xs text-red-600 line-through bg-red-50 p-1 rounded">
              {suggestion.original_text}
            </p>
          )}
          <p className="text-xs text-green-600 bg-green-50 p-1 rounded">
            {suggestion.suggested_text}
          </p>
        </div>
      )}

      {suggestion.comment && (
        <p className="text-xs text-muted-foreground mt-2 italic">
          {suggestion.comment}
        </p>
      )}

      {/* Ações para review */}
      {isPending && (
        <div className="flex gap-2 mt-3 pt-3 border-t">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onReview({ suggestionId: suggestion.id, status: 'accepted' })}
            className="gap-1 text-xs"
          >
            <ThumbsUp className="h-3 w-3" />
            Aceitar
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onReview({ suggestionId: suggestion.id, status: 'rejected' })}
            className="gap-1 text-xs"
          >
            <ThumbsDown className="h-3 w-3" />
            Rejeitar
          </Button>
        </div>
      )}
    </div>
  );
}

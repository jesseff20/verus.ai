'use client';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Plus,
  FileText,
  ChevronRight,
  MessageSquare,
  History,
  Trash2,
  Loader2,
  Search,
  ArrowLeft,
  Files,
} from 'lucide-react';
import type { IntelligentSession } from '@/hooks/use-intelligent-assistant';

interface SessionSidebarProps {
  sessions: IntelligentSession[];
  selectedSessionId: string | null;
  sessionDetail: IntelligentSession | null;
  isLoadingSessions: boolean;
  documentTypes: { code: string; name: string; description?: string }[];
  isLoadingDocumentTypes: boolean;
  documentTypeLabels: Record<string, string>;
  allBlueprints: { id: string; name: string; document_type_code: string; section_count: number; is_default?: boolean }[];
  blueprints: { id: string; name: string; document_type_code: string; section_count: number; is_default?: boolean }[];
  wizardStep: number;
  selectedDocumentType: string;
  selectedBlueprintId: string;
  newObjective: string;
  isCreatingSession: boolean;
  statusLabels: Record<string, { label: string; variant: string }>;
  lucideIcons: Record<string, React.ComponentType<any>>;
  documentDependencies: Record<string, { code: string; label: string }[]>;
  parentSessionId: string | null;
  onParentSessionSelect: (id: string | null) => void;
  onSelectSession: (id: string) => void;
  onDeselectSession: () => void;
  onSetWizardStep: (step: number) => void;
  onSelectDocumentType: (code: string) => void;
  onSelectBlueprint: (id: string) => void;
  onObjectiveChange: (value: string) => void;
  onCreateSession: () => Promise<void>;
  onDeleteSession: (id: string) => void;
  formatDate: (date: string) => string;
  className?: string;
}

export function SessionSidebar({
  sessions,
  selectedSessionId,
  sessionDetail,
  isLoadingSessions,
  documentTypes,
  isLoadingDocumentTypes,
  documentTypeLabels,
  allBlueprints,
  blueprints,
  wizardStep,
  selectedDocumentType,
  selectedBlueprintId,
  newObjective,
  isCreatingSession,
  statusLabels,
  lucideIcons,
  documentDependencies,
  parentSessionId,
  onParentSessionSelect,
  onSelectSession,
  onDeselectSession,
  onSetWizardStep,
  onSelectDocumentType,
  onSelectBlueprint,
  onObjectiveChange,
  onCreateSession,
  onDeleteSession,
  formatDate,
  className,
}: SessionSidebarProps) {
  const hasSession = !!selectedSessionId;

  return (
    <div className={cn('bg-card border rounded-lg', className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <h2 className="text-sm font-semibold flex items-center gap-2">
          <MessageSquare className="h-4 w-4" />
          {hasSession ? 'Sessão Ativa' : 'Nova Sessão'}
        </h2>
        {hasSession && (
          <Button variant="ghost" size="sm" className="h-7 text-xs gap-1" onClick={onDeselectSession}>
            <ArrowLeft className="h-3 w-3" />
            Voltar
          </Button>
        )}
      </div>

      <div className="p-4 space-y-4">
        {hasSession ? (
          // ─── Session Active View ──────────────────────────
          <div className="space-y-3">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Badge variant={statusLabels[sessionDetail?.status || 'initialized']?.variant as any || 'outline'}>
                  {statusLabels[sessionDetail?.status || 'initialized']?.label || 'Iniciada'}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {sessionDetail?.created_at ? formatDate(sessionDetail.created_at) : ''}
                </span>
              </div>
              <p className="text-sm font-medium line-clamp-2">{sessionDetail?.objective}</p>
            </div>

            <div className="space-y-1">
              <h3 className="text-xs text-muted-foreground uppercase tracking-wider">Documentos</h3>
              <div className="flex items-center gap-2 text-sm">
                <Files className="h-4 w-4 text-muted-foreground" />
                <span>{sessionDetail?.uploaded_documents?.length || 0} enviados</span>
              </div>
              {sessionDetail?.generated_documents && sessionDetail.generated_documents.length > 0 && (
                <div className="flex items-center gap-2 text-sm">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <span>{sessionDetail.generated_documents.length} gerados</span>
                </div>
              )}
            </div>

            <div className="pt-2 border-t">
              <Button
                variant="destructive"
                size="sm"
                className="w-full h-8 text-xs gap-1"
                onClick={() => onDeleteSession(selectedSessionId!)}
              >
                <Trash2 className="h-3 w-3" />
                Excluir Sessão
              </Button>
            </div>

            {/* Sessions list (compact) */}
            <div className="pt-2 border-t">
              <h3 className="text-xs text-muted-foreground uppercase tracking-wider mb-2">
                Histórico de Sessões
              </h3>
              <ScrollArea className="h-[200px]">
                <div className="space-y-1">
                  {sessions
                    .filter((s) => s.id !== selectedSessionId)
                    .slice(0, 20)
                    .map((session) => (
                      <button
                        key={session.id}
                        onClick={() => onSelectSession(session.id)}
                        className="w-full text-left p-2 rounded-md text-xs hover:bg-muted transition-colors"
                      >
                        <div className="font-medium truncate">{session.objective}</div>
                        <div className="text-muted-foreground">{formatDate(session.created_at)}</div>
                      </button>
                    ))}
                </div>
              </ScrollArea>
            </div>
          </div>
        ) : (
          // ─── Session Creation Wizard ──────────────────────
          <div className="space-y-4">
            {wizardStep >= 0 && (
              <div>
                <h3 className="text-xs text-muted-foreground uppercase tracking-wider mb-2">
                  Tipo de Documento
                </h3>
                {isLoadingDocumentTypes ? (
                  <div className="flex items-center justify-center py-4">
                    <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-1">
                    {documentTypes.map((dt) => {
                      const IconComponent = lucideIcons[dt.code] || FileText;
                      const deps = documentDependencies[dt.code];
                      const isDisabled = deps && deps.length > 0 && !parentSessionId;

                      return (
                        <button
                          key={dt.code}
                          onClick={() => !isDisabled && onSelectDocumentType(dt.code)}
                          disabled={isDisabled}
                          className={cn(
                            'flex items-center gap-3 p-3 rounded-lg border text-left transition-colors',
                            selectedDocumentType === dt.code
                              ? 'border-primary bg-primary/5'
                              : 'hover:border-muted-foreground/30',
                            isDisabled && 'opacity-50 cursor-not-allowed'
                          )}
                        >
                          <IconComponent className="h-5 w-5 text-primary shrink-0" />
                          <div className="min-w-0">
                            <div className="text-sm font-medium truncate">{dt.name}</div>
                            {isDisabled && (
                              <div className="text-xs text-muted-foreground mt-0.5">
                                Requer sessão de {deps?.map((d) => d.label).join(', ')}
                              </div>
                            )}
                          </div>
                          <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0 ml-auto" />
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            {wizardStep >= 1 && (
              <div>
                <h3 className="text-xs text-muted-foreground uppercase tracking-wider mb-2">
                  Modelo (Blueprint)
                </h3>
                <div className="grid grid-cols-1 gap-1">
                  {blueprints.length === 0 ? (
                    <div className="text-sm text-muted-foreground text-center py-4">
                      Nenhum blueprint disponível para este tipo de documento
                    </div>
                  ) : (
                    blueprints.map((bp) => (
                      <button
                        key={bp.id}
                        onClick={() => onSelectBlueprint(bp.id)}
                        className={cn(
                          'flex items-center gap-3 p-3 rounded-lg border text-left transition-colors',
                          selectedBlueprintId === bp.id
                            ? 'border-primary bg-primary/5'
                            : 'hover:border-muted-foreground/30'
                        )}
                      >
                        <FileText className="h-5 w-5 text-primary shrink-0" />
                        <div className="min-w-0">
                          <div className="text-sm font-medium truncate">{bp.name}</div>
                          <div className="text-xs text-muted-foreground">
                            {bp.section_count} seções
                            {bp.is_default && ' • Padrão'}
                          </div>
                        </div>
                        <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0 ml-auto" />
                      </button>
                    ))
                  )}
                </div>
              </div>
            )}

            {wizardStep >= 2 && (
              <div>
                <h3 className="text-xs text-muted-foreground uppercase tracking-wider mb-2">
                  Objetivo
                </h3>
                <div className="space-y-2">
                  <textarea
                    value={newObjective}
                    onChange={(e) => onObjectiveChange(e.target.value)}
                    placeholder="Descreva o objetivo do documento..."
                    className="w-full min-h-[80px] rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                  <Button
                    className="w-full gap-1"
                    size="sm"
                    onClick={onCreateSession}
                    disabled={isCreatingSession || !newObjective.trim()}
                  >
                    {isCreatingSession ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Plus className="h-4 w-4" />
                    )}
                    Criar Sessão
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

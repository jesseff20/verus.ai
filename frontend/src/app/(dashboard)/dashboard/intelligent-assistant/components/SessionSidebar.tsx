import React, { memo, useMemo, useState } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Plus,
  Loader2,
  Clock,
  FileText,
  Trash2,
  ArrowLeft,
  Bot,
  Sparkles,
  Layers,
} from 'lucide-react';
import type { DocumentBlueprint } from '@/types';
import type { DocumentType } from '@/hooks/use-document-types';
import { DocumentImportSelector } from './DocumentImportSelector';

interface SessionSidebarProps {
  sessions: any[];
  selectedSessionId: string | null;
  sessionDetail: any;
  isLoadingSessions: boolean;
  documentTypes: DocumentType[];
  isLoadingDocumentTypes: boolean;
  documentTypeLabels: Record<string, string>;
  allBlueprints: DocumentBlueprint[];
  blueprints: DocumentBlueprint[];
  wizardStep: number;
  selectedDocumentType: string;
  selectedBlueprintId: string;
  newObjective: string;
  isCreatingSession: boolean;
  statusLabels: Record<string, { label: string; variant: string }>;
  lucideIcons: Record<string, any>;
  documentDependencies: Record<string, { code: string; label: string }[]>;
  parentSessionId: string | null;
  onParentSessionSelect: (id: string | null) => void;
  onSelectSession: (id: string) => void;
  onDeselectSession: () => void;
  onSetWizardStep: (step: number) => void;
  onSelectDocumentType: (code: string) => void;
  onSelectBlueprint: (id: string) => void;
  onObjectiveChange: (value: string) => void;
  onCreateSession: () => void;
  onDeleteSession: (id: string) => void;
  formatDate: (date: string) => string;
}

function SessionSidebarComponent({
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
}: SessionSidebarProps) {
  const hasDependencies = !!(documentDependencies[selectedDocumentType]?.length > 0);

  // ── Área jurídica (step 0 interno) ──
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  // Deriva categorias únicas combinando AMBAS as fontes:
  // documentTypes → category (base) + blueprint.areas M2M (enriquecimento)
  const categories = useMemo(() => {
    const seen = new Map<string, string>();

    // Sempre adicionar categorias de documentTypes como base
    documentTypes.forEach((t) => {
      if (t.category && t.category_display && !seen.has(t.category)) {
        seen.set(t.category, t.category_display);
      }
    });

    // Enriquecer com blueprint.areas (pode adicionar categorias extras não em documentTypes)
    allBlueprints.forEach((bp) => {
      if (bp.areas && bp.areas.length > 0) {
        bp.areas.forEach((a) => {
          if (a.code && a.name && !seen.has(a.code)) {
            seen.set(a.code, a.name);
          }
        });
      }
    });

    return Array.from(seen.entries())
      .map(([code, label]) => ({ code, label }))
      .sort((a, b) => a.label.localeCompare(b.label, 'pt-BR'));
  }, [allBlueprints, documentTypes]);

  // Blueprints para a categoria selecionada — combina AMBAS as fontes por blueprint
  const blueprintsInCategory = useMemo(() => {
    if (!selectedCategory) return allBlueprints;

    const dtCodesInCat = new Set(
      documentTypes.filter((t) => t.category === selectedCategory).map((t) => t.code)
    );

    return allBlueprints.filter((bp) => {
      // Incluir se: (a) bp.areas contém a categoria, OU (b) document_type está na categoria
      const inAreas = bp.areas?.some((a) => a.code === selectedCategory) ?? false;
      const inDocType = dtCodesInCat.has(bp.document_type_code);
      return inAreas || inDocType;
    });
  }, [allBlueprints, documentTypes, selectedCategory]);

  // Tipos filtrados pela categoria (mantido para compatibilidade)
  const filteredDocumentTypes = useMemo(() => {
    if (!selectedCategory) return documentTypes;
    return documentTypes.filter((t) => t.category === selectedCategory);
  }, [documentTypes, selectedCategory]);

  // Compact mode: when a session is active, show only session info
  if (selectedSessionId && sessionDetail) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex flex-wrap gap-1.5">
              <Badge variant="outline" className="text-xs">
                {documentTypeLabels[sessionDetail.document_type] || sessionDetail.document_type}
              </Badge>
              {sessionDetail.blueprint_name && (
                <Badge variant="secondary" className="text-xs">
                  {sessionDetail.blueprint_name}
                </Badge>
              )}
            </div>
            <span className="text-sm text-slate-600 line-clamp-1 max-w-md">
              {sessionDetail.objective}
            </span>
          </div>
          <Button variant="ghost" size="sm" onClick={onDeselectSession} className="text-xs shrink-0">
            <Plus className="h-3 w-3 mr-1" />
            Nova Sessão
          </Button>
        </div>
      </div>
    );
  }

  // Full layout: wizard + session list side by side
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/10 mb-4">
          <Sparkles className="h-8 w-8 text-primary" />
        </div>
        <h2 className="text-2xl font-bold text-slate-800">Assistente Jurídico</h2>
        <p className="text-slate-500 mt-1">
          Crie uma sessão para começar a gerar peças jurídicas com IA.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Left: Creation wizard */}
        <div className="lg:col-span-3">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-slate-800">Nova Sessão</h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {wizardStep === 0
                      ? 'Selecione a área jurídica'
                      : wizardStep === 1
                        ? 'Escolha a peça jurídica'
                        : wizardStep === 2
                          ? 'Defina o objetivo da peça jurídica'
                          : 'Vincular documento anterior (opcional)'}
                  </p>
                </div>
                {wizardStep > 0 && (
                  <Button variant="ghost" size="sm" onClick={() => { onSetWizardStep(0); setSelectedCategory(null); }} className="text-xs">
                    Recomeçar
                  </Button>
                )}
              </div>

              {/* Progress */}
              <div className="flex items-center gap-1 mt-3">
                {(hasDependencies ? ['Área', 'Peça', 'Objetivo', 'Vínculo'] : ['Área', 'Peça', 'Objetivo']).map((label, step) => (
                  <div key={label} className="flex-1 flex flex-col items-center gap-1">
                    <div
                      className={cn(
                        'h-1.5 w-full rounded-full transition-colors',
                        step <= wizardStep ? 'bg-primary' : 'bg-slate-200'
                      )}
                    />
                    <span
                      className={cn(
                        'text-[10px] font-medium',
                        step <= wizardStep ? 'text-primary' : 'text-slate-400'
                      )}
                    >
                      {label}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-6">
              {/* Step 0: Área Jurídica */}
              {wizardStep === 0 && (
                <div className="space-y-3">
                  {isLoadingDocumentTypes ? (
                    <div className="flex justify-center py-12">
                      <Loader2 className="h-6 w-6 animate-spin text-primary" />
                    </div>
                  ) : categories.length === 0 ? (
                    <div className="text-center py-8 space-y-2">
                      <Layers className="h-8 w-8 text-slate-300 mx-auto" />
                      <p className="text-sm font-medium text-slate-500">Nenhuma área disponível</p>
                      <p className="text-xs text-slate-400">
                        Os blueprints ainda não foram classificados com áreas jurídicas.<br />
                        Aguarde o carregamento ou contate o administrador.
                      </p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 gap-3">
                      {categories.map((cat) => {
                        // Contar blueprints nesta categoria (via areas M2M ou fallback)
                        const bpCount = allBlueprints.filter(
                          (b) => b.areas?.some((a) => a.code === cat.code) ||
                            documentTypes.filter((t) => t.category === cat.code).map((t) => t.code).includes(b.document_type_code)
                        ).length;
                        const hasBlueprints = bpCount > 0;
                        return (
                          <button
                            key={cat.code}
                            type="button"
                            onClick={() => {
                              if (!hasBlueprints) return;
                              setSelectedCategory(cat.code);
                              onSetWizardStep(1);
                            }}
                            disabled={!hasBlueprints}
                            className={cn(
                              'p-4 rounded-2xl border text-left transition-all flex items-center gap-4',
                              hasBlueprints
                                ? 'cursor-pointer hover:shadow-sm hover:border-primary hover:bg-primary/5'
                                : 'opacity-40 cursor-not-allowed'
                            )}
                          >
                            <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                              <Layers className="h-5 w-5 text-primary" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="font-semibold text-sm text-slate-800">{cat.label}</p>
                              <p className="text-xs text-slate-400 mt-0.5">
                                {hasBlueprints
                                  ? `${bpCount} peça${bpCount !== 1 ? 's' : ''} disponível${bpCount !== 1 ? 'is' : ''}`
                                  : 'Sem peças cadastradas'}
                              </p>
                            </div>
                            {hasBlueprints && (
                              <span className="text-slate-300 text-sm">→</span>
                            )}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {/* Step 1: Selecionar Blueprint (dentro da área) */}
              {wizardStep === 1 && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 mb-2">
                    <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => { onSetWizardStep(0); }}>
                      <ArrowLeft className="h-4 w-4" />
                    </Button>
                    <Badge variant="outline" className="text-xs">
                      {categories.find((c) => c.code === selectedCategory)?.label || 'Área selecionada'}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {blueprintsInCategory.map((blueprint) => (
                      <button
                        key={blueprint.id}
                        type="button"
                        onClick={() => onSelectBlueprint(blueprint.id)}
                        className={cn(
                          'w-full p-4 rounded-2xl border text-left transition-all hover:border-primary hover:bg-primary/5 hover:shadow-sm',
                          selectedBlueprintId === blueprint.id ? 'border-primary bg-primary/5' : ''
                        )}
                      >
                        <p className="font-semibold text-sm text-slate-800">{blueprint.name}</p>
                        <p className="text-xs text-primary/70 mt-0.5">{blueprint.document_type_display}</p>
                        <p className="text-xs text-slate-400 mt-1">{blueprint.section_count} seções</p>
                      </button>
                    ))}
                    {blueprintsInCategory.length === 0 && (
                      <p className="text-center py-8 text-sm text-slate-400 col-span-2">
                        Nenhuma peça disponível nesta área.
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Step 2: Objective */}
              {wizardStep === 2 && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => onSetWizardStep(1)}>
                      <ArrowLeft className="h-4 w-4" />
                    </Button>
                    <div className="flex flex-wrap gap-1.5">
                      <Badge variant="outline" className="text-xs">
                        {categories.find((c) => c.code === selectedCategory)?.label || documentTypeLabels[selectedDocumentType]}
                      </Badge>
                      <Badge variant="secondary" className="text-xs">
                        {allBlueprints.find((b) => b.id === selectedBlueprintId)?.name}
                      </Badge>
                    </div>
                  </div>

                  <div className="relative">
                    <Textarea
                      placeholder="Descreva o objetivo da peça jurídica..."
                      value={newObjective}
                      onChange={(e) => onObjectiveChange(e.target.value)}
                      rows={4}
                      spellCheck
                      lang="pt-BR"
                      className="resize-y rounded-xl pr-32"
                    />
                    <div className="absolute top-1 right-1">
                      <AIEnhanceButton
                        value={newObjective}
                        onEnhance={onObjectiveChange}
                        context="objetivo de peça jurídica para geração de documento"
                      />
                    </div>
                  </div>

                  <Button
                    onClick={hasDependencies ? () => onSetWizardStep(3) : onCreateSession}
                    disabled={isCreatingSession || !newObjective.trim()}
                    className="w-full rounded-xl"
                    size="lg"
                  >
                    {isCreatingSession ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : hasDependencies ? (
                      <>
                        Avançar →
                      </>
                    ) : (
                      <>
                        <Plus className="h-4 w-4 mr-2" />
                        Criar Sessão
                      </>
                    )}
                  </Button>
                </div>
              )}

              {/* Step 3: Document dependency selection */}
              {wizardStep === 3 && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => onSetWizardStep(2)}>
                      <ArrowLeft className="h-4 w-4" />
                    </Button>
                    <Badge variant="outline">Vínculo Opcional</Badge>
                  </div>
                  <DocumentImportSelector
                    targetDocumentType={selectedDocumentType}
                    sourceCodes={documentDependencies[selectedDocumentType] || []}
                    onSelect={(id) => {
                      onParentSessionSelect(id);
                      onCreateSession();
                    }}
                    onSkip={() => {
                      onParentSessionSelect(null);
                      onCreateSession();
                    }}
                  />
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right: Session list */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50">
              <h3 className="font-bold text-slate-800 flex items-center gap-2">
                <Bot size={18} className="text-primary" />
                Sessões Existentes
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                {sessions.length} sessão(ões) criada(s)
              </p>
            </div>

            <ScrollArea className="h-[460px]">
              <div className="p-4">
                {isLoadingSessions ? (
                  <div className="flex justify-center py-12">
                    <Loader2 className="h-6 w-6 animate-spin text-primary" />
                  </div>
                ) : sessions.length === 0 ? (
                  <div className="text-center py-12 text-slate-400">
                    <Bot className="h-12 w-12 mx-auto mb-3 opacity-30" />
                    <p className="text-sm font-medium">Nenhuma sessão criada</p>
                    <p className="text-xs mt-1">Crie sua primeira sessão ao lado.</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {sessions.map((session) => (
                      <div
                        key={session.id}
                        className={cn(
                          'p-4 rounded-2xl border cursor-pointer transition-all',
                          selectedSessionId === session.id
                            ? 'border-primary bg-primary/5'
                            : 'border-slate-100 hover:bg-slate-50 hover:border-slate-200'
                        )}
                        onClick={() => onSelectSession(session.id)}
                      >
                        <p className="font-medium text-sm line-clamp-2 text-slate-700">
                          {session.objective}
                        </p>
                        <div className="flex items-center gap-2 mt-2 flex-wrap">
                          <Badge variant="outline" className="text-[10px]">
                            {documentTypeLabels[session.document_type] || session.document_type}
                          </Badge>
                          <Badge
                            variant={(statusLabels[session.status]?.variant as any) || 'outline'}
                            className="text-[10px]"
                          >
                            {statusLabels[session.status]?.label || session.status}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between mt-2">
                          <span className="text-[10px] text-slate-400 flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {formatDate(session.created_at)}
                          </span>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6"
                            onClick={(e) => {
                              e.stopPropagation();
                              onDeleteSession(session.id);
                            }}
                          >
                            <Trash2 className="h-3.5 w-3.5 text-red-400" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>
        </div>
      </div>
    </div>
  );
}

export const SessionSidebar = memo(SessionSidebarComponent);

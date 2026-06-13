'use client';

import { useState, useCallback, useEffect, useMemo, useRef } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useQueryClient } from '@tanstack/react-query';
import { useIntelligentAssistant } from '@/hooks/use-intelligent-assistant';
import { useBlueprints } from '@/hooks/use-blueprints';
import { useDocumentTypes, useDocumentTypeLabels } from '@/hooks/use-document-types';
import { useToast } from '@/hooks/use-toast';
import { useSubSectionDecisions } from '@/hooks/use-sub-section-decisions';
import { Loader2, Bot } from 'lucide-react';
import api from '@/lib/api';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Trash2 } from 'lucide-react';

import { PipelinePanel } from '@/components/graph/PipelinePanel';
import { PipelineDialog } from '@/components/graph/PipelineDialog';
import type { Phase, ApprovalStatus } from '../types';
import { PHASE_ORDER, STEP_TO_PHASE } from '../types';
import { Stepper } from '../components/Stepper';
import { DocumentHeader } from '../components/DocumentHeader';
import { SessionSidebar } from '../components/SessionSidebar';

// Direct imports (removed lazy loading to avoid AnimatePresence + Suspense incompatibility)
import { UploadPhase } from '../components/phases/UploadPhase';
import { GenerationPhase } from '../components/phases/GenerationPhase';
import { EvaluationPhase } from '../components/phases/EvaluationPhase';
import { AnalysisPhase } from '../components/phases/AnalysisPhase';
import { ResultPhase } from '../components/phases/ResultPhase';
import { HistoryPhase } from '../components/phases/HistoryPhase';

// Lucide icons map for document type icons from API
import {
  FileText, FileSearch, ClipboardList, ScrollText, Briefcase, Scale, Settings,
  AlertCircle, CheckCircle2, Clock, AlertTriangle, DollarSign, Wrench,
  CheckSquare, UserCheck, Award, MessageCircle, ArrowUpCircle, ArrowDownCircle,
  Gavel, Play, FilePlus, File,
  Shield, TrendingUp, Zap, Send, BookOpen, FileSignature,
  UserCheck as UserCheckIcon, FileEdit, FileWarning,
} from 'lucide-react';

const DOCUMENT_DEPENDENCIES: Record<string, { code: string; label: string }[]> = {
  contestacao: [{ code: 'peticao_inicial', label: 'Petição Inicial Cível' }],
  contrarrazoes_apelacao: [{ code: 'apelacao', label: 'Apelação' }],
  apelacao: [{ code: 'contestacao', label: 'Contestação' }, { code: 'peticao_inicial', label: 'Petição Inicial Cível' }],
  agravo_instrumento: [{ code: 'peticao_inicial', label: 'Petição Inicial Cível' }, { code: 'contestacao', label: 'Contestação' }],
  embargos_declaracao: [{ code: 'peticao_inicial', label: 'Petição Inicial Cível' }, { code: 'contestacao', label: 'Contestação' }, { code: 'apelacao', label: 'Apelação' }],
  recurso_especial: [{ code: 'apelacao', label: 'Apelação' }],
  recurso_extraordinario: [{ code: 'apelacao', label: 'Apelação' }],
  embargos_execucao: [{ code: 'acao_execucao', label: 'Ação de Execução de Título Extrajudicial' }],
  impugnacao_cumprimento: [{ code: 'acao_execucao', label: 'Execução de Título Extrajudicial' }, { code: 'peticao_inicial', label: 'Petição Inicial Cível' }],
  alegacoes_finais_criminais: [{ code: 'queixa_crime', label: 'Queixa-Crime / Denúncia' }],
  contestacao_trabalhista: [{ code: 'reclamacao_trabalhista', label: 'Reclamação Trabalhista' }],
};

const LUCIDE_ICONS: Record<string, any> = {
  FileText, FileSearch, ClipboardList, ScrollText, Briefcase, Scale, Settings,
  AlertCircle, CheckCircle2, Clock, AlertTriangle, DollarSign, Wrench,
  CheckSquare, UserCheck: UserCheckIcon, Award, CheckCircle: CheckCircle2, MessageCircle,
  ArrowUpCircle, ArrowDownCircle, Gavel, Play, FilePlus, File,
  Shield, TrendingUp, Zap, Send, BookOpen, FileSignature,
  FileEdit, FileWarning,
};

const STATUS_LABELS: Record<string, { label: string; variant: string }> = {
  initialized: { label: 'Iniciada', variant: 'outline' },
  uploading: { label: 'Enviando', variant: 'secondary' },
  processing: { label: 'Processando', variant: 'secondary' },
  generating: { label: 'Gerando', variant: 'secondary' },
  validating: { label: 'Validando', variant: 'secondary' },
  formatting: { label: 'Formatando', variant: 'secondary' },
  completed: { label: 'Concluída', variant: 'default' },
  failed: { label: 'Falhou', variant: 'destructive' },
};

function PhaseLoader() {
  return (
    <div className="flex items-center justify-center py-20">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
    </div>
  );
}

export default function IntelligentAssistantPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialLoadDone = useRef(false);
  const prevSessionRef = useRef<string | null>(null);

  // ─── Hooks ───
  const {
    sessions,
    isLoadingSessions,
    isCreatingSession,
    isDeletingSession,
    isUploadingDocuments,
    createSession,
    deleteSession,
    uploadDocuments,
    generateETPWithStreaming,
    generationProgress,
    cancelGeneration,
    resetProgress,
    loadGenerationSession,
    regenerateSectionWithStreaming,
    regeneratingSection,
    useSession,
    graphVisualization,
  } = useIntelligentAssistant();

  const {
    blueprints: allBlueprints,
    isLoading: isLoadingBlueprints,
    defaultBlueprint,
    useBlueprintSections,
  } = useBlueprints();

  const { documentTypes, isLoading: isLoadingDocumentTypes } = useDocumentTypes();
  const { labels: documentTypeLabels, fullNames: documentTypeFullNames } = useDocumentTypeLabels();

  // ─── State: Navigation ───
  const [currentPhase, setCurrentPhase] = useState<Phase>('upload');
  const [pipelineDialogOpen, setPipelineDialogOpen] = useState(false);

  // ─── State: Session ───
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null);
  const [documentToDelete, setDocumentToDelete] = useState<string | null>(null);
  const [isDeletingDocument, setIsDeletingDocument] = useState(false);
  const [selectedBlueprintId, setSelectedBlueprintId] = useState('');

  // ─── State: Session wizard ───
  const [wizardStep, setWizardStep] = useState(0);
  const [selectedDocumentType, setSelectedDocumentType] = useState('');
  const [newObjective, setNewObjective] = useState('');
  const [newDocumentType, setNewDocumentType] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [parentSessionId, setParentSessionId] = useState<string | null>(null);

  // ─── State: Generation ───
  const [generatedContent, setGeneratedContent] = useState<Record<string, string>>({});
  const [generationMetadata, setGenerationMetadata] = useState<any>(null);
  const [expandedSections, setExpandedSections] = useState<Set<number>>(new Set());
  const [selectedSectionsToGenerate, setSelectedSectionsToGenerate] = useState<Set<number>>(new Set());
  const [generateAllSections, setGenerateAllSections] = useState(true);
  const [sectionFieldsValues, setSectionFieldsValues] = useState<Record<number, Record<string, any>>>({});
  // ─── State: Auto-fill from uploaded documents ───
  const [isExtractingFields, setIsExtractingFields] = useState(false);
  const [extractionDone, setExtractionDone] = useState(false);
  const [autoFilledSections, setAutoFilledSections] = useState<Set<number>>(new Set());
  // ─── State: Evaluation ───
  const [sectionRatings, setSectionRatings] = useState<Record<number, number>>({});
  const [editingSection, setEditingSection] = useState<number | null>(null);
  const [editedContent, setEditedContent] = useState<Record<number, string>>({});
  const [savingFeedback, setSavingFeedback] = useState<Record<number, boolean>>({});
  const [evaluatedSections, setEvaluatedSections] = useState<Record<number, 'approved' | 'improved'>>({});
  const [approvalStatus, setApprovalStatus] = useState<Record<number, ApprovalStatus>>({});

  // ─── State: Result ───
  const [pdfStatus, setPdfStatus] = useState<'none' | 'generating' | 'ready' | 'failed'>('none');
  const [docxStatus, setDocxStatus] = useState<'none' | 'generating' | 'ready' | 'failed'>('none');
  const [odtStatus, setOdtStatus] = useState<'none' | 'generating' | 'ready' | 'failed'>('none');
  const [updatingDocument, setUpdatingDocument] = useState(false);

  // ─── Reset: limpa TODO estado de sessão ───
  const resetSessionState = useCallback(() => {
    setGeneratedContent({});
    setGenerationMetadata(null);
    setEditedContent({});
    setSectionRatings({});
    setEvaluatedSections({});
    setApprovalStatus({});
    setEditingSection(null);
    setSavingFeedback({});
    setPdfStatus('none');
    setDocxStatus('none');
    setOdtStatus('none');
    setUpdatingDocument(false);
    setSectionFieldsValues({});
    resetSubSectionDecisions();
    setExpandedSections(new Set());
    setGenerateAllSections(true);
    setIsExtractingFields(false);
    setExtractionDone(false);
    setAutoFilledSections(new Set());

  }, []);

  // Proteção: limpa dados sempre que selectedSessionId muda
  useEffect(() => {
    if (selectedSessionId !== prevSessionRef.current) {
      if (prevSessionRef.current !== null) {
        resetSessionState();
      }
      prevSessionRef.current = selectedSessionId;
    }
  }, [selectedSessionId, resetSessionState]);

  // ─── Derived data ───
  const { data: sessionDetail, isError: isSessionError } = useSession(selectedSessionId);

  // Sessão referenciada na URL não existe mais (404) - resetar para estado limpo
  useEffect(() => {
    if (selectedSessionId && isSessionError) {
      setSelectedSessionId(null);
      setCurrentPhase('upload');
      setGeneratedContent({});
      setGenerationMetadata(null);
      router.replace('/dashboard/intelligent-assistant', { scroll: false });
    }
  }, [selectedSessionId, isSessionError]);

  const blueprints = useMemo(() => {
    if (!selectedDocumentType) return allBlueprints;
    return allBlueprints.filter((b) => b.document_type_code === selectedDocumentType);
  }, [allBlueprints, selectedDocumentType]);

  const { data: blueprintSectionsData, isLoading: isLoadingSections } =
    useBlueprintSections(selectedBlueprintId);

  const sectionNames = useMemo(() => {
    const names: Record<number, string> = {};
    blueprintSectionsData?.sections?.forEach((s: any) => {
      names[s.section_number] = s.section_name;
    });
    return names;
  }, [blueprintSectionsData]);

  const sectionFieldsMap = useMemo(() => {
    const fields: Record<number, any[]> = {};
    blueprintSectionsData?.sections?.forEach((s: any) => {
      if (s.section_fields?.length > 0) {
        fields[s.section_number] = s.section_fields;
      }
    });
    return fields;
  }, [blueprintSectionsData]);

  const subSectionsMap = useMemo(() => {
    const map: Record<number, any[]> = {};
    blueprintSectionsData?.sections?.forEach((s: any) => {
      if (s.sub_sections?.length > 0) {
        map[s.section_number] = s.sub_sections;
      }
    });
    return map;
  }, [blueprintSectionsData]);

  const {
    decisions: subSectionDecisions,
    onChange: onSubSectionDecisionChange,
    reset: resetSubSectionDecisions,
  } = useSubSectionDecisions(subSectionsMap);

  const sectionAgentInfo = useMemo(() => {
    const info: Record<number, { generatorName?: string; validatorName?: string }> = {};
    blueprintSectionsData?.sections?.forEach((s: any) => {
      info[s.section_number] = {
        generatorName: s.generator_agent_name,
        validatorName: s.validator_agent_name,
      };
    });
    return info;
  }, [blueprintSectionsData]);

  const totalSections = useMemo(() => {
    return blueprints.find((b) => b.id === selectedBlueprintId)?.section_count || 0;
  }, [blueprints, selectedBlueprintId]);

  const selectedBlueprint = useMemo(
    () => blueprints.find((b) => b.id === selectedBlueprintId),
    [blueprints, selectedBlueprintId]
  );

  // ─── Effects ───

  // Sync blueprint from session
  useEffect(() => {
    if (sessionDetail?.blueprint_id) {
      setSelectedBlueprintId(sessionDetail.blueprint_id);
      if (sessionDetail.blueprint?.document_type) {
        setSelectedDocumentType(sessionDetail.blueprint.document_type);
        setNewDocumentType(sessionDetail.blueprint.document_type);
      }
    }
  }, [sessionDetail?.blueprint_id, sessionDetail?.blueprint?.document_type]);

  // URL query params → state (reage a mudanças na URL)
  useEffect(() => {
    const sessionParam = searchParams.get('session');
    const phaseParam = searchParams.get('phase');
    const stepParam = searchParams.get('step');

    // Sessão da URL
    if (sessionParam && sessionParam !== selectedSessionId) {
      setSelectedSessionId(sessionParam);
    }

    // Fase da URL (suporta ?phase= e ?step= legado)
    let targetPhase: Phase | null = null;
    if (phaseParam && PHASE_ORDER.includes(phaseParam as Phase)) {
      targetPhase = phaseParam as Phase;
    } else if (stepParam && STEP_TO_PHASE[stepParam]) {
      targetPhase = STEP_TO_PHASE[stepParam];
    }

    if (targetPhase && targetPhase !== currentPhase) {
      setCurrentPhase(targetPhase);
    }

    if (sessionParam) {
      initialLoadDone.current = true;
    }
  }, [searchParams]);

  // Restore GenerationSession from URL (ex: after F5 or navigating back)
  const restoredGenerationSession = useRef<string | null>(null);
  useEffect(() => {
    const gsParam = searchParams.get('generation_session');
    if (!gsParam || restoredGenerationSession.current === gsParam) return;

    restoredGenerationSession.current = gsParam;
    loadGenerationSession(gsParam).then((backendData) => {
      if (backendData) {
        setGeneratedContent(backendData.content);
        const completedCount = backendData.sessionData.completed_sections_count || 0;
        const avgScore = Object.values(backendData.sections)
          .filter((s: any) => s.score !== undefined)
          .reduce((acc: number, s: any, _, arr) => acc + (s.score || 0) / arr.length, 0);
        const genTime = backendData.sessionData.started_at && backendData.sessionData.completed_at
          ? (new Date(backendData.sessionData.completed_at).getTime() -
             new Date(backendData.sessionData.started_at).getTime()) / 1000
          : null;
        setGenerationMetadata({
          total_tokens_used: backendData.sessionData.total_tokens || 0,
          valid_sections: completedCount,
          average_score: Math.round(avgScore),
          generation_time: genTime,
          document_id: backendData.sessionData.latest_document_id || '',
          generation_session_id: gsParam,
        });
      } else {
        // Sessão de geração não existe mais (404) - limpar params obsoletos da URL
        restoredGenerationSession.current = null;
        const params = new URLSearchParams(searchParams.toString());
        params.delete('generation_session');
        params.delete('doc');
        params.delete('phase');
        const cleanUrl = params.toString()
          ? `/dashboard/intelligent-assistant?${params.toString()}`
          : '/dashboard/intelligent-assistant';
        router.replace(cleanUrl, { scroll: false });
      }
    });
  }, [searchParams]);

  // Load historical document from URL
  useEffect(() => {
    const docParam = searchParams.get('doc');
    if (!docParam || !sessionDetail?.generated_documents) return;
    if (generationMetadata?.document_id === docParam) return;
    const doc = sessionDetail.generated_documents.find((d: any) => d.id === docParam);
    if (doc) handleLoadHistoricalDocument(doc);
  }, [sessionDetail?.generated_documents, searchParams]);

  // Sync state → URL
  useEffect(() => {
    if (!initialLoadDone.current && !selectedSessionId) return;
    initialLoadDone.current = true;
    const params = new URLSearchParams();
    if (selectedSessionId) params.set('session', selectedSessionId);
    if (currentPhase !== 'upload') params.set('phase', currentPhase);
    if (generationMetadata?.document_id && PHASE_ORDER.indexOf(currentPhase) >= 2) {
      params.set('doc', generationMetadata.document_id);
    }
    if (generationMetadata?.generation_session_id) {
      params.set('generation_session', generationMetadata.generation_session_id);
    }
    const newUrl = params.toString()
      ? `/dashboard/intelligent-assistant/gerador?${params.toString()}`
      : '/dashboard/intelligent-assistant/gerador';
    router.replace(newUrl, { scroll: false });
  }, [selectedSessionId, currentPhase, generationMetadata?.document_id, generationMetadata?.generation_session_id]);

  // Default blueprint
  useEffect(() => {
    if (defaultBlueprint && !selectedBlueprintId && !selectedSessionId) {
      setSelectedBlueprintId(defaultBlueprint.id);
    }
  }, [defaultBlueprint, selectedBlueprintId, selectedSessionId]);

  // Update section selection when blueprint changes
  useEffect(() => {
    if (totalSections > 0) {
      setSelectedSectionsToGenerate(new Set(Array.from({ length: totalSections }, (_, i) => i + 1)));
      setGenerateAllSections(true);
    }
  }, [totalSections, selectedBlueprintId]);

  // Generation completed → load from backend (source of truth)
  const generationResultRef = useRef<string | null>(null);
  useEffect(() => {
    if (!generationProgress.result?.success) return;
    const gsId = generationProgress.result.generationSessionId;

    // Se temos generationSessionId, buscar do backend (persistido)
    if (gsId && gsId !== generationResultRef.current) {
      generationResultRef.current = gsId;
      loadGenerationSession(gsId).then((backendData) => {
        if (backendData) {
          setGeneratedContent(backendData.content);
        } else {
          // Fallback: extrair do SSE se backend falhar
          extractContentFromSSE();
        }
        setGenerationMetadata({
          total_tokens_used: generationProgress.result!.totalTokensUsed || 0,
          valid_sections: generationProgress.result!.validSections,
          average_score: generationProgress.result!.averageScore,
          pdf_url: generationProgress.result!.pdfUrl,
          generation_time: generationProgress.result!.generationTime,
          document_id: generationProgress.result!.documentId,
          generation_session_id: gsId,
        });
        toast({
          title: 'Documento gerado com sucesso',
          description: `${generationProgress.result!.validSections}/${totalSections} seções válidas. Score médio: ${generationProgress.result!.averageScore}%`,
        });
      });
    } else if (!gsId) {
      // Sem generationSessionId (legado) - usar dados do SSE
      extractContentFromSSE();
      setGenerationMetadata({
        total_tokens_used: generationProgress.result.totalTokensUsed || 0,
        valid_sections: generationProgress.result.validSections,
        average_score: generationProgress.result.averageScore,
        pdf_url: generationProgress.result.pdfUrl,
        generation_time: generationProgress.result.generationTime,
        document_id: generationProgress.result.documentId,
      });
      toast({
        title: 'Documento gerado com sucesso',
        description: `${generationProgress.result.validSections}/${totalSections} seções válidas. Score médio: ${generationProgress.result.averageScore}%`,
      });
    }
  }, [generationProgress.result]);

  // Extrai conteúdo do estado volátil SSE (fallback)
  const extractContentFromSSE = useCallback(() => {
    const content: Record<string, string> = {};
    Object.entries(generationProgress.sections).forEach(([key, section]) => {
      const sectionKey = `section_${key.padStart(2, '0')}`;
      if (section.content) {
        content[sectionKey] = section.content;
      } else if (section.status === 'rejected' || (section.score !== undefined && section.score < 60)) {
        content[sectionKey] = `*Esta seção não pôde ser gerada adequadamente (Score: ${section.score || 0}%).*\n\n**Motivos:**\n${section.feedback?.map((f) => `- ${f}`).join('\n') || '- Validação não passou nos critérios mínimos'}`;
      }
    });
    setGeneratedContent(content);
  }, [generationProgress.sections]);

  // Sincronizar generatedContent quando regeneração finalizar
  // useEffect roda APÓS o render, garantindo que generationProgress.sections já está atualizado
  const prevRegeneratingSectionRef = useRef<number | null>(null);
  useEffect(() => {
    if (prevRegeneratingSectionRef.current !== null && regeneratingSection === null) {
      extractContentFromSSE();
    }
    prevRegeneratingSectionRef.current = regeneratingSection;
  }, [regeneratingSection, extractContentFromSSE]);

  // Reset exports when content edited
  useEffect(() => {
    if (Object.keys(editedContent).length > 0) {
      setPdfStatus('none');
      setDocxStatus('none');
      setOdtStatus('none');
    }
  }, [editedContent]);

  // ─── Handlers ───

  const handleCreateSession = useCallback(async () => {
    if (!newObjective.trim()) {
      toast({ title: 'Objetivo obrigatório', description: 'Informe o objetivo.', variant: 'destructive' });
      return;
    }
    if (!selectedBlueprintId) {
      toast({ title: 'Blueprint obrigatório', description: 'Selecione um modelo.', variant: 'destructive' });
      return;
    }
    try {
      const session = await createSession({
        objective: newObjective,
        document_type: newDocumentType,
        blueprint_id: selectedBlueprintId,
        ...(parentSessionId ? { parent_etp_session_id: parentSessionId } : {}),
      });

      toast({ title: 'Sessão criada', description: 'Agora você pode enviar documentos.' });
      setSelectedSessionId(session.id);
      setNewObjective('');
      setWizardStep(0);
      setParentSessionId(null);
      setCurrentPhase('upload');
    } catch (error: any) {
      toast({
        title: 'Erro ao criar sessão',
        description: error.response?.data?.error || 'Tente novamente.',
        variant: 'destructive',
      });
    }
  }, [newObjective, selectedBlueprintId, newDocumentType, createSession, toast]);

  const handleDeleteSession = useCallback(async () => {
    if (!sessionToDelete) return;
    try {
      await deleteSession(sessionToDelete);
      toast({ title: 'Sessão removida' });
      if (selectedSessionId === sessionToDelete) {
        setSelectedSessionId(null);
        setCurrentPhase('upload');
      }
      setSessionToDelete(null);
    } catch (error: any) {
      toast({ title: 'Erro', description: error.response?.data?.error || 'Tente novamente.', variant: 'destructive' });
    }
  }, [sessionToDelete, selectedSessionId, deleteSession, toast]);

  const handleDeleteUploadedDocument = useCallback(
    async (documentId: string) => {
      if (!selectedSessionId) return;
      try {
        await api.delete(
          `/api/v1/intelligent-assistant/sessions/${selectedSessionId}/uploaded-documents/${documentId}/`
        );
        toast({ title: 'Documento removido' });
        // Invalidar cache da sessão para refetch automático
        queryClient.invalidateQueries({ queryKey: ['intelligent-session', selectedSessionId] });
      } catch (error: any) {
        toast({ title: 'Erro', description: error.message || 'Tente novamente.', variant: 'destructive' });
      }
    },
    [selectedSessionId, toast, queryClient]
  );

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === 'dragenter' || e.type === 'dragover');
  }, []);

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);
      if (!selectedSessionId) {
        toast({ title: 'Selecione uma sessão', variant: 'destructive' });
        return;
      }
      await handleUpload(Array.from(e.dataTransfer.files));
    },
    [selectedSessionId]
  );

  const handleFileSelect = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      if (!e.target.files || !selectedSessionId) return;
      await handleUpload(Array.from(e.target.files));
    },
    [selectedSessionId]
  );

  const handleUpload = async (files: File[]) => {
    if (!selectedSessionId) return;
    const validTypes = ['.pdf', '.docx', '.txt', '.odt'];
    const invalid = files.filter((f) => !validTypes.some((ext) => f.name.toLowerCase().endsWith(ext)));
    if (invalid.length > 0) {
      toast({
        title: 'Arquivos inválidos',
        description: `Apenas PDF, DOCX, TXT e ODT. Rejeitados: ${invalid.map((f) => f.name).join(', ')}`,
        variant: 'destructive',
      });
      return;
    }
    try {
      const result = await uploadDocuments({ sessionId: selectedSessionId, files });
      if (result.success) {
        toast({ title: 'Upload concluído', description: `${result.total_processed} documento(s) processado(s).` });
      }
      if (result.errors?.length) {
        toast({
          title: 'Alguns falharam',
          description: result.errors.map((e: any) => `${e.filename}: ${e.error}`).join('\n'),
          variant: 'destructive',
        });
      }
    } catch (error: any) {
      toast({ title: 'Erro no upload', description: error.response?.data?.error || 'Tente novamente.', variant: 'destructive' });
    }
  };

  // Auto-extract fields from uploaded documents when advancing to generation phase
  const handleAdvanceToGeneration = useCallback(async () => {
    setCurrentPhase('generation');

    // Only extract if there are uploaded docs and we haven't already extracted for this session
    const docs = sessionDetail?.documents || [];
    const hasCompletedDocs = docs.some((d: any) => d.extraction_status === 'completed');
    if (!hasCompletedDocs || !selectedSessionId || extractionDone) return;

    setIsExtractingFields(true);
    try {
      const { data } = await api.post(
        `/api/v1/intelligent-assistant/sessions/${selectedSessionId}/extract-fields/`
      );
      if (data.extracted && data.fields_filled > 0) {
        // Populate sectionFieldsValues with extracted data
        const newValues = { ...sectionFieldsValues };
        const filledSections = new Set<number>();
        for (const [secNum, fields] of Object.entries(data.extracted)) {
          const num = parseInt(secNum);
          if (isNaN(num)) continue;
          newValues[num] = {
            ...(newValues[num] || {}),
            ...(fields as Record<string, any>),
          };
          filledSections.add(num);
        }
        setSectionFieldsValues(newValues);
        setAutoFilledSections(filledSections);
        toast({
          title: 'Campos preenchidos automaticamente',
          description: `${data.fields_filled} de ${data.fields_total} campos preenchidos a partir dos documentos enviados.`,
        });
      }
    } catch (error: any) {
      // Non-blocking: if extraction fails, user can fill manually
      const msg = error?.response?.data?.error || '';
      if (msg && !msg.includes('Nenhum documento')) {
        console.warn('[extract-fields] Falha na extração automática:', msg);
      }
    } finally {
      setIsExtractingFields(false);
      setExtractionDone(true);
    }
  }, [selectedSessionId, sessionDetail, extractionDone, sectionFieldsValues, toast]);

  const handleGenerate = useCallback(async () => {
    if (!sessionDetail || selectedSectionsToGenerate.size === 0 || !selectedBlueprintId) return;
    try {
      const sectionsArray = Array.from(selectedSectionsToGenerate).sort((a, b) => a - b);
      await generateETPWithStreaming(
        sessionDetail.objective,
        selectedSessionId || undefined,
        sectionsArray,
        selectedBlueprintId,
        sectionFieldsValues,
        undefined,
        Object.keys(subSectionDecisions).length > 0 ? subSectionDecisions : undefined,
      );
    } catch (error: any) {
      toast({ title: 'Erro ao gerar', description: error.message || 'Tente novamente.', variant: 'destructive' });
    }
  }, [sessionDetail, selectedSectionsToGenerate, selectedBlueprintId, selectedSessionId, sectionFieldsValues, subSectionDecisions, generateETPWithStreaming, toast]);

  const toggleSectionToGenerate = useCallback(
    (num: number) => {
      setSelectedSectionsToGenerate((prev) => {
        const next = new Set(prev);
        if (next.has(num)) next.delete(num);
        else next.add(num);
        setGenerateAllSections(next.size === totalSections);
        return next;
      });
    },
    [totalSections]
  );

  const toggleAllSections = useCallback(
    (selectAll: boolean) => {
      setGenerateAllSections(selectAll);
      setSelectedSectionsToGenerate(
        selectAll ? new Set(Array.from({ length: totalSections }, (_, i) => i + 1)) : new Set()
      );
    },
    [totalSections]
  );

  const toggleSectionExpand = useCallback((num: number) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(num)) next.delete(num);
      else next.add(num);
      return next;
    });
  }, []);

  // Evaluation handlers
  const handleRate = useCallback((num: number, rating: number) => {
    setSectionRatings((prev) => ({ ...prev, [num]: rating }));
  }, []);

  const handleStartEdit = useCallback(
    (num: number) => {
      const key = `section_${String(num).padStart(2, '0')}`;
      setEditedContent((prev) => ({ ...prev, [num]: prev[num] || generatedContent[key] || '' }));
      setEditingSection(num);
    },
    [generatedContent]
  );

  const handleCancelEdit = useCallback(() => setEditingSection(null), []);

  const handleSaveEdit = useCallback(
    (num: number) => {
      const key = `section_${String(num).padStart(2, '0')}`;
      setGeneratedContent((prev) => ({ ...prev, [key]: editedContent[num] }));
      setEditingSection(null);
      toast({ title: 'Seção atualizada' });
    },
    [editedContent, toast]
  );

  const handleEditChange = useCallback((num: number, content: string) => {
    setEditedContent((prev) => ({ ...prev, [num]: content }));
  }, []);

  const handleSetApproval = useCallback((num: number, status: ApprovalStatus) => {
    setApprovalStatus((prev) => ({ ...prev, [num]: prev[num] === status ? 'pending' : status }));
  }, []);

  const handleSaveFeedback = useCallback(
    async (num: number) => {
      if (!selectedSessionId) return;
      const key = `section_${String(num).padStart(2, '0')}`;
      const original = generatedContent[key];
      const edited = editedContent[num] || original;
      const rating = sectionRatings[num] || 0;
      const sectionData = generationProgress.sections[num];
      if (!rating) {
        toast({ title: 'Avalie a seção', description: 'Dê uma nota de 1 a 5 estrelas.', variant: 'destructive' });
        return;
      }
      setSavingFeedback((prev) => ({ ...prev, [num]: true }));
      try {
        const { data: result } = await api.post('/api/v1/intelligent-assistant/section-feedback/', {
          session_id: selectedSessionId,
          section_number: num,
          section_name: sectionNames[num] || '',
          original_content: original,
          edited_content: edited,
          rating,
          ai_score: sectionData?.score || 0,
        });
        const hasEdited = edited.trim() !== original.trim();
        setEvaluatedSections((prev) => ({ ...prev, [num]: hasEdited ? 'improved' : 'approved' }));
        toast({
          title: 'Avaliação enviada!',
          description: result.embedding_created
            ? hasEdited
              ? 'Sua melhoria foi salva na base de conhecimento.'
              : 'Conteúdo aprovado e salvo como exemplo.'
            : 'Sua avaliação foi registrada.',
        });
      } catch (error: any) {
        toast({ title: 'Erro', description: error.response?.data?.error || error.message, variant: 'destructive' });
      } finally {
        setSavingFeedback((prev) => ({ ...prev, [num]: false }));
      }
    },
    [selectedSessionId, generatedContent, editedContent, sectionRatings, generationProgress.sections, sectionNames, toast]
  );

  const handleAdvanceFromEvaluation = useCallback(async () => {
    const hasEdits = Object.keys(editedContent).length > 0;
    if (hasEdits && generationMetadata?.document_id) {
      setUpdatingDocument(true);
      try {
        const sectionsToUpdate: Record<string, string> = {};
        Object.entries(editedContent).forEach(([num, content]) => {
          sectionsToUpdate[`section_${String(num).padStart(2, '0')}`] = content;
        });
        const { data } = await api.put(
          `/api/v1/intelligent-assistant/documents/${generationMetadata.document_id}/update-sections/`,
          { sections: sectionsToUpdate }
        );
        if (data.success) {
          setGeneratedContent((prev) => {
            const updated = { ...prev };
            Object.entries(editedContent).forEach(([num, content]) => {
              updated[`section_${String(num).padStart(2, '0')}`] = content;
            });
            return updated;
          });
          setEditedContent({});
          setPdfStatus('none');
          toast({ title: 'Documento atualizado', description: 'Edições salvas.' });
        }
      } catch {
        toast({ title: 'Erro', description: 'Falha ao salvar edições.', variant: 'destructive' });
      } finally {
        setUpdatingDocument(false);
      }
    }
    setCurrentPhase('analysis');
  }, [editedContent, generationMetadata, toast]);

  // Result handlers
  const handleGeneratePdf = useCallback(async () => {
    if (!generationMetadata?.document_id) return;
    setPdfStatus('generating');
    try {
      const response = await api.post(
        `/api/v1/intelligent-assistant/documents/${generationMetadata.document_id}/generate-pdf/`,
        {},
        { responseType: 'blob', timeout: 120000 }
      );
      const blobUrl = URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = 'documento.pdf';
      a.click();
      setTimeout(() => URL.revokeObjectURL(blobUrl), 10000);
      setPdfStatus('none');
      toast({ title: 'PDF gerado!', description: 'Download iniciado.' });
    } catch (error: any) {
      setPdfStatus('failed');
      toast({ title: 'Erro', description: error.message || 'Falha ao gerar PDF.', variant: 'destructive' });
    }
  }, [generationMetadata, toast]);

  const handleGenerateDocx = useCallback(async () => {
    if (!generationMetadata?.document_id) return;
    setDocxStatus('generating');
    try {
      const response = await api.post(
        `/api/v1/intelligent-assistant/documents/${generationMetadata.document_id}/generate-docx/`,
        {},
        { responseType: 'blob', timeout: 120000 }
      );
      const blobUrl = URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = 'documento.docx';
      a.click();
      setTimeout(() => URL.revokeObjectURL(blobUrl), 10000);
      setDocxStatus('none');
      toast({ title: 'DOCX gerado!', description: 'Download iniciado.' });
    } catch (error: any) {
      setDocxStatus('failed');
      toast({ title: 'Erro', description: error.message || 'Falha ao gerar DOCX.', variant: 'destructive' });
    }
  }, [generationMetadata, toast]);

  const handleGenerateOdt = useCallback(async () => {
    if (!generationMetadata?.document_id) return;
    setOdtStatus('generating');
    try {
      const response = await api.post(
        `/api/v1/intelligent-assistant/documents/${generationMetadata.document_id}/generate-odt/`,
        {},
        { responseType: 'blob', timeout: 120000 }
      );
      const blobUrl = URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = 'documento.odt';
      a.click();
      setTimeout(() => URL.revokeObjectURL(blobUrl), 10000);
      setOdtStatus('none');
      toast({ title: 'ODT gerado!', description: 'Download iniciado.' });
    } catch (error: any) {
      setOdtStatus('failed');
      toast({ title: 'Erro', description: error.message || 'Falha ao gerar ODT.', variant: 'destructive' });
    }
  }, [generationMetadata, toast]);

  const copyToClipboard = useCallback(async () => {
    const full = Object.entries(generatedContent)
      .map(([key, content]) => {
        const num = parseInt(key.replace('section_', ''));
        return `## ${num}. ${sectionNames[num] || key}\n\n${content}`;
      })
      .join('\n\n---\n\n');
    await navigator.clipboard.writeText(full);
    toast({ title: 'Copiado!' });
  }, [generatedContent, sectionNames, toast]);

  const handleLoadHistoricalDocument = useCallback(
    async (doc: any) => {
      // Parsear markdown em seções
      const content: Record<string, string> = {};
      const markdown = doc.markdown_content || '';
      const regex = /## (\d+)\.\s*([^\n]+)\n([\s\S]*?)(?=## \d+\.|$)/g;
      let match;
      while ((match = regex.exec(markdown)) !== null) {
        content[`section_${String(parseInt(match[1])).padStart(2, '0')}`] = match[3].trim();
      }
      setGeneratedContent(content);
      setEditedContent({});
      setSectionRatings({});
      setEditingSection(null);
      setApprovalStatus({});
      setPdfStatus('none');

      // Tentar carregar GenerationSession para popular scores/análise
      const gsId = sessionDetail?.generation_session_id;
      if (gsId) {
        const backendData = await loadGenerationSession(gsId);
        if (backendData) {
          const completedCount = backendData.sessionData.completed_sections_count || 0;
          const allScores = Object.values(backendData.sections)
            .map((s: any) => s.score)
            .filter((s: any) => s != null && s > 0);
          const avgScore = allScores.length > 0
            ? allScores.reduce((a: number, b: number) => a + b, 0) / allScores.length
            : 0;
          const genTime = backendData.sessionData.started_at && backendData.sessionData.completed_at
            ? (new Date(backendData.sessionData.completed_at).getTime() -
               new Date(backendData.sessionData.started_at).getTime()) / 1000
            : null;

          setGenerationMetadata({
            total_tokens_used: backendData.sessionData.total_tokens || 0,
            valid_sections: completedCount,
            average_score: Math.round(avgScore),
            generation_time: genTime,
            document_id: doc.id,
            generation_session_id: gsId,
          });
          setCurrentPhase('result');
          toast({ title: 'Documento carregado', description: `"${doc.title || 'Documento'}" com análise completa.` });
          return;
        }
      }

      // Fallback: sem GenerationSession (dados antigos)
      setGenerationMetadata({
        total_tokens_used: 0,
        valid_sections: doc.metadata?.sections_stats?.valid_count || Object.keys(content).length,
        average_score: doc.metadata?.sections_stats?.average_score || 0,
        generation_time: null,
        document_id: doc.id,
      });
      setCurrentPhase('result');
      toast({ title: 'Documento carregado', description: `"${doc.title || 'Documento'}" aberto.` });
    },
    [toast, sessionDetail?.generation_session_id, loadGenerationSession]
  );

  const handleDeleteDocument = useCallback(async () => {
    if (!documentToDelete || !selectedSessionId) return;
    setIsDeletingDocument(true);
    try {
      await api.delete(
        `/api/v1/intelligent-assistant/sessions/${selectedSessionId}/documents/${documentToDelete}/`
      );
      toast({ title: 'Documento removido' });
      // Invalidar cache e limpar URL params
      queryClient.invalidateQueries({ queryKey: ['intelligent-session', selectedSessionId] });
      const params = new URLSearchParams(searchParams.toString());
      params.delete('doc');
      params.delete('phase');
      router.replace(`/dashboard/intelligent-assistant/gerador?${params.toString()}`, { scroll: false });
    } catch (error: any) {
      toast({ title: 'Erro', description: error.message, variant: 'destructive' });
    } finally {
      setIsDeletingDocument(false);
      setDocumentToDelete(null);
    }
  }, [documentToDelete, selectedSessionId, toast, queryClient, searchParams, router]);

  // ─── Utils ───
  const formatDate = (d: string) =>
    new Date(d).toLocaleDateString('pt-BR', {
      day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
    });

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // Sidebar actions
  const handleSelectSession = useCallback((id: string) => {
    resetSessionState();
    setSelectedSessionId(id);
    setCurrentPhase('upload');
  }, [resetSessionState]);

  const handleDeselectSession = useCallback(() => {
    resetSessionState();
    setSelectedSessionId(null);
    setWizardStep(0);
    setSelectedDocumentType('');
    setSelectedBlueprintId('');
    setNewObjective('');
    setCurrentPhase('upload');
  }, [resetSessionState]);

  const handleSelectDocumentType = useCallback((code: string) => {
    setSelectedDocumentType(code);
    setNewDocumentType(code);
    setWizardStep(1);
  }, []);

  const handleSelectBlueprint = useCallback((id: string) => {
    setSelectedBlueprintId(id);
    // Derive document type automatically from the selected blueprint
    const bp = allBlueprints.find((b) => b.id === id);
    if (bp?.document_type_code) {
      setSelectedDocumentType(bp.document_type_code);
      setNewDocumentType(bp.document_type_code);
    }
    setWizardStep(2);
  }, [allBlueprints]);

  const handleUpdateObjective = useCallback(async (newObjective: string) => {
    if (!selectedSessionId) return;
    try {
      await api.patch(`/api/v1/intelligent-assistant/sessions/${selectedSessionId}/`, {
        objective: newObjective,
      });
      // Invalidar cache do React Query para refetch imediato
      queryClient.invalidateQueries({ queryKey: ['intelligent-session', selectedSessionId] });
      toast({ title: 'Objetivo atualizado' });
    } catch (error: any) {
      toast({
        title: 'Erro ao atualizar',
        description: error.response?.data?.error || 'Tente novamente.',
        variant: 'destructive',
      });
      throw error;
    }
  }, [selectedSessionId, toast, queryClient]);

  // ─── Render ───

  const documentTypeName =
    documentTypeFullNames[sessionDetail?.document_type || 'etp'] || selectedBlueprint?.name || 'Documento';

  return (
    <div className="min-h-screen flex flex-col -mx-3 sm:-mx-6 -mb-6">
      {/* Stepper */}
      <Stepper
        currentPhase={currentPhase}
        onPhaseChange={setCurrentPhase}
        disabled={!selectedSessionId}
      />

      {/* Header (only when session is selected) */}
      {selectedSessionId && sessionDetail && (
        <DocumentHeader
          documentTypeName={documentTypeName}
          blueprintName={sessionDetail.blueprint_name}
          objective={sessionDetail.objective}
          onSaveObjective={handleUpdateObjective}
        />
      )}

      {/* Main layout */}
      <div className="flex-1 max-w-[1600px] mx-auto w-full p-3 sm:p-6">
        {!selectedSessionId ? (
          <SessionSidebar
            sessions={sessions}
            selectedSessionId={selectedSessionId}
            sessionDetail={sessionDetail}
            isLoadingSessions={isLoadingSessions}
            documentTypes={documentTypes}
            isLoadingDocumentTypes={isLoadingDocumentTypes}
            documentTypeLabels={documentTypeLabels}
            allBlueprints={allBlueprints}
            blueprints={blueprints}
            wizardStep={wizardStep}
            selectedDocumentType={selectedDocumentType}
            selectedBlueprintId={selectedBlueprintId}
            newObjective={newObjective}
            isCreatingSession={isCreatingSession}
            statusLabels={STATUS_LABELS}
            lucideIcons={LUCIDE_ICONS}
            documentDependencies={DOCUMENT_DEPENDENCIES}
            parentSessionId={parentSessionId}
            onParentSessionSelect={setParentSessionId}
            onSelectSession={handleSelectSession}
            onDeselectSession={handleDeselectSession}
            onSetWizardStep={setWizardStep}
            onSelectDocumentType={handleSelectDocumentType}
            onSelectBlueprint={handleSelectBlueprint}
            onObjectiveChange={setNewObjective}
            onCreateSession={handleCreateSession}
            onDeleteSession={setSessionToDelete}
            formatDate={formatDate}
          />
        ) : (
          /* Session active: compact session bar + full-width phases */
          <div className="space-y-4 sm:space-y-6">
            <SessionSidebar
              sessions={sessions}
              selectedSessionId={selectedSessionId}
              sessionDetail={sessionDetail}
              isLoadingSessions={isLoadingSessions}
              documentTypes={documentTypes}
              isLoadingDocumentTypes={isLoadingDocumentTypes}
              documentTypeLabels={documentTypeLabels}
              allBlueprints={allBlueprints}
              blueprints={blueprints}
              wizardStep={wizardStep}
              selectedDocumentType={selectedDocumentType}
              selectedBlueprintId={selectedBlueprintId}
              newObjective={newObjective}
              isCreatingSession={isCreatingSession}
              statusLabels={STATUS_LABELS}
              lucideIcons={LUCIDE_ICONS}
              documentDependencies={DOCUMENT_DEPENDENCIES}
              parentSessionId={parentSessionId}
              onParentSessionSelect={setParentSessionId}
              onSelectSession={handleSelectSession}
              onDeselectSession={handleDeselectSession}
              onSetWizardStep={setWizardStep}
              onSelectDocumentType={handleSelectDocumentType}
              onSelectBlueprint={handleSelectBlueprint}
              onObjectiveChange={setNewObjective}
              onCreateSession={handleCreateSession}
              onDeleteSession={setSessionToDelete}
              formatDate={formatDate}
            />

            <div>
                {currentPhase === 'upload' && (
                  <UploadPhase
                    sessionDetail={sessionDetail}
                    isUploadingDocuments={isUploadingDocuments}
                    dragActive={dragActive}
                    onDrag={handleDrag}
                    onDrop={handleDrop}
                    onFileSelect={handleFileSelect}
                    onDeleteDocument={handleDeleteUploadedDocument}
                    onAdvance={handleAdvanceToGeneration}
                    formatFileSize={formatFileSize}
                  />
                )}

                {currentPhase === 'generation' && (() => {
                  const showSplitView = graphVisualization.isVisible && (generationProgress.isGenerating || regeneratingSection !== null);
                  const hasGraphData = graphVisualization.nodes.length > 0;
                  const showPostGenToggle = hasGraphData && !generationProgress.isGenerating;

                  return (
                    <div className={`flex gap-4 ${showSplitView ? '' : 'flex-col'}`}>
                      {/* Coluna principal: GenerationPhase */}
                      <div className={showSplitView ? 'w-1/2 min-w-0' : 'w-full'}>
                        {/* Botão "Ver Pipeline" pós-geração */}
                        {showPostGenToggle && (
                          <button
                            onClick={() => setPipelineDialogOpen(true)}
                            className="mb-3 w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border bg-muted/30 text-sm font-medium hover:bg-muted/50 transition-colors"
                          >
                            <div className="w-2 h-2 rounded-full bg-green-500" />
                            Ver Pipeline Executado
                          </button>
                        )}

                        <GenerationPhase
                          sessionDetail={sessionDetail}
                          blueprintName={selectedBlueprint?.name || 'Blueprint'}
                          sectionNames={sectionNames}
                          sectionFieldsMap={sectionFieldsMap}
                          sectionFieldsValues={sectionFieldsValues}
                          onSectionFieldsChange={(num, vals) =>
                            setSectionFieldsValues((prev) => ({ ...prev, [num]: vals }))
                          }
                          isExtractingFields={isExtractingFields}
                          autoFilledSections={autoFilledSections}
                          subSectionsMap={subSectionsMap}
                          subSectionDecisions={subSectionDecisions}
                          onSubSectionDecisionChange={onSubSectionDecisionChange}
                          selectedSections={selectedSectionsToGenerate}
                          totalSections={totalSections}
                          allSelected={generateAllSections}
                          onToggleSection={toggleSectionToGenerate}
                          onToggleAll={toggleAllSections}
                          generationProgress={generationProgress}
                          expandedSections={expandedSections}
                          onToggleExpand={toggleSectionExpand}
                          onGenerate={handleGenerate}
                          onCancel={cancelGeneration}
                          onReset={resetProgress}
                          onAdvance={() => setCurrentPhase('evaluation')}
                          isLoadingSections={isLoadingSections}
                          onRegenerateSection={(sectionNumber, feedback) => {
                            if (!sessionDetail || !selectedBlueprintId) return;
                            regenerateSectionWithStreaming(
                              sectionNumber,
                              feedback,
                              sessionDetail.objective,
                              selectedBlueprintId,
                              selectedSessionId || undefined,
                              Object.keys(subSectionDecisions).length > 0 ? subSectionDecisions : undefined,
                            ).catch((err) => {
                              toast({
                                title: 'Erro ao regenerar seção',
                                description: err.message,
                                variant: 'destructive',
                              });
                            });
                          }}
                          regeneratingSection={regeneratingSection}
                          onEtpImport={undefined}
                        />
                      </div>

                      {/* Durante geração: Split view em desktop */}
                      {showSplitView && (
                        <>
                          <div className="hidden lg:block w-1/2 min-w-0 h-[600px]">
                            <PipelinePanel graphVisualization={graphVisualization} />
                          </div>
                          <div className="lg:hidden">
                            <button
                              onClick={() => setPipelineDialogOpen(true)}
                              className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg border bg-muted/30 text-sm font-medium hover:bg-muted/50 transition-colors"
                            >
                              <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                              Ver Pipeline
                            </button>
                          </div>
                        </>
                      )}

                      {/* Dialog: mobile durante geração + pós-geração em qualquer tela */}
                      {hasGraphData && (
                        <PipelineDialog
                          open={pipelineDialogOpen}
                          onOpenChange={setPipelineDialogOpen}
                          graphVisualization={graphVisualization}
                        />
                      )}
                    </div>
                  );
                })()}

                {currentPhase === 'evaluation' && (
                  <EvaluationPhase
                    generatedContent={generatedContent}
                    sectionNames={sectionNames}
                    sections={generationProgress.sections}
                    sectionAgentInfo={sectionAgentInfo}
                    sectionRatings={sectionRatings}
                    onRate={handleRate}
                    editingSection={editingSection}
                    editedContent={editedContent}
                    onStartEdit={handleStartEdit}
                    onCancelEdit={handleCancelEdit}
                    onSaveEdit={handleSaveEdit}
                    onEditChange={handleEditChange}
                    savingFeedback={savingFeedback}
                    evaluatedSections={evaluatedSections}
                    onSaveFeedback={handleSaveFeedback}
                    approvalStatus={approvalStatus}
                    onSetApproval={handleSetApproval}
                    onAdvance={handleAdvanceFromEvaluation}
                    updatingDocument={updatingDocument}
                  />
                )}

                {currentPhase === 'analysis' && (
                  <AnalysisPhase
                    generatedContent={generatedContent}
                    sectionNames={sectionNames}
                    sections={generationProgress.sections}
                    generationMetadata={generationMetadata}
                    totalSections={totalSections}
                    approvalStatus={approvalStatus}
                    onSetApproval={handleSetApproval}
                    onAdvance={() => setCurrentPhase('result')}
                  />
                )}

                {currentPhase === 'result' && (
                  <ResultPhase
                    generatedContent={generatedContent}
                    sectionNames={sectionNames}
                    approvalStatus={approvalStatus}
                    generationMetadata={generationMetadata}
                    documentTypeName={documentTypeName}
                    sessionObjective={sessionDetail?.objective || ''}
                    pdfStatus={pdfStatus}
                    onGeneratePdf={handleGeneratePdf}
                    docxStatus={docxStatus}
                    onGenerateDocx={handleGenerateDocx}
                    odtStatus={odtStatus}
                    onGenerateOdt={handleGenerateOdt}
                    onCopyToClipboard={copyToClipboard}
                    sessionId={selectedSessionId}
                    documentTypeCode={sessionDetail?.document_type}
                  />
                )}

                {currentPhase === 'history' && (
                  <HistoryPhase
                    sessionDetail={sessionDetail}
                    totalSections={totalSections}
                    onLoadDocument={handleLoadHistoricalDocument}
                    onDeleteDocument={setDocumentToDelete}
                  />
                )}
            </div>
          </div>
        )}
      </div>

      {/* Delete session dialog */}
      <AlertDialog open={!!sessionToDelete} onOpenChange={() => setSessionToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir sessão?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta ação não pode ser desfeita. Todos os documentos, embeddings e dados serão excluídos.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteSession}
              disabled={isDeletingSession}
              className="bg-red-600 hover:bg-red-700"
            >
              {isDeletingSession ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Trash2 className="h-4 w-4 mr-2" />}
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete document dialog */}
      <AlertDialog open={!!documentToDelete} onOpenChange={() => setDocumentToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir documento?</AlertDialogTitle>
            <AlertDialogDescription>
              O documento e seu PDF serão permanentemente excluídos.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteDocument}
              disabled={isDeletingDocument}
              className="bg-red-600 hover:bg-red-700"
            >
              {isDeletingDocument ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Trash2 className="h-4 w-4 mr-2" />}
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

// ========== TYPES ==========

// Tipo para resposta de busca
export interface SearchResponse {
  results: Array<{
    content: string;
    metadata: Record<string, any>;
    similarity: number;
  }>;
  query: string;
  total_results: number;
}

// Tipos para eventos SSE
export interface SSEEvent {
  event: string;
  [key: string]: any;
}

export interface SectionProgress {
  section: number;
  section_name: string;
  status: 'pending' | 'generating' | 'validating' | 'approved' | 'rejected';
  is_valid?: boolean;
  score?: number;
  content?: string;
  feedback?: string[];
  attempt?: number;
}

export interface GenerationProgress {
  isGenerating: boolean;
  currentSection: number;
  totalSections: number;
  percentage: number;
  sectionsCompleted: number;
  sections: Record<number, SectionProgress>;
  message: string;
  error?: string;
  result?: {
    success: boolean;
    sessionId: string;
    documentId: string;
    pdfUrl: string;
    validSections: number;
    averageScore: number;
    totalTokensUsed: number;
    generationTime?: number;
    generationSessionId?: string;
  };
}

// Tipos para visualização do pipeline (React Flow)
export interface PipelineNode {
  id: string;
  type: string; // 'generate' | 'validate' | 'analyze' | 'refine' | 'finalize'
  label: string;
  section: number;
  section_name: string;
  status: 'pending' | 'running' | 'success' | 'error' | 'rejected';
  step_order?: number;
  position: { x: number; y: number };
  kbs?: Array<{ kb: string; purpose: string; results: number }>;
  llm?: { provider: string; model: string };
  duration_ms?: number;
  score?: number;
}

export interface PipelineEdge {
  id: string;
  source: string;
  target: string;
  animated: boolean;
  type?: string;
}

export interface PipelineLogEntry {
  timestamp: string;
  type: string;
  message: string;
  node?: string;
}

export interface GraphVisualization {
  nodes: PipelineNode[];
  edges: PipelineEdge[];
  log: PipelineLogEntry[];
  activeNode: string | null;
  isVisible: boolean;
}

export interface IntelligentSession {
  id: string;
  objective: string;
  document_type: string;
  status: 'initialized' | 'uploading' | 'processing' | 'generating' | 'validating' | 'formatting' | 'completed' | 'failed';
  error_message?: string;
  created_at: string;
  updated_at?: string;
  documents_count?: number;
}

export interface GeneratedDocument {
  id: string;
  title?: string;
  pdf_url?: string;
  created_at: string;
  metadata?: {
    sections_stats?: {
      valid_count: number;
      average_score: number;
    };
  };
}

export interface SessionDetail extends IntelligentSession {
  documents: UploadedDocument[];
  embedding_stats: {
    documents_processed: number;
    total_chunks: number;
    total_characters: number;
  };
  sections: GeneratedSection[];
  generated_documents?: GeneratedDocument[];
  blueprint_id?: string;
  blueprint_name?: string;
  blueprint?: {
    id: string;
    name: string;
    document_type: string;
    section_count: number;
  };
  generation_session_id?: string | null;
}

export interface UploadedDocument {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  extraction_status: string;
  uploaded_at: string;
}

export interface GeneratedSection {
  section_number: number;
  section_name: string;
  is_valid: boolean;
  created_at: string;
}

export interface ProcessedDocument {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  char_count: number;
  word_count: number;
  num_chunks: number;
  num_embeddings: number;
  warnings: string[];
}

export interface UploadResponse {
  success: boolean;
  processed: ProcessedDocument[];
  total_processed: number;
  errors?: { filename: string; error: string }[];
}

export interface GenerateETPResponse {
  success: boolean;
  requires_manual_review: boolean;
  section_01?: string;
  section_02?: string;
  sections: Record<string, string>;
  validations: Record<string, any>;
  metadata: {
    total_tokens_used: number;
    reasoning_log: string[];
    errors: string[];
    warnings: string[];
  };
}

export interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  stats: {
    sources_count: number;
    total_chunks: number;
    total_characters: number;
  };
  created_at: string;
}

// ========== HOOK ==========

export function useIntelligentAssistant() {
  const queryClient = useQueryClient();

  // Listar sessões do usuário
  const {
    data: sessionsData,
    isLoading: isLoadingSessions,
    error: sessionsError,
    refetch: refetchSessions,
  } = useQuery({
    queryKey: ['intelligent-sessions'],
    queryFn: async () => {
      const response = await api.get<{ sessions: IntelligentSession[] }>(
        '/api/v1/intelligent-assistant/sessions/list/'
      );
      return response.data.sessions;
    },
  });

  // Buscar detalhes de uma sessão
  const useSession = (sessionId: string | null) => {
    return useQuery({
      queryKey: ['intelligent-session', sessionId],
      queryFn: async () => {
        if (!sessionId) return null;
        const response = await api.get<SessionDetail>(
          `/api/v1/intelligent-assistant/sessions/${sessionId}/`
        );
        return response.data;
      },
      enabled: !!sessionId,
    });
  };

  // Criar nova sessão
  const createSessionMutation = useMutation({
    mutationFn: async (data: {
      objective: string;
      document_type?: string;
      blueprint_id?: string;
      parent_etp_session_id?: string | null;
    }) => {
      const response = await api.post<IntelligentSession>(
        '/api/v1/intelligent-assistant/sessions/',
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intelligent-sessions'] });
    },
  });

  // Deletar sessão
  const deleteSessionMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      await api.delete(`/api/v1/intelligent-assistant/sessions/${sessionId}/delete/`);
      return sessionId;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intelligent-sessions'] });
    },
  });

  // Upload de documentos
  const uploadDocumentsMutation = useMutation({
    mutationFn: async ({ sessionId, files }: { sessionId: string; files: File[] }) => {
      const formData = new FormData();
      files.forEach((file) => {
        formData.append('files', file);
      });

      const response = await api.post<UploadResponse>(
        `/api/v1/intelligent-assistant/sessions/${sessionId}/upload/`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 300000, // 5 minutos para upload + processamento
        }
      );
      return response.data;
    },
    onSuccess: (_, { sessionId }) => {
      queryClient.invalidateQueries({ queryKey: ['intelligent-session', sessionId] });
    },
  });

  // Busca semântica na sessão
  const searchSessionMutation = useMutation({
    mutationFn: async ({
      sessionId,
      query,
      n_results = 5,
      min_similarity = 0.7,
    }: {
      sessionId: string;
      query: string;
      n_results?: number;
      min_similarity?: number;
    }) => {
      const response = await api.post<SearchResponse>(
        `/api/v1/intelligent-assistant/sessions/${sessionId}/search/`,
        { query, n_results, min_similarity }
      );
      return response.data;
    },
  });

  // Gerar ETP
  const generateETPMutation = useMutation({
    mutationFn: async ({
      objective,
      sessionId,
    }: {
      objective: string;
      sessionId?: string;
    }) => {
      const response = await api.post<GenerateETPResponse>(
        '/api/v1/intelligent-assistant/generate/',
        {
          objective,
          collection_name: sessionId || 'default',
        },
        {
          timeout: 300000, // 5 minutos
        }
      );
      return response.data;
    },
  });

  // Listar bases de conhecimento
  const {
    data: knowledgeBases,
    isLoading: isLoadingKBs,
  } = useQuery({
    queryKey: ['knowledge-bases'],
    queryFn: async () => {
      const response = await api.get<{ knowledge_bases: KnowledgeBase[] }>(
        '/api/v1/intelligent-assistant/knowledge-bases/'
      );
      return response.data.knowledge_bases;
    },
    staleTime: 5 * 60 * 1000, // knowledge bases raramente mudam
  });

  // Busca na base de conhecimento
  const searchKnowledgeBaseMutation = useMutation({
    mutationFn: async ({
      query,
      knowledge_base = 'all',
      n_results = 5,
    }: {
      query: string;
      knowledge_base?: string;
      n_results?: number;
    }) => {
      const response = await api.post<SearchResponse>(
        '/api/v1/intelligent-assistant/knowledge-bases/search/',
        { query, knowledge_base, n_results }
      );
      return response.data;
    },
  });

  // Estado para geração com streaming
  const [generationProgress, setGenerationProgress] = useState<GenerationProgress>({
    isGenerating: false,
    currentSection: 0,
    totalSections: 0,
    percentage: 0,
    sectionsCompleted: 0,
    sections: {},
    message: '',
  });

  const [graphVisualization, setGraphVisualization] = useState<GraphVisualization>({
    nodes: [],
    edges: [],
    log: [],
    activeNode: null,
    isVisible: false,
  });

  const abortControllerRef = useRef<AbortController | null>(null);
  const currentGsIdRef = useRef<string | null>(null);
  const edgeTraverseTimerRef = useRef<ReturnType<typeof setTimeout>>();

  // ── Batching refs for fast streaming ─────────────────────────────────────
  // Instead of calling setGenerationProgress on every SSE section_chunk (which
  // triggers a React re-render per token), we accumulate incoming text in a
  // ref and flush to React state at ~20 fps.
  const pendingChunksRef = useRef<Record<number, string>>({});
  const chunkFlushTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Clean up flush timer and edge traverse timer on unmount
  useEffect(() => {
    return () => {
      if (chunkFlushTimerRef.current) clearTimeout(chunkFlushTimerRef.current);
      if (edgeTraverseTimerRef.current) clearTimeout(edgeTraverseTimerRef.current);
    };
  }, []);

  /** Append chunk text to the pending buffer and schedule a batched state flush. */
  const appendSectionChunk = useCallback((section: number, chunk: string) => {
    pendingChunksRef.current[section] = (pendingChunksRef.current[section] || '') + chunk;
    if (!chunkFlushTimerRef.current) {
      chunkFlushTimerRef.current = setTimeout(() => {
        const pending = { ...pendingChunksRef.current };
        pendingChunksRef.current = {};
        chunkFlushTimerRef.current = null;
        if (Object.keys(pending).length === 0) return;
        setGenerationProgress(prev => {
          const updated = { ...prev, sections: { ...prev.sections } };
          for (const [secStr, text] of Object.entries(pending)) {
            const sec = Number(secStr);
            updated.sections[sec] = {
              ...updated.sections[sec],
              content: (updated.sections[sec]?.content || '') + text,
              status: updated.sections[sec]?.status === 'pending'
                ? 'generating'
                : updated.sections[sec]?.status || 'generating',
            };
          }
          return updated;
        });
      }, 50); // flush every 50ms = 20 fps
    }
  }, []);

  /** Force-flush any remaining pending chunks (call at stream end / section_content). */
  const flushPendingChunks = useCallback(() => {
    if (chunkFlushTimerRef.current) {
      clearTimeout(chunkFlushTimerRef.current);
      chunkFlushTimerRef.current = null;
    }
    const pending = { ...pendingChunksRef.current };
    pendingChunksRef.current = {};
    if (Object.keys(pending).length === 0) return;
    setGenerationProgress(prev => {
      const updated = { ...prev, sections: { ...prev.sections } };
      for (const [secStr, text] of Object.entries(pending)) {
        const sec = Number(secStr);
        updated.sections[sec] = {
          ...updated.sections[sec],
          content: (updated.sections[sec]?.content || '') + text,
          status: updated.sections[sec]?.status === 'pending'
            ? 'generating'
            : updated.sections[sec]?.status || 'generating',
        };
      }
      return updated;
    });
  }, []);

  // Função para gerar documento com streaming SSE
  const generateETPWithStreaming = useCallback(async (
    objective: string,
    sessionId?: string,
    sections?: number[],
    blueprintId?: string,
    sectionFieldsData?: Record<number, Record<string, any>>,
    onEvent?: (event: SSEEvent) => void,
    subSectionDecisions?: Record<string, { action: string; fields_data: Record<string, any>; feedback?: string }>,
  ): Promise<void> => {
    // Cancelar geração anterior se existir
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Seções a gerar (default: todas - será determinado pelo blueprint)
    const sectionsToGenerate = sections || [];
    const totalSectionsCount = sectionsToGenerate.length;

    // Reset do progresso - inicializar apenas as seções selecionadas
    const initialSections: Record<number, SectionProgress> = {};
    for (const sectionNum of sectionsToGenerate) {
      initialSections[sectionNum] = {
        section: sectionNum,
        section_name: `Seção ${sectionNum}`,
        status: 'pending',
      };
    }

    setGenerationProgress({
      isGenerating: true,
      currentSection: 0,
      totalSections: totalSectionsCount,
      percentage: 0,
      sectionsCompleted: 0,
      sections: initialSections,
      message: 'Iniciando geração...',
    });

    return new Promise(async (resolve, reject) => {
      // Refresh preventivo do token antes de abrir o stream SSE
      // (SSE usa fetch nativo e não tem interceptor de refresh automático)
      let token = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const { data } = await api.post('/api/v1/auth/token/refresh/', { refresh: refreshToken });
          token = data.access;
          localStorage.setItem('access_token', data.access);
        } catch {
          // Se refresh falha, tenta com token atual mesmo
        }
      }
      const baseUrl = (/^https?:\/\//.test(process.env.NEXT_PUBLIC_API_URL || '')) ? process.env.NEXT_PUBLIC_API_URL! : '';

      const body = {
        objective,
        ...(sessionId && { session_id: sessionId }),
        ...(sections && sections.length > 0 && { sections: sections.join(',') }),
        ...(blueprintId && { blueprint_id: blueprintId }),
        ...(sectionFieldsData && Object.keys(sectionFieldsData).length > 0 && { section_fields_data: sectionFieldsData }),
        ...(subSectionDecisions && Object.keys(subSectionDecisions).length > 0 && { sub_section_decisions: subSectionDecisions }),
      };

      const endpoint = '/api/v1/intelligent-assistant/generate-stream/';
      const url = `${baseUrl}${endpoint}`;

      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'text/event-stream',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
        signal: abortController.signal,
      }).then(async (response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error('No reader available');
        }

        let buffer = '';
        let receivedCompleted = false;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6)) as SSEEvent;

                // Callback customizado
                onEvent?.(data);

                // Processar evento
                handleSSEEvent(data);

                // Verificar se completou
                if (data.event === 'completed') {
                  receivedCompleted = true;
                  flushPendingChunks();
                  setGenerationProgress(prev => ({
                    ...prev,
                    isGenerating: false,
                    message: data.message || 'Geração concluída!',
                    result: {
                      success: data.success,
                      sessionId: data.session_id,
                      documentId: data.document_id,
                      pdfUrl: data.pdf_url,
                      validSections: data.valid_sections,
                      averageScore: data.average_score,
                      totalTokensUsed: data.total_tokens_used || 0,
                      generationTime: data.generation_time,
                      generationSessionId: data.generation_session_id,
                    },
                  }));
                  // NÃO chamar invalidateQueries aqui - causa cascading reset de estado
                  resolve();
                } else if (data.event === 'error') {
                  flushPendingChunks();
                  setGenerationProgress(prev => ({
                    ...prev,
                    isGenerating: false,
                    error: data.message,
                    message: `Erro: ${data.message}`,
                  }));
                  reject(new Error(data.message));
                }
              } catch (e) {
                console.error('Error parsing SSE data:', e);
              }
            }
          }
        }

        // Fallback: se o stream fechou sem evento completed, finalizar mesmo assim
        if (!receivedCompleted) {
          flushPendingChunks();
          console.warn('SSE stream closed without completed event - forcing completion');
          setGenerationProgress(prev => ({
            ...prev,
            isGenerating: false,
            message: 'Geração concluída (stream encerrado)',
            result: {
              success: true,
              sessionId: sessionId || '',
              documentId: '',
              pdfUrl: '',
              validSections: prev.sectionsCompleted,
              averageScore: 0,
              totalTokensUsed: 0,
            },
          }));
          resolve();
        }
      }).catch((error) => {
        setGenerationProgress(prev => ({
          ...prev,
          isGenerating: false,
          error: error.message,
          message: `Erro: ${error.message}`,
        }));
        reject(error);
      });
    });
  }, [queryClient, flushPendingChunks]);

  // Processar eventos SSE
  const handleSSEEvent = useCallback((data: SSEEvent) => {
    switch (data.event) {
      case 'section_start':
        setGenerationProgress(prev => ({
          ...prev,
          currentSection: data.section,
          message: `Gerando ${data.section_name}... (tentativa ${data.attempt}/${data.max_attempts})`,
          sections: {
            ...prev.sections,
            [data.section]: {
              ...prev.sections[data.section],
              section_name: data.section_name,
              status: 'generating',
              attempt: data.attempt,
            },
          },
        }));
        break;

      case 'section_generated':
        setGenerationProgress(prev => ({
          ...prev,
          message: `Validando ${data.section_name}...`,
          sections: {
            ...prev.sections,
            [data.section]: {
              ...prev.sections[data.section],
              status: 'validating',
            },
          },
        }));
        break;

      case 'section_validated':
        setGenerationProgress(prev => ({
          ...prev,
          message: data.is_valid
            ? `${data.section_name}: Aprovada (${data.score}%)`
            : `${data.section_name}: Reprovada - regenerando...`,
          sections: {
            ...prev.sections,
            [data.section]: {
              ...prev.sections[data.section],
              status: data.is_valid ? 'approved' : 'rejected',
              is_valid: data.is_valid,
              score: data.score,
              feedback: data.feedback,
            },
          },
        }));
        break;

      case 'section_chunk':
        // Batched streaming: accumulate in ref, flush to state every 50ms (~20 fps)
        appendSectionChunk(data.section, data.chunk);
        break;

      case 'section_content':
        // Conteúdo final completo (sobrescreve chunks parciais)
        // Force-flush any pending chunks first so final content wins
        flushPendingChunks();
        setGenerationProgress(prev => ({
          ...prev,
          sections: {
            ...prev.sections,
            [data.section]: {
              ...prev.sections[data.section],
              content: data.content,
              ...(data.feedback ? { feedback: data.feedback } : {}),
              ...(data.score !== undefined ? { score: data.score } : {}),
              ...(data.is_valid !== undefined ? { is_valid: data.is_valid } : {}),
            },
          },
        }));
        break;

      case 'progress':
        setGenerationProgress(prev => ({
          ...prev,
          currentSection: data.current_section,
          percentage: data.percentage,
          sectionsCompleted: data.sections_completed,
        }));
        break;

      case 'saving':
      case 'finalizing':
        setGenerationProgress(prev => ({
          ...prev,
          message: data.message,
        }));
        break;

      case 'generation_session_started':
        currentGsIdRef.current = data.generation_session_id;
        break;

      // === Eventos do Pipeline (Visualização React Flow) ===

      case 'graph_structure':
        setGraphVisualization(prev => ({
          ...prev,
          nodes: (data.nodes || []).map((n: any) => ({ ...n, status: 'pending', kbs: [], llm: null })),
          edges: (data.edges || []).map((e: any) => ({ ...e, animated: false })),
          log: [],
          activeNode: null,
          isVisible: true,
        }));
        break;

      case 'node_enter': {
        const now = new Date().toLocaleTimeString('pt-BR');
        setGraphVisualization(prev => ({
          ...prev,
          activeNode: data.node,
          nodes: prev.nodes.map(n =>
            n.id === data.node ? { ...n, status: 'running' as const, kbs: [], llm: null } : n
          ),
          edges: prev.edges.map(e =>
            e.target === data.node ? { ...e, animated: true } : e
          ),
          log: [...prev.log, {
            timestamp: now,
            type: 'node_enter',
            message: `${data.agent} iniciou (${data.type})`,
            node: data.node,
          }],
        }));
        break;
      }

      case 'kb_query': {
        const now = new Date().toLocaleTimeString('pt-BR');
        setGraphVisualization(prev => ({
          ...prev,
          nodes: prev.nodes.map(n =>
            n.id === data.node
              ? { ...n, kbs: [...(n.kbs || []), { kb: data.kb, purpose: data.purpose, results: data.results }] }
              : n
          ),
          log: [...prev.log, {
            timestamp: now,
            type: 'kb_query',
            message: `KB "${data.kb}" (${data.purpose}): ${data.results} chunks`,
            node: data.node,
          }],
        }));
        break;
      }

      case 'llm_call': {
        const now = new Date().toLocaleTimeString('pt-BR');
        setGraphVisualization(prev => ({
          ...prev,
          nodes: prev.nodes.map(n =>
            n.id === data.node ? { ...n, llm: { provider: data.provider, model: data.model } } : n
          ),
          log: [...prev.log, {
            timestamp: now,
            type: 'llm_call',
            message: `Chamando ${data.model} (${data.provider})...`,
            node: data.node,
          }],
        }));
        break;
      }

      case 'node_exit': {
        const now = new Date().toLocaleTimeString('pt-BR');
        const exitStatus = data.status === 'success' ? 'success' as const
          : data.status === 'rejected' ? 'rejected' as const
          : 'error' as const;
        setGraphVisualization(prev => ({
          ...prev,
          activeNode: null,
          nodes: prev.nodes.map(n =>
            n.id === data.node
              ? { ...n, status: exitStatus, duration_ms: data.duration_ms, score: data.score }
              : n
          ),
          edges: prev.edges.map(e =>
            e.target === data.node ? { ...e, animated: false } : e
          ),
          log: [...prev.log, {
            timestamp: now,
            type: 'node_exit',
            message: data.status === 'success'
              ? `Concluído em ${(data.duration_ms / 1000).toFixed(1)}s${data.score ? ` (score: ${data.score})` : ''}`
              : `Erro: ${data.error || 'reprovado'}`,
            node: data.node,
          }],
        }));
        break;
      }

      case 'edge_traverse': {
        setGraphVisualization(prev => ({
          ...prev,
          edges: prev.edges.map(e =>
            e.source === data.source && e.target === data.target
              ? { ...e, animated: true }
              : e
          ),
        }));
        // Desanimar após 1.5s
        if (edgeTraverseTimerRef.current) clearTimeout(edgeTraverseTimerRef.current);
        edgeTraverseTimerRef.current = setTimeout(() => {
          setGraphVisualization(prev => ({
            ...prev,
            edges: prev.edges.map(e =>
              e.source === data.source && e.target === data.target
                ? { ...e, animated: false }
                : e
            ),
          }));
        }, 1500);
        break;
      }

      case 'sub_section_start': {
        const now = new Date().toLocaleTimeString('pt-BR');
        const subNodeId = data.sub_node;
        setGraphVisualization(prev => ({
          ...prev,
          activeNode: subNodeId,
          nodes: prev.nodes.map(n =>
            n.id === subNodeId ? { ...n, status: 'running' as const } : n
          ),
          edges: prev.edges.map(e =>
            e.target === subNodeId ? { ...e, animated: true } : e
          ),
          log: [...prev.log, {
            timestamp: now,
            type: 'sub_section_start',
            message: `${data.sub_number} ${data.sub_name} - ${data.action === 'generate' ? `gerando (${data.agent_name})` : 'texto padrão'}`,
            node: subNodeId,
          }],
        }));
        break;
      }

      case 'sub_section_complete': {
        const now = new Date().toLocaleTimeString('pt-BR');
        const subNodeId = data.sub_node;
        const subStatus = data.action === 'generate' ? 'success' as const : 'success' as const;
        setGraphVisualization(prev => ({
          ...prev,
          activeNode: null,
          nodes: prev.nodes.map(n =>
            n.id === subNodeId
              ? { ...n, status: subStatus, content_length: data.content_length }
              : n
          ),
          edges: prev.edges.map(e =>
            e.target === subNodeId ? { ...e, animated: false } : e
          ),
          log: [...prev.log, {
            timestamp: now,
            type: 'sub_section_complete',
            message: `${data.sub_number} - ${data.action === 'generate' ? `gerado (${data.content_length} chars)` : 'texto padrão'}`,
            node: subNodeId,
          }],
        }));
        break;
      }
    }
  }, [appendSectionChunk, flushPendingChunks]);

  // Cancelar geração - notifica backend e aborta o fetch
  const cancelGeneration = useCallback(() => {
    const gsId = currentGsIdRef.current;
    if (gsId) {
      api.post(
        `/api/v1/intelligent-assistant/generation-sessions/${gsId}/cancel/`
      ).catch(() => {});
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    currentGsIdRef.current = null;
    setGenerationProgress(prev => ({
      ...prev,
      isGenerating: false,
      message: 'Geração cancelada',
    }));
  }, []);

  // Reset do progresso
  const resetProgress = useCallback(() => {
    setGenerationProgress({
      isGenerating: false,
      currentSection: 0,
      totalSections: 0,
      percentage: 0,
      sectionsCompleted: 0,
      sections: {},
      message: '',
    });
    setGraphVisualization({
      nodes: [],
      edges: [],
      log: [],
      activeNode: null,
      isVisible: false,
    });
  }, []);

  // Carregar uma GenerationSession completa do backend (source of truth)
  const loadGenerationSession = useCallback(async (generationSessionId: string) => {
    try {
      const response = await api.get(
        `/api/v1/intelligent-assistant/generation-sessions/${generationSessionId}/`
      );
      const sessionData = response.data;

      // Reconstruir sections a partir de section_generations do backend
      const sections: Record<number, SectionProgress> = {};
      const content: Record<string, string> = {};

      for (const sg of sessionData.section_generations || []) {
        const num = sg.section_number;
        const statusMap: Record<string, SectionProgress['status']> = {
          completed: sg.is_valid ? 'approved' : 'rejected',
          validated: sg.is_valid ? 'approved' : 'rejected',
          generating: 'generating',
          validating: 'validating',
          pending: 'pending',
          failed: 'rejected',
          skipped: 'pending',
        };

        sections[num] = {
          section: num,
          section_name: sg.section_name || `Seção ${num}`,
          status: statusMap[sg.status] || 'pending',
          is_valid: sg.is_valid,
          score: sg.validation_score,
          content: sg.content || undefined,
          feedback: sg.validation_feedback
            ? sg.validation_feedback.split('\n').filter(Boolean)
            : sg.validation_errors?.length > 0
              ? sg.validation_errors
              : undefined,
        };

        if (sg.content) {
          const sectionKey = `section_${String(num).padStart(2, '0')}`;
          content[sectionKey] = sg.content;
        }
      }

      // Atualizar generationProgress com dados do backend
      const totalSections = sessionData.total_selected_sections || Object.keys(sections).length;
      const completedCount = sessionData.completed_sections_count || 0;

      setGenerationProgress(prev => ({
        ...prev,
        isGenerating: false,
        totalSections,
        sectionsCompleted: completedCount,
        percentage: sessionData.progress_percentage || 100,
        sections,
        message: 'Geração concluída!',
        result: prev.result || {
          success: sessionData.status === 'completed',
          sessionId: sessionData.id,
          documentId: sessionData.latest_document_id || '',
          pdfUrl: '',
          validSections: completedCount,
          averageScore: 0,
          totalTokensUsed: 0,
          generationSessionId: sessionData.id,
        },
      }));

      // Carregar pipeline_graph se disponível
      if (sessionData.pipeline_graph && sessionData.pipeline_graph.nodes?.length > 0) {
        const pg = sessionData.pipeline_graph;
        setGraphVisualization({
          nodes: (pg.nodes || []).map((n: any) => ({
            ...n,
            kbs: n.kbs || [],
            llm: n.llm || null,
          })),
          edges: (pg.edges || []).map((e: any) => ({ ...e, animated: false })),
          log: pg.log || [],
          activeNode: null,
          isVisible: true,
        });
      }

      return { sessionData, content, sections };
    } catch (error) {
      console.error('Erro ao carregar GenerationSession:', error);
      return null;
    }
  }, []);

  // Estado para rastrear qual seção está sendo regenerada
  const [regeneratingSection, setRegeneratingSection] = useState<number | null>(null);

  // Regenerar uma seção específica com feedback do usuário
  const regenerateSectionWithStreaming = useCallback(async (
    sectionNumber: number,
    feedback: string,
    objective: string,
    blueprintId: string,
    sessionId?: string,
    subSectionDecisions?: Record<string, { action: string; fields_data: Record<string, any>; feedback?: string }>,
  ): Promise<void> => {
    setRegeneratingSection(sectionNumber);

    // Marcar seção como gerando e limpar conteúdo anterior (para streaming limpo)
    setGenerationProgress(prev => ({
      ...prev,
      sections: {
        ...prev.sections,
        [sectionNumber]: {
          ...prev.sections[sectionNumber],
          status: 'generating',
          content: '',
        },
      },
    }));

    // Refresh preventivo do token
    let token = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      try {
        const { data } = await api.post('/api/v1/auth/token/refresh/', { refresh: refreshToken });
        token = data.access;
        localStorage.setItem('access_token', data.access);
      } catch {
        // Se refresh falha, tenta com token atual
      }
    }

    const baseUrl = (/^https?:\/\//.test(process.env.NEXT_PUBLIC_API_URL || '')) ? process.env.NEXT_PUBLIC_API_URL! : '';
    const body = {
      blueprint_id: blueprintId,
      section_number: sectionNumber,
      feedback,
      objective,
      ...(sessionId && { session_id: sessionId }),
      ...(subSectionDecisions && Object.keys(subSectionDecisions).length > 0 && { sub_section_decisions: subSectionDecisions }),
    };

    const url = `${baseUrl}/api/v1/intelligent-assistant/regenerate-section-stream/`;

    return new Promise(async (resolve, reject) => {
      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'text/event-stream',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
        signal: abortController.signal,
      }).then(async (response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error('No reader available');
        }

        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6)) as SSEEvent;

                // Processar eventos relevantes para atualizar apenas a seção
                switch (data.event) {
                  case 'section_chunk':
                    // Batched streaming: accumulate in ref, flush every 50ms
                    appendSectionChunk(data.section, data.chunk);
                    break;

                  case 'section_content':
                    flushPendingChunks();
                    setGenerationProgress(prev => ({
                      ...prev,
                      sections: {
                        ...prev.sections,
                        [data.section]: {
                          ...prev.sections[data.section],
                          content: data.content,
                          ...(data.feedback ? { feedback: data.feedback } : {}),
                          ...(data.score !== undefined ? { score: data.score } : {}),
                          ...(data.is_valid !== undefined ? { is_valid: data.is_valid } : {}),
                        },
                      },
                    }));
                    break;

                  case 'section_validated':
                    setGenerationProgress(prev => ({
                      ...prev,
                      sections: {
                        ...prev.sections,
                        [data.section]: {
                          ...prev.sections[data.section],
                          status: data.is_valid ? 'approved' : 'rejected',
                          is_valid: data.is_valid,
                          score: data.score,
                          feedback: data.feedback,
                        },
                      },
                    }));
                    break;

                  case 'completed':
                    flushPendingChunks();
                    setRegeneratingSection(null);
                    // Invalidar cache do useSession para que markdown_content reflita a regeneração
                    if (sessionId) {
                      queryClient.invalidateQueries({ queryKey: ['intelligent-session', sessionId] });
                    }
                    resolve();
                    break;

                  case 'error':
                    flushPendingChunks();
                    setRegeneratingSection(null);
                    // Restaurar status anterior da seção
                    setGenerationProgress(prev => ({
                      ...prev,
                      sections: {
                        ...prev.sections,
                        [sectionNumber]: {
                          ...prev.sections[sectionNumber],
                          status: prev.sections[sectionNumber]?.is_valid ? 'approved' : 'rejected',
                        },
                      },
                    }));
                    reject(new Error(data.message));
                    break;

                  default:
                    // Delegar eventos de grafo (graph_structure, node_enter, kb_query, llm_call, node_exit, edge_traverse)
                    handleSSEEvent(data);
                    break;
                }
              } catch (e) {
                console.error('Error parsing SSE data:', e);
              }
            }
          }
        }

        // Se o stream terminou sem evento completed
        setRegeneratingSection(null);
        resolve();
      }).catch((error) => {
        setRegeneratingSection(null);
        reject(error);
      });
    });
  }, [handleSSEEvent, appendSectionChunk, flushPendingChunks]);

  return {
    // Data
    sessions: sessionsData || [],
    knowledgeBases: knowledgeBases || [],

    // Loading states
    isLoadingSessions,
    isLoadingKBs,
    isCreatingSession: createSessionMutation.isPending,
    isDeletingSession: deleteSessionMutation.isPending,
    isUploadingDocuments: uploadDocumentsMutation.isPending,
    isSearching: searchSessionMutation.isPending,
    isGeneratingETP: generateETPMutation.isPending,
    isSearchingKB: searchKnowledgeBaseMutation.isPending,

    // Errors
    sessionsError,

    // Actions
    createSession: createSessionMutation.mutateAsync,
    deleteSession: deleteSessionMutation.mutateAsync,
    uploadDocuments: uploadDocumentsMutation.mutateAsync,
    searchSession: searchSessionMutation.mutateAsync,
    generateETP: generateETPMutation.mutateAsync,
    searchKnowledgeBase: searchKnowledgeBaseMutation.mutateAsync,
    refetchSessions,

    // Streaming
    generateETPWithStreaming,
    generationProgress,
    cancelGeneration,
    resetProgress,
    loadGenerationSession,

    // Pipeline Visualization (React Flow)
    graphVisualization,

    // Regeneração de seção
    regenerateSectionWithStreaming,
    regeneratingSection,

    // Hooks
    useSession,
  };
}

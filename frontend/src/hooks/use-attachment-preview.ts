'use client';

import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

// ─── Types ─────────────────────────────────────────────────────────

export interface AttachmentPreviewSection {
  section_number: number;
  section_name: string;
  content: string;
}

export interface AttachmentPreview {
  session_id: string;
  document_type: string;
  document_type_display: string;
  objective: string;
  status: string;
  blueprint_name: string | null;
  has_generated_doc: boolean;
  generated_doc_id: string | null;
  title: string;
  /** Secoes ja formatadas em HTML (vindo de SectionGeneration.content). */
  sections: AttachmentPreviewSection[];
  /** URL publica R2 do PDF, se ja gerado e enviado. */
  pdf_url: string | null;
  /** URL publica R2 do DOCX, se ja gerado e enviado. */
  docx_url: string | null;
  pdf_generated: boolean;
  docx_generated: boolean;
  generated_at: string | null;
  updated_at: string | null;
}

// ─── Hook ──────────────────────────────────────────────────────────

/**
 * Busca o preview consolidado de uma sessao (anexo, ETP, TR, etc.) para o
 * modal de visualizacao no ResultPhase. Retorna sections com HTML pronto +
 * URLs do R2, sem precisar montar URL com phase/doc/generation_session.
 *
 * Endpoint: GET /api/v1/intelligent-assistant/sessions/<id>/preview/
 *
 * @param sessionId UUID da sessao a visualizar (anexo). Quando null/undefined
 *                  ou enabled=false, query nao dispara.
 * @param enabled flag para so disparar quando o modal estiver aberto
 *                (evita prefetch desnecessario quando o usuario nao clicou).
 */
export function useAttachmentPreview(
  sessionId: string | null | undefined,
  enabled: boolean = true,
) {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['attachment-preview', sessionId],
    enabled: !!sessionId && enabled,
    staleTime: 30_000,
    queryFn: async () => {
      const response = await api.get<AttachmentPreview>(
        `/api/v1/intelligent-assistant/sessions/${sessionId}/preview/`,
      );
      return response.data;
    },
  });

  return {
    preview: data ?? null,
    isLoading,
    error,
    refetch,
  };
}

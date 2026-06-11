'use client';

import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

// ─── Types ─────────────────────────────────────────────────────────

export interface SessionAttachment {
  id: string;
  objective: string;
  objective_preview: string;
  document_type: string;
  document_type_display: string;
  blueprint_name: string | null;
  status: string;
  created_at: string;
}

interface SessionAttachmentsResponse {
  parent_session_id: string;
  parent_document_type: string;
  attachments: SessionAttachment[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

// ─── Hook ──────────────────────────────────────────────────────────

/**
 * Hook que lista anexos vinculados a uma sessao pai, paginada.
 *
 * Endpoint: GET /api/v1/intelligent-assistant/sessions/<id>/attachments/
 *
 * @param sessionId UUID da sessao pai. Quando ausente/null, query nao dispara.
 * @param page indice da pagina (1-based, default 1)
 * @param pageSize itens por pagina (default 10, max 50 no backend)
 */
export function useSessionAttachments(
  sessionId: string | null | undefined,
  page: number = 1,
  pageSize: number = 10,
) {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['session-attachments', sessionId, page, pageSize],
    enabled: !!sessionId,
    queryFn: async () => {
      const response = await api.get<SessionAttachmentsResponse>(
        `/api/v1/intelligent-assistant/sessions/${sessionId}/attachments/`,
        { params: { page, page_size: pageSize } },
      );
      return response.data;
    },
  });

  return {
    attachments: data?.attachments ?? [],
    parentDocumentType: data?.parent_document_type ?? null,
    page: data?.page ?? page,
    pageSize: data?.page_size ?? pageSize,
    total: data?.total ?? 0,
    totalPages: data?.total_pages ?? 0,
    hasNext: data?.has_next ?? false,
    hasPrevious: data?.has_previous ?? false,
    isLoading,
    error,
    refetch,
  };
}

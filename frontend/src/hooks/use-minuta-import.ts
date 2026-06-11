'use client';

import { useQuery, useMutation } from '@tanstack/react-query';
import api from '@/lib/api';

// ─── Types ───

export interface TrSessionForImport {
  id: string;
  objective: string;
  status: string;
  blueprint_name: string;
  created_at: string;
  progress_percentage: number;
  completed_sections: number;
  total_sections: number;
}

export interface SubSectionData {
  sub_number: string;
  sub_name: string;
  sub_key: string;
  content: string;
  is_required: boolean;
  has_content: boolean;
  source_type: 'tr_sub_section' | 'tr_section' | 'fixed' | 'empty';
}

export interface MinutaImportedSection {
  minuta_section_number: number;
  minuta_section_id: string;
  minuta_section_name: string;
  import_type: string;
  tr_source_label: string;
  tr_sections_used: number[];
  imported_content: string;
  fixed_content: string;
  has_content: boolean;
  has_fixed_content: boolean;
  has_sub_sections: boolean;
  sub_sections?: SubSectionData[];
  has_section_fields: boolean;
  needs_ai: boolean;
  needs_input: boolean;
  section_fields: any[];
}

export interface MinutaImportStats {
  total_sections: number;
  imported_from_tr: number;
  needs_ai_generation: number;
  needs_manual_input: number;
  ready_to_use: number;
}

export interface MinutaImportResult {
  sections: MinutaImportedSection[];
  stats: MinutaImportStats;
  tr_session_id: string;
  tr_objective: string;
}

interface MinutaBlueprint {
  id: string;
  name: string;
  document_type_code: string;
  section_count: number;
  is_default: boolean;
}

// ─── Hook ───

export function useMinutaImport(documentTypeCode: string = 'minuta_contrato') {
  // Buscar sessões TR disponíveis para importação
  const {
    data: trSessionsData,
    isLoading: isLoadingSessions,
    error: sessionsError,
  } = useQuery({
    queryKey: ['minuta-tr-sessions'],
    queryFn: async () => {
      const response = await api.get<{ tr_sessions: TrSessionForImport[] }>(
        '/api/v1/intelligent-assistant/minuta/tr-sessions/'
      );
      return response.data;
    },
  });

  // Buscar blueprints disponíveis filtrados por tipo de documento
  const {
    data: minutaBlueprintsData,
    isLoading: isLoadingBlueprints,
  } = useQuery({
    queryKey: ['minuta-blueprints', documentTypeCode],
    queryFn: async () => {
      const response = await api.get<{ blueprints: MinutaBlueprint[] }>(
        '/api/v1/intelligent-assistant/blueprints/',
        { params: { active_only: 'true' } }
      );
      const minutaBlueprints = response.data.blueprints.filter(
        (b) => b.document_type_code === documentTypeCode
      );
      return minutaBlueprints;
    },
  });

  // Mutation: importar TR para Minuta
  const importMutation = useMutation({
    mutationFn: async ({
      trSessionId,
      minutaBlueprintId,
    }: {
      trSessionId: string;
      minutaBlueprintId: string;
    }) => {
      const response = await api.get<{
        sections: MinutaImportedSection[];
        stats: MinutaImportStats;
        tr_session_id: string;
        tr_objective: string;
      }>(
        `/api/v1/intelligent-assistant/minuta/import/${trSessionId}/`,
        { params: { minuta_blueprint_id: minutaBlueprintId } }
      );
      return response.data as MinutaImportResult;
    },
  });

  const trSessions = trSessionsData?.tr_sessions || [];
  const minutaBlueprints = minutaBlueprintsData || [];
  const defaultMinutaBlueprint =
    minutaBlueprints.find((b) => b.is_default) || minutaBlueprints[0] || null;

  return {
    // TR Sessions
    trSessions,
    isLoadingSessions,
    sessionsError,

    // Blueprints
    minutaBlueprints,
    defaultMinutaBlueprint,
    defaultEditalBlueprint: defaultMinutaBlueprint,
    isLoadingBlueprints,

    // Import
    importTr: importMutation.mutateAsync,
    isImporting: importMutation.isPending,
    importError: importMutation.error,
    importResult: importMutation.data || null,
  };
}

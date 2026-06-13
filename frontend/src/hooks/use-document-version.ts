'use client';

import { useState, useCallback } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

export interface DocumentSection {
  id: string;
  title: string;
  content: string;
}

export interface DocumentVersion {
  version_id: string;
  version_number: string;
  version_type: 'major' | 'minor' | 'patch';
  created_at: string;
  created_by: number;
  created_by_name?: string;
  change_summary: string;
  tags: string[];
  parent_version?: string;
  sections_data?: DocumentSection[];
  section_hashes?: Record<string, string>;
}

export interface VersionDiff {
  old_version_id: string;
  new_version_id: string;
  summary: {
    added: number;
    removed: number;
    modified: number;
    unchanged: number;
  };
  similarity_score: number;
  changes: Array<{
    section_id: string;
    section_title: string;
    change_type: 'added' | 'removed' | 'modified' | 'unchanged';
    old_content?: string;
    new_content?: string;
    diff?: string[];
  }>;
  semantic_changes: Array<{
    section_id: string;
    paragraph_delta: number;
    citation_delta: number;
    content_delta: number;
    added_citations: boolean;
    expanded: boolean;
    condensed: boolean;
  }>;
}

export interface CreateVersionParams {
  sections: DocumentSection[];
  change_summary?: string;
  version_type?: 'major' | 'minor' | 'patch';
  tags?: string[];
}

export interface RollbackParams {
  sections?: string[];
  create_new_version?: boolean;
}

/**
 * Hook para versionamento semântico de documentos
 *
 * @example
 * const {
 *   versions,
 *   isLoading,
 *   createVersion,
 *   getDiff,
 *   rollback,
 * } = useDocumentVersion(documentId);
 */
export function useDocumentVersion(documentId: string | null) {
  const queryClient = useQueryClient();
  const [selectedVersion, setSelectedVersion] = useState<DocumentVersion | null>(null);
  const [diffResult, setDiffResult] = useState<VersionDiff | null>(null);

  // Query para listar versões
  const { data: versions = [], isLoading: loadingVersions } = useQuery({
    queryKey: ['document-versions', documentId],
    queryFn: async () => {
      if (!documentId) return [];
      const response = await api.get(`/api/v1/documents/items/${documentId}/versions/`);
      return response.data.results || [];
    },
    enabled: !!documentId,
  });

  // Mutation para criar versão
  const createVersionMutation = useMutation({
    mutationFn: async (params: CreateVersionParams) => {
      if (!documentId) throw new Error('Document ID required');
      const response = await api.post(
        `/api/v1/documents/items/${documentId}/versions/create/`,
        params
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document-versions', documentId] });
    },
  });

  // Mutation para rollback
  const rollbackMutation = useMutation({
    mutationFn: async ({ versionId, params }: { versionId: string; params?: RollbackParams }) => {
      if (!documentId) throw new Error('Document ID required');
      const response = await api.post(
        `/api/v1/documents/items/${documentId}/versions/${versionId}/rollback/`,
        params
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document-versions', documentId] });
      queryClient.invalidateQueries({ queryKey: ['document-detail', documentId] });
    },
  });

  const createVersion = useCallback((params: CreateVersionParams) => {
    createVersionMutation.mutate(params);
  }, [createVersionMutation]);

  const rollback = useCallback((versionId: string, params?: RollbackParams) => {
    rollbackMutation.mutate({ versionId, params });
  }, [rollbackMutation]);

  const getDiff = useCallback(async (oldVersionId: string, newVersionId: string) => {
    if (!documentId) return null;
    const response = await api.get(
      `/api/v1/documents/items/${documentId}/versions/diff/`,
      {
        params: {
          old_version: oldVersionId,
          new_version: newVersionId,
          include_semantic: true,
        },
      }
    );
    setDiffResult(response.data);
    return response.data as VersionDiff;
  }, [documentId]);

  return {
    // Estado
    versions,
    selectedVersion,
    diffResult,

    // Loading
    isLoading: loadingVersions,
    isCreating: createVersionMutation.isPending,
    isRollingBack: rollbackMutation.isPending,

    // Ações
    createVersion,
    rollback,
    getDiff,
    setSelectedVersion,
    clearDiff: () => setDiffResult(null),
    refetch: () => queryClient.invalidateQueries({ queryKey: ['document-versions', documentId] }),
  };
}

/**
 * Utilitários para formatar dados de versão
 */
export function formatVersionType(type: string): string {
  const labels: Record<string, string> = {
    major: 'Major',
    minor: 'Minor',
    patch: 'Patch',
  };
  return labels[type] || type;
}

export function getVersionTypeColor(type: string): string {
  switch (type) {
    case 'major':
      return 'bg-red-100 text-red-700 border-red-300';
    case 'minor':
      return 'bg-yellow-100 text-yellow-700 border-yellow-300';
    case 'patch':
      return 'bg-green-100 text-green-700 border-green-300';
    default:
      return 'bg-gray-100 text-gray-700 border-gray-300';
  }
}

export function getChangeTypeIcon(changeType: string): string {
  switch (changeType) {
    case 'added':
      return '+';
    case 'removed':
      return '-';
    case 'modified':
      return '±';
    default:
      return '=';
  }
}

export function getChangeTypeColor(changeType: string): string {
  switch (changeType) {
    case 'added':
      return 'text-green-600 bg-green-50';
    case 'removed':
      return 'text-red-600 bg-red-50';
    case 'modified':
      return 'text-yellow-600 bg-yellow-50';
    default:
      return 'text-gray-600 bg-gray-50';
  }
}

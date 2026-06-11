'use client';

import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

/**
 * Tipo de documento retornado pela API.
 */
export interface DocumentType {
  id: string;
  code: string;
  name: string;
  short_name: string;
  description: string;
  category: string;
  category_display: string;
  icon: string;
  color: string;
  legal_basis: string;
  display_order: number;
}

/**
 * Tipo de documento agrupado por categoria.
 */
export interface DocumentTypesByCategory {
  category: string;
  category_display: string;
  types: DocumentType[];
}

/**
 * Hook para buscar tipos de documento da API.
 *
 * Substitui o hardcode de DOCUMENT_TYPES no frontend.
 * Os tipos são gerenciados via admin no backend.
 */
export function useDocumentTypes(category?: string) {
  // Listar todos os tipos de documento
  const {
    data: documentTypesData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['document-types', category],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (category) {
        params.category = category;
      }

      const response = await api.get<DocumentType[]>(
        '/api/v1/core/document-types/',
        { params }
      );
      // Endpoint sem paginação retorna array direto
      const data = response.data;
      return Array.isArray(data) ? data : [];
    },
    staleTime: 1000 * 60 * 30, // 30 minutos - tipos raramente mudam
  });

  // Garantir que documentTypes é sempre um array
  const documentTypes = Array.isArray(documentTypesData) ? documentTypesData : [];

  // Buscar tipos agrupados por categoria
  const {
    data: typesByCategory,
    isLoading: isLoadingByCategory,
  } = useQuery({
    queryKey: ['document-types-by-category'],
    queryFn: async () => {
      const response = await api.get<DocumentTypesByCategory[]>(
        '/api/v1/core/document-types/by_category/'
      );
      return response.data;
    },
    staleTime: 1000 * 60 * 30,
  });

  // Buscar escolhas simples (para selects)
  const {
    data: choices,
    isLoading: isLoadingChoices,
  } = useQuery({
    queryKey: ['document-types-choices'],
    queryFn: async () => {
      const response = await api.get<{ value: string; label: string }[]>(
        '/api/v1/core/document-types/choices/'
      );
      return response.data;
    },
    staleTime: 1000 * 60 * 30,
  });

  // Helper: buscar tipo por código
  const getByCode = (code: string): DocumentType | undefined => {
    return documentTypes?.find(dt => dt.code === code);
  };

  // Helper: obter nome exibível
  const getDisplayName = (code: string): string => {
    const dt = getByCode(code);
    return dt?.short_name || dt?.name || code;
  };

  // Helper: obter nome completo
  const getFullName = (code: string): string => {
    const dt = getByCode(code);
    return dt?.name || code;
  };

  // Helper: obter ícone
  const getIcon = (code: string): string => {
    const dt = getByCode(code);
    return dt?.icon || 'FileText';
  };

  return {
    // Data
    documentTypes,
    typesByCategory: typesByCategory || [],
    choices: choices || [],

    // States
    isLoading,
    isLoadingByCategory,
    isLoadingChoices,
    error,

    // Helpers
    getByCode,
    getDisplayName,
    getFullName,
    getIcon,
  };
}

/**
 * Hook simplificado para selecionar tipo de documento em formulários.
 */
export function useDocumentTypeSelect() {
  const { documentTypes, isLoading, choices } = useDocumentTypes();

  return {
    options: documentTypes.map(dt => ({
      value: dt.code,
      label: dt.short_name || dt.name,
      fullName: dt.name,
      description: dt.description,
      icon: dt.icon,
      category: dt.category,
    })),
    choices, // Para selects simples (value/label)
    isLoading,
  };
}

/**
 * Hook para mapeamento de códigos para nomes (para componentes que só têm o código).
 */
export function useDocumentTypeLabels() {
  const { documentTypes, isLoading } = useDocumentTypes();

  // Mapa código -> nome curto
  const labels: Record<string, string> = {};
  // Mapa código -> nome completo
  const fullNames: Record<string, string> = {};
  // Mapa código -> ícone
  const icons: Record<string, string> = {};

  documentTypes.forEach(dt => {
    labels[dt.code] = dt.short_name || dt.name;
    fullNames[dt.code] = dt.name;
    icons[dt.code] = dt.icon;
  });

  return {
    labels,
    fullNames,
    icons,
    isLoading,
  };
}

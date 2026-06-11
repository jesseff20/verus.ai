'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

// ── Types ──

export interface ConsentTerm {
  id: string;
  title: string;
  version: string;
  content: string;
  purpose: string;
  purpose_display: string;
  is_active: boolean;
  created_by: string | null;
  created_by_name: string | null;
  created_at: string;
}

export interface ConsentRecord {
  id: string;
  client: string;
  client_name: string | null;
  consent_term: string;
  consent_term_title: string | null;
  granted: boolean;
  ip_address: string | null;
  granted_at: string;
  revoked_at: string | null;
}

export interface DataProcessingActivity {
  id: string;
  name: string;
  purpose: string;
  legal_basis: string;
  legal_basis_display: string;
  data_categories: string[];
  retention_period: string;
  shared_with: string[];
  risk_level: string;
  risk_level_display: string;
  is_active: boolean;
  created_at: string;
}

export interface DataSubjectRequest {
  id: string;
  client: string;
  client_name: string | null;
  request_type: string;
  request_type_display: string;
  description: string;
  status: string;
  status_display: string;
  response: string;
  requested_at: string;
  responded_at: string | null;
}

interface AIGenerateResponse {
  content: string;
  model: string;
}

/** Paginated response from DRF PageNumberPagination */
interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/**
 * Extracts an array from API response, handling both:
 * - Paginated DRF responses: { results: [...] }
 * - Direct array responses: [...]
 */
function extractResults<T>(data: T[] | PaginatedResponse<T> | undefined | null): T[] {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  if (typeof data === 'object' && 'results' in data && Array.isArray(data.results)) {
    return data.results;
  }
  return [];
}

const BASE = '/api/v1/auth/lgpd';

// ── Hook ──

export function useLGPD() {
  const queryClient = useQueryClient();

  // ── Consent Terms ──

  const consentTermsQuery = useQuery({
    queryKey: ['lgpd', 'consent-terms'],
    queryFn: async () => {
      const res = await api.get<ConsentTerm[] | PaginatedResponse<ConsentTerm>>(`${BASE}/consent-terms/`);
      return extractResults(res.data);
    },
    retry: 1,
  });

  const createConsentTerm = useMutation({
    mutationFn: async (data: Partial<ConsentTerm>) => {
      const res = await api.post(`${BASE}/consent-terms/`, data);
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lgpd', 'consent-terms'] }),
  });

  const updateConsentTerm = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<ConsentTerm> }) => {
      const res = await api.patch(`${BASE}/consent-terms/${id}/`, data);
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lgpd', 'consent-terms'] }),
  });

  const deleteConsentTerm = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`${BASE}/consent-terms/${id}/`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lgpd', 'consent-terms'] }),
  });

  // ── Consent Records ──

  const consentRecordsQuery = useQuery({
    queryKey: ['lgpd', 'consent-records'],
    queryFn: async () => {
      const res = await api.get<ConsentRecord[] | PaginatedResponse<ConsentRecord>>(`${BASE}/consent-records/`);
      return extractResults(res.data);
    },
    retry: 1,
  });

  const createConsentRecord = useMutation({
    mutationFn: async (data: Partial<ConsentRecord>) => {
      const res = await api.post(`${BASE}/consent-records/`, data);
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lgpd', 'consent-records'] }),
  });

  const revokeConsent = useMutation({
    mutationFn: async (id: string) => {
      const res = await api.post(`${BASE}/consent-records/${id}/revoke/`);
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lgpd', 'consent-records'] }),
  });

  // ── Data Processing Activities ──

  const activitiesQuery = useQuery({
    queryKey: ['lgpd', 'activities'],
    queryFn: async () => {
      const res = await api.get<DataProcessingActivity[] | PaginatedResponse<DataProcessingActivity>>(`${BASE}/data-processing-activities/`);
      return extractResults(res.data);
    },
    retry: 1,
  });

  const createActivity = useMutation({
    mutationFn: async (data: Partial<DataProcessingActivity>) => {
      const res = await api.post(`${BASE}/data-processing-activities/`, data);
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lgpd', 'activities'] }),
  });

  const updateActivity = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<DataProcessingActivity> }) => {
      const res = await api.patch(`${BASE}/data-processing-activities/${id}/`, data);
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lgpd', 'activities'] }),
  });

  const deleteActivity = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`${BASE}/data-processing-activities/${id}/`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lgpd', 'activities'] }),
  });

  // ── Data Subject Requests ──

  const dsrQuery = useQuery({
    queryKey: ['lgpd', 'dsr'],
    queryFn: async () => {
      const res = await api.get<DataSubjectRequest[] | PaginatedResponse<DataSubjectRequest>>(`${BASE}/data-subject-requests/`);
      return extractResults(res.data);
    },
    retry: 1,
  });

  const createDSR = useMutation({
    mutationFn: async (data: Partial<DataSubjectRequest>) => {
      const res = await api.post(`${BASE}/data-subject-requests/`, data);
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lgpd', 'dsr'] }),
  });

  const respondDSR = useMutation({
    mutationFn: async ({ id, response }: { id: string; response: string }) => {
      const res = await api.post(`${BASE}/data-subject-requests/${id}/respond/`, { response });
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lgpd', 'dsr'] }),
  });

  // ── AI Generation ──

  const generatePrivacyPolicy = useMutation({
    mutationFn: async (data: { company_name?: string }) => {
      const res = await api.post<AIGenerateResponse>(`${BASE}/ai/generate-privacy-policy/`, data);
      return res.data;
    },
  });

  const generateConsentTerm = useMutation({
    mutationFn: async (data: { purpose?: string; title?: string; company_name?: string }) => {
      const res = await api.post<AIGenerateResponse>(`${BASE}/ai/generate-consent-term/`, data);
      return res.data;
    },
  });

  return {
    // Consent Terms
    consentTerms: consentTermsQuery.data ?? [],
    isLoadingTerms: consentTermsQuery.isLoading,
    isErrorTerms: consentTermsQuery.isError,
    createConsentTerm,
    updateConsentTerm,
    deleteConsentTerm,

    // Consent Records
    consentRecords: consentRecordsQuery.data ?? [],
    isLoadingRecords: consentRecordsQuery.isLoading,
    isErrorRecords: consentRecordsQuery.isError,
    createConsentRecord,
    revokeConsent,

    // Activities
    activities: activitiesQuery.data ?? [],
    isLoadingActivities: activitiesQuery.isLoading,
    isErrorActivities: activitiesQuery.isError,
    createActivity,
    updateActivity,
    deleteActivity,

    // DSR
    dsrRequests: dsrQuery.data ?? [],
    isLoadingDSR: dsrQuery.isLoading,
    isErrorDSR: dsrQuery.isError,
    createDSR,
    respondDSR,

    // AI
    generatePrivacyPolicy,
    generateConsentTerm,
  };
}

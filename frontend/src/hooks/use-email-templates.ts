'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

// ── Types ──

export interface TemplateVariable {
  name: string;
  description: string;
}

export interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  body_html: string;
  category: string;
  category_display: string;
  variables: TemplateVariable[];
  variables_count: number;
  is_active: boolean;
  created_by: string | null;
  created_by_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmailTemplatePreview {
  subject: string;
  body_html: string;
}

export interface AIGeneratedTemplate {
  name: string;
  subject: string;
  body_html: string;
  variables: TemplateVariable[];
}

const BASE = '/api/v1/auth/email-templates';

// ── Hooks ──

export function useEmailTemplates(filters?: Record<string, string>) {
  return useQuery({
    queryKey: ['email-templates', filters],
    queryFn: async () => {
      const res = await api.get(`${BASE}/`, { params: filters });
      const data = res.data;
      return (data.results || data) as EmailTemplate[];
    },
  });
}

export function useEmailTemplate(id: string | undefined) {
  return useQuery({
    queryKey: ['email-templates', id],
    queryFn: async () => {
      const res = await api.get<EmailTemplate>(`${BASE}/${id}/`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateEmailTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<EmailTemplate>) => {
      const res = await api.post(`${BASE}/`, data);
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['email-templates'] }),
  });
}

export function useUpdateEmailTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<EmailTemplate> }) => {
      const res = await api.patch(`${BASE}/${id}/`, data);
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['email-templates'] }),
  });
}

export function useDeleteEmailTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`${BASE}/${id}/`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['email-templates'] }),
  });
}

export function usePreviewEmailTemplate() {
  return useMutation({
    mutationFn: async (data: { template_id: string; variables: Record<string, string> }) => {
      const res = await api.post<EmailTemplatePreview>(`${BASE}/preview/`, data);
      return res.data;
    },
  });
}

export function useGenerateEmailTemplateAI() {
  return useMutation({
    mutationFn: async (data: { description: string; category: string }) => {
      const res = await api.post<AIGeneratedTemplate>(`${BASE}/generate-ai/`, data);
      return res.data;
    },
  });
}

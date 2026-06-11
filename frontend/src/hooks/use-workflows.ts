'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

// ── Types ──

export interface WorkflowStep {
  name: string;
  description: string;
  order: number;
  auto_advance: boolean;
  deadline_days: number | null;
}

export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  specialty: string;
  specialty_display: string;
  steps: WorkflowStep[];
  steps_count: number;
  is_active: boolean;
  created_by: string | null;
  created_by_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface StepHistoryEntry {
  step: number;
  started_at: string;
  completed_at: string | null;
  notes: string;
}

export interface WorkflowExecution {
  id: string;
  template: string;
  template_name: string;
  case: string;
  case_titulo: string;
  current_step: number;
  total_steps: number;
  status: string;
  status_display: string;
  step_history: StepHistoryEntry[];
  started_at: string;
  completed_at: string | null;
}

const BASE = '/api/v1/processos/workflows';

// ── Template Hooks ──

export function useWorkflowTemplates(filters?: Record<string, string>) {
  return useQuery({
    queryKey: ['workflow-templates', filters],
    queryFn: async () => {
      const res = await api.get(`${BASE}/templates/`, { params: filters });
      const data = res.data;
      return (data.results || data) as WorkflowTemplate[];
    },
  });
}

export function useWorkflowTemplate(id: string | undefined) {
  return useQuery({
    queryKey: ['workflow-templates', id],
    queryFn: async () => {
      const res = await api.get<WorkflowTemplate>(`${BASE}/templates/${id}/`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateWorkflowTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<WorkflowTemplate>) => {
      const res = await api.post(`${BASE}/templates/`, data);
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['workflow-templates'] }),
  });
}

export function useUpdateWorkflowTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<WorkflowTemplate> }) => {
      const res = await api.patch(`${BASE}/templates/${id}/`, data);
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['workflow-templates'] }),
  });
}

export function useDeleteWorkflowTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`${BASE}/templates/${id}/`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['workflow-templates'] }),
  });
}

// ── Execution Hooks ──

export function useWorkflowExecutions(filters?: Record<string, string>) {
  return useQuery({
    queryKey: ['workflow-executions', filters],
    queryFn: async () => {
      const res = await api.get(`${BASE}/`, { params: filters });
      const data = res.data;
      return (data.results || data) as WorkflowExecution[];
    },
  });
}

export function useWorkflowExecution(id: string | undefined) {
  return useQuery({
    queryKey: ['workflow-executions', id],
    queryFn: async () => {
      const res = await api.get<WorkflowExecution>(`${BASE}/${id}/`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useStartWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { template: string; case: string }) => {
      const res = await api.post(`${BASE}/`, data);
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['workflow-executions'] }),
  });
}

export function useAdvanceWorkflowStep() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, notes }: { id: string; notes?: string }) => {
      const res = await api.post(`${BASE}/${id}/avancar/`, { notes });
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['workflow-executions'] }),
  });
}

export function useUpdateWorkflowExecution() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<WorkflowExecution> }) => {
      const res = await api.patch(`${BASE}/${id}/`, data);
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['workflow-executions'] }),
  });
}

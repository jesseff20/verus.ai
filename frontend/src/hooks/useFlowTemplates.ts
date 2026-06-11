import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

const BASE = '/api/v1/workflows/templates';

export type FlowNodeDto = {
  id?: string;
  node_id: string;
  node_type: string;
  label: string;
  description?: string;
  role: string;
  parent_node_id?: string;
  position: { x: number; y: number; width?: number; height?: number };
  data?: Record<string, unknown>;
  order?: number;
};

export type FlowEdgeDto = {
  id?: string;
  edge_id: string;
  source_node_id: string;
  target_node_id: string;
  source_handle?: string;
  target_handle?: string;
  label?: string;
  condition?: string;
  data?: Record<string, unknown>;
};

export type FlowTemplateListItem = {
  id: string;
  name: string;
  description: string;
  category: string;
  status: 'draft' | 'published' | 'archived';
  version: number;
  is_system_template: boolean;
  node_count: number;
  swimlane_count: number;
  created_by_name: string | null;
  created_at: string;
  updated_at: string;
  published_at: string | null;
};

export type FlowTemplateDetail = FlowTemplateListItem & {
  nodes: FlowNodeDto[];
  edges: FlowEdgeDto[];
  organ: string | null;
};

export function useFlowTemplates() {
  return useQuery<FlowTemplateListItem[]>({
    queryKey: ['flow-templates'],
    queryFn: () => api.get(BASE + '/').then((r) => r.data.results ?? r.data),
  });
}

export function useFlowTemplate(id: string | null) {
  return useQuery<FlowTemplateDetail>({
    queryKey: ['flow-template', id],
    queryFn: () => api.get(`${BASE}/${id}/`).then((r) => r.data),
    enabled: !!id,
  });
}

export function useCreateFlowTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; description?: string; category?: string }) =>
      api.post(BASE + '/', data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['flow-templates'] }),
  });
}

export function useSaveFlow(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      name: string;
      description?: string;
      category?: string;
      nodes: FlowNodeDto[];
      edges: FlowEdgeDto[];
    }) => api.post(`${BASE}/${id}/save/`, payload).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['flow-template', id] });
      qc.invalidateQueries({ queryKey: ['flow-templates'] });
    },
  });
}

export function usePublishFlow(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (notes?: string) =>
      api.post(`${BASE}/${id}/publish/`, { notes: notes ?? '' }).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['flow-template', id] });
      qc.invalidateQueries({ queryKey: ['flow-templates'] });
    },
  });
}

export function useDuplicateFlow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.post(`${BASE}/${id}/duplicate/`).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['flow-templates'] }),
  });
}

export function useDeleteFlowTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`${BASE}/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['flow-templates'] }),
  });
}

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import api from '@/lib/api';

const BASE = '/api/v1/workflow-execution';

// ── Types ──────────────────────────────────────────────────────

export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'skipped';
export type InstanceStatus = 'pending' | 'running' | 'completed' | 'cancelled';
export type RequestType = 'redistribuicao' | 'avocacao' | 'assessoria';
export type RequestStatus = 'pending' | 'approved' | 'rejected';

export type TaskRequestDto = {
  id: string;
  request_type: RequestType;
  requester: string;
  requester_name: string | null;
  target_user: string | null;
  target_user_name: string | null;
  justification: string;
  status: RequestStatus;
  resolution_note: string;
  created_at: string;
  resolved_at: string | null;
};

export type GatewayChoiceOption = {
  value: string;
  label: string;
  condition: string;
};

export type TaskInstanceDto = {
  id: string;
  instance: string;          // FlowInstance UUID — incluso nos resultados de my-tasks
  node_id: string;
  node_type: string;
  label: string;
  role_required: string;
  instructions: string;
  assigned_to: string | null;
  assigned_to_name: string | null;
  status: TaskStatus;
  gateway_choice: string;
  gateway_choices: GatewayChoiceOption[];
  due_date: string | null;
  notes: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  completed_by: string | null;
  completed_by_name: string | null;
  requests: TaskRequestDto[];
};

export type ExecutionEventDto = {
  id: string;
  event_type: string;
  node_id: string;
  node_label: string;
  actor: string | null;
  actor_name: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type FlowInstanceListItem = {
  id: string;
  template: string;
  template_name_snapshot: string;
  template_version_snapshot: number;
  case_ref: string;
  case_title: string;
  status: InstanceStatus;
  current_node_id: string;
  started_by: string | null;
  started_by_name: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  pending_task_count: number;
};

export type FlowInstanceDetail = FlowInstanceListItem & {
  tasks: TaskInstanceDto[];
  events: ExecutionEventDto[];
};

// ── Query keys ────────────────────────────────────────────────

const KEYS = {
  instances: (filters?: Record<string, string>) => ['flow-instances', filters ?? {}],
  instance: (id: string) => ['flow-instance', id],
  myTasks: (status?: string) => ['my-tasks', status ?? 'pending'],
  taskRequests: (status?: string) => ['task-requests', status ?? 'pending'],
};

// ── Hooks — FlowInstance ──────────────────────────────────────

export function useFlowInstances(filters?: { status?: string; template_id?: string }) {
  const params = new URLSearchParams();
  if (filters?.status) params.set('status', filters.status);
  if (filters?.template_id) params.set('template_id', filters.template_id);

  return useQuery<FlowInstanceListItem[]>({
    queryKey: KEYS.instances(filters as Record<string, string>),
    queryFn: async () => {
      const { data } = await api.get(`${BASE}/executions/?${params}`);
      return data.results ?? data;
    },
    // Poll every 30s for running instances — they can advance without user action
    refetchInterval: (query) => {
      const data = query.state.data as FlowInstanceListItem[] | undefined;
      if (data?.some((i) => i.status === 'running' || i.status === 'pending')) {
        return 30_000;
      }
      return false;
    },
  });
}

export function useFlowInstance(id: string) {
  return useQuery<FlowInstanceDetail>({
    queryKey: KEYS.instance(id),
    queryFn: async () => {
      const { data } = await api.get(`${BASE}/executions/${id}/`);
      return data;
    },
    enabled: Boolean(id),
  });
}

export function useStartFlow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      template_id: string;
      case_ref?: string;
      case_title?: string;
      case_id?: string;
    }) => {
      const { data } = await api.post<FlowInstanceDetail>(
        `${BASE}/executions/start/`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['flow-instances'] });
      qc.invalidateQueries({ queryKey: ['legal-cases'] });
      toast.success('Fluxo iniciado com sucesso.');
    },
  });
}

export function useStartFlowForCase() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { caseId: string; template_id: string }) => {
      const { data } = await api.post<FlowInstanceDetail>(
        `/api/v1/processos/${payload.caseId}/iniciar-fluxo/`,
        { template_id: payload.template_id },
      );
      return data;
    },
    onSuccess: (_data, payload) => {
      qc.invalidateQueries({ queryKey: ['flow-instances'] });
      qc.invalidateQueries({ queryKey: ['legal-cases'] });
      qc.invalidateQueries({ queryKey: ['caso', payload.caseId] });
      toast.success('Fluxo iniciado com sucesso.');
    },
  });
}

export function useCancelFlow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (instanceId: string) => {
      const { data } = await api.post<FlowInstanceDetail>(
        `${BASE}/executions/${instanceId}/cancel/`,
      );
      return data;
    },
    onSuccess: (_data, instanceId) => {
      qc.invalidateQueries({ queryKey: ['flow-instances'] });
      qc.invalidateQueries({ queryKey: KEYS.instance(instanceId) });
      toast.success('Fluxo cancelado.');
    },
  });
}

// ── Hooks — TaskInstance ──────────────────────────────────────

export function useCompleteTask(instanceId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      taskId: string;
      notes?: string;
      gateway_choice?: string;
    }) => {
      const { data } = await api.post<FlowInstanceDetail>(
        `${BASE}/executions/${instanceId}/tasks/${payload.taskId}/complete/`,
        { notes: payload.notes ?? '', gateway_choice: payload.gateway_choice ?? '' },
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.instance(instanceId) });
      qc.invalidateQueries({ queryKey: ['my-tasks'] });
      toast.success('Tarefa concluída.');
    },
  });
}

export function useCreateTaskRequest(instanceId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      taskId: string;
      request_type: RequestType;
      justification: string;
      target_user?: string;
    }) => {
      const { data } = await api.post<TaskRequestDto>(
        `${BASE}/executions/${instanceId}/tasks/${payload.taskId}/request/`,
        {
          request_type: payload.request_type,
          justification: payload.justification,
          target_user: payload.target_user,
        },
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.instance(instanceId) });
      toast.success('Solicitação enviada. Aguardando aprovação.');
    },
  });
}

// ── Hooks — My Tasks ─────────────────────────────────────────

export function useMyTasks(statusFilter: string = 'pending') {
  return useQuery<TaskInstanceDto[]>({
    queryKey: KEYS.myTasks(statusFilter),
    queryFn: async () => {
      const { data } = await api.get(
        `${BASE}/my-tasks/?status=${statusFilter}`,
      );
      return data.results ?? data;
    },
    // Poll every 15s for pending/in-progress tasks — new tasks may be assigned
    refetchInterval: statusFilter === 'pending' || statusFilter === 'in_progress' ? 15_000 : false,
  });
}

// ── Hooks — Task Requests (admin) ─────────────────────────────

export function useTaskRequests(statusFilter: string = 'pending') {
  return useQuery<TaskRequestDto[]>({
    queryKey: KEYS.taskRequests(statusFilter),
    queryFn: async () => {
      const { data } = await api.get(
        `${BASE}/task-requests/?status=${statusFilter}`,
      );
      return data.results ?? data;
    },
    // Poll for pending requests — managers need to see new ones promptly
    refetchInterval: statusFilter === 'pending' ? 20_000 : false,
  });
}

export function useApproveRequest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { requestId: string; resolution_note?: string }) => {
      const { data } = await api.post<TaskRequestDto>(
        `${BASE}/task-requests/${payload.requestId}/approve/`,
        { resolution_note: payload.resolution_note ?? '' },
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['task-requests'] });
      qc.invalidateQueries({ queryKey: ['flow-instances'] });
      qc.invalidateQueries({ queryKey: ['my-tasks'] });
      toast.success('Solicitação aprovada.');
    },
  });
}

export function useRejectRequest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { requestId: string; resolution_note?: string }) => {
      const { data } = await api.post<TaskRequestDto>(
        `${BASE}/task-requests/${payload.requestId}/reject/`,
        { resolution_note: payload.resolution_note ?? '' },
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['task-requests'] });
      toast.success('Solicitação rejeitada.');
    },
  });
}

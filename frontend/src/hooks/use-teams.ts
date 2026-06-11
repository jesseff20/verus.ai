'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

// ── Types ──

export interface TeamMember {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  role: string;
  full_name: string;
}

export interface Team {
  id: string;
  name: string;
  description: string;
  leader: number | null;
  leader_name: string | null;
  members: number[];
  members_count: number;
  members_detail: TeamMember[];
  specialty: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TeamAssignment {
  id: string;
  team: string;
  team_name: string;
  case: string;
  case_titulo: string | null;
  assigned_by: number | null;
  assigned_by_name: string | null;
  role_in_case: string;
  role_in_case_display: string;
  assigned_at: string;
}

const BASE = '/api/v1/auth/equipes';

// ── Hooks ──

export function useTeams(filters?: Record<string, string>) {
  return useQuery({
    queryKey: ['teams', filters],
    queryFn: async () => {
      const res = await api.get(`${BASE}/`, { params: filters });
      const data = res.data;
      return (data.results || data) as Team[];
    },
  });
}

export function useTeam(id: string | undefined) {
  return useQuery({
    queryKey: ['teams', id],
    queryFn: async () => {
      const res = await api.get<Team>(`${BASE}/${id}/`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateTeam() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Team>) => {
      const res = await api.post(`${BASE}/`, data);
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['teams'] }),
  });
}

export function useUpdateTeam() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Team> }) => {
      const res = await api.patch(`${BASE}/${id}/`, data);
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['teams'] }),
  });
}

export function useDeleteTeam() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`${BASE}/${id}/`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['teams'] }),
  });
}

export function useAddTeamMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ teamId, userId }: { teamId: string; userId: number }) => {
      const res = await api.post(`${BASE}/${teamId}/membros/adicionar/`, { user_id: userId });
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['teams'] }),
  });
}

export function useRemoveTeamMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ teamId, userId }: { teamId: string; userId: number }) => {
      const res = await api.post(`${BASE}/${teamId}/membros/remover/`, { user_id: userId });
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['teams'] }),
  });
}

export function useTeamAssignments(teamId: string | undefined) {
  return useQuery({
    queryKey: ['team-assignments', teamId],
    queryFn: async () => {
      const res = await api.get<TeamAssignment[]>(`${BASE}/${teamId}/atribuicoes/`);
      return res.data;
    },
    enabled: !!teamId,
  });
}

export function useCreateTeamAssignment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ teamId, caseId, roleInCase }: { teamId: string; caseId: string; roleInCase: string }) => {
      const res = await api.post(`${BASE}/${teamId}/atribuicoes/`, { case: caseId, role_in_case: roleInCase });
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['team-assignments'] }),
  });
}

export function useDeleteTeamAssignment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ teamId, assignmentId }: { teamId: string; assignmentId: string }) => {
      await api.delete(`${BASE}/${teamId}/atribuicoes/${assignmentId}/`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['team-assignments'] }),
  });
}

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import type { Simulation, JudgeProfile, Court, MinisterProfile } from '@/types';

// ========== Simulacoes ==========

export function useSimulations(filters?: {
  simulation_type?: string;
  status?: string;
}) {
  return useQuery<Simulation[]>({
    queryKey: ['simulations', filters],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/simulations/simulations/', {
        params: filters,
      });
      return data.results || data;
    },
  });
}

export function useSimulationDetail(id: string | null) {
  return useQuery<Simulation>({
    queryKey: ['simulation', id],
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/simulations/simulations/${id}/`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateSimulation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: {
      simulation_type: string;
      title: string;
      case_description?: string;
      crime_type?: string;
      metadata?: Record<string, any>;
    }) => {
      const { data } = await api.post('/api/v1/simulations/simulations/', payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['simulations'] });
    },
  });
}

export function useDeleteSimulation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/simulations/simulations/${id}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['simulations'] });
    },
  });
}

export function useDuplicateSimulation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await api.post(`/api/v1/simulations/simulations/${id}/duplicate/`);
      return data as Simulation;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['simulations'] });
    },
  });
}

export function usePatchSimulation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, ...payload }: { id: string; [key: string]: any }) => {
      const { data } = await api.patch(`/api/v1/simulations/simulations/${id}/`, payload);
      return data;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['simulations'] });
      queryClient.invalidateQueries({ queryKey: ['simulation', variables.id] });
    },
  });
}

// ========== Tribunais ==========

export function useCourts(state?: string) {
  return useQuery<Court[]>({
    queryKey: ['courts', state],
    queryFn: async () => {
      const params = state ? { state } : {};
      const { data } = await api.get('/api/v1/simulations/courts/', { params });
      return data.results || data;
    },
  });
}

// ========== Perfis de Juizes ==========

export function useJudgeProfiles(filters?: {
  state?: string;
  court?: string;
  comarca?: string;
}) {
  return useQuery<JudgeProfile[]>({
    queryKey: ['judge-profiles', filters],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/simulations/judges/', {
        params: filters,
      });
      return data.results || data;
    },
    enabled: !!filters?.state,
  });
}

// ========== Ministros STF/STJ ==========

export function useMinisterProfiles(courtType?: 'STF' | 'STJ' | 'TJ' | 'TRT' | 'TST' | 'TSE' | 'STM' | 'TRE') {
  return useQuery<MinisterProfile[]>({
    queryKey: ['minister-profiles', courtType],
    queryFn: async () => {
      const params = courtType ? { court_type: courtType } : {};
      const { data } = await api.get('/api/v1/simulations/ministers/', { params });
      return data;
    },
  });
}

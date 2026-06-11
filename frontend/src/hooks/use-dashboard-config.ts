'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

export interface WidgetConfig {
  id: string;
  type: string;
  position: number;
  size: string;
  config: Record<string, unknown>;
}

export interface DashboardConfigData {
  id: string;
  user: string;
  layout: WidgetConfig[];
  theme: string;
  theme_display: string;
  auto_refresh: boolean;
  refresh_interval: number;
  created_at: string;
  updated_at: string;
}

export interface WidgetsData {
  cases_summary: { active_count: number; total_count: number; recent_cases: Array<Record<string, unknown>> };
  deadlines_upcoming: { deadlines: Array<Record<string, unknown>> };
  financial_summary: { revenue: number; pending: number; overdue: number };
  activity_feed: { activities: Array<Record<string, unknown>> };
  calendar_today: { deadlines: Array<Record<string, unknown>>; audiencias: Array<Record<string, unknown>> };
  kpis: { total_cases: number; won_cases: number; win_rate: number; overdue_deadlines: number };
}

export function useDashboardConfig() {
  const queryClient = useQueryClient();

  const { data: config, isLoading, error } = useQuery({
    queryKey: ['dashboard-config'],
    queryFn: async () => {
      const res = await api.get<DashboardConfigData>('/api/v1/auth/dashboard-config/');
      return res.data;
    },
  });

  const updateConfig = useMutation({
    mutationFn: async (data: Partial<DashboardConfigData>) => {
      const res = await api.patch<DashboardConfigData>('/api/v1/auth/dashboard-config/', data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-config'] });
    },
  });

  return { config, isLoading, error, updateConfig };
}

export function useDashboardWidgetsData() {
  return useQuery({
    queryKey: ['dashboard-widgets-data'],
    queryFn: async () => {
      const res = await api.get<WidgetsData>('/api/v1/auth/dashboard-config/widgets/');
      return res.data;
    },
  });
}

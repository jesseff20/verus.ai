'use client';

import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

export interface AuditLogEntry {
  id: string;
  action: string;
  action_display: string;
  severity: string;
  severity_display: string;
  entity_type: string;
  entity_name: string;
  description: string;
  user_email: string;
  user?: string;
  user_role?: string;
  ip_address?: string;
  old_values?: Record<string, unknown>;
  new_values?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface AuditStats {
  total: number;
  today: number;
  last_24h: number;
  active_users: number;
  by_action: Array<{ action: string; count: number }>;
  by_user: Array<{ user_email: string; count: number }>;
  by_resource: Array<{ entity_type: string; count: number }>;
  recent_activity: AuditLogEntry[];
}

export interface AuditFilters {
  user?: string;
  action?: string;
  date_from?: string;
  date_to?: string;
  resource_type?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export function useAuditLogs(filters: AuditFilters = {}) {
  return useQuery({
    queryKey: ['audit-logs', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.user) params.set('user', filters.user);
      if (filters.action) params.set('action', filters.action);
      if (filters.date_from) params.set('date_from', filters.date_from);
      if (filters.date_to) params.set('date_to', filters.date_to);
      if (filters.resource_type) params.set('resource_type', filters.resource_type);
      if (filters.search) params.set('search', filters.search);
      if (filters.page) params.set('page', String(filters.page));
      if (filters.page_size) params.set('page_size', String(filters.page_size));

      const res = await api.get<{ count: number; results: AuditLogEntry[] }>(
        `/api/v1/core/auditoria/?${params.toString()}`
      );
      return res.data;
    },
  });
}

export function useAuditStats() {
  return useQuery({
    queryKey: ['audit-stats'],
    queryFn: async () => {
      const res = await api.get<AuditStats>('/api/v1/core/auditoria/stats/');
      return res.data;
    },
  });
}

export function useAuditUserActivity(userId: string | null) {
  return useQuery({
    queryKey: ['audit-user-activity', userId],
    queryFn: async () => {
      const res = await api.get(
        `/api/v1/core/auditoria/usuario/${userId}/`
      );
      return res.data;
    },
    enabled: !!userId,
  });
}

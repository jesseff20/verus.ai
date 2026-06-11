'use client';

import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

// ── Types ──

export interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  end: string | null;
  type: string; // 'deadline' | 'reminder' | 'hearing' | 'notification' | 'phase'
  case_id: string | null;
  case_title: string | null;
  color: string;
  priority: number;
  status: string;
  description: string;
}

const BASE = '/api/v1/processos/calendario';

// ── Hooks ──

export function useCalendarEvents(start: string, end: string) {
  return useQuery({
    queryKey: ['calendar', 'events', start, end],
    queryFn: async () => {
      const res = await api.get(`${BASE}/events/`, {
        params: { start, end },
      });
      const data = res.data;
      return (data.events || data.results || data) as CalendarEvent[];
    },
    enabled: !!start && !!end,
  });
}

export function useUpcomingDeadlines(days: number = 7) {
  return useQuery({
    queryKey: ['calendar', 'upcoming', days],
    queryFn: async () => {
      const res = await api.get(`${BASE}/proximos/`, {
        params: { days },
      });
      const data = res.data;
      return (data.deadlines || data.results || data) as CalendarEvent[];
    },
  });
}

export function useOverdueItems() {
  return useQuery({
    queryKey: ['calendar', 'overdue'],
    queryFn: async () => {
      const res = await api.get(`${BASE}/atrasados/`);
      const data = res.data;
      return (data.overdue || data.results || data) as CalendarEvent[];
    },
  });
}

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

export interface Notification {
  id: number;
  type: 'deadline' | 'document' | 'case' | 'system' | 'simulation' | 'task';
  type_display: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  priority_display: string;
  title: string;
  message: string;
  link: string;
  is_read: boolean;
  created_at: string;
  copilot_prompt?: string;
  action_type?: 'navigate' | 'copilot' | 'action';
  source?: 'system' | 'copilot' | 'user' | 'cron';
  metadata?: Record<string, unknown>;
}

interface NotificationsResponse {
  count: number;
  results: Notification[];
}

const NOTIFICATIONS_KEY = ['notifications'];
const UNREAD_COUNT_KEY = ['notifications-unread-count'];

export function useNotifications() {
  const queryClient = useQueryClient();

  // List notifications
  const {
    data: notificationsData,
    isLoading,
  } = useQuery({
    queryKey: NOTIFICATIONS_KEY,
    queryFn: async () => {
      const response = await api.get<NotificationsResponse | Notification[]>(
        '/api/v1/auth/notifications/',
        { params: { page_size: 20 } }
      );
      // Handle both paginated and non-paginated responses
      const data = response.data;
      if (Array.isArray(data)) {
        return data;
      }
      return (data as NotificationsResponse).results ?? [];
    },
    refetchInterval: 30000, // Poll every 30 seconds
    staleTime: 15000,
  });

  // Unread count
  const { data: unreadCountData } = useQuery({
    queryKey: UNREAD_COUNT_KEY,
    queryFn: async () => {
      const response = await api.get<{ count: number }>(
        '/api/v1/auth/notifications/unread-count/'
      );
      return response.data.count;
    },
    refetchInterval: 30000,
    staleTime: 15000,
  });

  // Mark single as read
  const markAsRead = useMutation({
    mutationFn: async (id: number) => {
      await api.post(`/api/v1/auth/notifications/${id}/read/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: NOTIFICATIONS_KEY });
      queryClient.invalidateQueries({ queryKey: UNREAD_COUNT_KEY });
    },
  });

  // Mark all as read
  const markAllAsRead = useMutation({
    mutationFn: async () => {
      await api.post('/api/v1/auth/notifications/read-all/');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: NOTIFICATIONS_KEY });
      queryClient.invalidateQueries({ queryKey: UNREAD_COUNT_KEY });
    },
  });

  return {
    notifications: notificationsData ?? [],
    unreadCount: unreadCountData ?? 0,
    isLoading,
    markAsRead: markAsRead.mutate,
    markAllAsRead: markAllAsRead.mutate,
    isMarkingRead: markAsRead.isPending,
    isMarkingAllRead: markAllAsRead.isPending,
  };
}

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useNotifications, type Notification } from '@/hooks/use-notifications';
import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Bell,
  Bot,
  Clock,
  FileText,
  Briefcase,
  Monitor,
  FlaskConical,
  CheckSquare,
  CheckCheck,
  MessageCircle,
} from 'lucide-react';
import api from '@/lib/api';
import { cn } from '@/lib/utils';

const typeIcons: Record<Notification['type'], React.ElementType> = {
  deadline: Clock,
  document: FileText,
  case: Briefcase,
  system: Monitor,
  simulation: FlaskConical,
  task: CheckSquare,
};

const priorityColors: Record<Notification['priority'], string> = {
  low: 'text-muted-foreground',
  medium: 'text-blue-500',
  high: 'text-orange-500',
  urgent: 'text-red-500',
};

function timeAgo(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return 'agora';
  if (diffMin < 60) return `${diffMin}min`;
  const diffHrs = Math.floor(diffMin / 60);
  if (diffHrs < 24) return `${diffHrs}h`;
  const diffDays = Math.floor(diffHrs / 24);
  if (diffDays < 30) return `${diffDays}d`;
  return `${Math.floor(diffDays / 30)}m`;
}

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    isMarkingAllRead,
  } = useNotifications();

  const handleWhatsAppClick = async (e: React.MouseEvent, notification: Notification) => {
    e.stopPropagation();
    try {
      const res = await api.post(`/api/v1/auth/notifications/${notification.id}/send-whatsapp/`);
      if (res.data.whatsapp_link) {
        window.open(res.data.whatsapp_link, '_blank');
      }
    } catch {
      // If WhatsApp channel not configured, silently ignore
    }
  };

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.is_read) {
      markAsRead(notification.id);
    }

    setOpen(false);

    // For copilot action_type, navigate to Copilot with pre-filled prompt
    if (notification.action_type === 'copilot' && notification.copilot_prompt) {
      router.push(
        `/dashboard/copilot?prompt=${encodeURIComponent(notification.copilot_prompt)}`
      );
      return;
    }

    if (notification.link) {
      router.push(notification.link);
    }
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative h-9 w-9 text-muted-foreground hover:text-foreground"
        >
          <Bell className="h-4 w-4" />
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
          <span className="sr-only">Notificações</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className="w-[calc(100vw-2rem)] sm:w-96 p-0"
        align="end"
        sideOffset={8}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b px-4 py-3">
          <h3 className="text-sm font-semibold">Notificações</h3>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="h-auto py-1 px-2 text-xs text-muted-foreground hover:text-foreground"
              onClick={() => markAllAsRead()}
              disabled={isMarkingAllRead}
            >
              <CheckCheck className="mr-1 h-3 w-3" />
              Marcar todas como lidas
            </Button>
          )}
        </div>

        {/* Notification list */}
        <ScrollArea className="max-h-[360px]">
          {notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
              <Bell className="mb-2 h-8 w-8 opacity-30" />
              <p className="text-sm">Nenhuma notificação</p>
            </div>
          ) : (
            <div className="divide-y">
              {notifications.map((notification) => {
                const Icon = typeIcons[notification.type] || Bell;
                return (
                  <button
                    key={notification.id}
                    className={cn(
                      'flex w-full items-start gap-3 px-4 py-3 text-left transition-colors hover:bg-muted/50',
                      !notification.is_read && 'bg-muted/30'
                    )}
                    onClick={() => handleNotificationClick(notification)}
                  >
                    <div
                      className={cn(
                        'mt-0.5 flex-shrink-0',
                        priorityColors[notification.priority]
                      )}
                    >
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p
                        className={cn(
                          'truncate text-sm',
                          !notification.is_read
                            ? 'font-semibold text-foreground'
                            : 'text-muted-foreground'
                        )}
                      >
                        {notification.title}
                      </p>
                      <div className="mt-0.5 flex items-center gap-1.5">
                        <p className="text-xs text-muted-foreground">
                          {timeAgo(notification.created_at)}
                        </p>
                        {notification.action_type === 'copilot' && (
                          <span className="inline-flex items-center gap-0.5 rounded bg-primary/10 px-1 py-0.5 text-[10px] font-medium text-primary">
                            <Bot className="h-2.5 w-2.5" />
                            Copilot
                          </span>
                        )}
                        <button
                          type="button"
                          title="Enviar via WhatsApp"
                          className="inline-flex items-center rounded p-0.5 text-green-600 hover:bg-green-50 dark:hover:bg-green-950 transition-colors"
                          onClick={(e) => handleWhatsAppClick(e, notification)}
                        >
                          <MessageCircle className="h-3 w-3" />
                        </button>
                      </div>
                    </div>
                    {!notification.is_read && (
                      <span className="mt-1.5 h-2 w-2 flex-shrink-0 rounded-full bg-primary" />
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </ScrollArea>
      </PopoverContent>
    </Popover>
  );
}

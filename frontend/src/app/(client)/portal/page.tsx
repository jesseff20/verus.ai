'use client';

import Link from 'next/link';
import {
  useClientPortalAuth,
  useClientPortalCases,
  useClientPortalNotifications,
  useClientPortalMessages,
  useClientPortalHearings,
  useClientPortalPendingConsents,
} from '@/hooks/use-client-portal';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Briefcase,
  FileText,
  Calendar,
  MessageSquare,
  Loader2,
  AlertTriangle,
  ArrowRight,
  Bell,
  ClipboardList,
  ShieldCheck,
  Upload,
} from 'lucide-react';

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '\u2014';
  return new Date(dateStr).toLocaleDateString('pt-BR');
}

function formatRelativeTime(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return 'agora';
  if (diffMin < 60) return `${diffMin}min atrás`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `${diffH}h atrás`;
  const diffD = Math.floor(diffH / 24);
  if (diffD < 7) return `${diffD}d atrás`;
  return formatDate(dateStr);
}

export default function ClientPortalDashboard() {
  const { client } = useClientPortalAuth();
  const { data: cases, isLoading: casesLoading } = useClientPortalCases();
  const { data: notifications } = useClientPortalNotifications();
  const { data: messages } = useClientPortalMessages();
  const { data: hearings } = useClientPortalHearings();
  const { data: pendingConsents } = useClientPortalPendingConsents();

  const activeCases = cases?.filter((c) => c.status === 'ativo') || [];
  const unreadMessages = messages?.filter((m) => !m.read) || [];

  // Next hearing: find the soonest future hearing
  const now = new Date();
  const nextHearing = hearings
    ?.filter((h) => new Date(h.data_audiencia) >= now)
    .sort((a, b) => new Date(a.data_audiencia).getTime() - new Date(b.data_audiencia).getTime())[0];

  const hasPendingConsents = pendingConsents && pendingConsents.length > 0;
  const recentNotifications = notifications?.slice(0, 5) || [];

  if (casesLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── LGPD Consent Banner ───────────────────────── */}
      {hasPendingConsents && (
        <div className="rounded-lg border border-yellow-300 bg-yellow-50 dark:border-yellow-700 dark:bg-yellow-900/20 p-4">
          <div className="flex items-start gap-3">
            <ShieldCheck className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5 shrink-0" />
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-yellow-800 dark:text-yellow-300">
                Consentimento Pendente
              </h3>
              <p className="text-xs text-yellow-700 dark:text-yellow-400 mt-1">
                Você possui {pendingConsents.length} termo(s) de consentimento pendente(s) de aceitação.
              </p>
            </div>
            <Button size="sm" variant="outline" asChild className="shrink-0">
              <Link href="/portal/consentimento">
                Revisar Termos
                <ArrowRight className="ml-1 h-3 w-3" />
              </Link>
            </Button>
          </div>
        </div>
      )}

      {/* ── Welcome ───────────────────────────────────── */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
          {client ? `Olá, ${client.name.split(' ')[0]}` : 'Portal do Cliente'}
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Acompanhe seus processos, documentos e comunicações
        </p>
      </div>

      {/* ── Stats Cards ───────────────────────────────── */}
      <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
              <Briefcase className="h-3.5 w-3.5" />
              Meus Casos
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{cases?.length || 0}</div>
            <p className="text-[11px] text-muted-foreground mt-0.5">
              {activeCases.length} ativo(s)
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
              <FileText className="h-3.5 w-3.5" />
              Documentos
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {cases?.reduce((acc, c) => acc, 0) || 0}
            </div>
            <p className="text-[11px] text-muted-foreground mt-0.5">
              nos seus casos
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5" />
              Próxima Audiência
            </CardTitle>
          </CardHeader>
          <CardContent>
            {nextHearing ? (
              <>
                <div className="text-lg font-bold">
                  {formatDate(nextHearing.data_audiencia)}
                </div>
                <p className="text-[11px] text-muted-foreground mt-0.5 truncate">
                  {nextHearing.titulo || nextHearing.tipo_display}
                </p>
              </>
            ) : (
              <>
                <div className="text-2xl font-bold text-muted-foreground/50">
                  --
                </div>
                <p className="text-[11px] text-muted-foreground mt-0.5">
                  nenhuma agendada
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
              <MessageSquare className="h-3.5 w-3.5" />
              Mensagens
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {unreadMessages.length}
            </div>
            <p className="text-[11px] text-muted-foreground mt-0.5">
              não lida(s)
            </p>
          </CardContent>
        </Card>
      </div>

      {/* ── Quick Actions ─────────────────────────────── */}
      <div className="grid gap-3 grid-cols-1 sm:grid-cols-3">
        <Button variant="outline" className="h-auto py-3 justify-start" asChild>
          <Link href="/portal" className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
              <Briefcase className="h-4 w-4 text-primary" />
            </div>
            <div className="text-left">
              <div className="text-sm font-medium">Ver Meus Casos</div>
              <div className="text-[11px] text-muted-foreground">
                {cases?.length || 0} processo(s)
              </div>
            </div>
            <ArrowRight className="ml-auto h-4 w-4 text-muted-foreground" />
          </Link>
        </Button>

        <Button variant="outline" className="h-auto py-3 justify-start" asChild>
          <Link href="/portal/documentos" className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-500/10">
              <Upload className="h-4 w-4 text-blue-600" />
            </div>
            <div className="text-left">
              <div className="text-sm font-medium">Enviar Documento</div>
              <div className="text-[11px] text-muted-foreground">
                upload de arquivos
              </div>
            </div>
            <ArrowRight className="ml-auto h-4 w-4 text-muted-foreground" />
          </Link>
        </Button>

        <Button variant="outline" className="h-auto py-3 justify-start" asChild>
          <Link href="/portal/contratos" className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-500/10">
              <ClipboardList className="h-4 w-4 text-violet-600" />
            </div>
            <div className="text-left">
              <div className="text-sm font-medium">Ver Contratos</div>
              <div className="text-[11px] text-muted-foreground">
                contratos e assinaturas
              </div>
            </div>
            <ArrowRight className="ml-auto h-4 w-4 text-muted-foreground" />
          </Link>
        </Button>
      </div>

      {/* ── Recent Notifications ──────────────────────── */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <Bell className="h-4 w-4" />
              Atualizações Recentes
            </CardTitle>
            {notifications && notifications.length > 5 && (
              <Button variant="ghost" size="sm" asChild>
                <Link href="/portal/notificacoes">
                  Ver todas
                  <ArrowRight className="ml-1 h-3 w-3" />
                </Link>
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {recentNotifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-muted-foreground gap-2">
              <Bell className="h-8 w-8 opacity-30" />
              <p className="text-sm">Nenhuma atualização recente</p>
            </div>
          ) : (
            <div className="space-y-2">
              {recentNotifications.map((notif) => (
                <div
                  key={notif.id}
                  className={`flex items-start gap-3 rounded-lg border p-3 transition-colors ${
                    !notif.lida
                      ? 'bg-primary/5 border-primary/20'
                      : 'bg-background'
                  }`}
                >
                  <div className="mt-0.5">
                    {!notif.lida && (
                      <div className="h-2 w-2 rounded-full bg-primary" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="text-sm font-medium truncate">
                        {notif.titulo}
                      </h4>
                      <span className="text-[10px] text-muted-foreground shrink-0">
                        {formatRelativeTime(notif.created_at)}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                      {notif.mensagem}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* ── Active Cases List ─────────────────────────── */}
      {activeCases.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <Briefcase className="h-4 w-4" />
                Casos Ativos
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {activeCases.slice(0, 5).map((caso) => (
                <Link
                  key={caso.id}
                  href={`/portal/casos/${caso.id}`}
                  className="flex items-center justify-between gap-3 rounded-lg border p-3 hover:bg-accent/30 transition-colors group"
                >
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-medium truncate group-hover:text-primary transition-colors">
                      {caso.titulo}
                    </h4>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="outline" className="text-[10px]">
                        {caso.especialidade_display}
                      </Badge>
                      {caso.numero_processo && (
                        <span className="text-[11px] text-muted-foreground font-mono">
                          {caso.numero_processo}
                        </span>
                      )}
                    </div>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

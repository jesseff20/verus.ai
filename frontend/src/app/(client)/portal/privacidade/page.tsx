'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Separator } from '@/components/ui/separator';
import {
  Shield,
  Loader2,
  AlertTriangle,
  Download,
  Trash2,
  UserCog,
  FileOutput,
  Eye,
  Mail,
  CheckCircle,
} from 'lucide-react';

// ─── Types ──────────────────────────────────────────────────────────────────

interface Consent {
  id: string;
  titulo: string;
  versao: string;
  aceito_em: string;
}

interface PrivacyData {
  consentimentos: Consent[];
}

// ─── API ────────────────────────────────────────────────────────────────────

const portalApi = axios.create({
  baseURL: '',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

portalApi.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('client_portal_access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// ─── Component ──────────────────────────────────────────────────────────────

function RightCard({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: React.ElementType;
  title: string;
  description: string;
  action: React.ReactNode;
}) {
  return (
    <Card>
      <CardContent className="p-4 sm:p-5 flex items-start gap-4">
        <div className="shrink-0 mt-0.5 text-primary">
          <Icon className="h-5 w-5" />
        </div>
        <div className="flex-1 min-w-0 space-y-2">
          <h3 className="font-medium text-sm">{title}</h3>
          <p className="text-xs text-muted-foreground">{description}</p>
          {action}
        </div>
      </CardContent>
    </Card>
  );
}

export default function PrivacidadePage() {
  const queryClient = useQueryClient();
  const [requestMsg, setRequestMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const { data, isLoading, error } = useQuery<PrivacyData>({
    queryKey: ['client-portal-privacidade'],
    queryFn: async () => {
      const consentsRes = await portalApi.get('/api/v1/auth/client-portal/consents/');
      return { consentimentos: consentsRes.data || [] } as PrivacyData;
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  const createRequest = useMutation({
    mutationFn: async (tipo: string) => {
      await portalApi.post('/api/v1/auth/client-portal/data-subject-request/', { tipo });
    },
    onSuccess: () => {
      setRequestMsg({ type: 'success', text: 'Solicitação enviada com sucesso! Entraremos em contato.' });
    },
    onError: () => {
      setRequestMsg({ type: 'error', text: 'Erro ao enviar solicitação. Tente novamente.' });
    },
  });

  const revokeConsent = useMutation({
    mutationFn: async (consentId: string) => {
      await portalApi.post(`/api/v1/auth/client-portal/privacidade/revogar/${consentId}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['client-portal-privacidade'] });
      setRequestMsg({ type: 'success', text: 'Consentimento revogado com sucesso.' });
    },
    onError: () => {
      setRequestMsg({ type: 'error', text: 'Erro ao revogar consentimento.' });
    },
  });

  const formatDate = (dateStr: string) =>
    new Date(dateStr).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight flex items-center gap-2">
          <Shield className="h-7 w-7 sm:h-8 sm:w-8" />
          Privacidade e Dados Pessoais
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Gerencie seus consentimentos e exerça seus direitos conforme a LGPD
        </p>
      </div>

      {requestMsg && (
        <div className={`flex items-center gap-2 text-sm p-3 rounded-lg ${
          requestMsg.type === 'success'
            ? 'bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-300'
            : 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-300'
        }`}>
          {requestMsg.type === 'success' ? <CheckCircle className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
          {requestMsg.text}
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <div className="flex items-center justify-center py-16 text-destructive gap-2">
          <AlertTriangle className="h-5 w-5" />
          <span>Erro ao carregar dados de privacidade</span>
        </div>
      ) : (
        <>
          {/* Consents Section */}
          <div className="space-y-3">
            <h2 className="text-lg font-semibold">Meus Consentimentos</h2>
            {data?.consentimentos && data.consentimentos.length > 0 ? (
              <div className="grid gap-3">
                {data.consentimentos.map((consent) => (
                  <Card key={consent.id}>
                    <CardContent className="p-4 sm:p-5 flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <h3 className="font-medium text-sm">{consent.titulo}</h3>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          Versão {consent.versao} &middot; Aceito em {formatDate(consent.aceito_em)}
                        </p>
                      </div>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button variant="outline" size="sm" className="text-xs shrink-0 text-destructive border-destructive/30 hover:bg-destructive/10">
                            Revogar
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Revogar consentimento?</AlertDialogTitle>
                            <AlertDialogDescription>
                              Ao revogar este consentimento, alguns serviços podem ser afetados.
                              Esta ação pode impactar o acompanhamento do seu processo. Deseja continuar?
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancelar</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => revokeConsent.mutate(consent.id)}
                              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                            >
                              Revogar
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Nenhum consentimento registrado.</p>
            )}
          </div>

          <Separator />

          {/* Rights Section */}
          <div className="space-y-3">
            <h2 className="text-lg font-semibold">Meus Direitos (LGPD)</h2>
            <div className="grid gap-3 sm:grid-cols-2">
              <RightCard
                icon={Eye}
                title="Acessar meus dados"
                description="Solicite uma cópia de todos os dados pessoais que armazenamos sobre você."
                action={
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs"
                    onClick={() => createRequest.mutate('acesso')}
                    disabled={createRequest.isPending}
                  >
                    <Download className="h-3 w-3 mr-1" />
                    Solicitar Exportação
                  </Button>
                }
              />
              <RightCard
                icon={UserCog}
                title="Corrigir dados"
                description="Atualize suas informações pessoais diretamente no seu perfil."
                action={
                  <Button variant="outline" size="sm" className="text-xs" asChild>
                    <Link href="/portal/perfil">
                      <UserCog className="h-3 w-3 mr-1" />
                      Ir para Perfil
                    </Link>
                  </Button>
                }
              />
              <RightCard
                icon={Trash2}
                title="Excluir dados"
                description="Solicite a exclusão dos seus dados pessoais. Dados necessários para obrigações legais podem ser mantidos."
                action={
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-xs text-destructive border-destructive/30 hover:bg-destructive/10"
                      >
                        <Trash2 className="h-3 w-3 mr-1" />
                        Solicitar Exclusão
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Solicitar exclusão de dados?</AlertDialogTitle>
                        <AlertDialogDescription>
                          Esta solicitação será analisada pela equipe. Dados necessários para
                          cumprimento de obrigações legais ou processuais podem ser mantidos
                          conforme previsto na LGPD. Você será notificado sobre o andamento.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancelar</AlertDialogCancel>
                        <AlertDialogAction
                          onClick={() => createRequest.mutate('exclusao')}
                          className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        >
                          Confirmar Solicitação
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                }
              />
              <RightCard
                icon={FileOutput}
                title="Portabilidade"
                description="Solicite a portabilidade dos seus dados para outro controlador."
                action={
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs"
                    onClick={() => createRequest.mutate('portabilidade')}
                    disabled={createRequest.isPending}
                  >
                    <FileOutput className="h-3 w-3 mr-1" />
                    Solicitar Portabilidade
                  </Button>
                }
              />
            </div>
          </div>

          <Separator />

          {/* DPO Section */}
          <div className="space-y-3">
            <h2 className="text-lg font-semibold">Encarregado de Dados (DPO)</h2>
            <Card>
              <CardContent className="p-4 sm:p-5 space-y-3">
                <div className="flex items-center gap-2">
                  <Mail className="h-4 w-4 text-primary" />
                  <a
                    href="mailto:dpo@verus.ai"
                    className="text-sm text-primary hover:underline"
                  >
                    dpo@verus.ai
                  </a>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Conforme a Lei Geral de Proteção de Dados (Lei n.º 13.709/2018), você tem o
                  direito de solicitar informações sobre o tratamento dos seus dados pessoais,
                  corrigir dados incompletos ou desatualizados, solicitar a anonimização, bloqueio
                  ou eliminação de dados desnecessários, e revogar consentimentos previamente
                  concedidos. Para exercer esses direitos ou esclarecer dúvidas, entre em contato
                  com nosso Encarregado de Dados (DPO) pelo e-mail acima.
                </p>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

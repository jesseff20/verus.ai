'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  useClientPortalPendingConsents,
  useClientPortalAcceptConsent,
} from '@/hooks/use-client-portal';
import type { ClientConsent } from '@/hooks/use-client-portal';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  ShieldCheck,
  Loader2,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react';

export default function ConsentimentoPage() {
  const { data: consents, isLoading, error } = useClientPortalPendingConsents();
  const acceptMutation = useClientPortalAcceptConsent();
  const router = useRouter();

  const [acceptedMap, setAcceptedMap] = useState<Record<string, boolean>>({});
  const [acceptingId, setAcceptingId] = useState<string | null>(null);

  const handleToggle = (id: string, checked: boolean) => {
    setAcceptedMap((prev) => ({ ...prev, [id]: checked }));
  };

  const handleAccept = async (consent: ClientConsent) => {
    setAcceptingId(consent.id);
    try {
      await acceptMutation.mutateAsync(consent.id);
    } finally {
      setAcceptingId(null);
    }
  };

  // Redirect when all consents are accepted (empty pending list after refetch)
  const allAccepted = consents && consents.length === 0;

  if (allAccepted) {
    router.push('/portal');
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-4">
        <CheckCircle2 className="h-12 w-12 text-green-600" />
        <p className="text-sm text-muted-foreground">
          Todos os termos foram aceitos. Redirecionando...
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="flex justify-center mb-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10">
            <ShieldCheck className="h-6 w-6 text-primary" />
          </div>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
          Termos de Consentimento
        </h1>
        <p className="text-muted-foreground text-sm mt-2 max-w-md mx-auto">
          Para continuar utilizando o portal, é necessário aceitar os termos abaixo conforme a LGPD.
        </p>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center justify-center py-16 text-destructive gap-2">
          <AlertTriangle className="h-5 w-5" />
          <span>Erro ao carregar termos de consentimento</span>
        </div>
      )}

      {/* Consent cards */}
      {consents && consents.length > 0 && (
        <div className="space-y-4 max-w-2xl mx-auto">
          {consents.map((consent) => {
            const isChecked = !!acceptedMap[consent.id];
            const isAccepting = acceptingId === consent.id;

            return (
              <Card key={consent.id} className="overflow-hidden">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-3">
                    <CardTitle className="text-base">{consent.title}</CardTitle>
                    <Badge variant="outline" className="text-[10px] shrink-0">
                      v{consent.version}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Scrollable content */}
                  <ScrollArea className="h-48 w-full rounded-lg border bg-muted/30 p-4">
                    <div className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
                      {consent.content}
                    </div>
                  </ScrollArea>

                  {/* Accept checkbox */}
                  <div className="flex items-start gap-3">
                    <Checkbox
                      id={`consent-${consent.id}`}
                      checked={isChecked}
                      onCheckedChange={(checked) =>
                        handleToggle(consent.id, checked === true)
                      }
                      disabled={isAccepting}
                    />
                    <label
                      htmlFor={`consent-${consent.id}`}
                      className="text-sm font-medium leading-tight cursor-pointer select-none"
                    >
                      Li e aceito os termos acima
                    </label>
                  </div>

                  {/* Accept button */}
                  <Button
                    className="w-full"
                    disabled={!isChecked || isAccepting}
                    onClick={() => handleAccept(consent)}
                  >
                    {isAccepting ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Aceitando...
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="mr-2 h-4 w-4" />
                        Aceitar Termo
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

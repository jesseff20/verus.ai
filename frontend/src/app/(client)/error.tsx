'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

export default function ClientPortalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Client portal error:', error);
  }, [error]);

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center space-y-6 max-w-md mx-auto px-4">
        <div className="mx-auto w-14 h-14 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
          <AlertTriangle className="h-7 w-7 text-red-600" />
        </div>
        <div>
          <h2 className="text-xl font-bold">Erro no portal</h2>
          <p className="text-muted-foreground mt-2">
            Ocorreu um erro ao carregar esta página. Por favor, tente novamente ou retorne à página inicial do portal.
          </p>
        </div>
        <div className="flex gap-3 justify-center">
          <Button onClick={reset} variant="default" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Tentar novamente
          </Button>
          <Button onClick={() => window.location.href = '/portal'} variant="outline" size="sm">
            <Home className="h-4 w-4 mr-2" />
            Portal
          </Button>
        </div>
      </div>
    </div>
  );
}

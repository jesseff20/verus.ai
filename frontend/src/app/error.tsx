'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('App error:', error);
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-center space-y-6 max-w-md mx-auto px-4">
        <div className="mx-auto w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
          <AlertTriangle className="h-8 w-8 text-red-600" />
        </div>
        <div>
          <h2 className="text-2xl font-bold">Algo deu errado</h2>
          <p className="text-muted-foreground mt-2">
            Ocorreu um erro inesperado. Tente novamente ou volte à página inicial.
          </p>
        </div>
        <div className="flex gap-3 justify-center">
          <Button onClick={reset} variant="default">
            <RefreshCw className="h-4 w-4 mr-2" />
            Tentar novamente
          </Button>
          <Button onClick={() => window.location.href = '/dashboard'} variant="outline">
            <Home className="h-4 w-4 mr-2" />
            Página inicial
          </Button>
        </div>
        {error.digest && (
          <p className="text-xs text-muted-foreground">Código: {error.digest}</p>
        )}
      </div>
    </div>
  );
}

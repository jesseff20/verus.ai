'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Dashboard error:', error);
  }, [error]);

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center space-y-6 max-w-md mx-auto px-4">
        <div className="mx-auto w-14 h-14 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
          <AlertTriangle className="h-7 w-7 text-red-600" />
        </div>
        <div>
          <h2 className="text-xl font-bold">Erro no módulo</h2>
          <p className="text-muted-foreground mt-2">
            Ocorreu um erro ao carregar esta funcionalidade. Os demais módulos continuam disponíveis.
          </p>
        </div>
        <div className="flex gap-3 justify-center">
          <Button onClick={reset} variant="default" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Tentar novamente
          </Button>
          <Button onClick={() => window.location.href = '/dashboard'} variant="outline" size="sm">
            <Home className="h-4 w-4 mr-2" />
            Dashboard
          </Button>
        </div>
      </div>
    </div>
  );
}

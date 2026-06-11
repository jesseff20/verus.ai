'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 5 * 60 * 1000, // 5 minutos - dados considerados frescos
            gcTime: 10 * 60 * 1000, // 10 minutos - tempo de cache
            refetchOnWindowFocus: false, // Não refetch ao focar janela
            retry: (failureCount, error: any) => {
              // Nunca retenta erros de autenticação — o interceptor já trata refresh/redirect
              const status = (error as any)?.response?.status;
              if (status === 401 || status === 403) return false;
              // Para outros erros, permite apenas 1 retry
              return failureCount < 1;
            },
            throwOnError: false, // Erros de query não quebram o render tree
          },
          mutations: {
            retry: 0, // Mutations nunca retentam — podem ter efeitos colaterais
            throwOnError: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}

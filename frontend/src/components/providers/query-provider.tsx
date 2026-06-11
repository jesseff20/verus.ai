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
            retry: 1, // Apenas 1 retry em caso de erro
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

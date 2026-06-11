'use client';

import { useEffect, useRef } from 'react';
import { useAuth } from './use-auth';

/**
 * Verifica periodicamente se a sessão ainda está válida.
 * Útil em páginas de longa duração onde o usuário pode ficar idle por > 1h.
 *
 * O interceptor do axios já trata 401 em qualquer requisição,
 * mas este hook adiciona uma verificação proativa opcional.
 */
export function useSessionGuard(intervalMs = 15 * 60 * 1000) {
  const { isAuthenticated, checkAuth } = useAuth();
  const lastCheckRef = useRef(Date.now());

  useEffect(() => {
    if (!isAuthenticated) return;

    const id = setInterval(() => {
      // Só verifica se passou o intervalo desde o último check
      if (Date.now() - lastCheckRef.current >= intervalMs) {
        lastCheckRef.current = Date.now();
        checkAuth();
      }
    }, Math.min(intervalMs, 60_000)); // tick no máximo a cada 1 min

    return () => clearInterval(id);
  }, [isAuthenticated, checkAuth, intervalMs]);
}

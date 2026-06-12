'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import api, { resetRedirectFlag } from '@/lib/api';
import type { User, LoginCredentials, AuthResponse } from '@/types';

export function useAuth() {
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const queryClient = useQueryClient();

  // Usar React Query para buscar dados do usuário autenticado
  const {
    data: user,
    isLoading: loading,
    refetch: checkAuth,
  } = useQuery({
    queryKey: ['current-user'],
    queryFn: async () => {
      const token = localStorage.getItem('access_token');
      if (!token) {
        return null;
      }

      try {
        const response = await api.get<User>('/api/v1/auth/users/me/');
        return response.data;
      } catch (err: any) {
        // Erros de rede (ERR_TOO_MANY_REDIRECTS, timeout, ECONNREFUSED) não devem
        // deslogar o usuário — o token pode ser válido mas o servidor estar
        // temporariamente inacessível. Só logout em rejeição explícita do servidor.
        const status = err?.response?.status;
        if (status === 401) {
          // 401 já foi tratado pelo interceptor (tentou refresh + redirect se necessário)
          return null;
        }
        if (!status) {
          // Erro de rede (sem resposta HTTP): preserva sessão, retorna token como sinal
          // de que o usuário pode estar autenticado — o interceptor não redirecionou.
          // Retorna undefined para não atualizar o cache, preservando valor anterior.
          throw err; // deixa React Query manter o estado anterior (staleWhileRevalidate)
        }
        // Qualquer outro erro HTTP (5xx, 403) — não deslogar
        throw err;
      }
    },
    staleTime: 24 * 60 * 60 * 1000, // 24 horas — coincide com o lifetime do access token
    gcTime: 30 * 60 * 1000,
    retry: (failureCount, error: any) => {
      // Nunca retenta em 401 (token inválido) — evita duplicate redirects
      // Retenta UMA vez em erros de rede (pode ser problema temporário)
      if (error?.response?.status === 401) return false;
      return failureCount < 1;
    },
    refetchOnWindowFocus: false,
  });

  const login = async (credentials: LoginCredentials): Promise<void> => {
    try {
      setError(null);

      // Reseta o flag de redirect para que a próxima expiração de token funcione corretamente
      resetRedirectFlag();

      const response = await api.post('/api/v1/auth/login/', credentials);
      const { user: userData, tokens } = response.data;

      // Salvar tokens no localStorage
      localStorage.setItem('access_token', tokens.access);
      localStorage.setItem('refresh_token', tokens.refresh);

      // Atualizar cache do React Query com dados do usuário
      queryClient.setQueryData(['current-user'], userData);

      // Todos os perfis vão para dashboard (sidebar filtra por permissões)
      router.push('/dashboard');
    } catch (err: any) {
      const responseData = err.response?.data;
      let errorMessage = 'Erro ao fazer login. Tente novamente.';

      if (responseData?.detail) {
        errorMessage = responseData.detail;
      } else if (responseData?.non_field_errors?.length > 0) {
        errorMessage = 'Usuário ou senha incorretos.';
      } else if (responseData?.username || responseData?.password) {
        errorMessage = 'Preencha todos os campos.';
      }

      setError(errorMessage);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');

    // Limpar cache do React Query
    queryClient.setQueryData(['current-user'], null);
    queryClient.clear(); // Limpar todo o cache ao fazer logout

    router.push('/login');
  };

  const isAuthenticated = !!user;

  const hasPermission = (requiredRole: User['role']): boolean => {
    if (!user) return false;

    // Espelha exatamente User.ROLE_HIERARCHY do backend (accounts/models.py)
    const roleHierarchy: Record<string, number> = {
      superadmin: 100,
      admin: 90,
      // Procuradoria roles (verus.ai) — ordem idêntica ao backend
      procurador_geral: 85,
      subprocurador_geral: 80,
      gerente: 70,
      procurador: 60,
      assessor_gerencial: 50,
      assessor_gabinete: 45,
      distribuidor: 30,
      servidor: 15,
      visualizador: 1,
      // Aliases legados do ROLE_ALIASES do backend (compatibilidade com dados migrados)
      socio: 85,           // → procurador_geral
      gestor: 70,          // → gerente
      coordenador: 70,     // → gerente
      advogado_senior: 60, // → procurador
      advogado_pleno: 60,  // → procurador
      advogado_junior: 60, // → procurador
      assessor: 50,        // → assessor_gerencial
      analista: 15,        // → servidor
      assistente: 15,      // → servidor
      paralegal: 15,       // → servidor
      revisor: 15,         // → servidor
      auditor: 15,         // → servidor
      secretaria: 30,      // → distribuidor
      estagiario: 1,       // → visualizador
      cliente: 1,          // → visualizador
      // Aliases antigos em inglês
      manager: 70,         // → gerente
      reviewer: 15,        // → servidor
      analyst: 15,         // → servidor
      viewer: 1,           // → visualizador
      // Outros legacy (backwards compatibility)
      defensor: 60,
      promotor: 60,
      supervisor: 60,
    };

    const userLevel = roleHierarchy[user.role] || 0;
    const requiredLevel = roleHierarchy[requiredRole] || 0;

    return userLevel >= requiredLevel;
  };

  return {
    user,
    loading,
    error,
    login,
    logout,
    isAuthenticated,
    hasPermission,
    checkAuth,
  };
}

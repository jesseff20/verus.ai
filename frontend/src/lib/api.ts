import axios from 'axios';
import { toast } from 'sonner';

// Sempre usar URLs relativas — o Next.js rewrites (next.config.js) proxia /api/v1/*
// para o backend Django dentro da rede Docker. Não depender de nenhuma variável de
// ambiente no browser para evitar loop de redirect quando NEXT_PUBLIC_API_URL aponta
// para o domínio público (que voltaria ao próprio Next.js).
const API_BASE_URL = '';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para adicionar token JWT em todas as requisições
api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Single-flight: todas as requisicoes que falharem 401 em paralelo
// compartilham o MESMO refresh - evita stampede e race condition no localStorage
let refreshPromise: Promise<string> | null = null;

// Flag para garantir que o redirect para /login ocorra no máximo uma vez por sessão,
// evitando ERR_TOO_MANY_REDIRECTS quando múltiplas requests 401 disparam em paralelo.
let redirectingToLogin = false;

function redirectToLogin() {
  if (typeof window !== 'undefined' && !redirectingToLogin && window.location.pathname !== '/login') {
    redirectingToLogin = true;
    // Limpar tokens antes de redirecionar
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  }
}

function refreshAccessToken(): Promise<string> {
  if (refreshPromise) return refreshPromise;

  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) {
    redirectToLogin();
    return Promise.reject(new Error('No refresh token'));
  }

  refreshPromise = axios
    .post(`${API_BASE_URL}/api/v1/auth/token/refresh/`, {
      refresh: refreshToken,
    })
    .then((response) => {
      const { access } = response.data;
      localStorage.setItem('access_token', access);
      return access as string;
    })
    .catch((refreshError) => {
      // Só redireciona para /login se o servidor REJEITOU explicitamente o token
      // (401/400/403). Erros de rede (ERR_TOO_MANY_REDIRECTS, ECONNREFUSED, timeout)
      // NÃO devem deslogar o usuário — o token pode ainda ser válido.
      const status = refreshError?.response?.status;
      const isExplicitAuthRejection = status === 401 || status === 400 || status === 403;
      if (isExplicitAuthRejection) {
        redirectToLogin();
      }
      throw refreshError;
    })
    .finally(() => {
      refreshPromise = null;
    });

  return refreshPromise;
}

// Interceptor para tratar erros e renovar token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      if (typeof window !== 'undefined') {
        try {
          const access = await refreshAccessToken();
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        } catch {
          return Promise.reject(error);
        }
      }
    }

    // Toast de erro para falhas HTTP genéricas (exceto 401 já tratado acima)
    const httpStatus = error.response?.status;
    if (httpStatus && httpStatus !== 401) {
      let message = 'Ocorreu um erro. Tente novamente.';
      if (httpStatus === 400 || httpStatus === 422) {
        message = 'Dados inválidos. Verifique as informações e tente novamente.';
      } else if (httpStatus === 403) {
        message = 'Você não tem permissão para esta ação.';
      } else if (httpStatus === 404) {
        message = 'Recurso não encontrado.';
      } else if (httpStatus === 429) {
        message = 'Muitas requisições. Aguarde um momento e tente novamente.';
      } else if (httpStatus >= 500) {
        message = 'Erro no servidor. Tente novamente em alguns instantes.';
      }
      if (typeof window !== 'undefined') {
        toast.error(message);
      }
    }

    return Promise.reject(error);
  }
);

// Reseta o flag de redirect (chamar após login bem-sucedido)
export function resetRedirectFlag() {
  redirectingToLogin = false;
}

// Cliente público sem autenticação (para endpoints públicos como brand-settings)
export const publicApi = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// publicApi não precisa de interceptor de auth, mas deve logar erros de servidor
publicApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status >= 500) {
      console.error('[publicApi] Server error:', error.response?.status, error.config?.url);
    }
    return Promise.reject(error);
  }
);

export default api;

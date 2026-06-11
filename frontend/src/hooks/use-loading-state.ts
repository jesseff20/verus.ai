'use client';

import { useState, useCallback, useEffect } from 'react';

export interface LoadingStateConfig {
  /** Tempo mínimo de exibição do loading (ms) - evita flicker */
  minDisplayTime?: number;
  /** Tempo máximo antes de mostrar estimativa "demorada" (ms) */
  slowThreshold?: number;
  /** Mensagem personalizada para cada estado */
  messages?: Record<string, string>;
  /** Callback quando loading completa */
  onComplete?: () => void;
  /** Callback quando loading demora muito */
  onSlow?: () => void;
}

export interface LoadingStateReturn {
  /** Loading está ativo? */
  isLoading: boolean;
  /** Inicia loading */
  startLoading: (operationId?: string) => void;
  /** Para loading */
  stopLoading: () => void;
  /** Loading com promise */
  withLoading: <T>(promise: Promise<T>) => Promise<T>;
  /** Progresso estimado (0-100) */
  progress: number | null;
  /** Tempo estimado restante (ms) */
  estimatedTimeRemaining: number | null;
  /** Mensagem atual do loading */
  loadingMessage: string;
  /** Loading está "lento"? */
  isSlow: boolean;
  /** Tempo decorrido (ms) */
  elapsedTime: number;
}

/**
 * Hook para gerenciar estados de loading com estimativa de tempo
 *
 * @example
 * const { isLoading, startLoading, stopLoading, withLoading, progress, loadingMessage } = useLoadingState({
 *   minDisplayTime: 300,
 *   slowThreshold: 3000,
 *   messages: {
 *     'saving': 'Salvando documento...',
 *     'generating': 'Gerando minuta...',
 *   },
 * });
 */
export function useLoadingState(config: LoadingStateConfig = {}): LoadingStateReturn {
  const {
    minDisplayTime = 300,
    slowThreshold = 3000,
    messages = {},
    onComplete,
    onSlow,
  } = config;

  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);
  const [estimatedTime, setEstimatedTime] = useState<number | null>(null);
  const [operationId, setOperationId] = useState<string | null>(null);
  const [startTime, setStartTime] = useState<number>(0);
  const [elapsedTime, setElapsedTime] = useState<number>(0);
  const [isSlow, setIsSlow] = useState(false);
  const [shouldWait, setShouldWait] = useState(false);

  // Timer para tempo decorrido
  useEffect(() => {
    if (!isLoading) {
      setElapsedTime(0);
      setIsSlow(false);
      return;
    }

    setStartTime(Date.now());
    const timer = setInterval(() => {
      const elapsed = Date.now() - startTime;
      setElapsedTime(elapsed);

      // Marcar como "lento" após threshold
      if (elapsed >= slowThreshold && !isSlow) {
        setIsSlow(true);
        onSlow?.();
      }

      // Estimativa de progresso (linear baseado no tempo)
      // Assume 10s como tempo "normal" de operação
      const estimatedProgress = Math.min((elapsed / 10000) * 100, 95);
      setProgress(Math.round(estimatedProgress));

      // Tempo estimado restante (baseado em 10s como referência)
      const remaining = Math.max(10000 - elapsed, 0);
      setEstimatedTime(remaining);
    }, 100);

    return () => clearInterval(timer);
  }, [isLoading, startTime, slowThreshold, isSlow, onSlow]);

  // Iniciar loading
  const startLoading = useCallback((id?: string) => {
    setOperationId(id || 'default');
    setIsLoading(true);
    setShouldWait(true);

    // Delay mínimo de exibição
    setTimeout(() => {
      setShouldWait(false);
    }, minDisplayTime);
  }, [minDisplayTime]);

  // Parar loading
  const stopLoading = useCallback(() => {
    if (shouldWait) {
      // Esperar tempo mínimo passar
      setTimeout(() => {
        setIsLoading(false);
        setProgress(null);
        setEstimatedTime(null);
        setOperationId(null);
        onComplete?.();
      }, minDisplayTime - elapsedTime);
    } else {
      setIsLoading(false);
      setProgress(null);
      setEstimatedTime(null);
      setOperationId(null);
      onComplete?.();
    }
  }, [shouldWait, elapsedTime, minDisplayTime, onComplete]);

  // Loading com promise
  const withLoading = useCallback(async <T>(promise: Promise<T>): Promise<T> => {
    startLoading();
    try {
      const result = await promise;
      stopLoading();
      return result;
    } catch (error) {
      stopLoading();
      throw error;
    }
  }, [startLoading, stopLoading]);

  // Mensagem atual baseada no operationId
  const loadingMessage = operationId ? (messages[operationId] || messages.default || 'Carregando...') : '';

  return {
    isLoading,
    startLoading,
    stopLoading,
    withLoading,
    progress,
    estimatedTimeRemaining: estimatedTime,
    loadingMessage,
    isSlow,
    elapsedTime,
  };
}

/**
 * Hook para loading de operações específicas com mensagens customizadas
 */
export function useOperationLoading(operations: Record<string, { message: string; estimatedDuration?: number }>) {
  const [currentOperation, setCurrentOperation] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [startTime, setStartTime] = useState<number>(0);

  const startOperation = useCallback((operationKey: string) => {
    const op = operations[operationKey];
    if (!op) return;

    setCurrentOperation(operationKey);
    setStartTime(Date.now());
    setProgress(0);

    // Simular progresso baseado na duração estimada
    if (op.estimatedDuration) {
      const interval = setInterval(() => {
        const elapsed = Date.now() - startTime;
        const newProgress = Math.min((elapsed / op.estimatedDuration!) * 100, 95);
        setProgress(Math.round(newProgress));
      }, 200);

      return () => clearInterval(interval);
    }
  }, [operations, startTime]);

  const completeOperation = useCallback(() => {
    setProgress(100);
    setTimeout(() => {
      setCurrentOperation(null);
      setProgress(0);
    }, 300);
  }, []);

  const currentMessage = currentOperation ? operations[currentOperation]?.message : '';
  const isLoading = currentOperation !== null;

  return {
    isLoading,
    currentOperation,
    currentMessage,
    progress,
    startOperation,
    completeOperation,
  };
}

/**
 * Componente de Loading Spinner com mensagem e tempo estimado
 */
export interface LoadingDisplayProps {
  isLoading: boolean;
  message?: string;
  progress?: number | null;
  estimatedTimeRemaining?: number | null;
  isSlow?: boolean;
}

export function formatTime(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.round(ms / 60000)}min`;
}

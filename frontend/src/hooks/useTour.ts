'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { usePathname } from 'next/navigation';
import { tourConfigs, type TourStep } from '@/components/tour/tourConfig';

// ── Tipos ──────────────────────────────────────────────────────

export type TourStatus = 'not_started' | 'in_progress' | 'completed' | 'skipped' | 'postponed_session';

export type TourAnalyticsEvent =
  | 'tour_shown'
  | 'tour_started'
  | 'tour_step_viewed'
  | 'tour_step_abandoned'
  | 'tour_completed'
  | 'tour_skipped'
  | 'tour_postponed';

export interface TourState {
  status: TourStatus;
  currentStepIndex: number;
  currentTourId: string | null;
}

// ── Constantes ─────────────────────────────────────────────────

const TOUR_VERSION = 'v1.0';
const STORAGE_KEY_PREFIX = 'verus_tour_';
const POSTPONED_SESSION_KEY = 'verus_tour_postponed';

// ── Persistência ───────────────────────────────────────────────

function getPersistedStatus(tourId: string): { status: TourStatus; version: string } | null {
  try {
    const raw = localStorage.getItem(`${STORAGE_KEY_PREFIX}${tourId}`);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function persistStatus(tourId: string, status: TourStatus): void {
  try {
    localStorage.setItem(
      `${STORAGE_KEY_PREFIX}${tourId}`,
      JSON.stringify({ status, version: TOUR_VERSION }),
    );
  } catch {
    // localStorage indisponível (private mode, quota)
  }
}

// ── Hook principal ─────────────────────────────────────────────

export function useTour() {
  const pathname = usePathname();
  const [state, setState] = useState<TourState>({
    status: 'not_started',
    currentStepIndex: 0,
    currentTourId: null,
  });
  const [targetElement, setTargetElement] = useState<Element | null>(null);
  const [isTargetReady, setIsTargetReady] = useState(false);
  const retryCount = useRef(0);
  const maxRetries = 10;

  // Determina qual tour configura para a rota atual
  const currentConfig = tourConfigs.find((cfg) => {
    if (typeof cfg.route === 'string') {
      return pathname === cfg.route;
    }
    return cfg.route.test(pathname);
  });

  // Tour ativo (em andamento)
  const isActive = state.status === 'in_progress' && state.currentTourId !== null;
  const currentSteps: TourStep[] = currentConfig?.steps ?? [];
  const currentStep = isActive ? currentSteps[state.currentStepIndex] : null;
  const isLastStep = isActive && state.currentStepIndex >= currentSteps.length - 1;
  const totalSteps = currentSteps.length;

  // ── Analytics ───────────────────────────────────────────────
  const track = useCallback((event: TourAnalyticsEvent, data?: Record<string, unknown>) => {
    if (typeof window === 'undefined') return;
    try {
      console.info('[Tour Analytics]', {
        event,
        tourId: state.currentTourId,
        stepIndex: state.currentStepIndex,
        pathname,
        timestamp: new Date().toISOString(),
        ...data,
      });
    } catch {
      // analytics não essencial
    }
  }, [state.currentTourId, state.currentStepIndex, pathname]);

  // ── Verificar se deve mostrar tour ─────────────────────────
  const shouldShowTour = useCallback((): boolean => {
    if (!currentConfig) return false;

    // Verificar postponed na sessão
    if (typeof window !== 'undefined' && sessionStorage.getItem(POSTPONED_SESSION_KEY) === 'true') {
      return false;
    }

    const persisted = getPersistedStatus(currentConfig.id);
    if (!persisted) return true;

    // Completed ou skipped: não mostrar
    if (persisted.status === 'completed' || persisted.status === 'skipped') {
      return false;
    }

    // Versão diferente: mostrar novamente
    if (persisted.version !== TOUR_VERSION) return true;

    // In progress: continuar
    if (persisted.status === 'in_progress') return true;

    return true;
  }, [currentConfig]);

  // ── Iniciar tour ────────────────────────────────────────────
  const startTour = useCallback(() => {
    if (!currentConfig || currentSteps.length === 0) return;

    setState({
      status: 'in_progress',
      currentStepIndex: 0,
      currentTourId: currentConfig.id,
    });
    track('tour_started');
  }, [currentConfig, currentSteps.length, track]);

  // ── Avançar etapa ───────────────────────────────────────────
  const nextStep = useCallback(() => {
    setState((prev) => {
      const nextIndex = prev.currentStepIndex + 1;
      if (nextIndex >= currentSteps.length) {
        // Última etapa → concluir
        if (prev.currentTourId) {
          persistStatus(prev.currentTourId, 'completed');
          track('tour_completed', { totalSteps: currentSteps.length });
        }
        return { status: 'completed', currentStepIndex: 0, currentTourId: null };
      }
      track('tour_step_viewed', { step: nextIndex });
      return { ...prev, currentStepIndex: nextIndex };
    });
  }, [currentSteps.length, track]);

  // ── Voltar etapa ────────────────────────────────────────────
  const prevStep = useCallback(() => {
    setState((prev) => ({
      ...prev,
      currentStepIndex: Math.max(0, prev.currentStepIndex - 1),
    }));
  }, []);

  // ── Pular tour (definitivo) ─────────────────────────────────
  const skipTour = useCallback(() => {
    if (state.currentTourId) {
      persistStatus(state.currentTourId, 'skipped');
      track('tour_skipped');
    }
    setState({ status: 'skipped', currentStepIndex: 0, currentTourId: null });
  }, [state.currentTourId, track]);

  // ── Deixar para depois (sessão) ─────────────────────────────
  const postponeTour = useCallback(() => {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem(POSTPONED_SESSION_KEY, 'true');
    }
    track('tour_postponed');
    setState({ status: 'postponed_session', currentStepIndex: 0, currentTourId: null });
  }, [track]);

  // ── Concluir tour ───────────────────────────────────────────
  const completeTour = useCallback(() => {
    if (state.currentTourId) {
      persistStatus(state.currentTourId, 'completed');
      track('tour_completed', { totalSteps: currentSteps.length });
    }
    setState({ status: 'completed', currentStepIndex: 0, currentTourId: null });
  }, [state.currentTourId, currentSteps.length, track]);

  // ── Reset manual (rever tour) ───────────────────────────────
  const resetTour = useCallback((tourId: string) => {
    try {
      localStorage.removeItem(`${STORAGE_KEY_PREFIX}${tourId}`);
    } catch {
      // ignore
    }
    track('tour_started', { reset: true });
  }, [track]);

  // ── Observar elemento alvo ──────────────────────────────────
  useEffect(() => {
    if (!isActive || !currentStep) {
      setTargetElement(null);
      setIsTargetReady(false);
      return;
    }

    const target = currentStep.target;
    if (!target) {
      // Step sem target específico (overlay central)
      setTargetElement(null);
      setIsTargetReady(true);
      return;
    }

    // Tentar encontrar o elemento com retry
    const findElement = () => {
      const el = document.querySelector(target);
      if (el) {
        setTargetElement(el);
        setIsTargetReady(true);
        retryCount.current = 0;
        return true;
      }
      return false;
    };

    if (findElement()) return;

    // Retry com MutationObserver + timeout
    const observer = new MutationObserver(() => {
      if (findElement()) observer.disconnect();
    });
    observer.observe(document.body, { childList: true, subtree: true });

    const interval = setInterval(() => {
      retryCount.current += 1;
      if (findElement() || retryCount.current >= maxRetries) {
        clearInterval(interval);
        observer.disconnect();
        if (!findElement()) {
          // Elemento não encontrado após retries: pular etapa
          console.warn(`[Tour] Elemento "${target}" não encontrado. Pulando etapa.`);
          setIsTargetReady(true);
        }
        retryCount.current = 0;
      }
    }, 500);

    return () => {
      clearInterval(interval);
      observer.disconnect();
      retryCount.current = 0;
    };
  }, [isActive, currentStep]);

  // ── Auto-exibir tour ao entrar na rota ──────────────────────
  useEffect(() => {
    if (!currentConfig || currentSteps.length === 0) return;

    // Se já está ativo, não reiniciar
    if (isActive) return;

    if (shouldShowTour()) {
      // Pequeno delay para garantir que o DOM esteja pronto
      const timer = setTimeout(() => {
        track('tour_shown');
        startTour();
      }, 800);
      return () => clearTimeout(timer);
    }
  }, [pathname, currentConfig, shouldShowTour, startTour, isActive, track, currentSteps.length]);

  // ── Tecla Esc ──────────────────────────────────────────────
  useEffect(() => {
    if (!isActive) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        postponeTour();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isActive, postponeTour]);

  return {
    // Estado
    isActive,
    isTargetReady,
    currentStep,
    currentStepIndex: state.currentStepIndex,
    totalSteps,
    isLastStep,
    currentTourId: state.currentTourId,
    tourStatus: state.status,

    // Ações
    startTour,
    nextStep,
    prevStep,
    skipTour,
    postponeTour,
    completeTour,
    resetTour,

    // DOM
    targetElement,
  };
}
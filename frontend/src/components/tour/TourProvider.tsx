'use client';

import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { useTour } from '@/hooks/useTour';
import TourStepOverlay from './TourStepOverlay';
import { type TourStep } from './tourConfig';
import { useAuth } from '@/hooks/use-auth';

// ── Contexto ───────────────────────────────────────────────────

interface TourContextValue {
  /** Se um tour está ativo no momento */
  isActive: boolean;
  /** Iniciar o tour manualmente */
  startTour: () => void;
  /** Resetar o estado de um tour para poder revê-lo */
  resetTour: (tourId: string) => void;
  /** Status atual do tour */
  tourStatus: string;
}

const TourContext = createContext<TourContextValue>({
  isActive: false,
  startTour: () => {},
  resetTour: () => {},
  tourStatus: 'not_started',
});

export function useTourContext() {
  return useContext(TourContext);
}

// ── Provider ───────────────────────────────────────────────────

export function TourProvider({ children }: { children: ReactNode }) {
  const { hasPermission } = useAuth();
  const [hasAborted, setHasAborted] = useState(false);

  const {
    isActive,
    isTargetReady,
    currentStep,
    currentStepIndex,
    totalSteps,
    isLastStep,
    startTour,
    nextStep,
    prevStep,
    skipTour,
    postponeTour,
    completeTour,
    resetTour,
    targetElement,
    tourStatus,
  } = useTour();

  // Safety abort: se o tour estiver ativo por mais de 15 minutos, força cancelamento
  useEffect(() => {
    if (!isActive) return;
    const safetyTimer = setTimeout(() => {
      console.warn('[Tour] Safety timeout atingido (15min). Abortando tour.');
      postponeTour();
      setHasAborted(true);
    }, 15 * 60 * 1000);
    return () => clearTimeout(safetyTimer);
  }, [isActive, postponeTour]);

  // Reset abort flag when tour becomes inactive
  useEffect(() => {
    if (!isActive) setHasAborted(false);
  }, [isActive]);

  const canRenderStep = (step: TourStep | null): boolean => {
    if (!step) return false;
    if (step.requiredPermission && !hasPermission(step.requiredPermission)) {
      return false;
    }
    return true;
  };

  return (
    <TourContext.Provider
      value={{
        isActive: isActive && !hasAborted,
        startTour,
        resetTour,
        tourStatus,
      }}
    >
      {children}

      {/* Renderizar overlay do tour quando ativo */}
      {isActive && !hasAborted && currentStep && canRenderStep(currentStep) && isTargetReady && (
        <TourStepOverlay
          step={currentStep}
          stepIndex={currentStepIndex}
          totalSteps={totalSteps}
          targetElement={targetElement}
          isLastStep={isLastStep}
          onNext={nextStep}
          onPrev={prevStep}
          onSkip={skipTour}
          onPostpone={postponeTour}
          onComplete={completeTour}
        />
      )}
    </TourContext.Provider>
  );
}
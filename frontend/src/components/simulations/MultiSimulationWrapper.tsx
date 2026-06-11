'use client';

import { useState, useCallback, createContext, useContext, type ReactNode } from 'react';
import SimulationCountSelector from './SimulationCountSelector';
import SimulationTabBar, { type SimTab, type SimTabStatus } from './SimulationTabBar';

// --- Context for multi-simulation state ---

interface MultiSimContextValue {
  simulationCount: number;
  activeSimIndex: number;
  setActiveSimIndex: (i: number) => void;
  tabs: SimTab[];
  updateTabStatus: (index: number, status: SimTabStatus) => void;
  /** Call this from the page's start function to get the list of indices to run */
  getIndicesToRun: () => number[];
}

const MultiSimContext = createContext<MultiSimContextValue | null>(null);

export function useMultiSimContext() {
  const ctx = useContext(MultiSimContext);
  if (!ctx) throw new Error('useMultiSimContext must be used within MultiSimulationProvider');
  return ctx;
}

// --- Provider component ---

interface MultiSimulationProviderProps {
  children: ReactNode;
  simulationCount: number;
  setSimulationCount: (n: number) => void;
  activeSimIndex: number;
  setActiveSimIndex: (i: number) => void;
  tabs: SimTab[];
  updateTabStatus: (index: number, status: SimTabStatus) => void;
  resetTabs: (count: number) => void;
}

export function MultiSimulationProvider({
  children,
  simulationCount,
  setSimulationCount,
  activeSimIndex,
  setActiveSimIndex,
  tabs,
  updateTabStatus,
  resetTabs,
}: MultiSimulationProviderProps) {
  const getIndicesToRun = useCallback(() => {
    return Array.from({ length: simulationCount }, (_, i) => i);
  }, [simulationCount]);

  return (
    <MultiSimContext.Provider
      value={{
        simulationCount,
        activeSimIndex,
        setActiveSimIndex,
        tabs,
        updateTabStatus,
        getIndicesToRun,
      }}
    >
      {children}
    </MultiSimContext.Provider>
  );
}

// --- Re-export for convenience ---
export { SimulationCountSelector, SimulationTabBar };
export type { SimTab, SimTabStatus };

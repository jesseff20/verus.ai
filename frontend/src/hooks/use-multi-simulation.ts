import { useState, useCallback, useRef } from 'react';
import type { SimTab, SimTabStatus } from '@/components/simulations/SimulationTabBar';

export interface MultiSimState {
  simulationCount: number;
  setSimulationCount: (count: number) => void;
  activeSimIndex: number;
  setActiveSimIndex: (index: number) => void;
  tabs: SimTab[];
  updateTabStatus: (index: number, status: SimTabStatus) => void;
  resetTabs: (count: number) => void;
  /** Store a snapshot of completed simulation results */
  storeResult: (index: number, result: any) => void;
  /** Get stored result for a given index */
  getResult: (index: number) => any;
  /** All stored results */
  storedResults: Map<number, any>;
}

export function useMultiSimulation(): MultiSimState {
  const [simulationCount, setSimulationCountState] = useState(1);
  const [activeSimIndex, setActiveSimIndex] = useState(0);
  const [tabs, setTabs] = useState<SimTab[]>([
    { index: 0, label: 'Sim #1', status: 'idle' },
  ]);
  const storedResultsRef = useRef<Map<number, any>>(new Map());
  const [storedResults, setStoredResults] = useState<Map<number, any>>(new Map());

  const updateTabStatus = useCallback((index: number, status: SimTabStatus) => {
    setTabs((prev) =>
      prev.map((t) => (t.index === index ? { ...t, status } : t))
    );
  }, []);

  const resetTabs = useCallback((count: number) => {
    setTabs(
      Array.from({ length: count }, (_, i) => ({
        index: i,
        label: `Sim #${i + 1}`,
        status: 'idle' as SimTabStatus,
      }))
    );
    setActiveSimIndex(0);
    storedResultsRef.current = new Map();
    setStoredResults(new Map());
  }, []);

  const setSimulationCount = useCallback((count: number) => {
    setSimulationCountState(count);
    setTabs(
      Array.from({ length: count }, (_, i) => ({
        index: i,
        label: `Sim #${i + 1}`,
        status: 'idle' as SimTabStatus,
      }))
    );
    setActiveSimIndex(0);
    storedResultsRef.current = new Map();
    setStoredResults(new Map());
  }, []);

  const storeResult = useCallback((index: number, result: any) => {
    storedResultsRef.current.set(index, result);
    setStoredResults(new Map(storedResultsRef.current));
  }, []);

  const getResult = useCallback((index: number) => {
    return storedResultsRef.current.get(index);
  }, []);

  return {
    simulationCount,
    setSimulationCount,
    activeSimIndex,
    setActiveSimIndex,
    tabs,
    updateTabStatus,
    resetTabs,
    storeResult,
    getResult,
    storedResults,
  };
}

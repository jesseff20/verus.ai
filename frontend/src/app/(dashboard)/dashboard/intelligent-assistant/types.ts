import type { ElementType } from 'react';

export type Phase = 'upload' | 'generation' | 'evaluation' | 'analysis' | 'result' | 'history';

export type ApprovalStatus = 'pending' | 'approved' | 'rejected';

export interface PhaseConfig {
  id: Phase;
  label: string;
  icon: ElementType;
}

/** Maps old step-based URL params to new phase system */
export const STEP_TO_PHASE: Record<string, Phase> = {
  upload: 'upload',
  generate: 'generation',
  analyze: 'evaluation',
  result: 'result',
};

export const PHASE_ORDER: Phase[] = [
  'upload',
  'generation',
  'evaluation',
  'analysis',
  'result',
  'history',
];

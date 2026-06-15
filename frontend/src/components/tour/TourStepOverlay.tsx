'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import {
  X,
  ChevronLeft,
  ChevronRight,
  SkipForward,
  Clock,
} from 'lucide-react';
import type { TourStep } from './tourConfig';

// ── Props ──────────────────────────────────────────────────────

interface TourStepOverlayProps {
  step: TourStep;
  stepIndex: number;
  totalSteps: number;
  targetElement: Element | null;
  isLastStep: boolean;
  onNext: () => void;
  onPrev: () => void;
  onSkip: () => void;
  onPostpone: () => void;
  onComplete: () => void;
}

// ── Cálculo de posição ─────────────────────────────────────────

interface Position {
  top: number;
  left: number;
  arrowDir: 'up' | 'down' | 'left' | 'right';
}

function calcPosition(
  target: Element | null,
  placement: TourStep['placement'],
  tooltipWidth: number,
  tooltipHeight: number,
): Position {
  const padding = 12;
  const winW = window.innerWidth;
  const winH = window.innerHeight;

  // Fallback: centralizar se não houver target ou se estiver fora da tela
  const center = {
    top: Math.max(padding, (winH - tooltipHeight) / 2),
    left: Math.max(padding, (winW - tooltipWidth) / 2),
    arrowDir: 'up' as const,
  };

  if (!target || placement === 'center') return center;

  const rect = target.getBoundingClientRect();

  // Se o target estiver fora da viewport, usar fallback central
  if (rect.bottom < 0 || rect.top > winH || rect.right < 0 || rect.left > winW) {
    return center;
  }

  const targetTop = rect.top;
  const targetLeft = rect.left;
  const targetWidth = rect.width;
  const targetHeight = rect.height;

  let pos: Position;
  switch (placement) {
    case 'bottom':
      pos = {
        top: targetTop + targetHeight + padding,
        left: targetLeft + targetWidth / 2 - tooltipWidth / 2,
        arrowDir: 'up',
      };
      break;
    case 'top':
      pos = {
        top: targetTop - tooltipHeight - padding,
        left: targetLeft + targetWidth / 2 - tooltipWidth / 2,
        arrowDir: 'down',
      };
      break;
    case 'left':
      pos = {
        top: targetTop + targetHeight / 2 - tooltipHeight / 2,
        left: targetLeft - tooltipWidth - padding,
        arrowDir: 'right',
      };
      break;
    case 'right':
      pos = {
        top: targetTop + targetHeight / 2 - tooltipHeight / 2,
        left: targetLeft + targetWidth + padding,
        arrowDir: 'left',
      };
      break;
    default:
      pos = center;
  }

  return clampPosition(pos, tooltipWidth, tooltipHeight);
}

// ── Garantir que o tooltip fique visível na tela ──────────────

function clampPosition(
  pos: Position,
  tooltipWidth: number,
  tooltipHeight: number,
): Position {
  const padding = 16;
  const maxTop = window.innerHeight - tooltipHeight - padding;
  const maxLeft = window.innerWidth - tooltipWidth - padding;
  return {
    ...pos,
    top: Math.max(padding, Math.min(pos.top, Math.max(padding, maxTop))),
    left: Math.max(padding, Math.min(pos.left, Math.max(padding, maxLeft))),
  };
}

// ── Componente ─────────────────────────────────────────────────

export default function TourStepOverlay({
  step,
  stepIndex,
  totalSteps,
  targetElement,
  isLastStep,
  onNext,
  onPrev,
  onSkip,
  onPostpone,
  onComplete,
}: TourStepOverlayProps) {
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState<Position>({ top: 0, left: 0, arrowDir: 'up' });
  const [tooltipSize, setTooltipSize] = useState({ width: 340, height: 200 });

  // Medir o tooltip e recalcular posição
  useEffect(() => {
    if (!tooltipRef.current) return;

    const rect = tooltipRef.current.getBoundingClientRect();
    const size = {
      width: Math.max(rect.width, 280),
      height: Math.max(rect.height, 160),
    };
    setTooltipSize(size);

    const raw = calcPosition(targetElement, step.placement, size.width, size.height);
    const clamped = clampPosition(raw, size.width, size.height);
    setPosition(clamped);
  }, [step, targetElement, tooltipRef.current]);

  // Recalcular em resize
  useEffect(() => {
    const handleResize = () => {
      if (tooltipRef.current) {
        const rect = tooltipRef.current.getBoundingClientRect();
        const size = { width: Math.max(rect.width, 280), height: Math.max(rect.height, 160) };
        setTooltipSize(size);
        const raw = calcPosition(targetElement, step.placement, size.width, size.height);
        const clamped = clampPosition(raw, size.width, size.height);
        setPosition(clamped);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [step, targetElement]);

  // Destacar elemento alvo com glow
  useEffect(() => {
    if (!targetElement) return;

    const originalOutline = (targetElement as HTMLElement).style.outline;
    const originalZIndex = (targetElement as HTMLElement).style.zIndex;
    const originalPosition = (targetElement as HTMLElement).style.position;

    (targetElement as HTMLElement).style.outline = '2px solid #7030A0';
    (targetElement as HTMLElement).style.outlineOffset = '2px';
    (targetElement as HTMLElement).style.zIndex = '999';

    return () => {
      (targetElement as HTMLElement).style.outline = originalOutline;
      (targetElement as HTMLElement).style.outlineOffset = '';
      (targetElement as HTMLElement).style.zIndex = originalZIndex;
      (targetElement as HTMLElement).style.position = originalPosition;
    };
  }, [targetElement]);

  // Foco no tooltip para acessibilidade
  useEffect(() => {
    tooltipRef.current?.focus();
  }, [stepIndex]);

  // Safety timeout: auto-aborta após 10 minutos para evitar travamentos
  useEffect(() => {
    const safetyTimer = setTimeout(() => {
      onPostpone();
    }, 10 * 60 * 1000); // 10 min
    return () => clearTimeout(safetyTimer);
  }, [stepIndex, onPostpone]);

  const handleAction = useCallback(() => {
    if (isLastStep) {
      onComplete();
    } else {
      onNext();
    }
  }, [isLastStep, onComplete, onNext]);

  const progressLabel = `Etapa ${stepIndex + 1} de ${totalSteps}`;

  return (
    <>
      {/* Backdrop semi-transparente (não bloqueia cliques) */}
      <div
        className="fixed inset-0 z-[998]"
        style={{ background: 'rgba(0,0,0,0.3)' }}
        onClick={onPostpone}
        aria-hidden="true"
      />

      {/* Tooltip */}
      <div
        ref={tooltipRef}
        role="dialog"
        aria-label={step.title}
        aria-describedby={`tour-desc-${step.id}`}
        aria-modal="false"
        tabIndex={0}
        className="fixed z-[999] rounded-xl border bg-card shadow-2xl p-5 w-[340px] max-w-[90vw]"
        style={{
          top: position.top,
          left: position.left,
          borderColor: '#7030A0',
          maxHeight: 'calc(100vh - 32px)',
          overflowY: 'auto',
        }}
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <div
              className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold text-white"
              style={{ background: '#7030A0' }}
            >
              {stepIndex + 1}
            </div>
            <span className="text-[10px] font-medium text-foreground/40 uppercase tracking-wider">
              {progressLabel}
            </span>
          </div>
          <button
            onClick={onPostpone}
            className="w-6 h-6 rounded flex items-center justify-center text-foreground/30 hover:text-foreground hover:bg-foreground/8 transition-all"
            aria-label="Fechar tour"
            title="Deixar para depois (Esc)"
          >
            <X size={14} />
          </button>
        </div>

        {/* Título */}
        <h3 className="text-sm font-semibold mb-1.5 text-foreground">
          {step.title}
        </h3>

        {/* Descrição */}
        <p
          id={`tour-desc-${step.id}`}
          className="text-xs text-foreground/60 leading-relaxed mb-4"
        >
          {step.description}
        </p>

        {/* Barra de progresso */}
        <div className="w-full h-1 rounded-full bg-foreground/8 mb-4 overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-300"
            style={{
              width: `${((stepIndex + 1) / totalSteps) * 100}%`,
              background: '#7030A0',
            }}
          />
        </div>

        {/* Botões */}
        <div className="flex flex-col gap-2">
          {/* Linha principal: navegação */}
          <div className="flex items-center gap-2">
            {stepIndex > 0 && (
              <button
                onClick={onPrev}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-foreground/50 hover:text-foreground hover:bg-foreground/8 transition-all"
                aria-label="Voltar etapa"
              >
                <ChevronLeft size={14} />
                {step.backButtonLabel || 'Voltar'}
              </button>
            )}

            <div className="flex-1" />

            <button
              onClick={handleAction}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-medium text-white transition-all hover:opacity-90"
              style={{ background: '#7030A0' }}
              aria-label={isLastStep ? 'Concluir tour' : 'Próxima etapa'}
            >
              {isLastStep ? 'Concluir' : (step.nextButtonLabel || 'Próximo')}
              {!isLastStep && <ChevronRight size={14} />}
            </button>
          </div>

          {/* Linha secundária: sair/adiar */}
          <div className="flex items-center justify-between pt-1">
            <button
              onClick={onSkip}
              className="flex items-center gap-1 px-2 py-1 rounded text-[10px] text-foreground/30 hover:text-foreground/50 transition-all"
              aria-label="Pular tour definitivamente"
            >
              <SkipForward size={10} />
              Pular tour
            </button>
            <button
              onClick={onPostpone}
              className="flex items-center gap-1 px-2 py-1 rounded text-[10px] text-foreground/30 hover:text-foreground/50 transition-all"
              aria-label="Deixar para depois"
            >
              <Clock size={10} />
              Agora não
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
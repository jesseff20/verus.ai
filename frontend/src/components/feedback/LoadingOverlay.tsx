'use client';

import { Loader2, Clock, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Progress } from '@/components/ui/progress';

export interface LoadingOverlayProps {
  /** Loading está ativo? */
  isLoading: boolean;
  /** Mensagem principal */
  message?: string;
  /** Mensagem secundária/descritiva */
  description?: string;
  /** Progresso (0-100) */
  progress?: number | null;
  /** Tempo estimado restante (ms) */
  estimatedTimeRemaining?: number | null;
  /** Loading está "lento"? */
  isSlow?: boolean;
  /** Mostrar ícone de sucesso quando completar */
  showSuccessIcon?: boolean;
  /** Classe CSS customizada */
  className?: string;
}

/**
 * Formata milissegundos para string legível
 */
function formatTime(ms: number | null): string {
  if (ms === null || ms === undefined) return '';
  if (ms < 1000) return `${Math.round(ms)}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.round(ms / 60000)}min`;
}

/**
 * Overlay de loading com progresso e estimativa de tempo
 *
 * @example
 * <LoadingOverlay
 *   isLoading={isGenerating}
 *   message="Gerando minuta..."
 *   progress={progress}
 *   estimatedTimeRemaining={eta}
 *   isSlow={isSlow}
 * />
 */
export function LoadingOverlay({
  isLoading,
  message = 'Carregando...',
  description,
  progress,
  estimatedTimeRemaining,
  isSlow = false,
  showSuccessIcon = false,
  className,
}: LoadingOverlayProps) {
  if (!isLoading) return null;

  return (
    <div
      className={cn(
        'fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm',
        className
      )}
      role="alert"
      aria-live="polite"
    >
      <div className="w-full max-w-md mx-auto p-6">
        <div
          className={cn(
            'rounded-lg border bg-card p-6 shadow-lg',
            isSlow && 'border-warning/50 bg-warning/5'
          )}
        >
          {/* Ícone */}
          <div className="flex justify-center mb-4">
            {showSuccessIcon ? (
              <CheckCircle2 className="h-12 w-12 text-green-600 animate-in zoom-in" />
            ) : (
              <Loader2
                className={cn(
                  'h-12 w-12 animate-spin',
                  isSlow ? 'text-warning' : 'text-primary'
                )}
              />
            )}
          </div>

          {/* Mensagem */}
          <div className="text-center mb-4">
            <h3 className="font-semibold text-lg text-foreground mb-1">
              {message}
            </h3>
            {description && (
              <p className="text-sm text-muted-foreground">
                {description}
              </p>
            )}
            {isSlow && !showSuccessIcon && (
              <p className="text-xs text-warning mt-2 flex items-center justify-center gap-1">
                <Clock className="h-3 w-3" />
                Isso está levando mais tempo que o esperado...
              </p>
            )}
          </div>

          {/* Barra de progresso */}
          {progress !== null && progress !== undefined && (
            <div className="space-y-2">
              <Progress value={progress} className="h-2" />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>{progress}% concluído</span>
                {estimatedTimeRemaining !== null && estimatedTimeRemaining !== undefined && (
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatTime(estimatedTimeRemaining)} restantes
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Apenas tempo estimado (sem progresso) */}
          {!progress && estimatedTimeRemaining !== null && estimatedTimeRemaining !== undefined && (
            <div className="text-center text-xs text-muted-foreground flex items-center justify-center gap-1">
              <Clock className="h-3 w-3" />
              Tempo estimado: {formatTime(estimatedTimeRemaining)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Loading inline para botões e ações menores
 */
export interface LoadingButtonProps {
  isLoading: boolean;
  children: React.ReactNode;
  className?: string;
}

export function LoadingButton({ isLoading, children, className }: LoadingButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-2',
        className
      )}
      disabled={isLoading}
    >
      {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
      {children}
    </button>
  );
}

/**
 * Esqueleto de loading para conteúdo
 */
export interface SkeletonProps {
  className?: string;
  lines?: number;
}

export function Skeleton({ className, lines = 1 }: SkeletonProps) {
  return (
    <div className="space-y-2">
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className={cn(
            'h-4 w-full animate-pulse rounded bg-muted',
            className
          )}
          style={{
            width: lines > 1 && i === lines - 1 ? '60%' : '100%',
          }}
        />
      ))}
    </div>
  );
}

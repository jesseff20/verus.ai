'use client';

import { useState } from 'react';
import { HelpCircle, X } from 'lucide-react';
import { useTourContext } from './TourProvider';
import { tourConfigs } from './tourConfig';

/**
 * Botão de ajuda flutuante fixo no canto inferior direito.
 * Permite ao usuário reiniciar tours manualmente a qualquer momento.
 */
export function TourHelpButton() {
  const { isActive, startTour, resetTour } = useTourContext();
  const [isOpen, setIsOpen] = useState(false);

  if (isActive) return null;

  return (
    <>
      {/* Botão flutuante */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 w-10 h-10 rounded-full flex items-center justify-center shadow-lg transition-all hover:scale-105"
        style={{ background: '#7030A0', color: '#fff' }}
        aria-label="Ajuda"
        title="Ajuda"
      >
        {isOpen ? <X size={18} /> : <HelpCircle size={18} />}
      </button>

      {/* Menu de ajuda */}
      {isOpen && (
        <div
          className="fixed bottom-20 right-6 z-50 w-72 rounded-xl border bg-card shadow-2xl p-4"
          style={{ borderColor: '#7030A040' }}
        >
          <h3 className="text-sm font-semibold mb-3">Ajuda</h3>

          <p className="text-[11px] text-foreground/50 mb-3 leading-relaxed">
            Explore os tours interativos para conhecer melhor o sistema.
          </p>

          <div className="flex flex-col gap-1.5">
            {tourConfigs.map((cfg) => {
              const routeLabel = typeof cfg.route === 'string' ? cfg.route : cfg.name;
              return (
                <button
                  key={cfg.id}
                  onClick={() => {
                    resetTour(cfg.id);
                    setIsOpen(false);
                    // Navegar para a rota — o tour será exibido ao entrar
                    const route = typeof cfg.route === 'string' ? cfg.route : null;
                    if (route && route !== window.location.pathname) {
                      window.location.href = route;
                    } else {
                      // Já está na rota, reinicia o tour manualmente
                      setTimeout(() => startTour(), 500);
                    }
                  }}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium text-left hover:bg-foreground/8 transition-all"
                >
                  <div
                    className="w-5 h-5 rounded-full flex items-center justify-center text-[8px] font-bold text-white shrink-0"
                    style={{ background: '#7030A0' }}
                  >
                    {cfg.steps.length}
                  </div>
                  <div>
                    <p className="text-foreground">{cfg.name}</p>
                    <p className="text-[10px] text-foreground/40">{cfg.steps.length} etapas · {routeLabel}</p>
                  </div>
                </button>
              );
            })}
          </div>

          <button
            onClick={() => setIsOpen(false)}
            className="mt-3 w-full py-1.5 rounded-lg text-[11px] text-foreground/40 hover:text-foreground hover:bg-foreground/8 transition-all"
          >
            Fechar
          </button>
        </div>
      )}
    </>
  );
}
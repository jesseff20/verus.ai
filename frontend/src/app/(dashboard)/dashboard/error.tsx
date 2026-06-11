'use client';

import { useEffect } from 'react';
import { AlertTriangle, RefreshCcw } from 'lucide-react';

export default function ContentError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('[Content Error]', error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-6 text-center">
      <div
        className="w-12 h-12 rounded-xl flex items-center justify-center mb-4"
        style={{ background: '#EF444415', border: '1px solid #EF444430' }}
      >
        <AlertTriangle size={18} className="text-red-400" />
      </div>

      <h2 className="text-base font-semibold mb-1">Erro ao carregar</h2>
      <p className="text-sm text-white/40 mb-4 max-w-xs leading-relaxed">
        {error.message || 'Não foi possível carregar este conteúdo.'}
      </p>

      <button
        onClick={reset}
        className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-all"
        style={{ background: '#7030A015', color: '#C084FC', border: '1px solid #7030A040' }}
      >
        <RefreshCcw size={13} />
        Tentar novamente
      </button>
    </div>
  );
}

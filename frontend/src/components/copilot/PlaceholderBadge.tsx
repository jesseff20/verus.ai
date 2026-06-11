import React from 'react';
import { countPlaceholders, PlaceholderCount } from './LegalPlaceholderHighlight';

interface PlaceholderBadgeProps {
  content: string;
  onReviewRequired?: () => void;
}

export const PlaceholderBadge: React.FC<PlaceholderBadgeProps> = ({ content, onReviewRequired }) => {
  const counts = countPlaceholders(content);

  if (counts.total === 0) {
    return (
      <div className="flex items-center gap-1 text-green-600 text-sm">
        <span>✅</span>
        <span>Nenhum item pendente de revisão</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {counts.critical > 0 && (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800 border border-red-300">
          🔴 {counts.critical} informação(ões) necessária(s)
        </span>
      )}
      {counts.warning > 0 && (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-300">
          🟡 {counts.warning} item(ns) a verificar
        </span>
      )}
      {counts.info > 0 && (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800 border border-blue-300">
          🔵 {counts.info} sugestão(ões) da IA
        </span>
      )}
      {onReviewRequired && counts.critical > 0 && (
        <button
          onClick={onReviewRequired}
          className="text-xs text-red-600 underline hover:text-red-800"
        >
          Ver itens críticos
        </button>
      )}
    </div>
  );
};

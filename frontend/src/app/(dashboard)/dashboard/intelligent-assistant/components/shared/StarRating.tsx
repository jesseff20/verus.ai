import React, { memo, useCallback } from 'react';
import { Star } from 'lucide-react';
import { cn } from '@/lib/utils';

interface StarRatingProps {
  value: number;
  onChange: (rating: number) => void;
  disabled?: boolean;
  size?: number;
}

function StarRatingComponent({ value, onChange, disabled = false, size = 18 }: StarRatingProps) {
  const handleClick = useCallback(
    (star: number) => {
      if (!disabled) onChange(star);
    },
    [disabled, onChange]
  );

  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          onClick={() => handleClick(star)}
          disabled={disabled}
          className={cn(
            'p-0.5 transition-all',
            value >= star ? 'text-amber-500' : 'text-slate-200 hover:text-amber-500/50',
            disabled && 'cursor-default opacity-70'
          )}
        >
          <Star size={size} fill={value >= star ? 'currentColor' : 'none'} />
        </button>
      ))}
    </div>
  );
}

export const StarRating = memo(StarRatingComponent);

'use client';

import React from 'react';
import ReactWordcloud from 'react-d3-cloud';
import type { WordCloudWord } from '@/types';

interface WordCloudChartProps {
  words: WordCloudWord[];
  title: string;
}

export function WordCloudChart({ words, title }: WordCloudChartProps) {
  if (!words || words.length === 0) {
    return (
      <div className="h-[300px] flex items-center justify-center bg-muted/20 rounded-lg border-2 border-dashed">
        <p className="text-sm text-muted-foreground">
          Sem dados suficientes para gerar nuvem de palavras
        </p>
      </div>
    );
  }

  // Configurar cores baseadas no título
  const colors = title.includes('Entrada')
    ? ['#3b82f6', '#2563eb', '#1d4ed8', '#1e40af', '#1e3a8a'] // Azuis
    : ['#10b981', '#059669', '#047857', '#065f46', '#064e3b']; // Verdes

  return (
    <div>
      <h4 className="text-sm font-semibold mb-3">{title}</h4>
      <div className="h-[300px] bg-muted/10 rounded-lg p-4 border">
        <ReactWordcloud
          data={words}
          width={600}
          height={300}
          font="Inter"
          fontWeight="bold"
          fontSize={(word) => Math.log2(word.value) * 15}
          spiral="rectangular"
          rotate={0}
          padding={5}
          random={Math.random}
          fill={(_, index) => colors[index % colors.length]}
        />
      </div>
      <p className="text-xs text-muted-foreground mt-2">
        {words.length} palavras mais frequentes (últimos 30 dias)
      </p>
    </div>
  );
}

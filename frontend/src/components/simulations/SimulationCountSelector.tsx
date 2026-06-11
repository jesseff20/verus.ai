'use client';

import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Copy } from 'lucide-react';

interface SimulationCountSelectorProps {
  value: number;
  onChange: (count: number) => void;
  max?: number;
}

export default function SimulationCountSelector({
  value,
  onChange,
  max = 5,
}: SimulationCountSelectorProps) {
  const options = Array.from({ length: max }, (_, i) => i + 1);

  return (
    <div className="space-y-2">
      <Label className="flex items-center gap-2">
        <Copy className="h-4 w-4" />
        Quantidade de Simulacoes Simultaneas
      </Label>
      <p className="text-xs text-muted-foreground">
        Execute multiplas simulacoes em paralelo com a mesma configuracao para comparar resultados.
      </p>
      <Select
        value={String(value)}
        onValueChange={(v) => onChange(Number(v))}
      >
        <SelectTrigger className="w-[200px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map((n) => (
            <SelectItem key={n} value={String(n)}>
              {n} {n === 1 ? 'simulacao' : 'simulacoes'}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

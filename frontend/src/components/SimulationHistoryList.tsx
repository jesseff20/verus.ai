'use client';

import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import Link from 'next/link';
import { Clock } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface SimulationHistoryListProps {
  type: string;
  /** The URL path segment for this simulation type (e.g. 'judge', 'tst-trabalho') */
  pathSegment?: string;
}

export default function SimulationHistoryList({ type, pathSegment }: SimulationHistoryListProps) {
  const segment = pathSegment || type.replace(/_/g, '-');

  const { data: history } = useQuery({
    queryKey: ['sim-history', type],
    queryFn: async () => {
      const res = await api.get(`/api/v1/simulations/simulations/?simulation_type=${type}&page_size=5`);
      return res.data.results || res.data;
    },
  });

  if (!history || history.length === 0) return null;

  return (
    <div className="mt-8 border-t pt-6">
      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
        <Clock className="h-5 w-5" />
        Ultimas Simulacoes
      </h3>
      <div className="space-y-2">
        {history.slice(0, 5).map((sim: any) => (
          <Link
            key={sim.id}
            href={`/dashboard/simulations/${segment}?id=${sim.id}`}
            className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent/50 transition-colors"
          >
            <div className="min-w-0">
              <p className="font-medium text-sm truncate">{sim.title}</p>
              <p className="text-xs text-muted-foreground">
                {new Date(sim.created_at).toLocaleDateString('pt-BR')}
              </p>
            </div>
            <Badge variant={sim.status === 'completed' ? 'default' : 'secondary'}>
              {sim.status === 'completed' ? 'Concluida' : sim.status}
            </Badge>
          </Link>
        ))}
      </div>
    </div>
  );
}

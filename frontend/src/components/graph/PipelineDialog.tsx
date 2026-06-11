'use client';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { PipelinePanel } from './PipelinePanel';
import type { GraphVisualization } from '@/hooks/use-intelligent-assistant';

interface PipelineDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  graphVisualization: GraphVisualization;
}

export function PipelineDialog({ open, onOpenChange, graphVisualization }: PipelineDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl h-[80vh] flex flex-col p-0 gap-0">
        <DialogHeader className="px-4 py-3 border-b shrink-0">
          <DialogTitle className="text-base">Pipeline de Geração</DialogTitle>
          <DialogDescription className="sr-only">Visualizar o pipeline de geração de documento</DialogDescription>
        </DialogHeader>
        <div className="flex-1 overflow-hidden">
          <PipelinePanel graphVisualization={graphVisualization} />
        </div>
      </DialogContent>
    </Dialog>
  );
}

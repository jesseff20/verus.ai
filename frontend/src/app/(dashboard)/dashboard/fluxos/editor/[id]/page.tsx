'use client';

import { use } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Loader2, AlertCircle } from 'lucide-react';
import { useFlowTemplate } from '@/hooks/useFlowTemplates';
import dynamic from 'next/dynamic';

// FlowEditor usa @xyflow/react que precisa de window — carregar só no client
const FlowEditor = dynamic(
  () => import('@/components/workflow-editor/FlowEditor'),
  {
    ssr: false,
    loading: () => (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 size={24} className="animate-spin text-foreground/20" />
      </div>
    ),
  },
);

export default function FlowEditorPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const { data: template, isLoading, error } = useFlowTemplate(id);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 size={24} className="animate-spin text-foreground/20" />
      </div>
    );
  }

  if (error || !template) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <AlertCircle size={32} className="text-red-400/50" />
        <p className="text-sm text-foreground/40">Template não encontrado.</p>
        <button
          onClick={() => router.push('/dashboard/fluxos')}
          className="text-sm text-[#8B5CF6] hover:underline"
        >
          Voltar para fluxos
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col" style={{ height: '100vh' }}>
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 px-4 h-10 border-b border-border bg-card shrink-0" data-tour="ef-toolbar">
        <button
          onClick={() => router.push('/dashboard/fluxos')}
          className="flex items-center gap-1.5 text-xs text-foreground/40 hover:text-foreground transition-colors"
        >
          <ArrowLeft size={12} />
          Fluxos
        </button>
        <span className="text-foreground/25 text-xs">/</span>
        <span className="text-xs text-foreground/60">{template.name}</span>
      </div>

      {/* Editor */}
      <div className="flex-1 overflow-hidden">
        <FlowEditor template={template} />
      </div>
    </div>
  );
}

'use client';

import { useParams, useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';
import { useBlueprints } from '@/hooks/use-blueprints';
import { BlueprintEditor } from '@/components/blueprint/BlueprintEditor';
import { Loader2, AlertTriangle, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { DocumentBlueprint } from '@/types';

export default function BlueprintEditorPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const isNew = id === 'new';

  const { useBlueprint } = useBlueprints();

  // Only fetch if editing an existing blueprint
  const {
    data: blueprint,
    isLoading,
    error,
  } = useBlueprint(isNew ? '' : id);

  // Loading state
  if (!isNew && isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground">Carregando blueprint...</p>
      </div>
    );
  }

  // Error state
  if (!isNew && error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <AlertTriangle className="h-12 w-12 text-destructive" />
        <div className="text-center space-y-2">
          <h2 className="text-lg font-semibold">Blueprint não encontrado</h2>
          <p className="text-sm text-muted-foreground">
            O blueprint solicitado não existe ou você não tem permissão para acessá-lo.
          </p>
        </div>
        <Button variant="outline" onClick={() => router.push('/dashboard/blueprints')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Voltar para Blueprints
        </Button>
      </div>
    );
  }

  // Not found (finished loading, no data, not new)
  if (!isNew && !blueprint) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <AlertTriangle className="h-12 w-12 text-amber-500" />
        <div className="text-center space-y-2">
          <h2 className="text-lg font-semibold">Blueprint nao encontrado</h2>
          <p className="text-sm text-muted-foreground">
            Nenhum blueprint com o ID informado foi localizado.
          </p>
        </div>
        <Button variant="outline" onClick={() => router.push('/dashboard/blueprints')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Voltar para Blueprints
        </Button>
      </div>
    );
  }

  return (
    <BlueprintEditor
      blueprint={isNew ? undefined : blueprint}
      isNew={isNew}
    />
  );
}

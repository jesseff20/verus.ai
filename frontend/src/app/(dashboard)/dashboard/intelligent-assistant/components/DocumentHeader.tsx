import React, { memo, useState, useCallback } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';
import { Check, Loader2, PenLine } from 'lucide-react';

interface DocumentHeaderProps {
  documentTypeName: string;
  blueprintName?: string;
  objective: string;
  onSaveObjective?: (value: string) => Promise<void>;
}

function DocumentHeaderComponent({
  documentTypeName,
  blueprintName,
  objective,
  onSaveObjective,
}: DocumentHeaderProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(objective);
  const [isSaving, setIsSaving] = useState(false);

  const handleStartEdit = useCallback(() => {
    setEditValue(objective);
    setIsEditing(true);
  }, [objective]);

  const handleSave = useCallback(async () => {
    if (!onSaveObjective || !editValue.trim()) return;
    setIsSaving(true);
    try {
      await onSaveObjective(editValue.trim());
      setIsEditing(false);
    } finally {
      setIsSaving(false);
    }
  }, [editValue, onSaveObjective]);

  const handleCancel = useCallback(() => {
    setEditValue(objective);
    setIsEditing(false);
  }, [objective]);

  return (
    <div className="bg-white border-b border-slate-200 py-3 sm:py-5 px-4 sm:px-8">
      <div className="max-w-[1600px] mx-auto grid grid-cols-1 lg:grid-cols-3 gap-3 sm:gap-6 items-start">
        <div className="lg:col-span-1">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary mb-1">
            Tipo de Documento
          </p>
          <h1 className="text-base sm:text-xl font-black tracking-tight text-slate-900 uppercase leading-tight">
            {documentTypeName}
          </h1>
          {blueprintName && (
            <Badge variant="secondary" className="mt-1 sm:mt-2 text-xs">
              {blueprintName}
            </Badge>
          )}
        </div>

        <div className="lg:col-span-2 bg-slate-50 rounded-2xl p-4 sm:p-5 border border-slate-200">
          <div className="flex items-center justify-between mb-2">
            <label className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400 flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-primary" />
              Objetivo da Sessão (Contexto para IA)
            </label>
            {!isEditing && onSaveObjective && (
              <button
                type="button"
                onClick={handleStartEdit}
                className="flex items-center gap-1 text-xs text-slate-400 hover:text-primary transition-colors"
              >
                <PenLine className="h-3 w-3" />
                Editar
              </button>
            )}
          </div>

          {isEditing ? (
            <div className="space-y-3">
              <div className="relative">
                <Textarea
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  rows={3}
                  className="resize-none rounded-xl bg-white pr-32"
                  autoFocus
                />
                <div className="absolute top-1 right-1">
                  <AIEnhanceButton
                    value={editValue}
                    onEnhance={setEditValue}
                    context="objetivo de documento jurídico"
                  />
                </div>
              </div>
              <div className="flex items-center justify-end gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCancel}
                  disabled={isSaving}
                  className="text-xs"
                >
                  Cancelar
                </Button>
                <Button
                  size="sm"
                  onClick={handleSave}
                  disabled={isSaving || !editValue.trim()}
                  className="rounded-lg gap-1"
                >
                  {isSaving ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <Check className="h-3 w-3" />
                  )}
                  Salvar
                </Button>
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-700 leading-relaxed">{objective}</p>
          )}

          <p className="text-[10px] text-slate-400 italic mt-2">
            Este campo serve como guia para os agentes de IA e não será exportado no documento.
          </p>
        </div>
      </div>
    </div>
  );
}

export const DocumentHeader = memo(DocumentHeaderComponent);

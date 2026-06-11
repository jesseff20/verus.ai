'use client';

import { useState, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Pencil, Check, X, FileText } from 'lucide-react';

interface DocumentHeaderProps {
  documentTypeName: string;
  blueprintName?: string;
  objective: string;
  onSaveObjective: (objective: string) => Promise<void>;
  className?: string;
}

export function DocumentHeader({
  documentTypeName,
  blueprintName,
  objective,
  onSaveObjective,
  className,
}: DocumentHeaderProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(objective);
  const [isSaving, setIsSaving] = useState(false);

  const handleStartEdit = useCallback(() => {
    setEditValue(objective);
    setIsEditing(true);
  }, [objective]);

  const handleCancelEdit = useCallback(() => {
    setIsEditing(false);
    setEditValue(objective);
  }, [objective]);

  const handleSave = useCallback(async () => {
    if (editValue.trim() === objective.trim()) {
      setIsEditing(false);
      return;
    }
    setIsSaving(true);
    try {
      await onSaveObjective(editValue.trim());
      setIsEditing(false);
    } catch {
      // Error handled upstream
    } finally {
      setIsSaving(false);
    }
  }, [editValue, objective, onSaveObjective]);

  return (
    <div className={cn('bg-muted/30 border-y px-6 py-3', className)}>
      <div className="max-w-[1600px] mx-auto flex items-center gap-4">
        <div className="flex items-center gap-2 min-w-0">
          <FileText className="h-5 w-5 text-primary shrink-0" />
          <span className="text-sm font-medium truncate">{documentTypeName}</span>
          {blueprintName && (
            <>
              <span className="text-muted-foreground text-sm">/</span>
              <span className="text-sm text-muted-foreground truncate">{blueprintName}</span>
            </>
          )}
        </div>

        <div className="flex-1 min-w-0 flex items-center gap-2">
          <span className="text-xs text-muted-foreground shrink-0">Objetivo:</span>
          {isEditing ? (
            <div className="flex items-center gap-1 flex-1">
              <Input
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                className="h-7 text-sm flex-1"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSave();
                  if (e.key === 'Escape') handleCancelEdit();
                }}
              />
              <Button
                size="icon"
                variant="ghost"
                className="h-7 w-7"
                onClick={handleSave}
                disabled={isSaving}
              >
                <Check className="h-3.5 w-3.5 text-green-600" />
              </Button>
              <Button
                size="icon"
                variant="ghost"
                className="h-7 w-7"
                onClick={handleCancelEdit}
              >
                <X className="h-3.5 w-3.5" />
              </Button>
            </div>
          ) : (
            <button
              onClick={handleStartEdit}
              className="group flex items-center gap-1.5 min-w-0 text-sm text-left hover:text-primary transition-colors"
            >
              <span className="truncate">{objective}</span>
              <Pencil className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

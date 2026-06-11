'use client';

import { X, Paperclip } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface FileAttachmentProps {
  file: File;
  onRemove: () => void;
}

export function FileAttachment({ file, onRemove }: FileAttachmentProps) {
  const sizeKb = (file.size / 1024).toFixed(1);

  return (
    <div className="flex items-center gap-2 rounded-md border bg-muted px-3 py-1.5 text-sm">
      <Paperclip className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
      <span className="truncate max-w-[200px] font-medium">{file.name}</span>
      <span className="text-muted-foreground shrink-0">{sizeKb} KB</span>
      <Button
        variant="ghost"
        size="icon"
        className="h-5 w-5 shrink-0 hover:bg-destructive/10 hover:text-destructive"
        onClick={onRemove}
        type="button"
      >
        <X className="h-3 w-3" />
      </Button>
    </div>
  );
}

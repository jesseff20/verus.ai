'use client';

import { Download, Copy, FileText } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';

interface ExportMenuProps {
  onCopy: () => void;
  onExport: (format: 'docx' | 'pdf' | 'odt') => void;
  disabled?: boolean;
}

export function ExportMenu({ onCopy, onExport, disabled }: ExportMenuProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" disabled={disabled}>
          <Download className="h-4 w-4 mr-1.5" />
          Exportar
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={onCopy}>
          <Copy className="h-4 w-4 mr-2" />
          Copiar texto
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => onExport('docx')}>
          <FileText className="h-4 w-4 mr-2" />
          Exportar DOCX
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => onExport('pdf')}>
          <FileText className="h-4 w-4 mr-2" />
          Exportar PDF
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => onExport('odt')}>
          <FileText className="h-4 w-4 mr-2" />
          Exportar ODT
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

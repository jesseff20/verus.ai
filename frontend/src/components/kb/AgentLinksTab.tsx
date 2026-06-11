'use client';

import { useState } from 'react';
import { useAgentKBLinks } from '@/hooks/use-agent-kb-links';
import { useKBSources } from '@/hooks/use-knowledge-base';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Loader2, Plus, Pencil, Trash2 } from 'lucide-react';
import { AgentLinkDialog } from './AgentLinkDialog';
import type { AgentKnowledgeBaseLink } from '@/types';

const PURPOSE_COLORS: Record<string, string> = {
  examples: 'bg-pink-100 text-pink-800',
  evaluation: 'bg-orange-100 text-orange-800',
  normative: 'bg-cyan-100 text-cyan-800',
  context: 'bg-green-100 text-green-800',
  reference: 'bg-gray-100 text-gray-800',
};

interface AgentLinksTabProps {
  kbId: string;
  kbName: string;
}

export function AgentLinksTab({ kbId, kbName }: AgentLinksTabProps) {
  const { links, isLoading, createLink, isCreatingLink, updateLink, isUpdatingLink, deleteLink, isDeletingLink } =
    useAgentKBLinks(kbId);
  const { data: sourcesData } = useKBSources(kbId);
  const sources = sourcesData?.sources || [];
  const { toast } = useToast();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingLink, setEditingLink] = useState<AgentKnowledgeBaseLink | null>(null);

  const handleCreate = (data: Record<string, any>) => {
    createLink(data as any, {
      onSuccess: () => {
        toast({ title: 'Agente vinculado com sucesso' });
        setDialogOpen(false);
      },
      onError: (error: any) => {
        toast({
          title: 'Erro ao vincular agente',
          description: error.response?.data?.agent?.[0] || error.response?.data?.detail || 'Erro desconhecido',
          variant: 'destructive',
        });
      },
    });
  };

  const handleUpdate = (data: Record<string, any>) => {
    if (!editingLink) return;
    updateLink(
      { linkId: editingLink.id, ...data } as any,
      {
        onSuccess: () => {
          toast({ title: 'Vínculo atualizado' });
          setEditingLink(null);
          setDialogOpen(false);
        },
        onError: () => {
          toast({ title: 'Erro ao atualizar', variant: 'destructive' });
        },
      }
    );
  };

  const handleDelete = (link: AgentKnowledgeBaseLink) => {
    if (!confirm(`Desvincular "${link.agent_name}" desta base?`)) return;
    deleteLink(link.id, {
      onSuccess: () => {
        toast({ title: 'Vínculo removido' });
      },
      onError: () => {
        toast({ title: 'Erro ao remover vínculo', variant: 'destructive' });
      },
    });
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {links.length} agente{links.length !== 1 ? 's' : ''} vinculado{links.length !== 1 ? 's' : ''}
        </p>
        <Button
          size="sm"
          onClick={() => {
            setEditingLink(null);
            setDialogOpen(true);
          }}
        >
          <Plus className="mr-1 h-3 w-3" />
          Vincular Agente
        </Button>
      </div>

      {links.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          <p>Nenhum agente vinculado a esta base.</p>
          <p className="text-xs mt-1">Vincule agentes para definir como usam esta KB.</p>
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[40px]">P</TableHead>
              <TableHead>Agente</TableHead>
              <TableHead>Propósito</TableHead>
              <TableHead className="w-[60px]">Top K</TableHead>
              <TableHead className="w-[60px]">Sim.</TableHead>
              <TableHead className="w-[70px]">Fontes</TableHead>
              <TableHead className="text-right w-[80px]">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {links.map((link) => (
              <TableRow key={link.id}>
                <TableCell className="font-mono text-center">{link.priority}</TableCell>
                <TableCell>
                  <div>
                    <span className="font-medium text-sm">{link.agent_name}</span>
                    <span className="ml-1 text-xs text-muted-foreground">({link.agent_type})</span>
                  </div>
                  {link.instruction && (
                    <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">
                      {link.instruction}
                    </p>
                  )}
                </TableCell>
                <TableCell>
                  <Badge
                    variant="secondary"
                    className={PURPOSE_COLORS[link.purpose] || PURPOSE_COLORS.reference}
                  >
                    {link.purpose_display}
                  </Badge>
                </TableCell>
                <TableCell className="text-center">{link.top_k}</TableCell>
                <TableCell className="text-center">{link.min_similarity}</TableCell>
                <TableCell className="text-center text-xs text-muted-foreground">
                  {link.selected_sources && link.selected_sources.length > 0
                    ? `${link.selected_sources.length}/${sources.length}`
                    : 'Todas'}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-1">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setEditingLink(link);
                        setDialogOpen(true);
                      }}
                    >
                      <Pencil className="h-3 w-3" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      onClick={() => handleDelete(link)}
                      disabled={isDeletingLink}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <AgentLinkDialog
        open={dialogOpen}
        onOpenChange={(open) => {
          setDialogOpen(open);
          if (!open) setEditingLink(null);
        }}
        kbName={kbName}
        editingLink={editingLink}
        sources={sources}
        onSubmit={editingLink ? handleUpdate : handleCreate}
        isSubmitting={isCreatingLink || isUpdatingLink}
      />
    </div>
  );
}

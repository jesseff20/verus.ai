'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useBlueprintManagement } from '@/hooks/use-blueprints';
import { useToast } from '@/hooks/use-toast';
import type { DocumentBlueprint } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Input } from '@/components/ui/input';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  LayoutTemplate,
  Plus,
  Edit,
  Power,
  PowerOff,
  Loader2,
  Trash2,
  Calendar,
  Search,
  X,
  LayoutGrid,
  List,
  Copy,
} from 'lucide-react';

export default function BlueprintsPage() {
  const { toast } = useToast();

  // Fetch all blueprints (including inactive)
  const {
    blueprints,
    total,
    isLoading,
    toggleActiveWithCallbacks,
    isTogglingActive,
    deleteBlueprintWithCallbacks,
    isDeletingBlueprint,
    duplicateBlueprintWithCallbacks,
    isDuplicatingBlueprint,
  } = useBlueprintManagement();

  // Busca por texto livre (filtra por nome, tipo ou descrição)
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Modo de visualização - persistido em localStorage
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const saved = localStorage.getItem('blueprints-view-mode');
    if (saved === 'grid' || saved === 'list') setViewMode(saved);
  }, []);
  useEffect(() => {
    if (typeof window === 'undefined') return;
    localStorage.setItem('blueprints-view-mode', viewMode);
  }, [viewMode]);

  // Delete dialog
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [blueprintToDelete, setBlueprintToDelete] = useState<DocumentBlueprint | null>(null);

  const handleDuplicate = (bp: DocumentBlueprint) => {
    duplicateBlueprintWithCallbacks(bp.id, {
      onSuccess: (newBp: DocumentBlueprint) => {
        toast({
          title: 'Blueprint duplicado',
          description: `"${newBp.name}" foi criado com sucesso.`,
        });
      },
      onError: (error: any) => {
        toast({
          title: 'Erro ao duplicar',
          description: error.response?.data?.detail || 'Não foi possível duplicar o blueprint.',
          variant: 'destructive',
        });
      },
    });
  };

  // Filtro por texto livre (case-insensitive, busca em nome, tipo e descrição)
  const filteredBlueprints = blueprints.filter((bp) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      bp.name?.toLowerCase().includes(q) ||
      bp.document_type_display?.toLowerCase().includes(q) ||
      bp.description?.toLowerCase().includes(q)
    );
  });

  // Toggle active/inactive
  const handleToggleActive = (bp: DocumentBlueprint) => {
    toggleActiveWithCallbacks(
      { id: bp.id, is_active: !bp.is_active },
      {
        onSuccess: () => {
          toast({
            title: bp.is_active ? 'Blueprint desativado' : 'Blueprint ativado',
            description: `"${bp.name}" foi ${bp.is_active ? 'desativado' : 'ativado'} com sucesso.`,
          });
        },
        onError: (error: any) => {
          toast({
            title: 'Erro ao alterar status',
            description: error.response?.data?.detail || 'Não foi possível alterar o status do blueprint.',
            variant: 'destructive',
          });
        },
      }
    );
  };

  // Delete blueprint
  const handleDeleteClick = (bp: DocumentBlueprint) => {
    setBlueprintToDelete(bp);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = () => {
    if (!blueprintToDelete) return;

    deleteBlueprintWithCallbacks(blueprintToDelete.id, {
      onSuccess: () => {
        toast({
          title: 'Blueprint removido',
          description: `"${blueprintToDelete.name}" foi removido com sucesso.`,
        });
        setDeleteDialogOpen(false);
        setBlueprintToDelete(null);
      },
      onError: (error: any) => {
        toast({
          title: 'Erro ao deletar',
          description:
            error.response?.data?.detail ||
            'Não foi possível deletar o blueprint. Verifique se não há dependências.',
          variant: 'destructive',
        });
      },
    });
  };

  // Format date
  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between" data-tour="bp-header">
        <div>
          <h1 className="text-3xl font-bold">Blueprints</h1>
          <p className="text-muted-foreground">
            Gerencie os modelos estruturais de documentos e suas seções de geração por IA
            {' '}&bull;{' '}{total} blueprint{total !== 1 ? 's' : ''}
          </p>
        </div>
        <Link href="/dashboard/blueprints/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Novo Blueprint
          </Button>
        </Link>
      </div>

      <Separator />

      {/* Busca + Toggle de visualização */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Buscar por nome, tipo ou descrição..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 pr-9"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground"
              title="Limpar busca"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
        <p className="text-xs text-muted-foreground">
          {filteredBlueprints.length} de {total}
        </p>
        <div className="ml-auto flex items-center border rounded-md">
          <Button
            variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
            size="icon"
            onClick={() => setViewMode('grid')}
            title="Grade"
            className="rounded-r-none"
          >
            <LayoutGrid className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'list' ? 'secondary' : 'ghost'}
            size="icon"
            onClick={() => setViewMode('list')}
            title="Lista"
            className="rounded-l-none"
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Loading */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      ) : filteredBlueprints.length === 0 ? (
        /* Empty state */
        <Card className="p-12">
          <div className="flex flex-col items-center text-center gap-4">
            <LayoutTemplate className="h-16 w-16 text-muted-foreground opacity-50" />
            <div>
              <h3 className="text-lg font-semibold mb-2">Nenhum blueprint encontrado</h3>
              <p className="text-sm text-muted-foreground mb-4">
                {searchQuery
                  ? `Nenhum blueprint corresponde a "${searchQuery}". Tente outro termo.`
                  : 'Crie seu primeiro blueprint para definir a estrutura de geração de documentos por IA.'}
              </p>
            </div>
            {!searchQuery && (
              <Link href="/dashboard/blueprints/new">
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Criar Primeiro Blueprint
                </Button>
              </Link>
            )}
          </div>
        </Card>
      ) : viewMode === 'grid' ? (
        /* Grid of blueprint cards */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" data-tour="bp-list">
          {filteredBlueprints.map((bp) => (
            <Card
              key={bp.id}
              className={`hover:shadow-lg transition-shadow ${
                !bp.is_active ? 'opacity-60' : ''
              }`}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <LayoutTemplate className="h-8 w-8 text-primary" />
                  <div className="flex gap-1.5 flex-wrap">
                    {bp.is_active ? (
                      <Badge>Ativo</Badge>
                    ) : (
                      <Badge variant="secondary">Inativo</Badge>
                    )}
                    {bp.is_default && (
                      <Badge
                        variant="secondary"
                        className="bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                      >
                        Padrão
                      </Badge>
                    )}
                  </div>
                </div>
                <CardTitle className="mt-4 truncate">{bp.name}</CardTitle>
                <CardDescription className="line-clamp-2">
                  {bp.description || 'Sem descrição'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-1">
                    <span className="text-muted-foreground">Tipo:</span>
                    <Badge variant="outline">
                      {bp.document_type_display}
                    </Badge>
                  </div>
                  <p>
                    <span className="text-muted-foreground">Seções:</span>{' '}
                    {bp.section_count}
                  </p>
                  <p>
                    <span className="text-muted-foreground">Versão:</span>{' '}
                    {bp.version}
                  </p>
                  {bp.created_at && (
                    <p className="flex items-center gap-1 text-muted-foreground">
                      <Calendar className="h-3 w-3" />
                      {formatDate(bp.created_at)}
                    </p>
                  )}
                  {bp.created_by_name && (
                    <p>
                      <span className="text-muted-foreground">Criado por:</span>{' '}
                      {bp.created_by_name}
                    </p>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-2 mt-4" data-tour="bp-actions">
                  <Link href={`/dashboard/blueprints/${bp.id}`} className="flex-1">
                    <Button variant="outline" className="w-full">
                      <Edit className="mr-2 h-4 w-4" />
                      Editar
                    </Button>
                  </Link>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDuplicate(bp)}
                    disabled={isDuplicatingBlueprint}
                    title="Duplicar blueprint"
                  >
                    {isDuplicatingBlueprint ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleToggleActive(bp)}
                    disabled={isTogglingActive}
                    title={bp.is_active ? 'Desativar' : 'Ativar'}
                  >
                    {bp.is_active ? (
                      <PowerOff className="h-4 w-4" />
                    ) : (
                      <Power className="h-4 w-4" />
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDeleteClick(bp)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    title="Excluir blueprint"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        /* Lista compacta */
        <div className="border rounded-lg divide-y bg-card">
          {filteredBlueprints.map((bp) => (
            <div
              key={bp.id}
              className={`flex items-center gap-3 p-3 hover:bg-muted/30 ${
                !bp.is_active ? 'opacity-60' : ''
              }`}
            >
              <LayoutTemplate className="h-5 w-5 text-primary shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <Link href={`/dashboard/blueprints/${bp.id}`} className="hover:underline">
                    <p className="font-medium truncate">{bp.name}</p>
                  </Link>
                  {bp.is_default && (
                    <Badge
                      variant="secondary"
                      className="bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 text-[10px] px-1.5 py-0 h-4"
                    >
                      Padrão
                    </Badge>
                  )}
                  {!bp.is_active && (
                    <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-4">
                      Inativo
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-muted-foreground truncate">
                  <span>{bp.document_type_display}</span>
                  <span className="mx-1.5">·</span>
                  <span>{bp.section_count} seções</span>
                  <span className="mx-1.5">·</span>
                  <span>v{bp.version}</span>
                  {bp.created_at && (
                    <>
                      <span className="mx-1.5">·</span>
                      <Calendar className="inline h-3 w-3 mr-0.5" />
                      <span>{formatDate(bp.created_at)}</span>
                    </>
                  )}
                </p>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <Link href={`/dashboard/blueprints/${bp.id}`}>
                  <Button variant="outline" size="sm">
                    <Edit className="h-3.5 w-3.5" />
                  </Button>
                </Link>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => handleDuplicate(bp)}
                  disabled={isDuplicatingBlueprint}
                  title="Duplicar blueprint"
                  className="h-8 w-8"
                >
                  {isDuplicatingBlueprint ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Copy className="h-3.5 w-3.5" />
                  )}
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => handleToggleActive(bp)}
                  disabled={isTogglingActive}
                  title={bp.is_active ? 'Desativar' : 'Ativar'}
                  className="h-8 w-8"
                >
                  {bp.is_active ? (
                    <PowerOff className="h-3.5 w-3.5" />
                  ) : (
                    <Power className="h-3.5 w-3.5" />
                  )}
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => handleDeleteClick(bp)}
                  className="text-red-600 hover:text-red-700 hover:bg-red-50 h-8 w-8"
                  title="Excluir blueprint"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirmar exclusão</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja deletar o blueprint &quot;{blueprintToDelete?.name}&quot;?
              Todas as seções, agentes e configurações associadas serão removidos permanentemente.
              Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={isDeletingBlueprint}
            >
              {isDeletingBlueprint ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Deletando...
                </>
              ) : (
                'Deletar'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

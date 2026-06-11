'use client';

import { useState, useEffect } from 'react';
import { useKnowledgeBase } from '@/hooks/use-knowledge-base';
import { useToast } from '@/hooks/use-toast';
import api from '@/lib/api';
import type { ManagedKnowledgeBase } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  BookOpen,
  FileText,
  Loader2,
  Trash2,
  Database,
  Plus,
  Power,
  PowerOff,
  Link2,
  Globe,
  Layers,
  Brain,
} from 'lucide-react';
import { KBDetailSheet } from '@/components/kb/KBDetailSheet';

interface Blueprint {
  id: string;
  name: string;
  document_type_display: string;
}

const layerLabels: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  global: { label: 'Global', icon: <Globe className="h-3 w-3" />, color: 'bg-blue-100 text-blue-800' },
  blueprint: { label: 'Blueprint', icon: <Layers className="h-3 w-3" />, color: 'bg-purple-100 text-purple-800' },
  agent: { label: 'Agente', icon: <Brain className="h-3 w-3" />, color: 'bg-green-100 text-green-800' },
  section_example: { label: 'Exemplo', icon: <FileText className="h-3 w-3" />, color: 'bg-orange-100 text-orange-800' },
};

export default function KnowledgeBasePage() {
  const {
    allKBs, globalKBs, blueprintKBs, agentKBs,
    total, isLoading,
    createKB, isCreating,
    uploadToKB, isUploading,
    toggleKBActive,
    deleteKB, isDeletingKB,
    deleteSource, isDeletingSource,
  } = useKnowledgeBase();
  const { toast } = useToast();

  // Tab state
  const [activeTab, setActiveTab] = useState('all');

  // Dialog states
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  // Sheet state
  const [selectedKB, setSelectedKB] = useState<ManagedKnowledgeBase | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);

  // KB pending delete
  const [kbToDelete, setKBToDelete] = useState<ManagedKnowledgeBase | null>(null);

  // Create form state
  const [blueprints, setBlueprints] = useState<Blueprint[]>([]);
  const [createForm, setCreateForm] = useState({
    name: '',
    description: '',
    kb_layer: 'global' as string,
    blueprint: '',
  });

  // Load blueprints when dialog opens
  useEffect(() => {
    if (createDialogOpen) {
      api.get('/api/v1/intelligent-assistant/blueprints/')
        .then(res => setBlueprints(res.data.blueprints || []))
        .catch(() => {});
    }
  }, [createDialogOpen]);

  // Filter KBs by active tab
  const getFilteredKBs = () => {
    switch (activeTab) {
      case 'global': return globalKBs;
      case 'blueprint': return blueprintKBs;
      case 'agent': return agentKBs;
      default: return allKBs;
    }
  };

  const filteredKBs = getFilteredKBs();

  // ── Create KB ──
  const handleCreate = () => {
    if (!createForm.name.trim()) {
      toast({ title: 'Nome obrigatório', variant: 'destructive' });
      return;
    }

    createKB(
      {
        name: createForm.name,
        description: createForm.description,
        kb_layer: createForm.kb_layer,
        blueprint: createForm.kb_layer === 'blueprint' ? createForm.blueprint || undefined : undefined,
      },
      {
        onSuccess: () => {
          toast({ title: 'Base criada com sucesso' });
          setCreateDialogOpen(false);
          setCreateForm({ name: '', description: '', kb_layer: 'global', blueprint: '' });
        },
        onError: (error: any) => {
          toast({
            title: 'Erro ao criar base',
            description: error.response?.data?.name?.[0] || error.response?.data?.detail || 'Erro desconhecido',
            variant: 'destructive',
          });
        },
      }
    );
  };

  // ── Delete KB ──
  const handleDeleteKB = () => {
    if (!kbToDelete) return;
    deleteKB(kbToDelete.id, {
      onSuccess: () => {
        toast({ title: 'Base removida com sucesso' });
        setDeleteDialogOpen(false);
        setKBToDelete(null);
        if (selectedKB?.id === kbToDelete.id) {
          setSheetOpen(false);
          setSelectedKB(null);
        }
      },
      onError: () => {
        toast({ title: 'Erro ao remover base', variant: 'destructive' });
      },
    });
  };

  // ── Blueprint select handler for auto-name ──
  const handleBlueprintSelect = (bpId: string) => {
    const bp = blueprints.find(b => b.id === bpId);
    setCreateForm(prev => ({
      ...prev,
      blueprint: bpId,
      name: prev.name || (bp ? `KB - ${bp.name}` : ''),
    }));
  };

  // ── Open KB detail ──
  const openKBDetail = (kb: ManagedKnowledgeBase) => {
    setSelectedKB(kb);
    setSheetOpen(true);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold">Base de Conhecimento</h1>
          <p className="text-muted-foreground text-sm sm:text-base">
            Gerencie bases, documentos e vínculos com agentes
          </p>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)} className="w-full sm:w-auto">
          <Plus className="mr-2 h-4 w-4" />
          Nova Base
        </Button>
      </div>

      {/* Tabs por camada - horizontal scroll on mobile */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="overflow-x-auto -mx-1 px-1">
          <TabsList className="w-max sm:w-auto">
            <TabsTrigger value="all" className="flex items-center gap-1 text-xs sm:text-sm">
              <BookOpen className="h-3 w-3" />
              Todas ({total})
            </TabsTrigger>
            <TabsTrigger value="global" className="flex items-center gap-1 text-xs sm:text-sm">
              <Globe className="h-3 w-3" />
              Global ({globalKBs.length})
            </TabsTrigger>
            <TabsTrigger value="blueprint" className="flex items-center gap-1 text-xs sm:text-sm">
              <Layers className="h-3 w-3" />
              Blueprint ({blueprintKBs.length})
            </TabsTrigger>
            <TabsTrigger value="agent" className="flex items-center gap-1 text-xs sm:text-sm">
              <Brain className="h-3 w-3" />
              Agente ({agentKBs.length})
            </TabsTrigger>
          </TabsList>
        </div>
      </Tabs>

      {/* Grid de KBs */}
      {filteredKBs.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <Database className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-lg font-medium">Nenhuma base de conhecimento</p>
            <p className="text-sm mt-1">Clique em &quot;Nova Base&quot; para criar.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
          {filteredKBs.map((kb) => {
            const layer = layerLabels[kb.kb_layer] || layerLabels.global;
            return (
              <Card
                key={kb.id}
                className={`cursor-pointer transition-shadow hover:shadow-md ${
                  !kb.is_active ? 'opacity-60' : ''
                }`}
                onClick={() => openKBDetail(kb)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div className="min-w-0 flex-1">
                      <CardTitle className="text-base truncate">{kb.name}</CardTitle>
                      <CardDescription className="text-xs mt-1">
                        {kb.blueprint_name || kb.document_type_name || kb.agent_config_name || 'Sem vínculo'}
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-1 ml-2 shrink-0">
                      <Badge className={`text-xs ${layer.color}`} variant="secondary">
                        {layer.icon}
                        <span className="ml-1">{layer.label}</span>
                      </Badge>
                      {!kb.is_active && (
                        <Badge variant="secondary">Inativo</Badge>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {kb.description && (
                    <p className="text-xs text-muted-foreground line-clamp-2">{kb.description}</p>
                  )}

                  {/* Stats */}
                  <div className="flex flex-wrap gap-3 text-sm text-muted-foreground">
                    <span className="inline-flex items-center gap-1">
                      <FileText className="h-3 w-3" />
                      {kb.sources_count} fonte{kb.sources_count !== 1 ? 's' : ''}
                    </span>
                    <span className="inline-flex items-center gap-1">
                      <Database className="h-3 w-3" />
                      {kb.total_chunks} chunks
                    </span>
                    {kb.kb_layer !== 'global' && (
                      <span className="inline-flex items-center gap-1">
                        <Link2 className="h-3 w-3" />
                        {kb.agent_links_count || 0} agente{(kb.agent_links_count || 0) !== 1 ? 's' : ''}
                      </span>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => toggleKBActive({ kbId: kb.id, isActive: !kb.is_active })}
                      title={kb.is_active ? 'Desativar' : 'Ativar'}
                    >
                      {kb.is_active ? <PowerOff className="h-3 w-3" /> : <Power className="h-3 w-3" />}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      onClick={() => {
                        setKBToDelete(kb);
                        setDeleteDialogOpen(true);
                      }}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Sheet: Detalhe da KB */}
      <KBDetailSheet
        kb={selectedKB}
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        onUpload={(kbId, formData, callbacks) => {
          uploadToKB({ kbId, formData }, callbacks);
        }}
        isUploading={isUploading}
        onDeleteSource={(kbId, sourceName, callbacks) => {
          deleteSource({ kbId, sourceName }, callbacks);
        }}
        isDeletingSource={isDeletingSource}
      />

      {/* Dialog: Criar Nova KB */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nova Base de Conhecimento</DialogTitle>
            <DialogDescription>
              Crie uma base para armazenar documentos de referência
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Camada</Label>
              <Select
                value={createForm.kb_layer}
                onValueChange={(value) => setCreateForm({ ...createForm, kb_layer: value, blueprint: '' })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="global">Global (disponível para todos os agentes)</SelectItem>
                  <SelectItem value="blueprint">Blueprint (vinculada a um tipo de documento)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {createForm.kb_layer === 'blueprint' && (
              <div className="space-y-2">
                <Label>Blueprint *</Label>
                <Select
                  value={createForm.blueprint}
                  onValueChange={handleBlueprintSelect}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione um blueprint" />
                  </SelectTrigger>
                  <SelectContent>
                    {blueprints.map((bp) => (
                      <SelectItem key={bp.id} value={bp.id}>
                        {bp.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="space-y-2">
              <Label>Nome *</Label>
              <Input
                value={createForm.name}
                onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                placeholder={createForm.kb_layer === 'global' ? 'Ex: KB Global - Legislação' : 'Ex: KB - Direito Trabalhista'}
              />
            </div>

            <div className="space-y-2">
              <Label>Descrição</Label>
              <Input
                value={createForm.description}
                onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                placeholder="Descrição opcional"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
              Cancelar
            </Button>
            <Button onClick={handleCreate} disabled={isCreating}>
              {isCreating ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Criando...</>
              ) : (
                'Criar Base'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog: Confirmar exclusão */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirmar Exclusão</DialogTitle>
            <DialogDescription>
              Deseja excluir a base &quot;{kbToDelete?.name}&quot;? Todos os embeddings associados serão removidos permanentemente.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)} disabled={isDeletingKB}>
              Cancelar
            </Button>
            <Button variant="destructive" onClick={handleDeleteKB} disabled={isDeletingKB}>
              {isDeletingKB ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Excluindo...</>
              ) : (
                <><Trash2 className="mr-2 h-4 w-4" />Excluir</>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

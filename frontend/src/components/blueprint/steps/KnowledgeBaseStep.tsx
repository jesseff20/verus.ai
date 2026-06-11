'use client';

import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import type { DocumentBlueprint, ManagedKnowledgeBase } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Database, Globe, ExternalLink, Plus, FileText, Loader2, AlertCircle } from 'lucide-react';
import Link from 'next/link';

interface KnowledgeBaseStepProps {
  blueprint: DocumentBlueprint;
}

/**
 * Step de visualizacao das Knowledge Bases vinculadas a um blueprint.
 * Exibe um grid de cards com informacoes de cada KB (nome, descricao, layer, chunks, sources).
 * Permite navegar para a pagina de gerenciamento de KBs e criar novas KBs.
 * Este componente e somente leitura -- o gerenciamento de KBs e feito na pagina dedicada.
 */
export function KnowledgeBaseStep({ blueprint }: KnowledgeBaseStepProps) {
  // Buscar KBs do blueprint + globais (lista unificada)
  const {
    data: knowledgeBases,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['blueprint-knowledge-bases', blueprint.id],
    queryFn: async () => {
      const response = await api.get<{
        knowledge_bases: ManagedKnowledgeBase[];
        global_kbs: ManagedKnowledgeBase[];
      }>(
        '/api/v1/intelligent-assistant/knowledge-bases/manage/',
        {
          params: {
            kb_layer: 'all',
          },
        }
      );
      const allKBs = response.data.knowledge_bases || [];
      // KBs deste blueprint + todas as globais
      const blueprintKBs = allKBs.filter((kb) => kb.kb_layer === 'blueprint' && kb.blueprint_id === blueprint.id);
      const globalKBs = allKBs.filter((kb) => kb.kb_layer === 'global');
      return [...blueprintKBs, ...globalKBs];
    },
    enabled: !!blueprint.id,
  });

  // Estado de carregamento
  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          <span className="ml-2 text-sm text-muted-foreground">
            Carregando bases de conhecimento...
          </span>
        </CardContent>
      </Card>
    );
  }

  // Estado de erro
  if (error) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <AlertCircle className="h-5 w-5 text-destructive" />
          <span className="ml-2 text-sm text-destructive">
            Erro ao carregar bases de conhecimento.
          </span>
        </CardContent>
      </Card>
    );
  }

  const kbs = knowledgeBases || [];

  return (
    <div className="space-y-6">
      {/* Header com acoes */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Bases de Conhecimento</h3>
          <p className="text-sm text-muted-foreground">
            KBs vinculadas ao blueprint &quot;{blueprint.name}&quot; e bases globais
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/dashboard/knowledge-base">
            <Button variant="outline" size="sm">
              <ExternalLink className="h-4 w-4 mr-2" />
              Gerenciar KBs
            </Button>
          </Link>
          <Link href={`/dashboard/knowledge-base?action=create&blueprint_id=${blueprint.id}`}>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Nova KB
            </Button>
          </Link>
        </div>
      </div>

      {/* Grid de KBs ou estado vazio */}
      {kbs.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Database className="h-12 w-12 text-muted-foreground/40 mb-4" />
            <p className="text-sm font-medium text-muted-foreground">
              Nenhuma base de conhecimento vinculada a este blueprint
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Crie uma nova KB ou vincule uma existente na pagina de gerenciamento.
            </p>
            <Link href={`/dashboard/knowledge-base?action=create&blueprint_id=${blueprint.id}`}>
              <Button variant="outline" size="sm" className="mt-4">
                <Plus className="h-4 w-4 mr-2" />
                Criar Base de Conhecimento
              </Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {kbs.map((kb) => (
            <Card key={kb.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2 min-w-0">
                    <Database className="h-4 w-4 text-primary shrink-0" />
                    <CardTitle className="text-sm font-semibold truncate">
                      {kb.name}
                    </CardTitle>
                  </div>
                  <Badge
                    variant={kb.is_active ? 'default' : 'secondary'}
                    className="text-[10px] shrink-0"
                  >
                    {kb.is_active ? 'Ativa' : 'Inativa'}
                  </Badge>
                </div>
                {kb.description && (
                  <CardDescription className="text-xs line-clamp-2 mt-1">
                    {kb.description}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent className="pt-0">
                <div className="flex flex-wrap gap-2 mb-3">
                  <Badge
                    variant="outline"
                    className={`text-[10px] ${kb.kb_layer === 'global' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : ''}`}
                  >
                    {kb.kb_layer === 'global' && <Globe className="h-3 w-3 mr-1" />}
                    {kb.kb_layer === 'global' ? 'Global' : 'Blueprint'}
                  </Badge>
                  {kb.document_type_name && (
                    <Badge variant="outline" className="text-[10px]">
                      {kb.document_type_name}
                    </Badge>
                  )}
                </div>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="rounded-lg bg-muted/50 p-2">
                    <p className="text-lg font-bold text-primary">{kb.total_chunks}</p>
                    <p className="text-[10px] text-muted-foreground">Chunks</p>
                  </div>
                  <div className="rounded-lg bg-muted/50 p-2">
                    <p className="text-lg font-bold text-primary">{kb.sources_count}</p>
                    <p className="text-[10px] text-muted-foreground">Fontes</p>
                  </div>
                  <div className="rounded-lg bg-muted/50 p-2">
                    <p className="text-lg font-bold text-primary">{kb.agent_links_count}</p>
                    <p className="text-[10px] text-muted-foreground">Agentes</p>
                  </div>
                </div>
                {kb.created_by_name && (
                  <p className="text-[10px] text-muted-foreground mt-3">
                    <FileText className="h-3 w-3 inline mr-1" />
                    Criada por {kb.created_by_name}
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

export default KnowledgeBaseStep;

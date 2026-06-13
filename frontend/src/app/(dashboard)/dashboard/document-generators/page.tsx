'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useDocumentGenerators } from '@/hooks/use-document-generators';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
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
  Plus, Eye, Edit, Trash2, Loader2, Sparkles,
  Copy, FileText, Search, Filter, ArrowLeft
} from 'lucide-react';
import * as LucideIcons from 'lucide-react';
import type { DocumentGenerator } from '@/hooks/use-document-generators';
import CreateDocumentGeneratorDialog from '@/components/documents/CreateDocumentGeneratorDialog';
import EditDocumentGeneratorDialog from '@/components/documents/EditDocumentGeneratorDialog';

const providerLabels: Record<string, string> = {
  openai: 'OpenAI',
  watsonx: 'IBM WatsonX',
};

const documentTypeLabels: Record<string, { label: string; color: string }> = {
  peticao_inicial: { label: 'Petição Inicial', color: 'bg-blue-100 text-blue-700' },
  contestacao: { label: 'Contestação', color: 'bg-amber-100 text-amber-700' },
  recurso: { label: 'Recurso', color: 'bg-orange-100 text-orange-700' },
  memoriais: { label: 'Memoriais', color: 'bg-indigo-100 text-indigo-700' },
  tutela_urgencia: { label: 'Tutela de Urgência', color: 'bg-yellow-100 text-yellow-700' },
  impugnacao: { label: 'Impugnação', color: 'bg-red-100 text-red-700' },
  embargos_declaracao: { label: 'Embargos de Declaração', color: 'bg-slate-100 text-slate-700' },
  contrato: { label: 'Contrato', color: 'bg-green-100 text-green-700' },
  procuracao: { label: 'Procuração', color: 'bg-teal-100 text-teal-700' },
  notificacao_extrajudicial: { label: 'Notificação Extrajudicial', color: 'bg-gray-100 text-gray-700' },
  parecer: { label: 'Parecer Jurídico', color: 'bg-yellow-100 text-yellow-800' },
  nota_juridica: { label: 'Nota Jurídica', color: 'bg-cyan-100 text-cyan-700' },
  habeas_corpus: { label: 'Habeas Corpus', color: 'bg-red-100 text-red-800' },
  mandado_seguranca: { label: 'Mandado de Segurança', color: 'bg-violet-100 text-violet-700' },
  acao_popular: { label: 'Ação Popular', color: 'bg-indigo-100 text-indigo-800' },
  acao_civil_publica: { label: 'Ação Civil Pública', color: 'bg-green-100 text-green-800' },
};

const ESPECIALIDADES = [
  { value: 'geral', label: 'Geral' },
  { value: 'civel', label: 'Direito Civil' },
  { value: 'penal', label: 'Direito Penal' },
  { value: 'trabalhista', label: 'Trabalhista' },
  { value: 'tributario', label: 'Tributário' },
  { value: 'previdenciario', label: 'Previdenciário' },
  { value: 'administrativo', label: 'Administrativo' },
  { value: 'constitucional', label: 'Constitucional' },
  { value: 'empresarial', label: 'Empresarial' },
  { value: 'consumidor', label: 'Consumidor' },
  { value: 'familia', label: 'Família e Sucessões' },
  { value: 'imobiliario', label: 'Imobiliário' },
  { value: 'ambiental', label: 'Ambiental' },
  { value: 'digital', label: 'Digital e LGPD' },
  { value: 'saude', label: 'Saúde' },
  { value: 'eleitoral', label: 'Eleitoral' },
  { value: 'internacional', label: 'Internacional' },
];

export default function DocumentGeneratorsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [providerFilter, setProviderFilter] = useState<string>('all');
  const [specialtyFilter, setSpecialtyFilter] = useState<string>('all');

  const {
    generators,
    count,
    isLoading,
    refetch,
    deleteGenerator,
    isDeleting,
    duplicateGenerator,
    isDuplicating,
    useStats
  } = useDocumentGenerators(1, 100);

  const { data: stats } = useStats();
  const { toast } = useToast();

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [generatorToDelete, setGeneratorToDelete] = useState<DocumentGenerator | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [generatorToEdit, setGeneratorToEdit] = useState<DocumentGenerator | null>(null);

  const handleDeleteClick = (generator: DocumentGenerator) => {
    setGeneratorToDelete(generator);
    setDeleteDialogOpen(true);
  };

  const handleEditClick = (generator: DocumentGenerator) => {
    setGeneratorToEdit(generator);
    setEditDialogOpen(true);
  };

  const handleDuplicateClick = async (generator: DocumentGenerator) => {
    try {
      await duplicateGenerator(generator.id);
      toast({
        title: 'Gerador duplicado',
        description: `Uma cópia de "${generator.name}" foi criada com sucesso.`,
      });
      refetch();
    } catch (error: any) {
      toast({
        title: 'Erro ao duplicar',
        description: error.response?.data?.detail || 'Não foi possível duplicar o gerador.',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteConfirm = async () => {
    if (!generatorToDelete) return;

    try {
      await deleteGenerator(generatorToDelete.id);
      toast({
        title: 'Gerador deletado',
        description: `O gerador "${generatorToDelete.name}" foi removido com sucesso.`,
      });
      setDeleteDialogOpen(false);
      setGeneratorToDelete(null);
      refetch();
    } catch (error: any) {
      toast({
        title: 'Erro ao deletar',
        description: error.response?.data?.detail || 'Não foi possível deletar o gerador.',
        variant: 'destructive',
      });
    }
  };

  // Função para obter ícone dinamicamente
  const getIcon = (iconName: string) => {
    const Icon = (LucideIcons as any)[iconName] || LucideIcons.FileText;
    return Icon;
  };

  // Filtrar geradores
  const filteredGenerators = generators.filter(generator => {
    const matchesSearch = generator.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         generator.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = typeFilter === 'all' || generator.document_type === typeFilter;
    const matchesProvider = providerFilter === 'all' || generator.llm_provider === providerFilter;
    const matchesSpecialty = specialtyFilter === 'all' || generator.specialty === specialtyFilter;

    return matchesSearch && matchesType && matchesProvider && matchesSpecialty;
  });

  // Obter tipos únicos dos geradores
  const uniqueTypes = Array.from(new Set(generators.map(g => g.document_type)));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/dashboard/agents">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Voltar
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold">Geradores de Documento</h1>
            <p className="text-muted-foreground">
              Agentes de IA especializados em gerar documentos completos
            </p>
          </div>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Novo Gerador
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total de Geradores</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total}</div>
              <p className="text-xs text-muted-foreground">
                {stats.active} ativos
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">OpenAI</CardTitle>
              <Sparkles className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.by_provider.openai.count}</div>
              <p className="text-xs text-muted-foreground">
                geradores
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">IBM WatsonX</CardTitle>
              <Sparkles className="h-4 w-4 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.by_provider.watsonx?.count ?? 0}</div>
              <p className="text-xs text-muted-foreground">
                geradores
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Filter className="h-4 w-4" />
            Filtros
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Buscar</label>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Nome ou descrição..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Tipo de Documento</label>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Todos os tipos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos os tipos</SelectItem>
                  {uniqueTypes.map(type => (
                    <SelectItem key={type} value={type}>
                      {documentTypeLabels[type]?.label || type}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Provider</label>
              <Select value={providerFilter} onValueChange={setProviderFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Todos os providers" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos os providers</SelectItem>
                  <SelectItem value="openai">OpenAI</SelectItem>
                  <SelectItem value="watsonx">IBM WatsonX</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Especialidade</label>
              <Select value={specialtyFilter} onValueChange={setSpecialtyFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Especialidade" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas as Especialidades</SelectItem>
                  {ESPECIALIDADES.map(esp => (
                    <SelectItem key={esp.value} value={esp.value}>{esp.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {(searchTerm || typeFilter !== 'all' || providerFilter !== 'all' || specialtyFilter !== 'all') && (
            <div className="flex items-center justify-between pt-2 border-t">
              <p className="text-sm text-muted-foreground">
                {filteredGenerators.length} de {generators.length} geradores
              </p>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setSearchTerm('');
                  setTypeFilter('all');
                  setProviderFilter('all');
                  setSpecialtyFilter('all');
                }}
              >
                Limpar filtros
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Generators Grid */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : filteredGenerators.length === 0 ? (
        <Card className="p-12">
          <div className="flex flex-col items-center text-center gap-4">
            <FileText className="h-16 w-16 text-muted-foreground opacity-50" />
            <div>
              <h3 className="text-lg font-semibold mb-2">
                {searchTerm || typeFilter !== 'all' || providerFilter !== 'all' || specialtyFilter !== 'all'
                  ? 'Nenhum gerador encontrado'
                  : 'Nenhum gerador configurado'
                }
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                {searchTerm || typeFilter !== 'all' || providerFilter !== 'all' || specialtyFilter !== 'all'
                  ? 'Tente ajustar os filtros de busca'
                  : 'Crie seu primeiro gerador de documento'
                }
              </p>
            </div>
            {!(searchTerm || typeFilter !== 'all' || providerFilter !== 'all' || specialtyFilter !== 'all') && (
              <Button onClick={() => setCreateDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Criar Gerador
              </Button>
            )}
          </div>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredGenerators.map((generator) => {
            const Icon = getIcon(generator.icon || 'FileText');
            const typeInfo = documentTypeLabels[generator.document_type];

            return (
              <Card key={generator.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <Icon
                        className="h-8 w-8"
                        style={{ color: generator.color }}
                      />
                    </div>
                    <div className="flex gap-2 flex-wrap">
                      {generator.is_active ? (
                        <Badge variant="default">Ativo</Badge>
                      ) : (
                        <Badge variant="secondary">Inativo</Badge>
                      )}
                      {generator.is_default && (
                        <Badge variant="outline" className="border-purple-500 text-purple-700">
                          Público
                        </Badge>
                      )}
                      {generator.use_rag && (
                        <Badge variant="secondary" className="bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
                          <Sparkles className="h-3 w-3 mr-1" />
                          RAG
                        </Badge>
                      )}
                    </div>
                  </div>
                  <CardTitle className="mt-4 line-clamp-1">{generator.name}</CardTitle>
                  <CardDescription className="line-clamp-2">
                    {generator.description || 'Sem descrição'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {/* Badge de Tipo */}
                    <div className="flex items-center gap-2 flex-wrap">
                      {typeInfo && (
                        <Badge className={typeInfo.color}>
                          {typeInfo.label}
                        </Badge>
                      )}
                      {generator.specialty && generator.specialty !== 'geral' && (
                        <Badge variant="secondary" className="text-xs">
                          {ESPECIALIDADES.find(e => e.value === generator.specialty)?.label || generator.specialty}
                        </Badge>
                      )}
                      {generator.document_template_name && (
                        <Badge variant="outline" className="text-xs">
                          Template: {generator.document_template_name}
                        </Badge>
                      )}
                    </div>

                    {/* Informações Técnicas */}
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <p className="text-muted-foreground text-xs">Provider</p>
                        <p className="font-medium">{generator.provider_display || providerLabels[generator.llm_provider]}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground text-xs">Modelo</p>
                        <p className="font-medium text-xs truncate" title={generator.model_name}>
                          {generator.model_name}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground text-xs">Temperature</p>
                        <p className="font-medium">{generator.temperature}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground text-xs">Max Tokens</p>
                        <p className="font-medium">{generator.max_tokens}</p>
                      </div>
                    </div>

                    {/* Metadados */}
                    {(generator.variable_count > 0 || generator.created_by_name) && (
                      <div className="pt-2 border-t space-y-1">
                        {generator.variable_count > 0 && (
                          <p className="text-xs text-muted-foreground">
                            Variáveis: <span className="font-medium">{generator.variable_count}</span>
                          </p>
                        )}
                        {generator.created_by_name && (
                          <p className="text-xs text-muted-foreground">
                            Criado por: <span className="font-medium">{generator.created_by_name}</span>
                          </p>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Ações */}
                  <div className="flex gap-2 mt-4">
                    <Link href={`/dashboard/document-generators/${generator.id}`} className="flex-1">
                      <Button variant="outline" className="w-full" size="sm">
                        <Eye className="mr-2 h-4 w-4" />
                        Detalhes
                      </Button>
                    </Link>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDuplicateClick(generator)}
                      title="Duplicar gerador"
                      disabled={isDuplicating}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEditClick(generator)}
                      title="Editar gerador"
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteClick(generator)}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      title="Deletar gerador"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Create Generator Dialog */}
      <CreateDocumentGeneratorDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onSuccess={refetch}
      />

      {/* Edit Generator Dialog */}
      {generatorToEdit && (
        <EditDocumentGeneratorDialog
          open={editDialogOpen}
          onOpenChange={setEditDialogOpen}
          generator={generatorToEdit}
          onSuccess={refetch}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirmar exclusão</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja deletar o gerador &quot;{generatorToDelete?.name}&quot;?
              Esta ação não pode ser desfeita.
              {generatorToDelete?.is_default && (
                <span className="block mt-2 text-amber-600 font-medium">
                  ⚠️ Este é um gerador público. Deletá-lo pode afetar outros usuários.
                </span>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={isDeleting}
            >
              {isDeleting ? (
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

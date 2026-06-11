'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { useUnifiedDocuments, useDocuments, type UnifiedDocument, type UnifiedDocumentsFilters } from '@/hooks/use-documents';
import api from '@/lib/api';
import { useAuth } from '@/hooks/use-auth';
import { usePermissions } from '@/hooks/use-permissions';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';

// Base URL da API backend
const API_BASE_URL = (/^https?:\/\//.test(process.env.NEXT_PUBLIC_API_URL || '')) ? process.env.NEXT_PUBLIC_API_URL! : '';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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
  FileText,
  Plus,
  Eye,
  Download,
  Loader2,
  Search,
  Filter,
  X,
  Bot,
  FileEdit,
  User,
  MoreHorizontal,
  ExternalLink,
  RefreshCw,
  Pencil,
  Trash2,
} from 'lucide-react';

// Mapeamento de status para badges
const statusConfig: Record<string, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
  draft: { label: 'Rascunho', variant: 'outline' },
  in_review: { label: 'Em Revisão', variant: 'secondary' },
  completed: { label: 'Completo', variant: 'default' },
  archived: { label: 'Arquivado', variant: 'destructive' },
};

// Mapeamento de origem para badges
const sourceConfig: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  manual: { label: 'Manual', icon: <FileEdit className="h-3 w-3" />, color: 'bg-slate-100 text-slate-700' },
  generator: { label: 'Gerador', icon: <FileText className="h-3 w-3" />, color: 'bg-blue-100 text-blue-700' },
  assistant: { label: 'Assistente IA', icon: <Bot className="h-3 w-3" />, color: 'bg-purple-100 text-purple-700' },
};

// Função para obter URL completa do PDF
const getPdfUrl = (doc: UnifiedDocument): string | null => {
  if (!doc.pdf_url) return null;

  // Se já é uma URL absoluta (ex: R2 storage), usar diretamente
  if (doc.pdf_url.startsWith('http://') || doc.pdf_url.startsWith('https://')) {
    return doc.pdf_url;
  }

  // Se é uma URL relativa da API, adicionar base URL do backend
  return `${API_BASE_URL}${doc.pdf_url}`;
};

export default function DocumentsPage() {
  const { user } = useAuth();
  const { hasPermission } = usePermissions();
  const { toast } = useToast();

  const canEditDocs = hasPermission('documents.edit_own') || hasPermission('documents.edit_all');
  const canDeleteDocs = hasPermission('documents.delete_own') || hasPermission('documents.delete_all');

  // Download PDF autenticado (resolve 401 em nova aba)
  const handleDownloadPdf = async (doc: UnifiedDocument) => {
    const pdfUrl = getPdfUrl(doc);
    if (!pdfUrl) return;
    try {
      const response = await api.get(pdfUrl, { responseType: 'blob' });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${doc.title || 'documento'}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch {
      toast({
        title: 'Erro ao baixar PDF',
        description: 'Não foi possível baixar o documento.',
        variant: 'destructive',
      });
    }
  };

  // Filtros
  const [filters, setFilters] = useState<UnifiedDocumentsFilters>({});
  const [searchInput, setSearchInput] = useState('');

  // Estado para dialog de exclusão
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [documentToDelete, setDocumentToDelete] = useState<UnifiedDocument | null>(null);

  // Buscar documentos unificados
  const { documents, count, isLoading, isFetching, refetch } = useUnifiedDocuments(filters);

  // Hook para operações de documentos (delete)
  const { deleteDocument, isDeleting } = useDocuments();

  // Função para abrir dialog de exclusão
  const handleDeleteClick = (doc: UnifiedDocument) => {
    setDocumentToDelete(doc);
    setDeleteDialogOpen(true);
  };

  // Função para confirmar exclusão
  const handleConfirmDelete = async () => {
    if (!documentToDelete) return;

    try {
      if (documentToDelete.system === 'intelligent_assistant') {
        // Documentos do Assistente IA: usa endpoint específico
        const sessionId = (documentToDelete as any).session_id;
        await api.delete(
          `/api/v1/intelligent-assistant/sessions/${sessionId}/documents/${documentToDelete.id}/`
        );
      } else {
        // Documentos do sistema tradicional
        await deleteDocument(documentToDelete.id);
      }
      toast({
        title: 'Documento excluído',
        description: 'O documento foi excluído com sucesso.',
      });
      refetch();
    } catch (error: any) {
      toast({
        title: 'Erro ao excluir',
        description: error.response?.data?.error || error.response?.data?.detail || 'Ocorreu um erro ao excluir o documento.',
        variant: 'destructive',
      });
    } finally {
      setDeleteDialogOpen(false);
      setDocumentToDelete(null);
    }
  };

  // Verificar se é Manager ou superior
  const canSeeAllUsers = user?.role && ['manager', 'superadmin', 'reviewer'].includes(user.role);

  // Aplicar busca com debounce
  const handleSearch = () => {
    setFilters((prev) => ({ ...prev, search: searchInput || undefined }));
  };

  // Limpar filtros
  const clearFilters = () => {
    setFilters({});
    setSearchInput('');
  };

  // Verificar se há filtros ativos
  const hasActiveFilters = useMemo(() => {
    return !!(filters.status || filters.source || filters.search || filters.system);
  }, [filters]);

  // Formatar data/hora
  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return {
      date: date.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      }),
      time: date.toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit',
      }),
    };
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Listagem de Arquivos</h1>
          <p className="text-muted-foreground">
            Visualize todos os arquivos e documentos gerados pelo sistema
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
          <RefreshCw className={`mr-2 h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
          Atualizar
        </Button>
      </div>

      {/* Filtros */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <CardTitle className="text-base">Filtros</CardTitle>
            </div>
            {hasActiveFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                <X className="mr-2 h-4 w-4" />
                Limpar filtros
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            {/* Busca */}
            <div className="flex gap-2 flex-1 min-w-[250px]">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Buscar por título ou processo..."
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  className="pl-9"
                />
              </div>
              <Button variant="secondary" onClick={handleSearch}>
                Buscar
              </Button>
            </div>

            {/* Filtro por Status */}
            <Select
              value={filters.status || 'all'}
              onValueChange={(value) =>
                setFilters((prev) => ({ ...prev, status: value === 'all' ? undefined : value }))
              }
            >
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos Status</SelectItem>
                <SelectItem value="draft">Rascunho</SelectItem>
                <SelectItem value="in_review">Em Revisão</SelectItem>
                <SelectItem value="completed">Completo</SelectItem>
                <SelectItem value="archived">Arquivado</SelectItem>
              </SelectContent>
            </Select>

            {/* Filtro por Origem */}
            <Select
              value={filters.source || 'all'}
              onValueChange={(value) =>
                setFilters((prev) => ({
                  ...prev,
                  source: value === 'all' ? undefined : (value as UnifiedDocumentsFilters['source']),
                }))
              }
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Origem" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas Origens</SelectItem>
                <SelectItem value="manual">Manual</SelectItem>
                <SelectItem value="generator">Gerador</SelectItem>
                <SelectItem value="assistant">Assistente IA</SelectItem>
              </SelectContent>
            </Select>

            {/* Filtro por Sistema */}
            <Select
              value={filters.system || 'all'}
              onValueChange={(value) =>
                setFilters((prev) => ({
                  ...prev,
                  system: value === 'all' ? undefined : (value as UnifiedDocumentsFilters['system']),
                }))
              }
            >
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Sistema" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos os Sistemas</SelectItem>
                <SelectItem value="documents">Geradores de Documento</SelectItem>
                <SelectItem value="intelligent_assistant">Assistente Inteligente</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Tabela de Documentos */}
      <Card>
        <CardHeader>
          <CardTitle>Lista de Documentos</CardTitle>
          <CardDescription>
            {count} documento{count !== 1 ? 's' : ''} encontrado{count !== 1 ? 's' : ''}
            {hasActiveFilters && ' (com filtros aplicados)'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : documents.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FileText className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">
                {hasActiveFilters ? 'Nenhum arquivo encontrado' : 'Nenhum arquivo disponível'}
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                {hasActiveFilters
                  ? 'Tente ajustar os filtros para encontrar o que procura'
                  : 'Os arquivos gerados aparecerão aqui'}
              </p>
              {hasActiveFilters && (
                <Button variant="outline" onClick={clearFilters}>
                  Limpar filtros
                </Button>
              )}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[300px]">Título</TableHead>
                  <TableHead>Processo</TableHead>
                  {canSeeAllUsers && <TableHead>Criado por</TableHead>}
                  <TableHead>Origem</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Criado em</TableHead>
                  <TableHead className="text-right">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {documents.map((doc) => {
                  const { date, time } = formatDateTime(doc.created_at);
                  const source = sourceConfig[doc.source] || sourceConfig.manual;
                  const status = statusConfig[doc.status] || { label: doc.status_display, variant: 'outline' as const };

                  return (
                    <TableRow key={`${doc.system}-${doc.id}`}>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium truncate max-w-[280px]" title={doc.title}>
                            {doc.title}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {doc.system === 'intelligent_assistant'
                              ? doc.blueprint_name || doc.document_type
                              : doc.form_template_name || doc.blueprint_name}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {doc.numero_processo || '-'}
                      </TableCell>
                      {canSeeAllUsers && (
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <User className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm">{doc.user_name}</span>
                          </div>
                        </TableCell>
                      )}
                      <TableCell>
                        <Badge variant="outline" className={`${source.color} gap-1`}>
                          {source.icon}
                          {source.label}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={status.variant}>{status.label}</Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="text-sm">{date}</span>
                          <span className="text-xs text-muted-foreground">{time}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          {/* Botão principal: PDF download autenticado */}
                          {doc.has_generated_content && getPdfUrl(doc) && (
                            <Button variant="default" size="sm" onClick={() => handleDownloadPdf(doc)}>
                              <Download className="mr-1 h-4 w-4" />
                              PDF
                            </Button>
                          )}
                          {/* Botão Ver HTML: só para quem pode editar */}
                          {canEditDocs && doc.has_generated_content && doc.preview_url && !getPdfUrl(doc) && (
                            <Button variant="default" size="sm" asChild>
                              <Link href={doc.preview_url}>
                                <Eye className="mr-1 h-4 w-4" />
                                Ver
                              </Link>
                            </Button>
                          )}
                          {/* Botão Visualizar no Assistente: só para quem pode editar */}
                          {canEditDocs && doc.system === 'intelligent_assistant' && (
                            <Button variant="outline" size="sm" asChild>
                              <Link href={doc.detail_url}>
                                <Eye className="mr-1 h-4 w-4" />
                                Visualizar
                              </Link>
                            </Button>
                          )}

                          {/* Menu secundário: só mostra se tem alguma ação disponível */}
                          {(canEditDocs || canDeleteDocs) && (
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              {/* Editar: só para quem tem permissão + documentos do sistema tradicional */}
                              {canEditDocs && doc.system === 'documents' && (
                                <DropdownMenuItem asChild>
                                  <Link href={doc.detail_url}>
                                    <Pencil className="mr-2 h-4 w-4" />
                                    Editar
                                  </Link>
                                </DropdownMenuItem>
                              )}
                              {/* Visualizar no Assistente: só para quem pode editar */}
                              {canEditDocs && doc.system === 'intelligent_assistant' && (
                                <DropdownMenuItem asChild>
                                  <Link href={doc.detail_url}>
                                    <Eye className="mr-2 h-4 w-4" />
                                    Visualizar no Assistente
                                  </Link>
                                </DropdownMenuItem>
                              )}
                              {/* Preview HTML: só para quem pode editar */}
                              {canEditDocs && doc.preview_url && (
                                <DropdownMenuItem asChild>
                                  <Link href={doc.preview_url}>
                                    <ExternalLink className="mr-2 h-4 w-4" />
                                    Preview HTML
                                  </Link>
                                </DropdownMenuItem>
                              )}
                              {/* Excluir: só para quem tem permissão */}
                              {canDeleteDocs && (
                                <DropdownMenuItem
                                  className="text-red-600 focus:text-red-600"
                                  onClick={() => handleDeleteClick(doc)}
                                >
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  Excluir
                                </DropdownMenuItem>
                              )}
                            </DropdownMenuContent>
                          </DropdownMenu>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Dialog de confirmação de exclusão */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir documento?</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja excluir o documento "{documentToDelete?.title}"?
              Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              disabled={isDeleting}
              className="bg-red-600 hover:bg-red-700"
            >
              {isDeleting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Excluindo...
                </>
              ) : (
                'Excluir'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

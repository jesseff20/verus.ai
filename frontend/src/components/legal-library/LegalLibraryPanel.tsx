'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import {
  BookOpen,
  Scale,
  TrendingUp,
  Plus,
  Search,
  Filter,
  Star,
  Copy,
  Edit,
  Trash2,
  CheckCircle,
  Clock,
  FileText,
  Tag,
  Building,
  User,
  Lightbulb,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  useLegalLibrary,
  type LegalArgument,
  type CreateArgumentParams,
  getCategoryColor,
  getSpecialtyIcon,
  getEffectivenessLabel,
  getEffectivenessColor,
} from '@/hooks/use-legal-library';

interface LegalLibraryPanelProps {
  /** Callback quando argumento é selecionado */
  onArgumentSelect?: (argument: LegalArgument) => void;
  /** Callback quando novo argumento é criado */
  onArgumentCreated?: () => void;
}

/**
 * Painel da Biblioteca Viva de Argumentos
 *
 * Permite:
 * - Buscar e filtrar argumentos
 * - Visualizar estatísticas
 * - Criar novos argumentos
 * - Copiar argumentos para uso
 */
export function LegalLibraryPanel({
  onArgumentSelect,
  onArgumentCreated,
}: LegalLibraryPanelProps) {
  const {
    arguments: args,
    collections,
    stats,
    isLoading,
    createArgument,
    suggest,
    setSearchParams,
    refetch,
  } = useLegalLibrary();

  const [searchQuery, setSearchQuery] = React.useState('');
  const [selectedSpecialty, setSelectedSpecialty] = React.useState('');
  const [showCreateForm, setShowCreateForm] = React.useState(false);
  const [suggestions, setSuggestions] = React.useState<LegalArgument[]>([]);

  // Novo argumento
  const [newArgument, setNewArgument] = React.useState<Partial<CreateArgumentParams>>({
    title: '',
    content: '',
    summary: '',
    category: 'merito',
    specialty: 'CIV',
    subcategories: [],
  });

  // Buscar argumentos ao mudar filtros
  React.useEffect(() => {
    setSearchParams({
      query: searchQuery || undefined,
      specialty: selectedSpecialty || undefined,
      sort: '-effectiveness_score',
    });
  }, [searchQuery, selectedSpecialty]);

  // Lidar com busca contextual
  const handleSuggest = async (query: string) => {
    if (!query.trim()) return;
    const results = await suggest({ query, limit: 5 });
    setSuggestions(results);
  };

  // Criar argumento
  const handleCreate = () => {
    if (!newArgument.title || !newArgument.content) return;
    createArgument(newArgument as CreateArgumentParams);
    setShowCreateForm(false);
    setNewArgument({
      title: '',
      content: '',
      summary: '',
      category: 'merito',
      specialty: 'CIV',
      subcategories: [],
    });
    onArgumentCreated?.();
  };

  // Copiar argumento
  const handleCopy = (argument: LegalArgument) => {
    navigator.clipboard.writeText(argument.content);
    onArgumentSelect?.(argument);
  };

  return (
    <div className="space-y-6">
      {/* Header com Stats */}
      <div className="grid gap-4 sm:grid-cols-4">
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <BookOpen className="h-8 w-8 text-primary" />
              <div>
                <p className="text-2xl font-bold">{stats?.total || 0}</p>
                <p className="text-xs text-muted-foreground">Argumentos</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-8 w-8 text-green-600" />
              <div>
                <p className="text-2xl font-bold">{stats?.approved || 0}</p>
                <p className="text-xs text-muted-foreground">Aprovados</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <TrendingUp className="h-8 w-8 text-blue-600" />
              <div>
                <p className="text-2xl font-bold">
                  {stats?.top_effective?.[0]?.effectiveness_score
                    ? (stats.top_effective[0].effectiveness_score * 100).toFixed(0)
                    : 0}%
                </p>
                <p className="text-xs text-muted-foreground">Maior Eficácia</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <Star className="h-8 w-8 text-yellow-600" />
              <div>
                <p className="text-2xl font-bold">
                  {stats?.top_used?.[0]?.usage_count || 0}
                </p>
                <p className="text-xs text-muted-foreground">Mais Usado</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Busca e Filtros */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Scale className="h-5 w-5" />
                Biblioteca de Argumentos
              </CardTitle>
              <CardDescription>
                Encontre argumentos jurídicos por especialidade e categoria
              </CardDescription>
            </div>
            <Button
              onClick={() => setShowCreateForm(!showCreateForm)}
              className="gap-2"
            >
              <Plus className="h-4 w-4" />
              Novo Argumento
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar argumentos..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <select
              value={selectedSpecialty}
              onChange={(e) => setSelectedSpecialty(e.target.value)}
              className="rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">Todas especialidades</option>
              <option value="CIV">Cível</option>
              <option value="PEN">Criminal</option>
              <option value="TRB">Trabalhista</option>
              <option value="FAM">Família</option>
              <option value="PRE">Previdenciário</option>
              <option value="ADM">Administrativo</option>
              <option value="TRI">Tributário</option>
              <option value="EMP">Empresarial</option>
            </select>
          </div>

          {/* Sugestões */}
          {suggestions.length > 0 && (
            <div className="mt-4 p-3 rounded-lg bg-muted/50">
              <div className="flex items-center gap-2 mb-2">
                <Lightbulb className="h-4 w-4 text-yellow-600" />
                <span className="text-sm font-medium">Sugestões</span>
              </div>
              <div className="flex gap-2 flex-wrap">
                {suggestions.map((arg) => (
                  <Badge
                    key={arg.id}
                    variant="outline"
                    className="cursor-pointer hover:bg-primary hover:text-primary-foreground"
                    onClick={() => handleCopy(arg)}
                  >
                    {arg.title}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Formulário de Criação */}
      {showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle>Novo Argumento</CardTitle>
            <CardDescription>
              Crie um novo argumento jurídico para reutilização
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">Título *</label>
                <Input
                  value={newArgument.title}
                  onChange={(e) =>
                    setNewArgument({ ...newArgument, title: e.target.value })
                  }
                  placeholder="Ex: Tese de prescrição"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Especialidade *</label>
                <select
                  value={newArgument.specialty}
                  onChange={(e) =>
                    setNewArgument({
                      ...newArgument,
                      specialty: e.target.value,
                    })
                  }
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="CIV">Cível</option>
                  <option value="PEN">Criminal</option>
                  <option value="TRB">Trabalhista</option>
                  <option value="FAM">Família</option>
                  <option value="PRE">Previdenciário</option>
                  <option value="ADM">Administrativo</option>
                  <option value="TRI">Tributário</option>
                  <option value="EMP">Empresarial</option>
                </select>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">Categoria *</label>
                <select
                  value={newArgument.category}
                  onChange={(e) =>
                    setNewArgument({
                      ...newArgument,
                      category: e.target.value,
                    })
                  }
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="preliminar">Preliminar</option>
                  <option value="merito">Mérito</option>
                  <option value="pedido">Pedido</option>
                  <option value="fundamentacao">Fundamentação</option>
                  <option value="recurso">Recurso</option>
                  <option value="contrarrazoes">Contrarrazões</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Tribunal (opcional)</label>
                <Input
                  value={newArgument.tribunal}
                  onChange={(e) =>
                    setNewArgument({ ...newArgument, tribunal: e.target.value })
                  }
                  placeholder="Ex: STJ, TJSP"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Resumo</label>
              <div className="relative">
                <Textarea
                  value={newArgument.summary}
                  onChange={(e) =>
                    setNewArgument({ ...newArgument, summary: e.target.value })
                  }
                  placeholder="Síntese do argumento em 1-2 frases"
                  className="min-h-[60px] pr-32"
                />
                <div className="absolute top-1 right-1">
                  <AIEnhanceButton
                    value={newArgument.summary}
                    onEnhance={(text) => setNewArgument({ ...newArgument, summary: text })}
                    context="resumo de argumento jurídico"
                  />
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Conteúdo *</label>
              <div className="relative">
                <Textarea
                  value={newArgument.content}
                  onChange={(e) =>
                    setNewArgument({ ...newArgument, content: e.target.value })
                  }
                  placeholder="Conteúdo completo do argumento..."
                  className="min-h-[200px] pr-32"
                />
                <div className="absolute top-1 right-1">
                  <AIEnhanceButton
                    value={newArgument.content}
                    onEnhance={(text) => setNewArgument({ ...newArgument, content: text })}
                    context="conteúdo de argumento jurídico"
                    objective="Melhore a fundamentação jurídica, clareza e precisão terminológica"
                  />
                </div>
              </div>
            </div>

            <div className="flex gap-2">
              <Button onClick={handleCreate} className="gap-2">
                <CheckCircle className="h-4 w-4" />
                Criar Argumento
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowCreateForm(false)}
              >
                <X className="h-4 w-4" />
                Cancelar
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Lista de Argumentos */}
      <ScrollArea className="h-[500px]">
        <div className="space-y-3">
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">
              <Clock className="h-8 w-8 mx-auto mb-2 animate-spin" />
              <p>Carregando argumentos...</p>
            </div>
          ) : args.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <BookOpen className="h-8 w-8 mx-auto mb-2 opacity-30" />
              <p>Nenhum argumento encontrado</p>
            </div>
          ) : (
            args.map((arg) => (
              <ArgumentCard
                key={arg.id}
                argument={arg}
                onCopy={() => handleCopy(arg)}
                onSelect={() => onArgumentSelect?.(arg)}
              />
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

interface ArgumentCardProps {
  argument: LegalArgument;
  onCopy: () => void;
  onSelect: () => void;
}

function ArgumentCard({ argument, onCopy, onSelect }: ArgumentCardProps) {
  const effectiveness = getEffectivenessLabel(argument.effectiveness_score);
  const effectivenessColor = getEffectivenessColor(argument.effectiveness_score);

  return (
    <div className="rounded-lg border p-4 space-y-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <Badge className={getCategoryColor(argument.category)}>
              {argument.category_display || argument.category}
            </Badge>
            <Badge variant="outline">
              {getSpecialtyIcon(argument.specialty)} {argument.specialty_display || argument.specialty}
            </Badge>
            {argument.tribunal && (
              <Badge variant="secondary" className="text-xs">
                <Building className="h-3 w-3 mr-1" />
                {argument.tribunal}
              </Badge>
            )}
          </div>
          <h3 className="font-semibold text-lg">{argument.title}</h3>
        </div>

        {/* Eficácia */}
        <div className="text-right">
          <div className={cn('text-2xl font-bold', effectivenessColor)}>
            {(argument.effectiveness_score * 100).toFixed(0)}%
          </div>
          <p className="text-xs text-muted-foreground">{effectiveness}</p>
        </div>
      </div>

      {/* Resumo */}
      {argument.summary && (
        <p className="text-sm text-muted-foreground">{argument.summary}</p>
      )}

      {/* Meta */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <User className="h-3 w-3" />
            {argument.created_by_name || `User #${argument.created_by}`}
          </span>
          <span className="flex items-center gap-1">
            <FileText className="h-3 w-3" />
            {argument.usage_count} usos
          </span>
          <span className="flex items-center gap-1">
            <Star className="h-3 w-3" />
            {argument.success_count} sucessos
          </span>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={onCopy}
            className="h-7 text-xs gap-1"
          >
            <Copy className="h-3 w-3" />
            Copiar
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onSelect}
            className="h-7 text-xs gap-1"
          >
            <Edit className="h-3 w-3" />
            Ver
          </Button>
        </div>
      </div>
    </div>
  );
}

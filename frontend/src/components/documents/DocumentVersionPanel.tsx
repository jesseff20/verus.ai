'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import {
  History,
  GitCompare,
  RotateCcw,
  FileText,
  User,
  Calendar,
  Tag,
  ChevronRight,
  Download,
  Eye,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Plus,
  Minus,
  Edit,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';
import {
  useDocumentVersion,
  type DocumentVersion,
  type VersionDiff,
  formatVersionType,
  getVersionTypeColor,
  getChangeTypeColor,
} from '@/hooks/use-document-version';

interface DocumentVersionPanelProps {
  /** ID do documento */
  documentId: string;
  /** Callback quando versão é selecionada */
  onVersionSelect?: (version: DocumentVersion) => void;
  /** Callback quando rollback é completado */
  onRollbackComplete?: () => void;
}

/**
 * Painel de Versionamento de Documentos
 *
 * Mostra:
 * - Histórico de versões
 * - Diff entre versões
 * - Opções de rollback
 */
export function DocumentVersionPanel({
  documentId,
  onVersionSelect,
  onRollbackComplete,
}: DocumentVersionPanelProps) {
  const {
    versions,
    isLoading,
    createVersion,
    rollback,
    getDiff,
    diffResult,
    isCreating,
    isRollingBack,
    setSelectedVersion,
    clearDiff,
  } = useDocumentVersion(documentId);

  const [selectedVersions, setSelectedVersions] = React.useState<string[]>([]);
  const [showDiff, setShowDiff] = React.useState(false);
  const [rollbackVersion, setRollbackVersion] = React.useState<string | null>(null);
  const [changeSummary, setChangeSummary] = React.useState('');

  // Selecionar versão para diff
  const handleVersionSelect = (versionId: string) => {
    if (selectedVersions.includes(versionId)) {
      setSelectedVersions(selectedVersions.filter((id) => id !== versionId));
    } else {
      if (selectedVersions.length >= 2) {
        setSelectedVersions([selectedVersions[1], versionId]);
      } else {
        setSelectedVersions([...selectedVersions, versionId]);
      }
    }
  };

  // Calcular diff quando 2 versões selecionadas
  React.useEffect(() => {
    if (selectedVersions.length === 2) {
      getDiff(selectedVersions[0], selectedVersions[1]);
      setShowDiff(true);
    }
  }, [selectedVersions]);

  // Executar rollback
  const handleRollback = () => {
    if (!rollbackVersion) return;
    rollback(rollbackVersion, { create_new_version: true });
    setRollbackVersion(null);
    onRollbackComplete?.();
  };

  // Criar nova versão manualmente
  const handleCreateVersion = () => {
    if (!versions.length) return;
    // Usar seções da versão mais recente
    const latestVersion = versions[0];
    createVersion({
      sections: latestVersion.sections_data || [],
      change_summary: changeSummary || 'Nova versão criada manualmente',
      version_type: 'minor',
    });
    setChangeSummary('');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="h-5 w-5" />
            Histórico de Versões
          </CardTitle>
          <CardDescription>
            Gerencie versões do documento com versionamento semântico
          </CardDescription>
        </CardHeader>
        <CardContent>
          {versions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <History className="h-8 w-8 mx-auto mb-2 opacity-30" />
              <p>Nenhuma versão encontrada</p>
              <p className="text-xs mt-1">
                As versões são criadas automaticamente ao salvar alterações
              </p>
            </div>
          ) : (
            <ScrollArea className="h-[400px]">
              <div className="space-y-2">
                {versions.map((version, idx) => (
                  <VersionItem
                    key={version.version_id}
                    version={version}
                    isSelected={selectedVersions.includes(version.version_id)}
                    onSelect={() => handleVersionSelect(version.version_id)}
                    onRollback={() => setRollbackVersion(version.version_id)}
                    isLatest={idx === 0}
                  />
                ))}
              </div>
            </ScrollArea>
          )}

          {/* Instruções */}
          {versions.length > 0 && (
            <div className="mt-4 p-3 rounded-lg bg-muted text-xs text-muted-foreground">
              <p className="flex items-center gap-1">
                <GitCompare className="h-3 w-3" />
                Selecione 2 versões para comparar
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Diff View */}
      {showDiff && diffResult && (
        <DiffView
          diff={diffResult}
          onClose={() => {
            setShowDiff(false);
            setSelectedVersions([]);
            clearDiff();
          }}
        />
      )}

      {/* Rollback Dialog */}
      {rollbackVersion && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <RotateCcw className="h-5 w-5" />
              Confirmar Rollback
            </CardTitle>
            <CardDescription>
              Deseja realmente fazer rollback para esta versão?
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-2 text-sm">
              <AlertCircle className="h-4 w-4 text-yellow-600" />
              <span>
                Uma nova versão será criada para registrar o rollback
              </span>
            </div>

            <div className="flex gap-2">
              <Button
                onClick={handleRollback}
                disabled={isRollingBack}
                className="gap-2"
              >
                {isRollingBack ? (
                  <>
                    <span className="animate-spin">⏳</span>
                    Executando...
                  </>
                ) : (
                  <>
                    <RotateCcw className="h-4 w-4" />
                    Confirmar Rollback
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                onClick={() => setRollbackVersion(null)}
              >
                Cancelar
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Criar Versão Manual */}
      {versions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Criar Nova Versão
            </CardTitle>
            <CardDescription>
              Crie uma nova versão manualmente a partir da versão atual
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Resumo das alterações
              </label>
              <div className="relative">
                <Textarea
                  placeholder="Descreva as mudanças feitas nesta versão..."
                  value={changeSummary}
                  onChange={(e) => setChangeSummary(e.target.value)}
                  className="min-h-[80px] pr-32"
                />
                <div className="absolute top-1 right-1">
                  <AIEnhanceButton
                    value={changeSummary}
                    onEnhance={setChangeSummary}
                    context="resumo de alterações em documento jurídico"
                  />
                </div>
              </div>
            </div>

            <Button
              onClick={handleCreateVersion}
              disabled={isCreating}
              className="gap-2"
            >
              {isCreating ? (
                <>
                  <span className="animate-spin">⏳</span>
                  Criando versão...
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4" />
                  Criar Versão
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

interface VersionItemProps {
  version: DocumentVersion;
  isSelected: boolean;
  onSelect: () => void;
  onRollback: () => void;
  isLatest: boolean;
}

function VersionItem({
  version,
  isSelected,
  onSelect,
  onRollback,
  isLatest,
}: VersionItemProps) {
  const date = new Date(version.created_at);

  return (
    <div
      className={cn(
        'rounded-lg border p-3 transition-colors cursor-pointer',
        isSelected && 'border-primary bg-primary/5'
      )}
      onClick={onSelect}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Badge className={getVersionTypeColor(version.version_type)}>
            v{version.version_number}
          </Badge>
          {isLatest && (
            <Badge variant="secondary" className="text-xs">
              Mais recente
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onRollback();
            }}
            className="h-7 text-xs"
          >
            <RotateCcw className="h-3 w-3 mr-1" />
            Rollback
          </Button>
        </div>
      </div>

      {/* Meta */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <User className="h-3 w-3" />
            {version.created_by_name || `User #${version.created_by}`}
          </span>
          <span className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            {date.toLocaleDateString('pt-BR')} às{' '}
            {date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      </div>

      {/* Resumo */}
      {version.change_summary && (
        <p className="text-sm mt-2 text-muted-foreground">
          {version.change_summary}
        </p>
      )}

      {/* Tags */}
      {version.tags && version.tags.length > 0 && (
        <div className="flex gap-1 mt-2 flex-wrap">
          {version.tags.map((tag, idx) => (
            <span
              key={idx}
              className="text-[10px] bg-muted px-1.5 py-0.5 rounded flex items-center gap-1"
            >
              <Tag className="h-2 w-2" />
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

interface DiffViewProps {
  diff: VersionDiff;
  onClose: () => void;
}

function DiffView({ diff, onClose }: DiffViewProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <GitCompare className="h-5 w-5" />
              Comparação de Versões
            </CardTitle>
            <CardDescription>
              Diff entre {diff.old_version_id.slice(0, 8)}... e {diff.new_version_id.slice(0, 8)}...
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <XCircle className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Resumo */}
        <div className="grid gap-3 sm:grid-cols-4">
          <div className="rounded-lg border p-3 text-center">
            <p className="text-xs text-muted-foreground">Adicionadas</p>
            <p className="text-xl font-bold text-green-600">
              {diff.summary.added}
            </p>
          </div>
          <div className="rounded-lg border p-3 text-center">
            <p className="text-xs text-muted-foreground">Removidas</p>
            <p className="text-xl font-bold text-red-600">
              {diff.summary.removed}
            </p>
          </div>
          <div className="rounded-lg border p-3 text-center">
            <p className="text-xs text-muted-foreground">Modificadas</p>
            <p className="text-xl font-bold text-yellow-600">
              {diff.summary.modified}
            </p>
          </div>
          <div className="rounded-lg border p-3 text-center">
            <p className="text-xs text-muted-foreground">Inalteradas</p>
            <p className="text-xl font-bold text-muted-foreground">
              {diff.summary.unchanged}
            </p>
          </div>
        </div>

        {/* Similaridade */}
        <div className="rounded-lg border p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Similaridade</span>
            <span className="text-sm text-muted-foreground">
              {(diff.similarity_score * 100).toFixed(1)}%
            </span>
          </div>
          <div className="h-2 rounded-full bg-muted overflow-hidden">
            <div
              className="h-full bg-primary transition-all"
              style={{ width: `${diff.similarity_score * 100}%` }}
            />
          </div>
        </div>

        {/* Mudanças */}
        {diff.changes.length > 0 && (
          <ScrollArea className="h-[300px]">
            <div className="space-y-3">
              {diff.changes.map((change, idx) => (
                <ChangeItem key={idx} change={change} />
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}

interface ChangeItemProps {
  change: {
    section_id: string;
    section_title: string;
    change_type: 'added' | 'removed' | 'modified' | 'unchanged';
    old_content?: string;
    new_content?: string;
    diff?: string[];
  };
}

function ChangeItem({ change }: ChangeItemProps) {
  const colorClass = getChangeTypeColor(change.change_type);

  return (
    <div className="rounded-lg border p-3">
      <div className="flex items-center gap-2 mb-2">
        <Badge className={cn('text-xs', colorClass)}>
          {change.change_type === 'added' && <Plus className="h-3 w-3 mr-1" />}
          {change.change_type === 'removed' && <Minus className="h-3 w-3 mr-1" />}
          {change.change_type === 'modified' && <Edit className="h-3 w-3 mr-1" />}
          {formatVersionType(change.change_type)}
        </Badge>
        <span className="font-medium text-sm">{change.section_title}</span>
      </div>

      {/* Diff em linha */}
      {change.diff && change.diff.length > 0 && (
        <pre className="text-xs bg-muted p-2 rounded overflow-x-auto font-mono">
          {change.diff.slice(0, 10).join('\n')}
          {change.diff.length > 10 && (
            <span className="block text-muted-foreground">
              ... mais {change.diff.length - 10} linhas
            </span>
          )}
        </pre>
      )}
    </div>
  );
}

'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import {
  Building2,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw,
  FileText,
  Upload,
  Send,
  Plus,
  Settings,
  Loader2,
  Database,
  Gavel,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  useTribunalIntegration,
  type TribunalIntegration,
  type ProcessSync,
  type PetitionProtocol,
} from '@/hooks/use-tribunal-integration';

interface TribunalIntegrationPanelProps {
  /** Callback quando tribunal é configurado */
  onTribunalConfigured?: () => void;
  /** Callback quando petição é enviada */
  onPetitionSent?: () => void;
}

/**
 * Painel de Integração com Tribunais
 *
 * Permite:
 * - Configurar integrações com tribunais
 * - Sincronizar processos
 * - Protocolar petições
 */
export function TribunalIntegrationPanel({
  onTribunalConfigured,
  onPetitionSent,
}: TribunalIntegrationPanelProps) {
  const {
    tribunais,
    syncs,
    petitions,
    loadingTribunais,
    isTestingConnection,
    isSyncing,
    testConnection,
    createTribunal,
    syncProcess,
  } = useTribunalIntegration();

  const [activeTab, setActiveTab] = React.useState<'tribunais' | 'sync' | 'petitions'>('tribunais');
  const [showNewTribunal, setShowNewTribunal] = React.useState(false);
  const [newTribunal, setNewTribunal] = React.useState<Partial<TribunalIntegration>>({
    name: '',
    code: '',
    system_type: 'esaj',
    api_endpoint: '',
    requires_certificate: true,
  });
  const [processNumber, setProcessNumber] = React.useState('');

  const handleCreateTribunal = () => {
    createTribunal(newTribunal);
    setShowNewTribunal(false);
    setNewTribunal({
      name: '',
      code: '',
      system_type: 'esaj',
      api_endpoint: '',
      requires_certificate: true,
    });
    onTribunalConfigured?.();
  };

  const handleSyncProcess = (tribunalId: string) => {
    if (!processNumber.trim()) return;
    syncProcess({
      tribunal_id: tribunalId,
      process_number: processNumber,
    });
    setProcessNumber('');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Building2 className="h-5 w-5" />
          <span className="font-semibold text-lg">Integração com Tribunais</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setActiveTab('tribunais')}
          className={cn(
            'rounded-none border-b-2 border-transparent',
            activeTab === 'tribunais' && 'border-primary bg-muted'
          )}
        >
          <Building2 className="h-4 w-4 mr-1" />
          Tribunais
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setActiveTab('sync')}
          className={cn(
            'rounded-none border-b-2 border-transparent',
            activeTab === 'sync' && 'border-primary bg-muted'
          )}
        >
          <RefreshCw className="h-4 w-4 mr-1" />
          Sincronização
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setActiveTab('petitions')}
          className={cn(
            'rounded-none border-b-2 border-transparent',
            activeTab === 'petitions' && 'border-primary bg-muted'
          )}
        >
          <FileText className="h-4 w-4 mr-1" />
          Petições
        </Button>
      </div>

      {/* Conteúdo */}
      {activeTab === 'tribunais' && (
        <TribunaisList
          tribunais={tribunais}
          loading={loadingTribunais}
          isTesting={isTestingConnection}
          onTestConnection={testConnection}
          showNewForm={showNewTribunal}
          setShowNewForm={setShowNewTribunal}
          newTribunal={newTribunal}
          setNewTribunal={setNewTribunal}
          onCreate={handleCreateTribunal}
        />
      )}

      {activeTab === 'sync' && (
        <SyncPanel
          tribunais={tribunais}
          syncs={syncs}
          isSyncing={isSyncing}
          processNumber={processNumber}
          setProcessNumber={setProcessNumber}
          onSync={handleSyncProcess}
        />
      )}

      {activeTab === 'petitions' && (
        <PetitionsList petitions={petitions} onSend={onPetitionSent} />
      )}
    </div>
  );
}

interface TribunaisListProps {
  tribunais: TribunalIntegration[];
  loading: boolean;
  isTesting: boolean;
  onTestConnection: (id: string) => void;
  showNewForm: boolean;
  setShowNewForm: (show: boolean) => void;
  newTribunal: Partial<TribunalIntegration>;
  setNewTribunal: (data: Partial<TribunalIntegration>) => void;
  onCreate: () => void;
}

function TribunaisList({
  tribunais,
  loading,
  isTesting,
  onTestConnection,
  showNewForm,
  setShowNewForm,
  newTribunal,
  setNewTribunal,
  onCreate,
}: TribunaisListProps) {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'connected':
        return <Badge className="bg-green-100 text-green-700"><CheckCircle2 className="h-3 w-3 mr-1" />Conectado</Badge>;
      case 'error':
        return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Erro</Badge>;
      default:
        return <Badge variant="secondary"><AlertCircle className="h-3 w-3 mr-1" />Desconhecido</Badge>;
    }
  };

  const getSystemTypeBadge = (type: string) => {
    const badges: Record<string, string> = {
      esaj: 'e-SAJ',
      pje: 'PJe',
      eproc: 'Eproc',
      prejudi: 'Projudi',
      outro: 'Outro',
    };
    return badges[type] || type;
  };

  return (
    <div className="space-y-4">
      {/* Novo Tribunal */}
      {!showNewForm ? (
        <Button
          variant="outline"
          onClick={() => setShowNewForm(true)}
          className="w-full gap-2"
        >
          <Plus className="h-4 w-4" />
          Novo Tribunal
        </Button>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Novo Tribunal</CardTitle>
            <CardDescription>Configure integração com um novo tribunal</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">Nome</label>
                <Input
                  value={newTribunal.name}
                  onChange={(e) => setNewTribunal({ ...newTribunal, name: e.target.value })}
                  placeholder="Ex: TJSP"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Código</label>
                <Input
                  value={newTribunal.code}
                  onChange={(e) => setNewTribunal({ ...newTribunal, code: e.target.value })}
                  placeholder="Ex: TJSP"
                />
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">Tipo de Sistema</label>
                <select
                  value={newTribunal.system_type}
                  onChange={(e) => setNewTribunal({ ...newTribunal, system_type: e.target.value as any })}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="esaj">e-SAJ</option>
                  <option value="pje">PJe</option>
                  <option value="eproc">Eproc</option>
                  <option value="projudi">Projudi</option>
                  <option value="outro">Outro</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Endpoint da API</label>
                <Input
                  value={newTribunal.api_endpoint}
                  onChange={(e) => setNewTribunal({ ...newTribunal, api_endpoint: e.target.value })}
                  placeholder="https://..."
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Button onClick={onCreate}>
                <CheckCircle2 className="h-4 w-4" />
                Criar
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowNewForm(false)}
              >
                <XCircle className="h-4 w-4" />
                Cancelar
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Lista de Tribunais */}
      <ScrollArea className="h-[400px]">
        <div className="space-y-3">
          {loading ? (
            <div className="text-center py-8">
              <Loader2 className="h-8 w-8 mx-auto animate-spin" />
              <p className="text-muted-foreground">Carregando tribunais...</p>
            </div>
          ) : tribunais.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Building2 className="h-8 w-8 mx-auto mb-2 opacity-30" />
              <p>Nenhum tribunal configurado</p>
            </div>
          ) : (
            tribunais.map((tribunal) => (
              <div
                key={tribunal.id}
                className="rounded-lg border p-4 space-y-3"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Gavel className="h-5 w-5 text-primary" />
                    <div>
                      <h3 className="font-semibold">{tribunal.name}</h3>
                      <p className="text-xs text-muted-foreground">{tribunal.code}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(tribunal.connection_status)}
                    <Badge variant="outline">{getSystemTypeBadge(tribunal.system_type)}</Badge>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="text-xs text-muted-foreground">
                    {tribunal.api_endpoint && (
                      <p className="truncate max-w-[300px]">{tribunal.api_endpoint}</p>
                    )}
                    {tribunal.last_connection_test && (
                      <p>
                        Último teste: {new Date(tribunal.last_connection_test).toLocaleDateString('pt-BR')}
                      </p>
                    )}
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onTestConnection(tribunal.id)}
                    disabled={isTesting}
                  >
                    <RefreshCw className={cn("h-4 w-4 mr-1", isTesting && "animate-spin")} />
                    Testar Conexão
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

interface SyncPanelProps {
  tribunais: TribunalIntegration[];
  syncs: ProcessSync[];
  isSyncing: boolean;
  processNumber: string;
  setProcessNumber: (value: string) => void;
  onSync: (tribunalId: string) => void;
}

function SyncPanel({
  tribunais,
  syncs,
  isSyncing,
  processNumber,
  setProcessNumber,
  onSync,
}: SyncPanelProps) {
  const [selectedTribunal, setSelectedTribunal] = React.useState('');

  return (
    <div className="space-y-4">
      {/* Sincronizar Processo */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Sincronizar Processo
          </CardTitle>
          <CardDescription>
            Consulte andamentos processuais no tribunal
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Tribunal</label>
              <select
                value={selectedTribunal}
                onChange={(e) => setSelectedTribunal(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Selecione...</option>
                {tribunais.filter(t => t.is_active).map((t) => (
                  <option key={t.id} value={t.id}>{t.name}</option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Número do Processo</label>
              <Input
                value={processNumber}
                onChange={(e) => setProcessNumber(e.target.value)}
                placeholder="0000000-00.2024.8.26.0000"
              />
            </div>
          </div>
          <Button
            onClick={() => onSync(selectedTribunal)}
            disabled={!selectedTribunal || !processNumber.trim() || isSyncing}
            className="gap-2"
          >
            {isSyncing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Sincronizando...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4" />
                Sincronizar
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Histórico de Sincronização */}
      <Card>
        <CardHeader>
          <CardTitle>Histórico de Sincronizações</CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[300px]">
            <div className="space-y-2">
              {syncs.length === 0 ? (
                <p className="text-center text-muted-foreground py-4">
                  Nenhuma sincronização realizada
                </p>
              ) : (
                syncs.map((sync) => (
                  <div
                    key={sync.id}
                    className="flex items-center justify-between p-3 rounded-lg border"
                  >
                    <div>
                      <p className="font-medium">{sync.process_number}</p>
                      <p className="text-xs text-muted-foreground">
                        {sync.tribunal_name} • {sync.sync_count} sincronizações
                      </p>
                    </div>
                    <Badge
                      variant={sync.status === 'completed' ? 'default' : sync.status === 'error' ? 'destructive' : 'secondary'}
                    >
                      {sync.status_display || sync.status}
                    </Badge>
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}

interface PetitionsListProps {
  petitions: PetitionProtocol[];
  onSend?: () => void;
}

function PetitionsList({ petitions, onSend }: PetitionsListProps) {
  return (
    <ScrollArea className="h-[500px]">
      <div className="space-y-3">
        {petitions.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="h-8 w-8 mx-auto mb-2 opacity-30" />
            <p>Nenhuma petição protocolada</p>
          </div>
        ) : (
          petitions.map((petition) => (
            <div
              key={petition.id}
              className="rounded-lg border p-4 space-y-2"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold">{petition.petition_title}</h3>
                  <p className="text-xs text-muted-foreground">
                    {petition.petition_type_display} • {petition.tribunal_name}
                  </p>
                  {petition.process_number && (
                    <p className="text-xs text-muted-foreground">
                      Processo: {petition.process_number}
                    </p>
                  )}
                </div>
                <Badge
                  variant={
                    petition.status === 'confirmed' ? 'default' :
                    petition.status === 'error' ? 'destructive' : 'secondary'
                  }
                >
                  {petition.status_display || petition.status}
                </Badge>
              </div>
              {petition.protocol_number && (
                <p className="text-xs">
                  Protocolo: <span className="font-mono">{petition.protocol_number}</span>
                </p>
              )}
              <div className="text-xs text-muted-foreground">
                {new Date(petition.created_at).toLocaleDateString('pt-BR')}
                {' • '}
                Por: {petition.created_by_name}
              </div>
            </div>
          ))
        )}
      </div>
    </ScrollArea>
  );
}

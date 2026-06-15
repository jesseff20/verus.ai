'use client';

import { useState } from 'react';
import {
  useTeams,
  useCreateTeam,
  useUpdateTeam,
  useAddTeamMember,
  useRemoveTeamMember,
  useTeamAssignments,
  useCreateTeamAssignment,
  Team,
} from '@/hooks/use-teams';
import { useUsers } from '@/hooks/use-users';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { AIInput } from '@/components/ui/ai-input';
import { AITextarea } from '@/components/ui/ai-textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';
import {
  UsersRound,
  Plus,
  UserPlus,
  UserMinus,
  ChevronDown,
  ChevronUp,
  LinkIcon,
  Search,
  Sparkles,
  Scale,
  Clock,
  Target,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Info,
} from 'lucide-react';

const SPECIALTIES = [
  { value: 'civel', label: 'Cível' },
  { value: 'criminal', label: 'Criminal' },
  { value: 'trabalhista', label: 'Trabalhista' },
  { value: 'tributario', label: 'Tributário' },
  { value: 'familia', label: 'Família' },
  { value: 'empresarial', label: 'Empresarial' },
  { value: 'previdenciario', label: 'Previdenciário' },
  { value: 'administrativo', label: 'Administrativo' },
  { value: 'outros', label: 'Outros' },
];

const ROLE_OPTIONS = [
  { value: 'responsavel', label: 'Responsável' },
  { value: 'auxiliar', label: 'Auxiliar' },
  { value: 'membro', label: 'Membro' },
  { value: 'revisor', label: 'Revisor' },
];

interface TeamSuggestion {
  team_id: string;
  team_name: string;
  score: number;
  reasons: string[];
  specialty_match: boolean;
  availability: 'high' | 'medium' | 'low';
}

interface BalanceData {
  balance_score: number;
  team_loads: { team_id: string; team_name: string; load_percentage: number; active_cases: number }[];
  overloaded: string[];
  underloaded: string[];
  recommendations: string[];
}

interface AvailabilityData {
  available: boolean;
  availability_score: number;
  estimated_capacity: 'baixa' | 'media' | 'alta' | 'critica';
  factors: string[];
  recommendation: string;
  estimated_response_time: string;
}

export default function EquipePage() {
  const { data: teams, isLoading } = useTeams();
  const createTeam = useCreateTeam();
  const updateTeam = useUpdateTeam();
  const addMember = useAddTeamMember();
  const removeMember = useRemoveTeamMember();
  const createAssignment = useCreateTeamAssignment();
  const { users: usersList, isLoading: usersLoading } = useUsers();
  const users = usersList ?? [];

  const [expandedTeam, setExpandedTeam] = useState<string | null>(null);
  const [showNewTeam, setShowNewTeam] = useState(false);
  const [showAssignDialog, setShowAssignDialog] = useState<string | null>(null);
  const [showAddMember, setShowAddMember] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Copilot state
  const [showSuggestDialog, setShowSuggestDialog] = useState<string | null>(null);
  const [showBalanceDialog, setShowBalanceDialog] = useState(false);
  const [suggestions, setSuggestions] = useState<TeamSuggestion[]>([]);
  const [balanceData, setBalanceData] = useState<BalanceData | null>(null);
  const [availabilityData, setAvailabilityData] = useState<Record<string, AvailabilityData>>({});
  const [loadingSuggest, setLoadingSuggest] = useState(false);
  const [loadingBalance, setLoadingBalance] = useState(false);
  const [loadingAvailability, setLoadingAvailability] = useState<string | null>(null);

  // Form state
  const [newTeam, setNewTeam] = useState({
    name: '',
    description: '',
    leader: '',
    specialty: '',
  });
  const [assignForm, setAssignForm] = useState({ caseId: '', roleInCase: 'membro' });
  const [selectedUserId, setSelectedUserId] = useState('');
  const [selectedCaseForSuggest, setSelectedCaseForSuggest] = useState('');

  const handleCreateTeam = async () => {
    if (!newTeam.name.trim()) {
      toast.error('Nome da equipe é obrigatório.');
      return;
    }
    try {
      await createTeam.mutateAsync({
        name: newTeam.name,
        description: newTeam.description,
        leader: newTeam.leader ? Number(newTeam.leader) : null,
        specialty: newTeam.specialty,
      });
      toast.success('Equipe criada com sucesso!');
      setShowNewTeam(false);
      setNewTeam({ name: '', description: '', leader: '', specialty: '' });
    } catch {
      toast.error('Erro ao criar equipe.');
    }
  };

  const handleToggleActive = async (team: Team) => {
    try {
      await updateTeam.mutateAsync({
        id: team.id,
        data: { is_active: !team.is_active },
      });
      toast.success(team.is_active ? 'Equipe desativada.' : 'Equipe ativada.');
    } catch {
      toast.error('Erro ao atualizar equipe.');
    }
  };

  const handleAddMember = async (teamId: string) => {
    if (!selectedUserId) return;
    try {
      await addMember.mutateAsync({ teamId, userId: Number(selectedUserId) });
      toast.success('Membro adicionado!');
      setSelectedUserId('');
      setShowAddMember(null);
    } catch {
      toast.error('Erro ao adicionar membro.');
    }
  };

  const handleRemoveMember = async (teamId: string, userId: number) => {
    try {
      await removeMember.mutateAsync({ teamId, userId });
      toast.success('Membro removido.');
    } catch {
      toast.error('Erro ao remover membro.');
    }
  };

  const handleAssign = async (teamId: string) => {
    if (!assignForm.caseId) {
      toast.error('Selecione um caso.');
      return;
    }
    try {
      await createAssignment.mutateAsync({
        teamId,
        caseId: assignForm.caseId,
        roleInCase: assignForm.roleInCase,
      });
      toast.success('Equipe atribuída ao caso!');
      setShowAssignDialog(null);
      setAssignForm({ caseId: '', roleInCase: 'membro' });
    } catch {
      toast.error('Erro ao atribuir equipe ao caso.');
    }
  };

  // Copilot: Sugerir equipe para caso
  const handleSuggestTeam = async (teamId: string) => {
    setLoadingSuggest(true);
    try {
      const payload = selectedCaseForSuggest
        ? { case_id: selectedCaseForSuggest }
        : {
            case_data: {
              specialty: 'civel',
              complexity: 'media',
              valor_causa: 50000,
              urgency: false,
            },
          };

      const response = await api.post('/api/v1/processos/copilot/equipe/sugerir/', payload);
      setSuggestions(response.data.suggestions || []);
      setShowSuggestDialog(teamId);
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Erro ao buscar sugestões.');
    } finally {
      setLoadingSuggest(false);
    }
  };

  // Copilot: Balanceamento de carga
  const handleLoadBalance = async () => {
    setLoadingBalance(true);
    try {
      const response = await api.get('/api/v1/processos/copilot/equipe/balancear/');
      setBalanceData(response.data);
      setShowBalanceDialog(true);
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Erro ao analisar balanceamento.');
    } finally {
      setLoadingBalance(false);
    }
  };

  // Copilot: Disponibilidade da equipe
  const handleCheckAvailability = async (teamId: string, urgent = false) => {
    setLoadingAvailability(teamId);
    try {
      const response = await api.get(
        `/api/v1/processos/copilot/equipe/disponibilidade/?team_id=${teamId}&urgent=${urgent}`
      );
      setAvailabilityData((prev) => ({ ...prev, [teamId]: response.data }));
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Erro ao verificar disponibilidade.');
    } finally {
      setLoadingAvailability(null);
    }
  };

  const filteredTeams = (teams ?? []).filter(
    (t) =>
      t.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.specialty.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between" data-tour="eq-header">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Gestão de Equipe</h1>
          <p className="text-muted-foreground">Gerencie equipes, membros e atribuições a casos.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleLoadBalance} disabled={loadingBalance}>
            <Scale className="mr-2 h-4 w-4" />
            Balanceamento
          </Button>
          <Dialog open={showNewTeam} onOpenChange={setShowNewTeam}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Nova Equipe
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Nova Equipe</DialogTitle>
                <DialogDescription>Crie uma nova equipe de trabalho para a procuradoria.</DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="team-name">Nome da Equipe *</Label>
                  <AIInput
                    id="team-name"
                    placeholder="Ex: Equipe Tributária"
                    value={newTeam.name}
                    onChange={(e) => setNewTeam({ ...newTeam, name: e.target.value })}
                    setValue={(v) => setNewTeam((prev) => ({ ...prev, name: v }))}
                    aiContext="nome de equipe jurídica numa procuradoria municipal"
                    aiObjective="Sugira um nome claro e institucional para a equipe, indicando sua área de atuação"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="team-description">Descrição</Label>
                  <AITextarea
                    id="team-description"
                    placeholder="Descreva as responsabilidades e área de atuação da equipe..."
                    value={newTeam.description}
                    onChange={(e) => setNewTeam({ ...newTeam, description: e.target.value })}
                    setValue={(v) => setNewTeam((prev) => ({ ...prev, description: v }))}
                    aiContext="descrição de equipe jurídica numa procuradoria municipal"
                    aiObjective="Elabore uma descrição objetiva das responsabilidades, área de atuação e competências da equipe"
                    rows={3}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Especialidade</Label>
                  <Select
                    value={newTeam.specialty}
                    onValueChange={(v) => setNewTeam({ ...newTeam, specialty: v })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione a especialidade" />
                    </SelectTrigger>
                    <SelectContent>
                      {SPECIALTIES.map((s) => (
                        <SelectItem key={s.value} value={s.value}>
                          {s.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Líder da Equipe</Label>
                  <Select
                    value={newTeam.leader}
                    onValueChange={(v) => setNewTeam({ ...newTeam, leader: v })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione o líder (opcional)" />
                    </SelectTrigger>
                    <SelectContent>
                      {(Array.isArray(users) ? users : []).map((u: any) => (
                        <SelectItem key={u.id} value={String(u.id)}>
                          {u.first_name} {u.last_name} ({u.username})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button
                  onClick={handleCreateTeam}
                  disabled={createTeam.isPending}
                  className="w-full"
                >
                  {createTeam.isPending ? 'Criando...' : 'Criar Equipe'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Card de Balanceamento de Carga (Copilot) */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-primary" />
              <CardTitle className="text-lg">Balanceamento de Carga - IA</CardTitle>
            </div>
            <Badge variant={balanceData && balanceData.balance_score >= 80 ? 'default' : 'secondary'}>
              Score: {balanceData?.balance_score ?? '--'}%
            </Badge>
          </div>
          <CardDescription>
            Análise inteligente da distribuição de casos entre equipes
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Button size="sm" variant="outline" onClick={handleLoadBalance} disabled={loadingBalance}>
              <Sparkles className="mr-2 h-4 w-4" />
              {loadingBalance ? 'Analisando...' : 'Analisar Balanceamento'}
            </Button>
            {balanceData && (
              <div className="flex gap-4 text-sm">
                <span className="flex items-center gap-1 text-green-600">
                  <CheckCircle className="h-4 w-4" />
                  {balanceData.team_loads?.length ?? 0} equipes
                </span>
                {balanceData.overloaded?.length > 0 && (
                  <span className="flex items-center gap-1 text-red-600">
                    <AlertCircle className="h-4 w-4" />
                    {balanceData.overloaded.length} sobrecarregadas
                  </span>
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="flex items-center gap-2">
        <Search className="h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Buscar equipes..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-sm"
        />
      </div>

      {isLoading ? (
        <p className="text-muted-foreground">Carregando equipes...</p>
      ) : filteredTeams.length === 0 ? (
        <p className="text-muted-foreground">Nenhuma equipe encontrada.</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3" data-tour="eq-teams">
          {filteredTeams.map((team) => {
            const isExpanded = expandedTeam === team.id;
            const teamAvailability = availabilityData[team.id];

            return (
              <Card key={team.id} className="flex flex-col">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <UsersRound className="h-5 w-5 text-primary" />
                      <CardTitle className="text-lg">{team.name}</CardTitle>
                    </div>
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={team.is_active}
                        onCheckedChange={() => handleToggleActive(team)}
                      />
                    </div>
                  </div>
                  <CardDescription>{team.description || 'Sem descrição'}</CardDescription>
                </CardHeader>
                <CardContent className="flex-1 space-y-3">
                  <div className="flex flex-wrap gap-2">
                    {team.specialty && (
                      <Badge variant="secondary">{team.specialty}</Badge>
                    )}
                    <Badge variant="outline">{team.members_count} membros</Badge>
                    {!team.is_active && <Badge variant="destructive">Inativa</Badge>}
                  </div>
                  {team.leader_name && (
                    <p className="text-sm text-muted-foreground">
                      Líder: <span className="font-medium text-foreground">{team.leader_name}</span>
                    </p>
                  )}

                  {/* Indicador de Disponibilidade (Copilot) */}
                  {teamAvailability && (
                    <Card className="bg-muted/30">
                      <CardContent className="p-3 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            Disponibilidade
                          </span>
                          <Badge
                            variant={
                              teamAvailability.available
                                ? 'default'
                                : teamAvailability.availability_score > 50
                                ? 'secondary'
                                : 'destructive'
                            }
                            className="text-xs"
                          >
                            {teamAvailability.available ? 'Disponível' : 'Indisponível'}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {teamAvailability.recommendation}
                        </p>
                      </CardContent>
                    </Card>
                  )}

                  <div className="flex flex-wrap gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setExpandedTeam(isExpanded ? null : team.id)}
                    >
                      {isExpanded ? <ChevronUp className="mr-1 h-3 w-3" /> : <ChevronDown className="mr-1 h-3 w-3" />}
                      Membros
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleCheckAvailability(team.id)}
                      disabled={loadingAvailability === team.id}
                    >
                      <Clock className="mr-1 h-3 w-3" />
                      {loadingAvailability === team.id ? '...' : 'Disponibilidade'}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleSuggestTeam(team.id)}
                    >
                      <Sparkles className="mr-1 h-3 w-3" />
                      Sugerir
                    </Button>
                    <Dialog open={showAssignDialog === team.id} onOpenChange={(open) => setShowAssignDialog(open ? team.id : null)}>
                      <DialogTrigger asChild>
                        <Button variant="outline" size="sm">
                          <LinkIcon className="mr-1 h-3 w-3" />
                          Atribuir
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Atribuir Equipe a Caso</DialogTitle>
                          <DialogDescription className="sr-only">Selecione o caso para atribuir a equipe</DialogDescription>
                        </DialogHeader>
                        <AssignToCaseForm
                          onSubmit={() => handleAssign(team.id)}
                          form={assignForm}
                          setForm={setAssignForm}
                          isPending={createAssignment.isPending}
                        />
                      </DialogContent>
                    </Dialog>
                  </div>

                  {isExpanded && (
                    <div className="mt-3 space-y-2 border-t pt-3">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium">Membros da Equipe</p>
                        <Dialog open={showAddMember === team.id} onOpenChange={(open) => setShowAddMember(open ? team.id : null)}>
                          <DialogTrigger asChild>
                            <Button size="sm" variant="ghost">
                              <UserPlus className="mr-1 h-3 w-3" />
                              Adicionar
                            </Button>
                          </DialogTrigger>
                          <DialogContent>
                            <DialogHeader>
                              <DialogTitle>Adicionar Membro</DialogTitle>
                              <DialogDescription className="sr-only">Selecione o usuário para adicionar à equipe</DialogDescription>
                            </DialogHeader>
                            <div className="space-y-4">
                              <Select value={selectedUserId} onValueChange={setSelectedUserId}>
                                <SelectTrigger>
                                  <SelectValue placeholder="Selecione o usuário" />
                                </SelectTrigger>
                                <SelectContent>
                                  {(Array.isArray(users) ? users : []).map((u: any) => (
                                    <SelectItem key={u.id} value={String(u.id)}>
                                      {u.first_name} {u.last_name} ({u.username})
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                              <Button
                                onClick={() => handleAddMember(team.id)}
                                disabled={addMember.isPending}
                                className="w-full"
                              >
                                {addMember.isPending ? 'Adicionando...' : 'Adicionar'}
                              </Button>
                            </div>
                          </DialogContent>
                        </Dialog>
                      </div>
                      {team.members_detail.length === 0 ? (
                        <p className="text-sm text-muted-foreground">Nenhum membro.</p>
                      ) : (
                        <ul className="space-y-1">
                          {team.members_detail.map((member) => (
                            <li key={member.id} className="flex items-center justify-between rounded-md border px-3 py-2 text-sm">
                              <span>{member.full_name} ({member.role})</span>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-7 text-destructive hover:text-destructive"
                                onClick={() => handleRemoveMember(team.id, member.id)}
                              >
                                <UserMinus className="h-3 w-3" />
                              </Button>
                            </li>
                          ))}
                        </ul>
                      )}
                      <TeamAssignmentsList teamId={team.id} />
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Dialog: Sugestões de Equipe (Copilot) */}
      <Dialog open={showSuggestDialog !== null} onOpenChange={(open) => {
        if (!open) {
          setShowSuggestDialog(null);
          setSuggestions([]);
          setSelectedCaseForSuggest('');
        }
      }}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              Sugestões de Equipe - IA
            </DialogTitle>
            <DialogDescription>
              Equipes recomendadas para alocação no caso
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Label>Caso (opcional):</Label>
              <Select value={selectedCaseForSuggest} onValueChange={setSelectedCaseForSuggest}>
                <SelectTrigger className="flex-1">
                  <SelectValue placeholder="Selecionar caso específico" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Análise genérica</SelectItem>
                  {(Array.isArray(teams) ? teams : []).map((c: any) => (
                    <SelectItem key={c.id} value={c.id}>
                      {c.name} ({c.specialty || 'Geral'})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button size="sm" onClick={() => handleSuggestTeam(showSuggestDialog!)} disabled={loadingSuggest}>
                <Sparkles className="h-4 w-4" />
              </Button>
            </div>

            {loadingSuggest && (
              <div className="text-center py-8 text-muted-foreground">
                <Sparkles className="h-8 w-8 mx-auto mb-2 animate-pulse" />
                <p>Analisando equipes disponíveis...</p>
              </div>
            )}

            {!loadingSuggest && suggestions.length > 0 && (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {suggestions.map((suggestion, index) => (
                  <Card key={suggestion.team_id} className={index === 0 ? 'border-primary' : ''}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="space-y-2 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold">{suggestion.team_name}</span>
                            {index === 0 && (
                              <Badge variant="default" className="text-xs">
                                <Target className="h-3 w-3 mr-1" />
                                Melhor Match
                              </Badge>
                            )}
                            {suggestion.specialty_match && (
                              <Badge variant="secondary" className="text-xs">
                                Especialidade Compatível
                              </Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-4 text-sm">
                            <span className="text-muted-foreground">
                              Score: <span className="font-medium text-foreground">{suggestion.score.toFixed(0)}</span>
                            </span>
                            <span className="text-muted-foreground">
                              Disponibilidade:{' '}
                              <span className={
                                suggestion.availability === 'high' ? 'text-green-600' :
                                suggestion.availability === 'medium' ? 'text-yellow-600' : 'text-red-600'
                              }>
                                {suggestion.availability === 'high' ? 'Alta' :
                                 suggestion.availability === 'medium' ? 'Média' : 'Baixa'}
                              </span>
                            </span>
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {suggestion.reasons.map((reason, i) => (
                              <Badge key={i} variant="outline" className="text-xs">
                                <Info className="h-3 w-3 mr-1" />
                                {reason}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-primary">{suggestion.score.toFixed(0)}</div>
                          <div className="text-xs text-muted-foreground">pontos</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {!loadingSuggest && suggestions.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                <p>Clique em "Analisar" para ver sugestões da IA</p>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Dialog: Balanceamento de Carga (Copilot) */}
      <Dialog open={showBalanceDialog} onOpenChange={(open) => {
        if (!open) setShowBalanceDialog(false);
      }}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Scale className="h-5 w-5 text-primary" />
              Balanceamento de Carga - IA
            </DialogTitle>
            <DialogDescription>
              Análise da distribuição de casos entre equipes
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {balanceData && (
              <>
                <div className="flex items-center justify-center gap-4">
                  <div className="text-center">
                    <div className="text-3xl font-bold">{balanceData.balance_score}%</div>
                    <div className="text-sm text-muted-foreground">Score de Balanceamento</div>
                  </div>
                </div>

                {balanceData.recommendations?.length > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <AlertCircle className="h-4 w-4" />
                        Recomendações
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="list-disc list-inside space-y-1 text-sm">
                        {balanceData.recommendations.map((rec, i) => (
                          <li key={i} className="text-muted-foreground">{rec}</li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}

                <div className="space-y-2 max-h-64 overflow-y-auto">
                  <h4 className="font-medium text-sm">Carga por Equipe</h4>
                  {balanceData.team_loads?.map((load) => (
                    <div key={load.team_id} className="flex items-center gap-2">
                      <span className="text-sm flex-1 truncate">{load.team_name}</span>
                      <div className="w-32 h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className={`h-full ${
                            load.load_percentage > 150 ? 'bg-red-500' :
                            load.load_percentage > 100 ? 'bg-yellow-500' :
                            'bg-green-500'
                          }`}
                          style={{ width: `${Math.min(100, load.load_percentage)}%` }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground w-12 text-right">
                        {load.load_percentage.toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>

                {(balanceData.overloaded?.length > 0 || balanceData.underloaded?.length > 0) && (
                  <div className="flex gap-4 text-sm">
                    {balanceData.overloaded?.length > 0 && (
                      <span className="text-red-600 flex items-center gap-1">
                        <AlertCircle className="h-4 w-4" />
                        {balanceData.overloaded.length} sobrecarregadas
                      </span>
                    )}
                    {balanceData.underloaded?.length > 0 && (
                      <span className="text-yellow-600 flex items-center gap-1">
                        <Info className="h-4 w-4" />
                        {balanceData.underloaded.length} com capacidade ociosa
                      </span>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>

      <TeamAssignmentsList teamId="" />
    </div>
  );
}

function AssignToCaseForm({
  onSubmit,
  form,
  setForm,
  isPending,
}: {
  onSubmit: () => void;
  form: { caseId: string; roleInCase: string };
  setForm: (f: { caseId: string; roleInCase: string }) => void;
  isPending: boolean;
}) {
  const { data: casesData } = useQuery({
    queryKey: ['cases-list-for-assign'],
    queryFn: async () => {
      const res = await api.get('/api/v1/processos/', { params: { page_size: 100 } });
      return res.data;
    },
  });
  const cases = casesData?.results ?? casesData ?? [];

  return (
    <div className="space-y-4">
      <div>
        <Label>Caso</Label>
        <Select value={form.caseId} onValueChange={(v) => setForm({ ...form, caseId: v })}>
          <SelectTrigger>
            <SelectValue placeholder="Selecione o caso" />
          </SelectTrigger>
          <SelectContent>
            {(Array.isArray(cases) ? cases : []).map((c: any) => (
              <SelectItem key={c.id} value={c.id}>
                {c.titulo} {c.numero_processo ? `(${c.numero_processo})` : ''}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div>
        <Label>Papel no Caso</Label>
        <Select value={form.roleInCase} onValueChange={(v) => setForm({ ...form, roleInCase: v })}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {ROLE_OPTIONS.map((r) => (
              <SelectItem key={r.value} value={r.value}>
                {r.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <Button onClick={onSubmit} disabled={isPending} className="w-full">
        {isPending ? 'Atribuindo...' : 'Atribuir'}
      </Button>
    </div>
  );
}

function TeamAssignmentsList({ teamId }: { teamId: string }) {
  const { data: assignments } = useTeamAssignments(teamId);

  if (!teamId || !assignments || assignments.length === 0) return null;

  return (
    <div className="mt-2" data-tour="eq-assignments">
      <p className="text-sm font-medium mb-1">Casos Atribuídos</p>
      <ul className="space-y-1">
        {assignments.map((a) => (
          <li key={a.id} className="flex items-center justify-between rounded-md bg-muted/50 px-3 py-2 text-sm">
            <span>{a.case_titulo || 'Caso sem título'}</span>
            <Badge variant="secondary">{a.role_in_case_display}</Badge>
          </li>
        ))}
      </ul>
    </div>
  );
}

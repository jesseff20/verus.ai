'use client';

import { useState } from 'react';
import DOMPurify from 'isomorphic-dompurify';
import { useLGPD } from '@/hooks/use-lgpd';
import type { ConsentTerm, DataProcessingActivity, DataSubjectRequest } from '@/hooks/use-lgpd';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AIInput } from '@/components/ui/ai-input';
import { AITextarea } from '@/components/ui/ai-textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';
import {
  Shield,
  Plus,
  Trash2,
  Edit,
  Sparkles,
  Loader2,
  FileText,
  ClipboardList,
  UserCheck,
  AlertTriangle,
} from 'lucide-react';
import { PermissionGuard } from '@/components/auth/permission-guard';

// ── Consent Terms Tab ──

function ConsentTermsTab() {
  const {
    consentTerms, isLoadingTerms, isErrorTerms, createConsentTerm, updateConsentTerm,
    deleteConsentTerm, generateConsentTerm,
  } = useLGPD();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingTerm, setEditingTerm] = useState<ConsentTerm | null>(null);
  const [form, setForm] = useState({ title: '', version: '1.0', content: '', purpose: 'data_processing' });
  const [generating, setGenerating] = useState(false);
  const [confirmDeleteTermId, setConfirmDeleteTermId] = useState<string | null>(null);

  const resetForm = () => {
    setForm({ title: '', version: '1.0', content: '', purpose: 'data_processing' });
    setEditingTerm(null);
  };

  const handleSave = async () => {
    if (!form.title || !form.content) {
      toast.error('Preencha título e conteúdo.');
      return;
    }
    try {
      if (editingTerm) {
        await updateConsentTerm.mutateAsync({ id: editingTerm.id, data: form });
        toast.success('Termo atualizado.');
      } else {
        await createConsentTerm.mutateAsync(form);
        toast.success('Termo criado.');
      }
      setDialogOpen(false);
      resetForm();
    } catch {
      toast.error('Erro ao salvar termo.');
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const result = await generateConsentTerm.mutateAsync({
        purpose: form.purpose,
        title: form.title || 'Termo de Consentimento',
      });
      setForm((prev) => ({ ...prev, content: result.content }));
      toast.success('Conteúdo gerado com IA.');
    } catch {
      toast.error('Erro ao gerar com IA.');
    } finally {
      setGenerating(false);
    }
  };

  const handleEdit = (term: ConsentTerm) => {
    setEditingTerm(term);
    setForm({ title: term.title, version: term.version, content: term.content, purpose: term.purpose });
    setDialogOpen(true);
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteConsentTerm.mutateAsync(id);
      toast.success('Termo excluído.');
      setConfirmDeleteTermId(null);
    } catch {
      toast.error('Erro ao excluir.');
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Termos de Consentimento
          </CardTitle>
          <CardDescription>Gerencie os termos de consentimento LGPD</CardDescription>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button size="sm"><Plus className="h-4 w-4 mr-1" /> Novo Termo</Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editingTerm ? 'Editar Termo' : 'Novo Termo de Consentimento'}</DialogTitle>
              <DialogDescription>Preencha os dados ou gere o conteúdo com IA</DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Título</Label>
                  <AIInput
                    value={form.title}
                    onChange={(e) => setForm({ ...form, title: e.target.value })}
                    onAIChange={(v) => setForm((prev) => ({ ...prev, title: v }))}
                    placeholder="Título do termo"
                    aiContext="título de termo de consentimento LGPD"
                    aiObjective="Sugira um título claro e formal para o termo de consentimento"
                  />
                </div>
                <div>
                  <Label>Versão</Label>
                  <AIInput
                    value={form.version}
                    onChange={(e) => setForm({ ...form, version: e.target.value })}
                    onAIChange={(v) => setForm((prev) => ({ ...prev, version: v }))}
                    placeholder="1.0"
                    aiContext="versão do termo de consentimento LGPD"
                  />
                </div>
              </div>
              <div>
                <Label>Finalidade</Label>
                <Select value={form.purpose} onValueChange={(v) => setForm({ ...form, purpose: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="data_processing">Tratamento de dados</SelectItem>
                    <SelectItem value="marketing">Marketing</SelectItem>
                    <SelectItem value="sharing">Compartilhamento de dados</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <Label>Conteúdo (HTML)</Label>
                  <Button variant="outline" size="sm" onClick={handleGenerate} disabled={generating}>
                    {generating ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Sparkles className="h-4 w-4 mr-1" />}
                    Gerar com IA
                  </Button>
                </div>
                <AITextarea
                  value={form.content}
                  onChange={(e) => setForm({ ...form, content: e.target.value })}
                  onAIChange={(v) => setForm((prev) => ({ ...prev, content: v }))}
                  placeholder="Conteúdo HTML do termo..."
                  rows={12}
                  aiContext="conteúdo HTML de termo de consentimento LGPD"
                  aiObjective="Redija ou melhore o conteúdo do termo de consentimento em conformidade com a LGPD"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }}>Cancelar</Button>
              <Button onClick={handleSave} disabled={createConsentTerm.isPending || updateConsentTerm.isPending}>
                {(createConsentTerm.isPending || updateConsentTerm.isPending) && <Loader2 className="h-4 w-4 mr-1 animate-spin" />}
                Salvar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </CardHeader>
      <CardContent>
        {isLoadingTerms ? (
          <div className="flex justify-center py-8"><Loader2 className="h-6 w-6 animate-spin" /></div>
        ) : isErrorTerms ? (
          <div className="text-center py-8 space-y-2">
            <AlertTriangle className="h-8 w-8 text-destructive mx-auto" />
            <p className="text-muted-foreground">Erro ao carregar termos de consentimento.</p>
            <p className="text-sm text-muted-foreground">Verifique sua conexao e tente novamente.</p>
          </div>
        ) : consentTerms.length === 0 ? (
          <div className="text-center py-8 space-y-2">
            <FileText className="h-8 w-8 text-muted-foreground mx-auto" />
            <p className="text-muted-foreground">Nenhum termo cadastrado.</p>
            <p className="text-sm text-muted-foreground">Clique em &quot;Novo Termo&quot; para criar o primeiro termo de consentimento.</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Título</TableHead>
                <TableHead>Versão</TableHead>
                <TableHead>Finalidade</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Criado em</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {consentTerms.map((term) => (
                <TableRow key={term.id}>
                  <TableCell className="font-medium">{term.title}</TableCell>
                  <TableCell>{term.version}</TableCell>
                  <TableCell>{term.purpose_display}</TableCell>
                  <TableCell>
                    <Badge variant={term.is_active ? 'default' : 'secondary'}>
                      {term.is_active ? 'Ativo' : 'Inativo'}
                    </Badge>
                  </TableCell>
                  <TableCell>{new Date(term.created_at).toLocaleDateString('pt-BR')}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm" onClick={() => handleEdit(term)} aria-label="Editar termo">
                      <Edit className="h-4 w-4" />
                    </Button>
                    {confirmDeleteTermId === term.id ? (
                      <>
                        <Button variant="destructive" size="sm" onClick={() => handleDelete(term.id)}>Sim</Button>
                        <Button variant="ghost" size="sm" onClick={() => setConfirmDeleteTermId(null)}>Não</Button>
                      </>
                    ) : (
                      <Button variant="ghost" size="sm" onClick={() => setConfirmDeleteTermId(term.id)} aria-label="Excluir termo">
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

// ── Data Processing Activities Tab ──

function ActivitiesTab() {
  const {
    activities, isLoadingActivities, isErrorActivities, createActivity, updateActivity,
    deleteActivity, generatePrivacyPolicy,
  } = useLGPD();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingActivity, setEditingActivity] = useState<DataProcessingActivity | null>(null);
  const [policyDialogOpen, setPolicyDialogOpen] = useState(false);
  const [policyContent, setPolicyContent] = useState('');
  const [generatingPolicy, setGeneratingPolicy] = useState(false);
  const [confirmDeleteActId, setConfirmDeleteActId] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: '', purpose: '', legal_basis: 'consent',
    data_categories: '' as string, retention_period: '',
    shared_with: '' as string, risk_level: 'baixo',
  });

  const resetForm = () => {
    setForm({ name: '', purpose: '', legal_basis: 'consent', data_categories: '', retention_period: '', shared_with: '', risk_level: 'baixo' });
    setEditingActivity(null);
  };

  const handleSave = async () => {
    if (!form.name || !form.purpose) {
      toast.error('Preencha nome e finalidade.');
      return;
    }
    const payload = {
      ...form,
      data_categories: form.data_categories.split(',').map((s) => s.trim()).filter(Boolean),
      shared_with: form.shared_with.split(',').map((s) => s.trim()).filter(Boolean),
    };
    try {
      if (editingActivity) {
        await updateActivity.mutateAsync({ id: editingActivity.id, data: payload });
        toast.success('Atividade atualizada.');
      } else {
        await createActivity.mutateAsync(payload);
        toast.success('Atividade criada.');
      }
      setDialogOpen(false);
      resetForm();
    } catch {
      toast.error('Erro ao salvar atividade.');
    }
  };

  const handleEdit = (act: DataProcessingActivity) => {
    setEditingActivity(act);
    setForm({
      name: act.name,
      purpose: act.purpose,
      legal_basis: act.legal_basis,
      data_categories: act.data_categories.join(', '),
      retention_period: act.retention_period,
      shared_with: act.shared_with.join(', '),
      risk_level: act.risk_level,
    });
    setDialogOpen(true);
  };

  const handleDelete = async (id: string) => {
    setConfirmDeleteActId(null);
    try {
      await deleteActivity.mutateAsync(id);
      toast.success('Atividade excluída.');
    } catch {
      toast.error('Erro ao excluir.');
    }
  };

  const handleGeneratePolicy = async () => {
    setGeneratingPolicy(true);
    try {
      const result = await generatePrivacyPolicy.mutateAsync({});
      setPolicyContent(result.content);
      setPolicyDialogOpen(true);
    } catch {
      toast.error('Erro ao gerar política de privacidade.');
    } finally {
      setGeneratingPolicy(false);
    }
  };

  const riskColors: Record<string, 'default' | 'secondary' | 'destructive'> = {
    baixo: 'secondary',
    medio: 'default',
    alto: 'destructive',
  };

  return (
    <>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <ClipboardList className="h-5 w-5" />
              Atividades de Tratamento
            </CardTitle>
            <CardDescription>Registro de atividades de tratamento de dados pessoais (RIPD)</CardDescription>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleGeneratePolicy} disabled={generatingPolicy}>
              {generatingPolicy ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Sparkles className="h-4 w-4 mr-1" />}
              Gerar Política de Privacidade
            </Button>
            <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
              <DialogTrigger asChild>
                <Button size="sm"><Plus className="h-4 w-4 mr-1" /> Nova Atividade</Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>{editingActivity ? 'Editar Atividade' : 'Nova Atividade de Tratamento'}</DialogTitle>
                  <DialogDescription className="sr-only">Formulário para cadastrar ou editar atividade de tratamento de dados pessoais</DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div>
                    <Label>Nome</Label>
                    <AIInput
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      onAIChange={(v) => setForm((prev) => ({ ...prev, name: v }))}
                      aiContext="nome da atividade de tratamento de dados LGPD"
                      aiObjective="Sugira um nome descritivo para a atividade de tratamento"
                    />
                  </div>
                  <div>
                    <Label>Finalidade</Label>
                    <AITextarea
                      value={form.purpose}
                      onChange={(e) => setForm({ ...form, purpose: e.target.value })}
                      onAIChange={(v) => setForm((prev) => ({ ...prev, purpose: v }))}
                      rows={3}
                      aiContext="finalidade do tratamento de dados pessoais LGPD"
                      aiObjective="Descreva de forma clara e completa a finalidade do tratamento conforme LGPD"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Base Legal</Label>
                      <Select value={form.legal_basis} onValueChange={(v) => setForm({ ...form, legal_basis: v })}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="consent">Consentimento</SelectItem>
                          <SelectItem value="contract">Execução de contrato</SelectItem>
                          <SelectItem value="legal_obligation">Obrigação legal</SelectItem>
                          <SelectItem value="legitimate_interest">Interesse legítimo</SelectItem>
                          <SelectItem value="judicial_process">Exercício regular de direito</SelectItem>
                          <SelectItem value="life_protection">Proteção da vida</SelectItem>
                          <SelectItem value="public_policy">Políticas públicas</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Nível de Risco</Label>
                      <Select value={form.risk_level} onValueChange={(v) => setForm({ ...form, risk_level: v })}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="baixo">Baixo</SelectItem>
                          <SelectItem value="medio">Médio</SelectItem>
                          <SelectItem value="alto">Alto</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div>
                    <Label>Categorias de Dados (separadas por vírgula)</Label>
                    <AIInput
                      value={form.data_categories}
                      onChange={(e) => setForm({ ...form, data_categories: e.target.value })}
                      onAIChange={(v) => setForm((prev) => ({ ...prev, data_categories: v }))}
                      placeholder="nome, CPF, email, telefone"
                      aiContext="categorias de dados pessoais tratados conforme LGPD"
                      aiObjective="Liste as categorias de dados pessoais tratados nesta atividade"
                    />
                  </div>
                  <div>
                    <Label>Período de Retenção</Label>
                    <AIInput
                      value={form.retention_period}
                      onChange={(e) => setForm({ ...form, retention_period: e.target.value })}
                      onAIChange={(v) => setForm((prev) => ({ ...prev, retention_period: v }))}
                      placeholder="5 anos após encerramento do contrato"
                      aiContext="período de retenção de dados pessoais conforme LGPD"
                      aiObjective="Defina o período de retenção adequado para esta categoria de dados"
                    />
                  </div>
                  <div>
                    <Label>Compartilhado com (separados por vírgula)</Label>
                    <AIInput
                      value={form.shared_with}
                      onChange={(e) => setForm({ ...form, shared_with: e.target.value })}
                      onAIChange={(v) => setForm((prev) => ({ ...prev, shared_with: v }))}
                      placeholder="tribunais, órgãos públicos"
                      aiContext="destinatários do compartilhamento de dados pessoais"
                      aiObjective="Liste as entidades com quem os dados são compartilhados"
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }}>Cancelar</Button>
                  <Button onClick={handleSave} disabled={createActivity.isPending || updateActivity.isPending}>
                    {(createActivity.isPending || updateActivity.isPending) && <Loader2 className="h-4 w-4 mr-1 animate-spin" />}
                    Salvar
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          {isLoadingActivities ? (
            <div className="flex justify-center py-8"><Loader2 className="h-6 w-6 animate-spin" /></div>
          ) : isErrorActivities ? (
            <div className="text-center py-8 space-y-2">
              <AlertTriangle className="h-8 w-8 text-destructive mx-auto" />
              <p className="text-muted-foreground">Erro ao carregar atividades de tratamento.</p>
              <p className="text-sm text-muted-foreground">Verifique sua conexao e tente novamente.</p>
            </div>
          ) : activities.length === 0 ? (
            <div className="text-center py-8 space-y-2">
              <ClipboardList className="h-8 w-8 text-muted-foreground mx-auto" />
              <p className="text-muted-foreground">Nenhuma atividade cadastrada.</p>
              <p className="text-sm text-muted-foreground">Clique em &quot;Nova Atividade&quot; para registrar atividades de tratamento de dados.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nome</TableHead>
                  <TableHead>Base Legal</TableHead>
                  <TableHead>Risco</TableHead>
                  <TableHead>Retenção</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {activities.map((act) => (
                  <TableRow key={act.id}>
                    <TableCell className="font-medium">{act.name}</TableCell>
                    <TableCell>{act.legal_basis_display}</TableCell>
                    <TableCell>
                      <Badge variant={riskColors[act.risk_level] || 'secondary'}>
                        {act.risk_level === 'alto' && <AlertTriangle className="h-3 w-3 mr-1" />}
                        {act.risk_level_display}
                      </Badge>
                    </TableCell>
                    <TableCell>{act.retention_period}</TableCell>
                    <TableCell>
                      <Badge variant={act.is_active ? 'default' : 'secondary'}>
                        {act.is_active ? 'Ativa' : 'Inativa'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm" onClick={() => handleEdit(act)} aria-label="Editar atividade">
                        <Edit className="h-4 w-4" />
                      </Button>
                      {confirmDeleteActId === act.id ? (
                        <>
                          <Button variant="destructive" size="sm" onClick={() => handleDelete(act.id)}>Sim</Button>
                          <Button variant="ghost" size="sm" onClick={() => setConfirmDeleteActId(null)}>Não</Button>
                        </>
                      ) : (
                        <Button variant="ghost" size="sm" onClick={() => setConfirmDeleteActId(act.id)} aria-label="Excluir atividade">
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Policy Preview Dialog */}
      <Dialog open={policyDialogOpen} onOpenChange={setPolicyDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Política de Privacidade Gerada</DialogTitle>
            <DialogDescription>Revise e copie o conteúdo gerado pela IA</DialogDescription>
          </DialogHeader>
          <div className="prose dark:prose-invert max-w-none py-4" dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(policyContent) }} />
          <DialogFooter>
            <Button variant="outline" onClick={() => { navigator.clipboard.writeText(policyContent); toast.success('Copiado!'); }}>
              Copiar HTML
            </Button>
            <Button onClick={() => setPolicyDialogOpen(false)}>Fechar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

// ── Data Subject Requests Tab ──

function DSRTab() {
  const { dsrRequests, isLoadingDSR, isErrorDSR, createDSR, respondDSR } = useLGPD();
  const [respondDialogOpen, setRespondDialogOpen] = useState(false);
  const [selectedDSR, setSelectedDSR] = useState<DataSubjectRequest | null>(null);
  const [responseText, setResponseText] = useState('');

  const handleRespond = async () => {
    if (!selectedDSR || !responseText) {
      toast.error('Preencha a resposta.');
      return;
    }
    try {
      await respondDSR.mutateAsync({ id: selectedDSR.id, response: responseText });
      toast.success('Solicitação respondida.');
      setRespondDialogOpen(false);
      setResponseText('');
      setSelectedDSR(null);
    } catch {
      toast.error('Erro ao responder.');
    }
  };

  const statusColors: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
    pending: 'secondary',
    in_progress: 'default',
    completed: 'outline',
    rejected: 'destructive',
  };

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UserCheck className="h-5 w-5" />
            Solicitações do Titular
          </CardTitle>
          <CardDescription>Acompanhe e responda solicitações de titulares de dados (DSR)</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoadingDSR ? (
            <div className="flex justify-center py-8"><Loader2 className="h-6 w-6 animate-spin" /></div>
          ) : isErrorDSR ? (
            <div className="text-center py-8 space-y-2">
              <AlertTriangle className="h-8 w-8 text-destructive mx-auto" />
              <p className="text-muted-foreground">Erro ao carregar solicitacoes do titular.</p>
              <p className="text-sm text-muted-foreground">Verifique sua conexao e tente novamente.</p>
            </div>
          ) : dsrRequests.length === 0 ? (
            <div className="text-center py-8 space-y-2">
              <UserCheck className="h-8 w-8 text-muted-foreground mx-auto" />
              <p className="text-muted-foreground">Nenhuma solicitação registrada.</p>
              <p className="text-sm text-muted-foreground">Solicitacoes de acesso, retificacao, eliminacao e portabilidade de dados aparecerao aqui.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Cliente</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Solicitado em</TableHead>
                  <TableHead>Respondido em</TableHead>
                  <TableHead className="text-right">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {dsrRequests.map((dsr) => (
                  <TableRow key={dsr.id}>
                    <TableCell className="font-medium">{dsr.client_name || dsr.client}</TableCell>
                    <TableCell>{dsr.request_type_display}</TableCell>
                    <TableCell>
                      <Badge variant={statusColors[dsr.status] || 'secondary'}>
                        {dsr.status_display}
                      </Badge>
                    </TableCell>
                    <TableCell>{new Date(dsr.requested_at).toLocaleDateString('pt-BR')}</TableCell>
                    <TableCell>{dsr.responded_at ? new Date(dsr.responded_at).toLocaleDateString('pt-BR') : '-'}</TableCell>
                    <TableCell className="text-right">
                      {dsr.status === 'pending' || dsr.status === 'in_progress' ? (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => { setSelectedDSR(dsr); setRespondDialogOpen(true); }}
                        >
                          Responder
                        </Button>
                      ) : (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => { setSelectedDSR(dsr); setRespondDialogOpen(true); }}
                        >
                          Ver
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Respond Dialog */}
      <Dialog open={respondDialogOpen} onOpenChange={setRespondDialogOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>
              {selectedDSR?.status === 'completed' || selectedDSR?.status === 'rejected'
                ? 'Detalhes da Solicitação'
                : 'Responder Solicitação'}
            </DialogTitle>
            <DialogDescription className="sr-only">Detalhes e resposta da solicitação do titular de dados</DialogDescription>
          </DialogHeader>
          <div className="grid gap-3 py-4">
            <div>
              <Label className="text-muted-foreground">Tipo</Label>
              <p className="font-medium">{selectedDSR?.request_type_display}</p>
            </div>
            <div>
              <Label className="text-muted-foreground">Descrição</Label>
              <p>{selectedDSR?.description}</p>
            </div>
            {(selectedDSR?.status === 'completed' || selectedDSR?.status === 'rejected') ? (
              <div>
                <Label className="text-muted-foreground">Resposta</Label>
                <p>{selectedDSR?.response}</p>
              </div>
            ) : (
              <div>
                <Label>Resposta</Label>
                <AITextarea
                  value={responseText}
                  onChange={(e) => setResponseText(e.target.value)}
                  setValue={setResponseText}
                  rows={5}
                  placeholder="Digite a resposta ao titular..."
                  aiContext="resposta a solicitação de titular de dados LGPD"
                  aiObjective="Redija uma resposta formal e completa ao titular dos dados conforme exigido pela LGPD"
                />
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRespondDialogOpen(false)}>Fechar</Button>
            {selectedDSR?.status !== 'completed' && selectedDSR?.status !== 'rejected' && (
              <Button onClick={handleRespond} disabled={respondDSR.isPending}>
                {respondDSR.isPending && <Loader2 className="h-4 w-4 mr-1 animate-spin" />}
                Enviar Resposta
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

// ── Main Page ──

export default function LGPDSettingsPage() {
  return (
    <PermissionGuard permissions={['settings.edit']}>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Shield className="h-6 w-6" />
            Conformidade LGPD
          </h1>
          <p className="text-muted-foreground">
            Gerencie termos de consentimento, atividades de tratamento e solicitações de titulares
          </p>
        </div>

        <Tabs defaultValue="terms" className="space-y-4">
          <TabsList>
            <TabsTrigger value="terms">
              <FileText className="h-4 w-4 mr-1" />
              Termos de Consentimento
            </TabsTrigger>
            <TabsTrigger value="activities">
              <ClipboardList className="h-4 w-4 mr-1" />
              Atividades de Tratamento
            </TabsTrigger>
            <TabsTrigger value="dsr">
              <UserCheck className="h-4 w-4 mr-1" />
              Solicitações do Titular
            </TabsTrigger>
          </TabsList>

          <TabsContent value="terms">
            <ConsentTermsTab />
          </TabsContent>

          <TabsContent value="activities">
            <ActivitiesTab />
          </TabsContent>

          <TabsContent value="dsr">
            <DSRTab />
          </TabsContent>
        </Tabs>
      </div>
    </PermissionGuard>
  );
}

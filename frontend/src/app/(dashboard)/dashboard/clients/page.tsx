'use client';

import { useState, useEffect, useCallback, Fragment, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import {
  Users,
  Plus,
  Search,
  Loader2,
  AlertTriangle,
  Building2,
  User,
  Phone,
  Mail,
  MapPin,
  Pencil,
  Trash2,
  X,
  Scale,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Briefcase,
  ShieldCheck,
  Eye,
  EyeOff,
  MessageSquare,
  Upload,
  FileUp,
  Brain,
  CheckCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import api from '@/lib/api';

// ─── Types ───────────────────────────────────────────────────────────────────

interface Client {
  id: string;
  name: string;
  client_type: string;
  client_type_display: string;
  cpf_cnpj: string;
  rg: string;
  email: string;
  phone: string;
  phone_secondary: string;
  address: string;
  city: string;
  state: string;
  zipcode: string;
  company_name: string;
  contact_person: string;
  responsible_lawyer: string | null;
  responsible_lawyer_name: string | null;
  notes: string;
  is_active: boolean;
  portal_active: boolean;
  total_cases: number;
  created_at: string;
  updated_at: string;
}

interface PaginatedResponse {
  count: number;
  results: Client[];
}

interface ClientFormData {
  name: string;
  client_type: string;
  cpf_cnpj: string;
  rg: string;
  email: string;
  phone: string;
  phone_secondary: string;
  address: string;
  city: string;
  state: string;
  zipcode: string;
  company_name: string;
  contact_person: string;
  notes: string;
  is_active: boolean;
}

interface ClientCase {
  id: string;
  titulo: string;
  numero_processo: string;
  especialidade: string;
  especialidade_display: string;
  status: string;
  status_display: string;
  cliente_nome: string;
  parte_contraria: string;
  tribunal: string;
  created_at: string;
}

interface ClientWithCases extends Client {
  cases?: ClientCase[];
}

const SPECIALTY_COLORS: Record<string, string> = {
  trabalhista: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
  criminal: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300',
  consumidor: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300',
  civel: 'bg-slate-100 text-slate-800 dark:bg-slate-800/40 dark:text-slate-300',
  tributario: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
  administrativo: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/40 dark:text-cyan-300',
  previdenciario: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300',
  familia: 'bg-pink-100 text-pink-800 dark:bg-pink-900/40 dark:text-pink-300',
  empresarial: 'bg-violet-100 text-violet-800 dark:bg-violet-900/40 dark:text-violet-300',
  ambiental: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
  imobiliario: 'bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300',
  outros: 'bg-gray-100 text-gray-800 dark:bg-gray-800/40 dark:text-gray-300',
};

const STATUS_COLORS: Record<string, string> = {
  ativo: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300',
  aguardando: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300',
  suspenso: 'bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300',
  encerrado: 'bg-gray-100 text-gray-600 dark:bg-gray-800/40 dark:text-gray-400',
  arquivado: 'bg-gray-100 text-gray-500 dark:bg-gray-800/40 dark:text-gray-500',
  ganho: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
  perdido: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300',
  acordo: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300',
};

const EMPTY_FORM: ClientFormData = {
  name: '',
  client_type: 'pessoa_fisica',
  cpf_cnpj: '',
  rg: '',
  email: '',
  phone: '',
  phone_secondary: '',
  address: '',
  city: '',
  state: '',
  zipcode: '',
  company_name: '',
  contact_person: '',
  notes: '',
  is_active: true,
};

const STATES = [
  'AC','AL','AM','AP','BA','CE','DF','ES','GO','MA','MG','MS','MT',
  'PA','PB','PE','PI','PR','RJ','RN','RO','RR','RS','SC','SE','SP','TO',
];

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '\u2014';
  return new Date(dateStr).toLocaleDateString('pt-BR');
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function ClientsPage() {
  const queryClient = useQueryClient();

  // Filters
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingClient, setEditingClient] = useState<Client | null>(null);
  const [formData, setFormData] = useState<ClientFormData>(EMPTY_FORM);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  // Portal activation dialog
  const [portalClient, setPortalClient] = useState<Client | null>(null);
  const [portalPassword, setPortalPassword] = useState('');
  const [showPortalPassword, setShowPortalPassword] = useState(false);

  // Detail expansion
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Copilot states
  const [extractedData, setExtractedData] = useState<Partial<ClientFormData> | null>(null);
  const [conflictCheck, setConflictCheck] = useState<{
    has_conflict: boolean;
    risk_level: string;
    recommendation: string;
  } | null>(null);
  const [isCheckingConflict, setIsCheckingConflict] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput), 400);
    return () => clearTimeout(timer);
  }, [searchInput]);

  // ─── Queries ───────────────────────────────────────────────────────────────

  const { data, isLoading, error } = useQuery({
    queryKey: ['clients', search, typeFilter],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (typeFilter && typeFilter !== 'all') params.client_type = typeFilter;
      const response = await api.get<PaginatedResponse>('/api/v1/clientes/', { params });
      return response.data;
    },
  });

  // ─── Mutations ─────────────────────────────────────────────────────────────

  const createMutation = useMutation({
    mutationFn: (data: ClientFormData) => api.post('/api/v1/clientes/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
      toast.success('Cliente criado com sucesso');
      closeDialog();
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || err?.response?.data?.detail || 'Erro ao processar solicitação');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: ClientFormData }) =>
      api.patch(`/api/v1/clientes/${id}/`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
      toast.success('Cliente atualizado com sucesso');
      closeDialog();
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || err?.response?.data?.detail || 'Erro ao processar solicitação');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/clientes/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
      toast.success('Cliente removido com sucesso');
      setDeleteConfirmId(null);
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || err?.response?.data?.detail || 'Erro ao processar solicitação');
    },
  });

  const portalMutation = useMutation({
    mutationFn: ({ clientId, password, active }: { clientId: string; password: string; active: boolean }) =>
      api.post(`/api/v1/auth/client-portal/activate/${clientId}/`, { password, active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
      toast.success('Portal do cliente configurado com sucesso');
      setPortalClient(null);
      setPortalPassword('');
    },
    onError: () => {
      toast.error('Erro ao configurar portal do cliente');
    },
  });

  // Copilot: Extract data from document
  const extractClientData = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      const res = await api.post('/api/v1/processos/copilot/extrair-dados-cliente/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return res.data;
    },
    onSuccess: (data) => {
      if (data.data && Object.keys(data.data).length > 0) {
        const extracted = data.data;
        setExtractedData(extracted);
        // Auto-fill form fields
        setFormData(prev => ({
          ...prev,
          name: extracted.name || prev.name,
          cpf_cnpj: extracted.cpf_cnpj || prev.cpf_cnpj,
          rg: extracted.rg || prev.rg,
          email: extracted.email || prev.email,
          phone: extracted.phone || prev.phone,
          address: extracted.address || prev.address,
          city: extracted.city || prev.city,
          state: extracted.state || prev.state,
          zipcode: extracted.zipcode || prev.zipcode,
          company_name: extracted.company_name || prev.company_name,
          contact_person: extracted.contact_person || prev.contact_person,
        }));
        toast.success(`Dados extraídos com ${data.confidence}% de confiança`);
      } else {
        toast.error('Não foi possível extrair dados do documento');
      }
    },
    onError: () => {
      toast.error('Erro ao processar documento');
    },
  });

  // Copilot: Check conflict of interest
  const checkConflict = useMutation({
    mutationFn: async () => {
      const res = await api.post('/api/v1/processos/copilot/conflito-cliente/', {
        client_name: formData.name,
        cpf_cnpj: formData.cpf_cnpj,
        company_name: formData.company_name,
      });
      return res.data;
    },
    onSuccess: (data) => {
      setConflictCheck(data);
      if (data.has_conflict) {
        toast.warning(`Conflito identificado: ${data.risk_level === 'high' ? 'Alto risco' : 'Risco médio'}`);
      } else {
        toast.success('Nenhum conflito identificado');
      }
    },
    onError: () => {
      toast.error('Erro ao verificar conflito');
    },
  });

  const handleFileUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    extractClientData.mutate(file);
    // Reset input to allow re-uploading same file
    if (fileInputRef.current) fileInputRef.current.value = '';
  }, [extractClientData]);

  const handleCheckConflict = useCallback(() => {
    if (!formData.name) {
      toast.error('Preencha o nome do cliente para verificar conflito');
      return;
    }
    setIsCheckingConflict(true);
    setConflictCheck(null);
    setTimeout(() => {
      checkConflict.mutate();
      setIsCheckingConflict(false);
    }, 100);
  }, [formData, checkConflict]);

  // ─── Handlers ──────────────────────────────────────────────────────────────

  const openCreateDialog = () => {
    setEditingClient(null);
    setFormData(EMPTY_FORM);
    setDialogOpen(true);
  };

  const openEditDialog = (client: Client) => {
    setEditingClient(client);
    setFormData({
      name: client.name,
      client_type: client.client_type,
      cpf_cnpj: client.cpf_cnpj,
      rg: client.rg,
      email: client.email,
      phone: client.phone,
      phone_secondary: client.phone_secondary,
      address: client.address,
      city: client.city,
      state: client.state,
      zipcode: client.zipcode,
      company_name: client.company_name,
      contact_person: client.contact_person,
      notes: client.notes,
      is_active: client.is_active,
    });
    setDialogOpen(true);
  };

  const closeDialog = () => {
    setDialogOpen(false);
    setEditingClient(null);
    setFormData(EMPTY_FORM);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast.error('O nome do cliente é obrigatório');
      return;
    }
    if (editingClient) {
      updateMutation.mutate({ id: editingClient.id, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const updateField = useCallback(
    <K extends keyof ClientFormData>(field: K, value: ClientFormData[K]) => {
      setFormData((prev) => ({ ...prev, [field]: value }));
    },
    [],
  );

  const clients = data?.results || [];
  const isSaving = createMutation.isPending || updateMutation.isPending;

  // ─── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6 pb-20 sm:pb-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight flex items-center gap-2">
            <Users className="h-7 w-7 sm:h-8 sm:w-8" />
            Clientes
          </h1>
          <p className="text-muted-foreground text-sm sm:text-base">
            Gerencie os clientes do escritório
          </p>
        </div>
        <Button onClick={openCreateDialog} className="hidden sm:inline-flex self-auto">
          <Plus className="h-4 w-4 mr-2" />
          Novo Cliente
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-3 sm:gap-4 grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total de Clientes</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.count ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pessoa Física</CardTitle>
            <User className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {clients.filter((c) => c.client_type === 'pessoa_fisica').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pessoa Jurídica</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {clients.filter((c) => c.client_type === 'pessoa_juridica').length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters + Table */}
      <Card>
        <CardHeader>
          <CardTitle>Lista de Clientes</CardTitle>
          <CardDescription>{data?.count ?? 0} clientes encontrados</CardDescription>
        </CardHeader>
        <CardContent>
          {/* Search - sticky on mobile */}
          <div className="sticky top-0 z-10 bg-card pb-3 -mt-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar por nome, CPF/CNPJ, e-mail..."
                className="pl-9 text-[16px] sm:text-sm"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
              />
            </div>
          </div>

          {/* Filter chips on mobile, dropdown on desktop */}
          <div className="sm:hidden flex gap-2 mb-4 overflow-x-auto pb-2 -mx-1 px-1 scrollbar-hide">
            {[
              { value: 'all', label: 'Todos' },
              { value: 'pessoa_fisica', label: 'Pessoa Física' },
              { value: 'pessoa_juridica', label: 'Pessoa Jurídica' },
            ].map((item) => (
              <button
                key={item.value}
                type="button"
                onClick={() => setTypeFilter(item.value)}
                className={`inline-flex items-center whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-medium transition-colors shrink-0 min-h-[36px] touch-manipulation ${
                  typeFilter === item.value
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          <div className="hidden sm:flex gap-3 mb-4">
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Tipo" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos os tipos</SelectItem>
                <SelectItem value="pessoa_fisica">Pessoa Física</SelectItem>
                <SelectItem value="pessoa_juridica">Pessoa Jurídica</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : error ? (
            <div className="flex items-center justify-center py-12 text-destructive gap-2">
              <AlertTriangle className="h-5 w-5" />
              <span>Erro ao carregar clientes</span>
            </div>
          ) : clients.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground gap-3">
              <Users className="h-12 w-12 opacity-30" />
              <p className="text-sm">Nenhum cliente encontrado</p>
              <Button onClick={openCreateDialog} size="sm" variant="outline">
                <Plus className="h-4 w-4 mr-2" />
                Cadastrar primeiro cliente
              </Button>
            </div>
          ) : (
            <>
              {/* Desktop table - hidden on mobile */}
              <Table className="hidden md:table">
                <TableHeader>
                  <TableRow>
                    <TableHead>Nome</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead>CPF/CNPJ</TableHead>
                    <TableHead>Contato</TableHead>
                    <TableHead>Cidade/UF</TableHead>
                    <TableHead>Casos</TableHead>
                    <TableHead>Cadastro</TableHead>
                    <TableHead className="w-[100px]">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {clients.map((client) => (
                    <Fragment key={client.id}>
                      <TableRow
                        className="cursor-pointer hover:bg-accent/50"
                        onClick={() =>
                          setExpandedId(expandedId === client.id ? null : client.id)
                        }
                      >
                        <TableCell>
                          <div className="flex items-center gap-2">
                            {client.client_type === 'pessoa_juridica' ? (
                              <Building2 className="h-4 w-4 text-muted-foreground shrink-0" />
                            ) : (
                              <User className="h-4 w-4 text-muted-foreground shrink-0" />
                            )}
                            <div>
                              <p className="font-medium text-sm flex items-center gap-1.5">
                                {client.name}
                                {client.portal_active && (
                                  <span className="inline-block h-2 w-2 rounded-full bg-green-500 shrink-0" title="Portal ativo" />
                                )}
                              </p>
                              {client.company_name && (
                                <p className="text-xs text-muted-foreground">{client.company_name}</p>
                              )}
                            </div>
                            {expandedId === client.id ? (
                              <ChevronUp className="h-3 w-3 text-muted-foreground ml-1" />
                            ) : (
                              <ChevronDown className="h-3 w-3 text-muted-foreground ml-1" />
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="text-xs">
                            {client.client_type_display}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm font-mono">{client.cpf_cnpj || '\u2014'}</span>
                        </TableCell>
                        <TableCell>
                          <div className="text-xs space-y-0.5">
                            {client.email && (
                              <p className="flex items-center gap-1">
                                <Mail className="h-3 w-3" /> {client.email}
                              </p>
                            )}
                            {client.phone && (
                              <p className="flex items-center gap-1">
                                <Phone className="h-3 w-3" /> {client.phone}
                              </p>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          {client.city || client.state ? (
                            <span className="text-sm">
                              {[client.city, client.state].filter(Boolean).join('/')}
                            </span>
                          ) : (
                            '\u2014'
                          )}
                        </TableCell>
                        <TableCell>
                          {client.total_cases > 0 ? (
                            <Badge className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 text-xs">
                              <Scale className="h-3 w-3 mr-1" />
                              {client.total_cases}
                            </Badge>
                          ) : (
                            <span className="text-xs text-muted-foreground">\u2014</span>
                          )}
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {formatDate(client.created_at)}
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
                            {client.portal_active && (
                              <Link href={`/dashboard/mensagens-clientes?client=${client.id}`}>
                                <Button
                                  size="icon"
                                  variant="ghost"
                                  className="h-7 w-7"
                                  title="Ver Mensagens"
                                >
                                  <MessageSquare className="h-3.5 w-3.5 text-blue-600" />
                                </Button>
                              </Link>
                            )}
                            <Button
                              size="icon"
                              variant="ghost"
                              className="h-7 w-7"
                              title={client.portal_active ? 'Portal ativo' : 'Ativar Portal'}
                              onClick={() => { setPortalClient(client); setPortalPassword(''); }}
                            >
                              <ShieldCheck className={`h-3.5 w-3.5 ${client.portal_active ? 'text-green-600' : 'text-muted-foreground'}`} />
                            </Button>
                            <Button
                              size="icon"
                              variant="ghost"
                              className="h-7 w-7"
                              onClick={() => openEditDialog(client)}
                            >
                              <Pencil className="h-3.5 w-3.5" />
                            </Button>
                            <Button
                              size="icon"
                              variant="ghost"
                              className="h-7 w-7 text-destructive hover:text-destructive"
                              onClick={() => setDeleteConfirmId(client.id)}
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>

                      {/* Expanded detail row */}
                      {expandedId === client.id && (
                        <TableRow key={`${client.id}-detail`}>
                          <TableCell colSpan={8} className="bg-muted/30 p-0">
                            <ClientExpandedDetail clientId={client.id} client={client} />
                          </TableCell>
                        </TableRow>
                      )}
                    </Fragment>
                  ))}
                </TableBody>
              </Table>

              {/* Mobile card layout - shown only on mobile */}
              <div className="md:hidden space-y-3">
                {clients.map((client) => (
                  <Fragment key={`mobile-${client.id}`}>
                    <div
                      className="border rounded-lg p-4 cursor-pointer hover:bg-accent/50 active:bg-accent/70 transition-colors touch-manipulation"
                      onClick={() =>
                        setExpandedId(expandedId === client.id ? null : client.id)
                      }
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-2 min-w-0">
                          {client.client_type === 'pessoa_juridica' ? (
                            <Building2 className="h-5 w-5 text-muted-foreground shrink-0" />
                          ) : (
                            <User className="h-5 w-5 text-muted-foreground shrink-0" />
                          )}
                          <div className="min-w-0">
                            <p className="font-medium text-sm truncate flex items-center gap-1.5">
                              {client.name}
                              {client.portal_active && (
                                <span className="inline-block h-2 w-2 rounded-full bg-green-500 shrink-0" title="Portal ativo" />
                              )}
                            </p>
                            {client.company_name && (
                              <p className="text-xs text-muted-foreground truncate">{client.company_name}</p>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2 shrink-0" onClick={(e) => e.stopPropagation()}>
                          {client.portal_active && (
                            <Link href={`/dashboard/mensagens-clientes?client=${client.id}`}>
                              <Button size="icon" variant="ghost" className="h-10 w-10 touch-manipulation" title="Ver Mensagens">
                                <MessageSquare className="h-4 w-4 text-blue-600" />
                              </Button>
                            </Link>
                          )}
                          <Button size="icon" variant="ghost" className="h-10 w-10 touch-manipulation" title={client.portal_active ? 'Portal ativo' : 'Ativar Portal'} onClick={() => { setPortalClient(client); setPortalPassword(''); }}>
                            <ShieldCheck className={`h-4 w-4 ${client.portal_active ? 'text-green-600' : 'text-muted-foreground'}`} />
                          </Button>
                          <Button size="icon" variant="ghost" className="h-10 w-10 touch-manipulation" onClick={() => openEditDialog(client)}>
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button size="icon" variant="ghost" className="h-10 w-10 text-destructive hover:text-destructive touch-manipulation" onClick={() => setDeleteConfirmId(client.id)}>
                            <Trash2 className="h-4 w-4" />
                          </Button>
                          {expandedId === client.id ? (
                            <ChevronUp className="h-5 w-5 text-muted-foreground" />
                          ) : (
                            <ChevronDown className="h-5 w-5 text-muted-foreground" />
                          )}
                        </div>
                      </div>

                      <div className="mt-2 flex flex-wrap gap-2">
                        <Badge variant="outline" className="text-xs">{client.client_type_display}</Badge>
                        {client.total_cases > 0 && (
                          <Badge className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 text-xs">
                            <Scale className="h-3 w-3 mr-1" />{client.total_cases}
                          </Badge>
                        )}
                      </div>

                      <div className="mt-2 text-xs space-y-1.5 text-muted-foreground">
                        {client.cpf_cnpj && (
                          <p className="font-mono">{client.cpf_cnpj}</p>
                        )}
                        {client.email && (
                          <p className="flex items-center gap-1.5"><Mail className="h-3.5 w-3.5" /> {client.email}</p>
                        )}
                        {client.phone && (
                          <p className="flex items-center gap-1.5"><Phone className="h-3.5 w-3.5" /> {client.phone}</p>
                        )}
                        {(client.city || client.state) && (
                          <p className="flex items-center gap-1.5">
                            <MapPin className="h-3.5 w-3.5" /> {[client.city, client.state].filter(Boolean).join('/')}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Mobile expanded detail - smooth accordion */}
                    {expandedId === client.id && (
                      <div className="border rounded-lg bg-muted/30 animate-in slide-in-from-top-2 duration-200">
                        <ClientExpandedDetail clientId={client.id} client={client} />
                      </div>
                    )}
                  </Fragment>
                ))}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* FAB - Floating Action Button for mobile */}
      <button
        type="button"
        onClick={openCreateDialog}
        className="sm:hidden fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg hover:bg-primary/90 active:scale-95 transition-transform touch-manipulation"
      >
        <Plus className="h-6 w-6" />
      </button>

      {/* Create / Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={(open) => !open && closeDialog()}>
        <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingClient ? 'Editar Cliente' : 'Novo Cliente'}
            </DialogTitle>
            <DialogDescription>
              {editingClient
                ? 'Atualize os dados do cliente.'
                : 'Preencha os dados para cadastrar um novo cliente.'}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Preenchimento automático com IA */}
            {!editingClient && (
              <Card className="border-primary/20 bg-primary/5">
                <CardContent className="flex flex-col sm:flex-row items-start sm:items-center gap-4 py-4">
                  <FileUp className="h-8 w-8 text-primary flex-shrink-0 hidden sm:block" />
                  <div className="flex-1">
                    <h3 className="font-semibold flex items-center gap-2">
                      <FileUp className="h-5 w-5 text-primary sm:hidden" />
                      Preenchimento Automático
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      Anexe CPF/CNPJ, RG ou Contrato Social para preencher automaticamente.
                    </p>
                  </div>
                  <input
                    type="file"
                    ref={fileInputRef}
                    className="hidden"
                    accept=".pdf,.docx,.doc,.png,.jpg,.jpeg"
                    onChange={handleFileUpload}
                  />
                  <Button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={extractClientData.isPending}
                    className="w-full sm:w-auto"
                  >
                    {extractClientData.isPending ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Upload className="h-4 w-4 mr-2" />
                    )}
                    {extractClientData.isPending ? 'Extraindo...' : 'Anexar Documento'}
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* Dados extraídos */}
            {extractedData && !editingClient && (
              <div className="p-4 rounded-lg border bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800">
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-green-500 shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-green-700 dark:text-green-300">
                      Dados extraídos do documento
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Revise os campos preenchidos antes de salvar.
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setExtractedData(null)}
                    className="h-6 w-6 p-0"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            )}

            {/* Tipo e Nome */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label>Tipo *</Label>
                <Select
                  value={formData.client_type}
                  onValueChange={(v) => updateField('client_type', v)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pessoa_fisica">Pessoa Física</SelectItem>
                    <SelectItem value="pessoa_juridica">Pessoa Jurídica</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="md:col-span-2">
                <div className="flex items-center justify-between">
                  <Label>Nome *</Label>
                  {!editingClient && formData.name && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={handleCheckConflict}
                      disabled={isCheckingConflict || checkConflict.isPending}
                      className="h-7 text-xs gap-1"
                    >
                      {isCheckingConflict || checkConflict.isPending ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : (
                        <ShieldCheck className="h-3 w-3 text-green-500" />
                      )}
                      Verificar Conflito
                    </Button>
                  )}
                </div>
                <Input
                  value={formData.name}
                  onChange={(e) => updateField('name', e.target.value)}
                  placeholder="Nome completo ou razão social"
                  className="text-[16px] sm:text-sm"
                />
              </div>
            </div>

            {/* Resultado da verificação de conflito */}
            {conflictCheck && (
              <div className={`p-4 rounded-lg border ${
                conflictCheck.has_conflict
                  ? 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800'
                  : 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800'
              }`}>
                <div className="flex items-start gap-3">
                  {conflictCheck.has_conflict ? (
                    <AlertTriangle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
                  ) : (
                    <CheckCircle className="h-5 w-5 text-green-500 shrink-0 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <p className={`text-sm font-semibold ${
                      conflictCheck.has_conflict ? 'text-red-700 dark:text-red-300' : 'text-green-700 dark:text-green-300'
                    }`}>
                      {conflictCheck.has_conflict
                        ? `Conflito Identificado - Risco ${conflictCheck.risk_level === 'high' ? 'Alto' : 'Médio'}`
                        : 'Nenhum Conflito Identificado'}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {conflictCheck.recommendation}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Documentos */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label>{formData.client_type === 'pessoa_juridica' ? 'CNPJ' : 'CPF'}</Label>
                <Input
                  value={formData.cpf_cnpj}
                  onChange={(e) => updateField('cpf_cnpj', e.target.value)}
                  placeholder={formData.client_type === 'pessoa_juridica' ? '00.000.000/0001-00' : '000.000.000-00'}
                />
              </div>
              {formData.client_type === 'pessoa_fisica' && (
                <div>
                  <Label>RG</Label>
                  <Input
                    value={formData.rg}
                    onChange={(e) => updateField('rg', e.target.value)}
                  />
                </div>
              )}
              <div>
                <Label>E-mail</Label>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => updateField('email', e.target.value)}
                />
              </div>
            </div>

            {/* Telefones */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label>Telefone</Label>
                <Input
                  value={formData.phone}
                  onChange={(e) => updateField('phone', e.target.value)}
                  placeholder="(00) 00000-0000"
                />
              </div>
              <div>
                <Label>Telefone Secundário</Label>
                <Input
                  value={formData.phone_secondary}
                  onChange={(e) => updateField('phone_secondary', e.target.value)}
                />
              </div>
            </div>

            {/* PJ fields */}
            {formData.client_type === 'pessoa_juridica' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Razão Social</Label>
                  <Input
                    value={formData.company_name}
                    onChange={(e) => updateField('company_name', e.target.value)}
                  />
                </div>
                <div>
                  <Label>Pessoa de Contato</Label>
                  <Input
                    value={formData.contact_person}
                    onChange={(e) => updateField('contact_person', e.target.value)}
                  />
                </div>
              </div>
            )}

            {/* Address */}
            <div>
              <Label>Endereço</Label>
              <Input
                value={formData.address}
                onChange={(e) => updateField('address', e.target.value)}
                placeholder="Rua, número, complemento"
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label>Cidade</Label>
                <Input
                  value={formData.city}
                  onChange={(e) => updateField('city', e.target.value)}
                />
              </div>
              <div>
                <Label>UF</Label>
                <Select
                  value={formData.state || 'none'}
                  onValueChange={(v) => updateField('state', v === 'none' ? '' : v)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Selecione</SelectItem>
                    {STATES.map((uf) => (
                      <SelectItem key={uf} value={uf}>{uf}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>CEP</Label>
                <Input
                  value={formData.zipcode}
                  onChange={(e) => updateField('zipcode', e.target.value)}
                  placeholder="00000-000"
                />
              </div>
            </div>

            {/* Notes */}
            <div>
              <Label>Observações</Label>
              <Textarea
                value={formData.notes}
                onChange={(e) => updateField('notes', e.target.value)}
                rows={3}
                placeholder="Anotações sobre o cliente..."
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={closeDialog}>
                Cancelar
              </Button>
              <Button type="submit" disabled={isSaving}>
                {isSaving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                {editingClient ? 'Salvar' : 'Cadastrar'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={!!deleteConfirmId}
        onOpenChange={(open) => !open && setDeleteConfirmId(null)}
      >
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>Confirmar Exclusão</DialogTitle>
            <DialogDescription>
              Tem certeza que deseja excluir este cliente? Esta ação não pode ser desfeita.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfirmId(null)}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              disabled={deleteMutation.isPending}
              onClick={() => deleteConfirmId && deleteMutation.mutate(deleteConfirmId)}
            >
              {deleteMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Excluir
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Portal Activation Dialog */}
      <Dialog
        open={!!portalClient}
        onOpenChange={(open) => { if (!open) { setPortalClient(null); setPortalPassword(''); } }}
      >
        <DialogContent className="sm:max-w-[450px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5" />
              Portal do Cliente
            </DialogTitle>
            <DialogDescription>
              {portalClient?.portal_active
                ? `O portal esta ativo para ${portalClient?.name}. Voce pode atualizar a senha ou desativar.`
                : `Ative o acesso ao portal para ${portalClient?.name}. O cliente podera acompanhar seus processos.`}
            </DialogDescription>
          </DialogHeader>

          {portalClient?.email ? (
            <div className="space-y-4">
              <div>
                <Label className="text-xs text-muted-foreground">E-mail de acesso</Label>
                <p className="text-sm font-medium">{portalClient.email}</p>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="portal-password">
                  {portalClient.portal_active ? 'Nova senha (deixe em branco para manter)' : 'Senha do portal *'}
                </Label>
                <div className="relative">
                  <Input
                    id="portal-password"
                    type={showPortalPassword ? 'text' : 'password'}
                    value={portalPassword}
                    onChange={(e) => setPortalPassword(e.target.value)}
                    placeholder="Senha para o cliente"
                    className="pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPortalPassword(!showPortalPassword)}
                    className="absolute right-1 top-1/2 -translate-y-1/2 flex items-center justify-center h-9 w-9 text-muted-foreground hover:text-foreground transition-colors"
                    tabIndex={-1}
                  >
                    {showPortalPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <DialogFooter className="gap-2">
                {portalClient.portal_active && (
                  <Button
                    variant="outline"
                    className="text-destructive hover:text-destructive"
                    disabled={portalMutation.isPending}
                    onClick={() => portalMutation.mutate({
                      clientId: portalClient.id,
                      password: '',
                      active: false,
                    })}
                  >
                    Desativar Portal
                  </Button>
                )}
                <Button
                  disabled={portalMutation.isPending || (!portalClient.portal_active && !portalPassword)}
                  onClick={() => portalMutation.mutate({
                    clientId: portalClient.id,
                    password: portalPassword,
                    active: true,
                  })}
                >
                  {portalMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  {portalClient.portal_active ? 'Atualizar' : 'Ativar Portal'}
                </Button>
              </DialogFooter>
            </div>
          ) : (
            <div className="text-center py-4">
              <p className="text-sm text-muted-foreground">
                Este cliente nao possui e-mail cadastrado. Cadastre um e-mail antes de ativar o portal.
              </p>
              <DialogFooter className="mt-4">
                <Button variant="outline" onClick={() => setPortalClient(null)}>
                  Fechar
                </Button>
                <Button onClick={() => { setPortalClient(null); openEditDialog(portalClient!); }}>
                  Editar Cliente
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ─── Client Expanded Detail (with linked cases) ──────────────────────────────

function ClientExpandedDetail({ clientId, client }: { clientId: string; client: Client }) {
  const { data: clientDetail, isLoading } = useQuery<ClientWithCases>({
    queryKey: ['client-detail', clientId],
    queryFn: async () => {
      const response = await api.get<ClientWithCases>(`/api/v1/clientes/${clientId}/`);
      return response.data;
    },
  });

  const cases = clientDetail?.cases || [];

  return (
    <div className="p-4 space-y-4">
      {/* Client info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <div>
          <h4 className="font-semibold mb-2 flex items-center gap-1">
            <User className="h-4 w-4" /> Dados Pessoais
          </h4>
          <dl className="space-y-1">
            <div><dt className="text-muted-foreground inline">RG:</dt> {client.rg || '\u2014'}</div>
            <div><dt className="text-muted-foreground inline">Tel. secundario:</dt> {client.phone_secondary || '\u2014'}</div>
            {client.contact_person && (
              <div><dt className="text-muted-foreground inline">Contato PJ:</dt> {client.contact_person}</div>
            )}
          </dl>
        </div>
        <div>
          <h4 className="font-semibold mb-2 flex items-center gap-1">
            <MapPin className="h-4 w-4" /> Endereço
          </h4>
          <p>{client.address || '\u2014'}</p>
          <p>
            {[client.city, client.state].filter(Boolean).join(' - ')}{' '}
            {client.zipcode && `CEP ${client.zipcode}`}
          </p>
        </div>
        <div>
          <h4 className="font-semibold mb-2">Observações</h4>
          <p className="text-muted-foreground whitespace-pre-wrap">
            {client.notes || 'Nenhuma observação.'}
          </p>
          {client.responsible_lawyer_name && (
            <p className="mt-2">
              <span className="text-muted-foreground">Advogado resp.:</span>{' '}
              {client.responsible_lawyer_name}
            </p>
          )}
        </div>
      </div>

      {/* Linked Cases */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-semibold text-sm flex items-center gap-1.5">
            <Briefcase className="h-4 w-4" />
            Processos Vinculados
            {cases.length > 0 && (
              <Badge className="ml-1 bg-primary/10 text-primary text-xs">{cases.length}</Badge>
            )}
          </h4>
          <Button size="sm" variant="outline" asChild className="min-h-[44px] sm:min-h-0 touch-manipulation">
            <Link href={`/dashboard/processos/novo?client_id=${clientId}&client_name=${encodeURIComponent(client.name)}`}>
              <Plus className="h-4 w-4 sm:h-3.5 sm:w-3.5 sm:mr-1.5" />
              <span className="hidden sm:inline">Novo Caso</span>
            </Link>
          </Button>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-6">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : cases.length === 0 ? (
          <div className="text-center py-6 text-muted-foreground border border-dashed rounded-lg">
            <Scale className="h-8 w-8 mx-auto mb-2 opacity-30" />
            <p className="text-sm">Nenhum processo vinculado a este cliente</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-2">
            {cases.map((caso) => (
              <Link
                key={caso.id}
                href={`/dashboard/processos/${caso.id}`}
                className="group block p-3 rounded-lg border bg-background hover:border-primary/40 hover:shadow-sm active:bg-accent/50 transition-all duration-150 touch-manipulation"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap mb-1">
                      <Badge className={`text-[10px] px-1.5 py-0 ${SPECIALTY_COLORS[caso.especialidade] || SPECIALTY_COLORS.outros}`}>
                        {caso.especialidade_display}
                      </Badge>
                      <Badge className={`text-[10px] px-1.5 py-0 ${STATUS_COLORS[caso.status] || STATUS_COLORS.encerrado}`}>
                        {caso.status_display}
                      </Badge>
                    </div>
                    <p className="font-medium text-sm truncate group-hover:text-primary transition-colors">
                      {caso.titulo}
                    </p>
                    {caso.parte_contraria && (
                      <p className="text-xs text-muted-foreground truncate">
                        vs {caso.parte_contraria}
                      </p>
                    )}
                    {caso.numero_processo && (
                      <p className="text-[11px] text-muted-foreground font-mono mt-0.5">
                        {caso.numero_processo}
                      </p>
                    )}
                    {caso.tribunal && (
                      <p className="text-[11px] text-muted-foreground mt-0.5">
                        {caso.tribunal}
                      </p>
                    )}
                  </div>
                  <ExternalLink className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0 mt-1" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

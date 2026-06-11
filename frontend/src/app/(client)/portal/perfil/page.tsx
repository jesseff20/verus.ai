'use client';

import { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { useClientPortalAuth } from '@/hooks/use-client-portal';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import {
  User,
  Loader2,
  Save,
  Lock,
  AlertTriangle,
  CheckCircle,
} from 'lucide-react';

// ─── API ────────────────────────────────────────────────────────────────────

const portalApi = axios.create({
  baseURL: '',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

portalApi.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('client_portal_access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// ─── Component ──────────────────────────────────────────────────────────────

export default function PerfilPage() {
  const { client, loading } = useClientPortalAuth();

  // Profile form
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [zipcode, setZipcode] = useState('');
  const [profileMsg, setProfileMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Password form
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordMsg, setPasswordMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    if (client) {
      setEmail(client.email || '');
      setPhone(client.phone || '');
      setAddress(client.address || '');
      setCity(client.city || '');
      setState(client.state || '');
      setZipcode(client.zipcode || '');
    }
  }, [client]);

  const updateProfile = useMutation({
    mutationFn: async () => {
      await portalApi.patch('/api/v1/auth/client-portal/me/', {
        email,
        phone,
        address,
        city,
        state,
        zipcode,
      });
    },
    onSuccess: () => {
      setProfileMsg({ type: 'success', text: 'Dados atualizados com sucesso!' });
    },
    onError: () => {
      setProfileMsg({ type: 'error', text: 'Erro ao atualizar dados. Tente novamente.' });
    },
  });

  const changePassword = useMutation({
    mutationFn: async () => {
      await portalApi.post('/api/v1/auth/client-portal/change-password/', {
        current_password: currentPassword,
        new_password: newPassword,
      });
    },
    onSuccess: () => {
      setPasswordMsg({ type: 'success', text: 'Senha alterada com sucesso!' });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || 'Erro ao alterar senha. Verifique os dados.';
      setPasswordMsg({ type: 'error', text: msg });
    },
  });

  const handleProfileSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setProfileMsg(null);
    updateProfile.mutate();
  };

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMsg(null);
    if (newPassword.length < 8) {
      setPasswordMsg({ type: 'error', text: 'A nova senha deve ter no mínimo 8 caracteres.' });
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordMsg({ type: 'error', text: 'As senhas não coincidem.' });
      return;
    }
    changePassword.mutate();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!client) {
    return (
      <div className="flex items-center justify-center py-16 text-destructive gap-2">
        <AlertTriangle className="h-5 w-5" />
        <span>Erro ao carregar perfil</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight flex items-center gap-2">
          <User className="h-7 w-7 sm:h-8 sm:w-8" />
          Meus Dados
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Gerencie suas informações pessoais
        </p>
      </div>

      {/* Profile Form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Informações Pessoais</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleProfileSubmit} className="space-y-4">
            {/* Read-only fields */}
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground">Nome</Label>
                <Input value={client.name} disabled className="bg-muted/50" />
              </div>
              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground">CPF/CNPJ</Label>
                <Input value={client.cpf_cnpj} disabled className="bg-muted/50 font-mono" />
              </div>
              <div className="space-y-2 sm:col-span-2">
                <Label className="text-xs text-muted-foreground">Tipo</Label>
                <Input value={client.client_type_display} disabled className="bg-muted/50" />
              </div>
            </div>

            <Separator />

            {/* Editable fields */}
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="email">E-mail</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Telefone</Label>
                <Input
                  id="phone"
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                />
              </div>
              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="address">Endereço</Label>
                <Input
                  id="address"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="city">Cidade</Label>
                <Input
                  id="city"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="state">Estado</Label>
                <Input
                  id="state"
                  value={state}
                  onChange={(e) => setState(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="zipcode">CEP</Label>
                <Input
                  id="zipcode"
                  value={zipcode}
                  onChange={(e) => setZipcode(e.target.value)}
                />
              </div>
            </div>

            {profileMsg && (
              <div className={`flex items-center gap-2 text-sm ${profileMsg.type === 'success' ? 'text-green-600' : 'text-destructive'}`}>
                {profileMsg.type === 'success' ? <CheckCircle className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
                {profileMsg.text}
              </div>
            )}

            <Button type="submit" disabled={updateProfile.isPending}>
              {updateProfile.isPending ? (
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              ) : (
                <Save className="h-4 w-4 mr-1" />
              )}
              Salvar Alterações
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Password Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Lock className="h-4 w-4" />
            Alterar Senha
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-1 max-w-md">
              <div className="space-y-2">
                <Label htmlFor="currentPassword">Senha atual</Label>
                <Input
                  id="currentPassword"
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="newPassword">Nova senha</Label>
                <Input
                  id="newPassword"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={8}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirmar nova senha</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  minLength={8}
                />
              </div>
            </div>

            <p className="text-xs text-muted-foreground">
              Mínimo 8 caracteres
            </p>

            {passwordMsg && (
              <div className={`flex items-center gap-2 text-sm ${passwordMsg.type === 'success' ? 'text-green-600' : 'text-destructive'}`}>
                {passwordMsg.type === 'success' ? <CheckCircle className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
                {passwordMsg.text}
              </div>
            )}

            <Button type="submit" variant="outline" disabled={changePassword.isPending}>
              {changePassword.isPending ? (
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              ) : (
                <Lock className="h-4 w-4 mr-1" />
              )}
              Alterar Senha
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

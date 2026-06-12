'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/hooks/use-auth';
import { useTheme } from 'next-themes';
import { useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { AIInput } from '@/components/ui/ai-input';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { User, Lock, Bell, Palette, Loader2, Scale, Upload, X, MessageCircle, Mail, Monitor } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import api from '@/lib/api';

const LAWYER_SPECIALTIES_OPTIONS = [
  'Administrativo',
  'Tributário Municipal',
  'Dívida Ativa',
  'Licitações e Contratos',
  'Urbanismo e Uso do Solo',
  'Ambiental',
  'Previdenciário',
  'Constitucional',
  'Cível',
  'Responsabilidade Civil do Estado',
  'Controle Interno e Compliance',
  'Improbidade Administrativa',
];

const BRAZILIAN_STATES = [
  'AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG',
  'PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO',
];

export default function ProfileSettingsPage() {
  const { user } = useAuth();
  const { theme, setTheme } = useTheme();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [savingProfile, setSavingProfile] = useState(false);

  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [changingPassword, setChangingPassword] = useState(false);

  // Lawyer profile state
  const [oabNumber, setOabNumber] = useState('');
  const [oabState, setOabState] = useState('');
  const [lawyerSpecialties, setLawyerSpecialties] = useState<string[]>([]);
  const [signatureName, setSignatureName] = useState('');
  const [signaturePreview, setSignaturePreview] = useState<string | null>(null);
  const [signatureFile, setSignatureFile] = useState<File | null>(null);
  const [savingLawyer, setSavingLawyer] = useState(false);
  const signatureInputRef = useRef<HTMLInputElement>(null);

  // Notification channel state
  const [whatsappNumber, setWhatsappNumber] = useState('');
  const [whatsappVerified, setWhatsappVerified] = useState(false);
  const [whatsappEnabled, setWhatsappEnabled] = useState(false);
  const [whatsappAutoSend, setWhatsappAutoSend] = useState(false);
  const [notifEmail, setNotifEmail] = useState('');
  const [emailEnabled, setEmailEnabled] = useState(false);
  const [emailAutoSend, setEmailAutoSend] = useState(false);
  const [appEnabled, setAppEnabled] = useState(true);
  const [savingChannels, setSavingChannels] = useState(false);
  const [verifyingWhatsapp, setVerifyingWhatsapp] = useState(false);

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || '');
      setEmail(user.email || '');
      setPhone(user.phone || '');
      setOabNumber(user.oab_number || '');
      setOabState(user.oab_state || '');
      setLawyerSpecialties(user.lawyer_specialties || []);
      setSignatureName(user.signature_name || '');
      setSignaturePreview(user.signature_image || null);
    }
  }, [user]);

  // Load notification channels
  useEffect(() => {
    async function loadChannels() {
      try {
        const res = await api.get('/api/v1/auth/notification-channels/');
        const channels = Array.isArray(res.data) ? res.data : res.data.results || [];
        for (const ch of channels) {
          if (ch.channel === 'whatsapp') {
            setWhatsappNumber(ch.whatsapp_number || '');
            setWhatsappVerified(ch.whatsapp_verified || false);
            setWhatsappEnabled(ch.is_active);
            setWhatsappAutoSend(ch.auto_send || false);
          } else if (ch.channel === 'email') {
            setNotifEmail(ch.email_address || '');
            setEmailEnabled(ch.is_active);
            setEmailAutoSend(ch.auto_send || false);
          } else if (ch.channel === 'app') {
            setAppEnabled(ch.is_active);
          }
        }
      } catch {
        // Channels not yet configured, keep defaults
      }
    }
    loadChannels();
  }, []);

  const handleSaveChannels = async () => {
    setSavingChannels(true);
    try {
      const channels = [
        { channel: 'whatsapp', is_active: whatsappEnabled, auto_send: whatsappAutoSend, whatsapp_number: whatsappNumber, email_address: '' },
        { channel: 'email', is_active: emailEnabled, auto_send: emailAutoSend, whatsapp_number: '', email_address: notifEmail || user?.email || '' },
        { channel: 'app', is_active: appEnabled, auto_send: true, whatsapp_number: '', email_address: '' },
      ];

      for (const ch of channels) {
        try {
          // Try to find existing channel
          const existing = await api.get('/api/v1/auth/notification-channels/', {
            params: { channel: ch.channel },
          });
          const items = Array.isArray(existing.data) ? existing.data : existing.data.results || [];
          const found = items.find((item: any) => item.channel === ch.channel);
          if (found) {
            await api.patch(`/api/v1/auth/notification-channels/${found.id}/`, ch);
          } else {
            await api.post('/api/v1/auth/notification-channels/', ch);
          }
        } catch {
          // If get fails, create new
          await api.post('/api/v1/auth/notification-channels/', ch);
        }
      }

      toast({ title: 'Canais de notificação atualizados!' });
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'Erro ao salvar canais de notificação.';
      toast({ title: detail, variant: 'destructive' });
    } finally {
      setSavingChannels(false);
    }
  };

  const handleVerifyWhatsApp = async () => {
    if (!whatsappNumber) {
      toast({ title: 'Informe o numero do WhatsApp', variant: 'destructive' });
      return;
    }
    setVerifyingWhatsapp(true);
    try {
      // First ensure channel exists
      const existing = await api.get('/api/v1/auth/notification-channels/');
      const items = Array.isArray(existing.data) ? existing.data : existing.data.results || [];
      const found = items.find((item: any) => item.channel === 'whatsapp');
      if (!found) {
        await api.post('/api/v1/auth/notification-channels/', {
          channel: 'whatsapp',
          is_active: true,
          whatsapp_number: whatsappNumber,
          email_address: '',
        });
      } else {
        await api.patch(`/api/v1/auth/notification-channels/${found.id}/`, {
          whatsapp_number: whatsappNumber,
        });
      }

      const res = await api.post('/api/v1/auth/notification-channels/verify-whatsapp/');
      if (res.data.whatsapp_link) {
        window.open(res.data.whatsapp_link, '_blank');
        setWhatsappVerified(true);
        toast({ title: 'WhatsApp verificado com sucesso!' });
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'Erro ao verificar WhatsApp.';
      toast({ title: detail, variant: 'destructive' });
    } finally {
      setVerifyingWhatsapp(false);
    }
  };

  const handleSaveProfile = async () => {
    if (!user) return;
    const parts = fullName.trim().split(/\s+/);
    const first_name = parts[0] || '';
    const last_name = parts.slice(1).join(' ') || '';
    setSavingProfile(true);
    try {
      await api.patch(`/api/v1/auth/users/${user.id}/`, { first_name, last_name, email, phone });
      queryClient.invalidateQueries({ queryKey: ['current-user'] });
      toast({ title: 'Perfil atualizado com sucesso!' });
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.response?.data?.email?.[0] || 'Erro ao salvar perfil.';
      toast({ title: detail, variant: 'destructive' });
    } finally {
      setSavingProfile(false);
    }
  };

  const handleChangePassword = async () => {
    if (!oldPassword || !newPassword || !confirmPassword) {
      toast({ title: 'Preencha todos os campos de senha', variant: 'destructive' });
      return;
    }
    if (newPassword !== confirmPassword) {
      toast({ title: 'As senhas não coincidem', variant: 'destructive' });
      return;
    }

    setChangingPassword(true);
    try {
      await api.post('/api/v1/auth/users/change_password/', {
        old_password: oldPassword,
        new_password: newPassword,
        new_password_confirm: confirmPassword,
      });
      toast({ title: 'Senha alterada com sucesso!' });
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      const data = err?.response?.data;
      const message =
        data?.old_password?.[0] ||
        data?.new_password?.[0] ||
        data?.detail ||
        'Erro ao alterar senha. Verifique os dados e tente novamente.';
      toast({ title: message, variant: 'destructive' });
    } finally {
      setChangingPassword(false);
    }
  };

  const handleSignatureFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      toast({ title: 'Selecione um arquivo de imagem (PNG, JPG, etc.)', variant: 'destructive' });
      return;
    }
    setSignatureFile(file);
    const reader = new FileReader();
    reader.onload = () => setSignaturePreview(reader.result as string);
    reader.readAsDataURL(file);
  };

  const handleRemoveSignature = () => {
    setSignatureFile(null);
    setSignaturePreview(null);
    if (signatureInputRef.current) {
      signatureInputRef.current.value = '';
    }
  };

  const toggleSpecialty = (specialty: string) => {
    setLawyerSpecialties((prev) =>
      prev.includes(specialty)
        ? prev.filter((s) => s !== specialty)
        : [...prev, specialty]
    );
  };

  const handleSaveLawyerProfile = async () => {
    if (!user) return;
    setSavingLawyer(true);
    try {
      const formData = new FormData();
      formData.append('oab_number', oabNumber);
      formData.append('oab_state', oabState);
      formData.append('lawyer_specialties', JSON.stringify(lawyerSpecialties));
      formData.append('signature_name', signatureName);
      if (signatureFile) {
        formData.append('signature_image', signatureFile);
      } else if (signaturePreview === null && user.signature_image) {
        // User removed existing signature
        formData.append('signature_image', '');
      }

      await api.patch('/api/v1/auth/users/me/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      queryClient.invalidateQueries({ queryKey: ['current-user'] });
      toast({ title: 'Perfil profissional atualizado com sucesso!' });
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'Erro ao salvar perfil profissional.';
      toast({ title: detail, variant: 'destructive' });
    } finally {
      setSavingLawyer(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold">Configurações</h1>
        <p className="text-muted-foreground text-sm sm:text-base">Gerencie suas preferências do sistema</p>
      </div>

      <div className="grid gap-4 sm:gap-6 grid-cols-1 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Perfil
            </CardTitle>
            <CardDescription>Informações da sua conta</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Nome Completo</Label>
              <AIInput
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                setValue={setFullName}
                aiContext="nome completo do usuário"
                aiObjective="Formate o nome completo corretamente"
              />
            </div>
            <div className="space-y-2">
              <Label>Email</Label>
              <AIInput
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                setValue={setEmail}
                aiContext="endereço de e-mail do usuário"
                aiObjective="Verifique e formate o e-mail corretamente"
              />
            </div>
            <div className="space-y-2">
              <Label>Telefone</Label>
              <AIInput
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                setValue={setPhone}
                aiContext="número de telefone do usuário"
                aiObjective="Formate o número de telefone no padrão brasileiro"
              />
            </div>
            <Button className="w-full" onClick={handleSaveProfile} disabled={savingProfile}>
              {savingProfile ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Salvando...</> : 'Salvar Alterações'}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lock className="h-5 w-5" />
              Segurança
            </CardTitle>
            <CardDescription>Alterar senha e configurações de segurança</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Senha Atual</Label>
              <Input type="password" value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Nova Senha</Label>
              <Input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Confirmar Nova Senha</Label>
              <Input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
            </div>
            <Button className="w-full" onClick={handleChangePassword} disabled={changingPassword}>
              {changingPassword ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Alterando...</> : 'Alterar Senha'}
            </Button>
          </CardContent>
        </Card>

        {/* Professional Profile Card */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Scale className="h-5 w-5" />
              Perfil Profissional
            </CardTitle>
            <CardDescription>Registro profissional, especializações e assinatura digital para documentos</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-4 grid-cols-1 sm:grid-cols-2">
              {/* Registration Number */}
              <div className="space-y-2">
                <Label>Registro Profissional</Label>
                <AIInput
                  placeholder="ex: OAB/SP 123.456 ou matrícula"
                  value={oabNumber}
                  onChange={(e) => setOabNumber(e.target.value)}
                  setValue={setOabNumber}
                  aiContext="registro profissional do procurador ou servidor"
                  aiObjective="Formate o número de registro profissional corretamente"
                />
              </div>
              {/* Registration State */}
              <div className="space-y-2">
                <Label>UF do Registro</Label>
                <select
                  className="w-full p-2.5 sm:p-2 rounded-md border bg-background text-foreground min-h-[44px] sm:min-h-0"
                  value={oabState}
                  onChange={(e) => setOabState(e.target.value)}
                >
                  <option value="">Selecione...</option>
                  {BRAZILIAN_STATES.map((st) => (
                    <option key={st} value={st}>{st}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Specialties */}
            <div className="space-y-2">
              <Label>Áreas de Atuação</Label>
              <div className="flex flex-wrap gap-2">
                {LAWYER_SPECIALTIES_OPTIONS.map((specialty) => {
                  const isSelected = lawyerSpecialties.includes(specialty);
                  return (
                    <button
                      key={specialty}
                      type="button"
                      onClick={() => toggleSpecialty(specialty)}
                      className={`px-3 py-2 sm:py-1.5 text-sm rounded-full border transition-colors min-h-[36px] ${
                        isSelected
                          ? 'bg-primary text-primary-foreground border-primary'
                          : 'bg-background text-foreground border-border hover:bg-muted'
                      }`}
                    >
                      {specialty}
                    </button>
                  );
                })}
              </div>
            </div>

            <Separator />

            {/* Signature Name */}
            <div className="space-y-2">
              <Label>Nome na Assinatura</Label>
              <AIInput
                placeholder="ex: Dr. Fulano de Tal — Procurador Municipal"
                value={signatureName}
                onChange={(e) => setSignatureName(e.target.value)}
                setValue={setSignatureName}
                aiContext="nome na assinatura de documentos da procuradoria"
                aiObjective="Formate o nome completo com cargo e registro profissional para assinatura"
              />
              <p className="text-xs text-muted-foreground">
                Nome como aparece abaixo da assinatura nos documentos gerados.
              </p>
            </div>

            {/* Signature Image Upload */}
            <div className="space-y-2">
              <Label>Imagem da Assinatura</Label>
              {signaturePreview ? (
                <div className="relative inline-block border rounded-lg p-4 bg-white">
                  <img
                    src={signaturePreview}
                    alt="Assinatura"
                    className="max-h-24 max-w-[300px] object-contain"
                  />
                  <button
                    type="button"
                    onClick={handleRemoveSignature}
                    className="absolute -top-2 -right-2 bg-destructive text-destructive-foreground rounded-full p-1 hover:bg-destructive/80"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </div>
              ) : (
                <div
                  onClick={() => signatureInputRef.current?.click()}
                  className="flex items-center justify-center gap-2 border-2 border-dashed rounded-lg p-8 sm:p-6 cursor-pointer hover:border-primary transition-colors text-muted-foreground active:bg-muted/50"
                >
                  <Upload className="h-5 w-5" />
                  <span className="text-sm">Clique para enviar a imagem da assinatura</span>
                </div>
              )}
              <input
                ref={signatureInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleSignatureFileChange}
              />
              <p className="text-xs text-muted-foreground">
                PNG ou JPG com fundo transparente/branco. Recomendado: 300x100px.
              </p>
            </div>

            <div className="sticky bottom-0 bg-card pt-4 pb-2 -mx-6 px-6 border-t sm:border-t-0 sm:relative sm:mx-0 sm:px-0 sm:pt-0 sm:pb-0">
              <Button className="w-full min-h-[44px]" onClick={handleSaveLawyerProfile} disabled={savingLawyer}>
                {savingLawyer ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Salvando...</> : 'Salvar Perfil Profissional'}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Canais de Notificação
            </CardTitle>
            <CardDescription>Configure como e onde receber notificações do Verus.AI</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {/* WhatsApp */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <MessageCircle className="h-4 w-4 text-green-500" />
                <Label className="font-medium">WhatsApp</Label>
              </div>
              <div className="flex gap-2">
                <AIInput
                  placeholder="+55 21 99999-8888"
                  value={whatsappNumber}
                  onChange={(e) => setWhatsappNumber(e.target.value)}
                  setValue={setWhatsappNumber}
                  aiContext="número de WhatsApp para notificações"
                  aiObjective="Formate o número de WhatsApp com código do país"
                />
                <Button
                  variant="outline"
                  onClick={handleVerifyWhatsApp}
                  disabled={verifyingWhatsapp}
                  className="shrink-0"
                >
                  {verifyingWhatsapp ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Verificar'}
                </Button>
              </div>
              {whatsappVerified && (
                <Badge className="bg-green-500 text-white">Verificado</Badge>
              )}
            </div>

            <Separator />

            {/* Email */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-blue-500" />
                <Label className="font-medium">E-mail para Notificacoes</Label>
              </div>
              <AIInput
                placeholder="seu@email.com"
                value={notifEmail}
                onChange={(e) => setNotifEmail(e.target.value)}
                setValue={setNotifEmail}
                aiContext="e-mail para recebimento de notificações"
                aiObjective="Verifique e formate o endereço de e-mail corretamente"
              />
              <p className="text-xs text-muted-foreground">
                Deixe vazio para usar o e-mail da sua conta.
              </p>
            </div>

            <Separator />

            {/* Canais */}
            <div className="space-y-4">
              {/* WhatsApp */}
              <div className="rounded-lg border p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <MessageCircle className="h-4 w-4 text-green-500" />
                    <span className="text-sm font-medium">WhatsApp</span>
                  </div>
                  <Switch checked={whatsappEnabled} onCheckedChange={setWhatsappEnabled} />
                </div>
                {whatsappEnabled && (
                  <div className="flex items-center justify-between pl-6">
                    <span className="text-xs text-muted-foreground">Envio automático (Celery)</span>
                    <Switch checked={whatsappAutoSend} onCheckedChange={setWhatsappAutoSend} />
                  </div>
                )}
                {whatsappEnabled && !whatsappAutoSend && (
                  <p className="text-[11px] text-amber-600 pl-6">Modo manual: você envia clicando no botão WhatsApp em cada notificação.</p>
                )}
                {whatsappEnabled && whatsappAutoSend && (
                  <p className="text-[11px] text-green-600 pl-6">Modo automático: notificações serão enviadas automaticamente.</p>
                )}
              </div>

              {/* Email */}
              <div className="rounded-lg border p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-blue-500" />
                    <span className="text-sm font-medium">E-mail</span>
                  </div>
                  <Switch checked={emailEnabled} onCheckedChange={setEmailEnabled} />
                </div>
                {emailEnabled && (
                  <div className="flex items-center justify-between pl-6">
                    <span className="text-xs text-muted-foreground">Envio automático (Celery)</span>
                    <Switch checked={emailAutoSend} onCheckedChange={setEmailAutoSend} />
                  </div>
                )}
                {emailEnabled && !emailAutoSend && (
                  <p className="text-[11px] text-amber-600 pl-6">Modo manual: você envia clicando no botão E-mail em cada notificação.</p>
                )}
                {emailEnabled && emailAutoSend && (
                  <p className="text-[11px] text-green-600 pl-6">Modo automático: e-mails serão enviados automaticamente.</p>
                )}
              </div>

              {/* App */}
              <div className="rounded-lg border p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Monitor className="h-4 w-4 text-purple-500" />
                    <span className="text-sm font-medium">Notificações no App</span>
                  </div>
                  <Switch checked={appEnabled} onCheckedChange={setAppEnabled} />
                </div>
                <p className="text-[11px] text-muted-foreground pl-6 mt-1">Sempre ativas no sino de notificações.</p>
              </div>
            </div>

            <Button className="w-full" onClick={handleSaveChannels} disabled={savingChannels}>
              {savingChannels ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Salvando...</> : 'Salvar Canais de Notificação'}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Palette className="h-5 w-5" />
              Aparência
            </CardTitle>
            <CardDescription>Personalize a aparência do sistema</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Tema</Label>
              <select
                className="w-full p-2 rounded-md border bg-background text-foreground"
                value={theme}
                onChange={(e) => setTheme(e.target.value)}
              >
                <option value="light">Claro</option>
                <option value="dark">Escuro</option>
                <option value="system">Sistema</option>
              </select>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

"use client";

import { useState, useEffect } from 'react';
import { useBrandSettings } from '@/hooks/use-brand-settings';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ColorPicker } from '@/components/ui/color-picker';
import { Separator } from '@/components/ui/separator';
import { Loader2, Upload, X, RotateCcw, Save, Palette, Image as ImageIcon } from 'lucide-react';
import { toast } from 'sonner';
import { AIInput } from '@/components/ui/ai-input';
import { AITextarea } from '@/components/ui/ai-textarea';
import Image from 'next/image';

export default function BrandSettingsPage() {
  const { brandSettings, isLoading, updateBrandSettings, isUpdating, resetBrandSettings, isResetting } = useBrandSettings();

  // Estados do formulário
  const [systemName, setSystemName] = useState('Verus.AI');
  const [systemTagline, setSystemTagline] = useState('');
  const [primaryColor, setPrimaryColor] = useState('#3b82f6');
  const [secondaryColor, setSecondaryColor] = useState('#8b5cf6');
  const [accentColor, setAccentColor] = useState('#10b981');

  const [confirmReset, setConfirmReset] = useState(false);

  // Estados para preview de imagens
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const [logoDarkFile, setLogoDarkFile] = useState<File | null>(null);
  const [logoDarkPreview, setLogoDarkPreview] = useState<string | null>(null);
  const [faviconFile, setFaviconFile] = useState<File | null>(null);
  const [faviconPreview, setFaviconPreview] = useState<string | null>(null);

  // Carregar dados do backend
  useEffect(() => {
    if (brandSettings) {
      setSystemName(brandSettings.system_name);
      setSystemTagline(brandSettings.system_tagline || '');
      setPrimaryColor(brandSettings.primary_color);
      setSecondaryColor(brandSettings.secondary_color);
      setAccentColor(brandSettings.accent_color);

      // Carregar previews de imagens existentes (backend já retorna URL completa)
      if (brandSettings.logo) {
        setLogoPreview(brandSettings.logo);
      }
      if (brandSettings.logo_dark) {
        setLogoDarkPreview(brandSettings.logo_dark);
      }
      if (brandSettings.favicon) {
        setFaviconPreview(brandSettings.favicon);
      }
    }
  }, [brandSettings]);

  // Handlers de upload
  const handleLogoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setLogoFile(file);
      setLogoPreview(URL.createObjectURL(file));
    }
  };

  const handleLogoDarkUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setLogoDarkFile(file);
      setLogoDarkPreview(URL.createObjectURL(file));
    }
  };

  const handleFaviconUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFaviconFile(file);
      setFaviconPreview(URL.createObjectURL(file));
    }
  };

  // Remover imagens
  const removeLogo = () => {
    setLogoFile(null);
    setLogoPreview(null);
  };

  const removeLogoDark = () => {
    setLogoDarkFile(null);
    setLogoDarkPreview(null);
  };

  const removeFavicon = () => {
    setFaviconFile(null);
    setFaviconPreview(null);
  };

  // Salvar alterações
  const handleSave = async () => {
    try {
      await updateBrandSettings({
        system_name: systemName,
        system_tagline: systemTagline,
        primary_color: primaryColor,
        secondary_color: secondaryColor,
        accent_color: accentColor,
        logo: logoFile || (logoPreview ? undefined : null),
        logo_dark: logoDarkFile || (logoDarkPreview ? undefined : null),
        favicon: faviconFile || (faviconPreview ? undefined : null),
      });
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Erro ao salvar configurações de identidade visual.');
    }
  };

  // Resetar para padrões
  const handleReset = async () => {
    try {
      await resetBrandSettings();
      setLogoFile(null);
      setLogoDarkFile(null);
      setFaviconFile(null);
      setConfirmReset(false);
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Erro ao resetar configurações.');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Identidade Visual</h1>
        <p className="text-muted-foreground">
          Configure a aparência do sistema, incluindo nome, cores e logos
        </p>
      </div>

      {/* Card: Informações Básicas */}
      <Card>
        <CardHeader>
          <CardTitle>Informações Básicas</CardTitle>
          <CardDescription>
            Nome e descrição do sistema
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="system-name">Nome do Sistema</Label>
            <AIInput
              id="system-name"
              value={systemName}
              onChange={(e) => setSystemName(e.target.value)}
              setValue={setSystemName}
              placeholder="Verus.AI"
              aiContext="nome do sistema jurídico"
              aiObjective="Sugira um nome adequado para o sistema"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="system-tagline">Tagline (Opcional)</Label>
            <AITextarea
              id="system-tagline"
              value={systemTagline}
              onChange={(e) => setSystemTagline(e.target.value)}
              setValue={setSystemTagline}
              placeholder="Descrição curta do sistema"
              rows={2}
              aiContext="tagline de sistema jurídico"
              aiObjective="Melhore a concisão e impacto da frase"
            />
          </div>
        </CardContent>
      </Card>

      {/* Card: Logos e Ícones */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <ImageIcon className="h-5 w-5" />
            <CardTitle>Logos e Ícones</CardTitle>
          </div>
          <CardDescription>
            Faça upload das imagens da marca (PNG, SVG, JPG)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Logo Principal */}
          <div className="space-y-2">
            <Label>Logo Principal</Label>
            <p className="text-sm text-muted-foreground">
              Recomendado: 200x60px (formato landscape)
            </p>
            <div className="flex items-center gap-4">
              {logoPreview ? (
                <div className="relative">
                  <img
                    src={logoPreview}
                    alt="Logo preview"
                    className="h-16 object-contain border rounded p-2"
                  />
                  <Button
                    type="button"
                    variant="destructive"
                    size="icon"
                    className="absolute -top-2 -right-2 h-6 w-6"
                    onClick={removeLogo}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ) : (
                <div className="h-16 w-48 border-2 border-dashed rounded flex items-center justify-center text-sm text-muted-foreground">
                  Nenhuma logo
                </div>
              )}
              <Input
                type="file"
                accept="image/*"
                onChange={handleLogoUpload}
                className="hidden"
                id="logo-upload"
              />
              <Label htmlFor="logo-upload">
                <Button type="button" variant="outline" asChild>
                  <span>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload
                  </span>
                </Button>
              </Label>
            </div>
          </div>

          <Separator />

          {/* Logo Dark Mode */}
          <div className="space-y-2">
            <Label>Logo Dark Mode (Opcional)</Label>
            <p className="text-sm text-muted-foreground">
              Logo alternativa para tema escuro
            </p>
            <div className="flex items-center gap-4">
              {logoDarkPreview ? (
                <div className="relative">
                  <img
                    src={logoDarkPreview}
                    alt="Logo dark preview"
                    className="h-16 object-contain border rounded p-2 bg-slate-100 dark:bg-slate-900"
                  />
                  <Button
                    type="button"
                    variant="destructive"
                    size="icon"
                    className="absolute -top-2 -right-2 h-6 w-6"
                    onClick={removeLogoDark}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ) : (
                <div className="h-16 w-48 border-2 border-dashed rounded flex items-center justify-center text-sm text-muted-foreground">
                  Nenhuma logo dark
                </div>
              )}
              <Input
                type="file"
                accept="image/*"
                onChange={handleLogoDarkUpload}
                className="hidden"
                id="logo-dark-upload"
              />
              <Label htmlFor="logo-dark-upload">
                <Button type="button" variant="outline" asChild>
                  <span>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload
                  </span>
                </Button>
              </Label>
            </div>
          </div>

          <Separator />

          {/* Favicon */}
          <div className="space-y-2">
            <Label>Favicon</Label>
            <p className="text-sm text-muted-foreground">
              Ícone do navegador (32x32px ou 64x64px)
            </p>
            <div className="flex items-center gap-4">
              {faviconPreview ? (
                <div className="relative">
                  <img
                    src={faviconPreview}
                    alt="Favicon preview"
                    className="h-12 w-12 object-contain border rounded p-1"
                  />
                  <Button
                    type="button"
                    variant="destructive"
                    size="icon"
                    className="absolute -top-2 -right-2 h-6 w-6"
                    onClick={removeFavicon}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ) : (
                <div className="h-12 w-12 border-2 border-dashed rounded flex items-center justify-center text-xs text-muted-foreground">
                  N/A
                </div>
              )}
              <Input
                type="file"
                accept="image/*,.ico"
                onChange={handleFaviconUpload}
                className="hidden"
                id="favicon-upload"
              />
              <Label htmlFor="favicon-upload">
                <Button type="button" variant="outline" asChild>
                  <span>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload
                  </span>
                </Button>
              </Label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Card: Paleta de Cores */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Palette className="h-5 w-5" />
            <CardTitle>Paleta de Cores</CardTitle>
          </div>
          <CardDescription>
            Defina as cores principais do sistema
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <ColorPicker
            label="Cor Primária"
            value={primaryColor}
            onChange={setPrimaryColor}
          />

          <ColorPicker
            label="Cor Secundária"
            value={secondaryColor}
            onChange={setSecondaryColor}
          />

          <ColorPicker
            label="Cor de Destaque"
            value={accentColor}
            onChange={setAccentColor}
          />

          {/* Preview das cores */}
          <div className="mt-6 p-4 border rounded-lg bg-muted/30">
            <p className="text-sm font-medium mb-3">Preview das Cores:</p>
            <div className="flex gap-4">
              <div className="flex-1 text-center">
                <div
                  className="h-16 rounded mb-2"
                  style={{ backgroundColor: primaryColor }}
                />
                <p className="text-xs text-muted-foreground">Primária</p>
              </div>
              <div className="flex-1 text-center">
                <div
                  className="h-16 rounded mb-2"
                  style={{ backgroundColor: secondaryColor }}
                />
                <p className="text-xs text-muted-foreground">Secundária</p>
              </div>
              <div className="flex-1 text-center">
                <div
                  className="h-16 rounded mb-2"
                  style={{ backgroundColor: accentColor }}
                />
                <p className="text-xs text-muted-foreground">Destaque</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex justify-between">
        {confirmReset ? (
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Confirmar reset?</span>
            <Button
              variant="destructive"
              size="sm"
              onClick={handleReset}
              disabled={isResetting}
            >
              {isResetting ? <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" /> : null}
              Confirmar
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setConfirmReset(false)}
              disabled={isResetting}
            >
              Cancelar
            </Button>
          </div>
        ) : (
          <Button
            variant="outline"
            onClick={() => setConfirmReset(true)}
            disabled={isResetting || isUpdating}
          >
            <RotateCcw className="mr-2 h-4 w-4" />
            Resetar para Padrão
          </Button>
        )}

        <Button
          onClick={handleSave}
          disabled={isUpdating || isResetting}
        >
          {isUpdating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {!isUpdating && <Save className="mr-2 h-4 w-4" />}
          Salvar Alterações
        </Button>
      </div>
    </div>
  );
}

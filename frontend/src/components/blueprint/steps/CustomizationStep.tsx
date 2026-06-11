'use client';

import { useState, useEffect } from 'react';
import { useBlueprints } from '@/hooks/use-blueprints';
import type { DocumentBlueprint } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { ColorPicker } from '@/components/ui/color-picker';
import { Save, Loader2, Palette, Type, Layout } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface CustomizationStepProps {
  blueprint: DocumentBlueprint;
  onUpdate: (blueprint: DocumentBlueprint) => void;
}

/**
 * Step de customizacao do blueprint.
 * Permite configurar organizacao, cabecalho/rodape, pagina de rosto,
 * tipografia, margens, cores e CSS customizado.
 * Organizado em secoes colapsaveis usando Accordion.
 */
export function CustomizationStep({ blueprint, onUpdate }: CustomizationStepProps) {
  const { updateBlueprint, isUpdatingBlueprint } = useBlueprints();
  const { toast } = useToast();

  // Estado local do formulario, inicializado com os dados do blueprint
  const [formData, setFormData] = useState({
    // Organizacao
    organization_name: blueprint.organization_name || '',
    organization_acronym: blueprint.organization_acronym || '',
    // Cabecalho/Rodape
    header_text: blueprint.header_text || '',
    footer_text: blueprint.footer_text || '',
    // Pagina de Rosto
    cover_page_enabled: blueprint.cover_page_enabled || false,
    cover_title: blueprint.cover_title || '',
    cover_subtitle: blueprint.cover_subtitle || '',
    cover_organization_text: blueprint.cover_organization_text || '',
    cover_footer_text: blueprint.cover_footer_text || '',
    cover_background_color: blueprint.cover_background_color || '#ffffff',
    // Tipografia
    pdf_font_family: blueprint.pdf_font_family || 'Arial',
    pdf_font_size: blueprint.pdf_font_size || 12,
    pdf_line_height: blueprint.pdf_line_height || 1.5,
    pdf_text_align: blueprint.pdf_text_align || 'justify',
    pdf_paragraph_indent: blueprint.pdf_paragraph_indent || '0',
    pdf_paragraph_spacing: blueprint.pdf_paragraph_spacing || '1em',
    // Margens
    pdf_page_margin_top: blueprint.pdf_page_margin_top || '2cm',
    pdf_page_margin_bottom: blueprint.pdf_page_margin_bottom || '2cm',
    pdf_page_margin_left: blueprint.pdf_page_margin_left || '3cm',
    pdf_page_margin_right: blueprint.pdf_page_margin_right || '2cm',
    // Cores e Estilo
    primary_color: blueprint.primary_color || '#3b82f6',
    secondary_color: blueprint.secondary_color || '#64748b',
    custom_css: blueprint.custom_css || '',
  });

  // Sincronizar se o blueprint mudar externamente
  useEffect(() => {
    setFormData({
      organization_name: blueprint.organization_name || '',
      organization_acronym: blueprint.organization_acronym || '',
      header_text: blueprint.header_text || '',
      footer_text: blueprint.footer_text || '',
      cover_page_enabled: blueprint.cover_page_enabled || false,
      cover_title: blueprint.cover_title || '',
      cover_subtitle: blueprint.cover_subtitle || '',
      cover_organization_text: blueprint.cover_organization_text || '',
      cover_footer_text: blueprint.cover_footer_text || '',
      cover_background_color: blueprint.cover_background_color || '#ffffff',
      pdf_font_family: blueprint.pdf_font_family || 'Arial',
      pdf_font_size: blueprint.pdf_font_size || 12,
      pdf_line_height: blueprint.pdf_line_height || 1.5,
      pdf_text_align: blueprint.pdf_text_align || 'justify',
      pdf_paragraph_indent: blueprint.pdf_paragraph_indent || '0',
      pdf_paragraph_spacing: blueprint.pdf_paragraph_spacing || '1em',
      pdf_page_margin_top: blueprint.pdf_page_margin_top || '2cm',
      pdf_page_margin_bottom: blueprint.pdf_page_margin_bottom || '2cm',
      pdf_page_margin_left: blueprint.pdf_page_margin_left || '3cm',
      pdf_page_margin_right: blueprint.pdf_page_margin_right || '2cm',
      primary_color: blueprint.primary_color || '#3b82f6',
      secondary_color: blueprint.secondary_color || '#64748b',
      custom_css: blueprint.custom_css || '',
    });
  }, [blueprint]);

  // Helper para atualizar campo
  const updateField = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  // Salvar customizacoes
  const handleSave = async () => {
    try {
      const updatedBlueprint = await updateBlueprint({
        id: blueprint.id,
        data: formData,
      });
      onUpdate(updatedBlueprint);
      toast({
        title: 'Customização salva',
        description: 'As configurações do blueprint foram atualizadas com sucesso.',
      });
    } catch (err: any) {
      toast({
        title: 'Erro ao salvar',
        description: err?.response?.data?.detail || 'Não foi possível salvar as customizações.',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Customização do Documento</h3>
          <p className="text-sm text-muted-foreground">
            Configure a aparência e formatação do PDF gerado
          </p>
        </div>
        <Button onClick={handleSave} disabled={isUpdatingBlueprint}>
          {isUpdatingBlueprint ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Save className="h-4 w-4 mr-2" />
          )}
          Salvar Alterações
        </Button>
      </div>

      {/* Secao: Organizacao */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Layout className="h-4 w-4 text-primary" />
            <CardTitle className="text-sm font-semibold">Organização</CardTitle>
          </div>
          <CardDescription className="text-xs">
            Dados da organização que aparecem no documento
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="organization_name">Nome da Organização</Label>
              <Input
                id="organization_name"
                value={formData.organization_name}
                onChange={(e) => updateField('organization_name', e.target.value)}
                placeholder="Ex: Prefeitura Municipal..."
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="organization_acronym">Sigla</Label>
              <Input
                id="organization_acronym"
                value={formData.organization_acronym}
                onChange={(e) => updateField('organization_acronym', e.target.value)}
                placeholder="Ex: OAB, TJSP, MPF"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Secao: Cabecalho / Rodape */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Layout className="h-4 w-4 text-primary" />
            <CardTitle className="text-sm font-semibold">Cabecalho e Rodape</CardTitle>
          </div>
          <CardDescription className="text-xs">
            Textos exibidos no topo e rodape de cada pagina do PDF
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="header_text">Texto do Cabecalho</Label>
            <Input
              id="header_text"
              value={formData.header_text}
              onChange={(e) => updateField('header_text', e.target.value)}
              placeholder="Texto exibido no cabecalho do PDF..."
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="footer_text">Texto do Rodape</Label>
            <Input
              id="footer_text"
              value={formData.footer_text}
              onChange={(e) => updateField('footer_text', e.target.value)}
              placeholder="Texto exibido no rodape do PDF..."
            />
          </div>
        </CardContent>
      </Card>

      {/* Secoes colapsaveis */}
      <Accordion type="multiple" defaultValue={['cover']} className="space-y-2">
        {/* Pagina de Rosto */}
        <AccordionItem value="cover" className="border rounded-lg px-4">
          <AccordionTrigger className="hover:no-underline">
            <div className="flex items-center gap-2">
              <Layout className="h-4 w-4 text-primary" />
              <span className="text-sm font-semibold">Pagina de Rosto</span>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <div className="space-y-4 pt-2">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="cover_page_enabled">Habilitar Pagina de Rosto</Label>
                  <p className="text-xs text-muted-foreground">
                    Adiciona uma pagina de capa antes do conteudo do documento
                  </p>
                </div>
                <Switch
                  id="cover_page_enabled"
                  checked={formData.cover_page_enabled}
                  onCheckedChange={(checked) => updateField('cover_page_enabled', checked)}
                />
              </div>

              {formData.cover_page_enabled && (
                <>
                  <Separator />
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="cover_title">Título da Capa</Label>
                      <Input
                        id="cover_title"
                        value={formData.cover_title}
                        onChange={(e) => updateField('cover_title', e.target.value)}
                        placeholder="Título principal da capa..."
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="cover_subtitle">Subtítulo</Label>
                      <Input
                        id="cover_subtitle"
                        value={formData.cover_subtitle}
                        onChange={(e) => updateField('cover_subtitle', e.target.value)}
                        placeholder="Subtítulo da capa..."
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="cover_organization_text">Texto da Organização (Capa)</Label>
                      <Input
                        id="cover_organization_text"
                        value={formData.cover_organization_text}
                        onChange={(e) => updateField('cover_organization_text', e.target.value)}
                        placeholder="Nome completo da organização na capa..."
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="cover_footer_text">Rodape da Capa</Label>
                      <Input
                        id="cover_footer_text"
                        value={formData.cover_footer_text}
                        onChange={(e) => updateField('cover_footer_text', e.target.value)}
                        placeholder="Texto no rodape da capa..."
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <ColorPicker
                      label="Cor de Fundo da Capa"
                      value={formData.cover_background_color}
                      onChange={(color) => updateField('cover_background_color', color)}
                    />
                  </div>
                </>
              )}
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* Tipografia */}
        <AccordionItem value="typography" className="border rounded-lg px-4">
          <AccordionTrigger className="hover:no-underline">
            <div className="flex items-center gap-2">
              <Type className="h-4 w-4 text-primary" />
              <span className="text-sm font-semibold">Tipografia</span>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <div className="space-y-4 pt-2">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="pdf_font_family">Fonte</Label>
                  <Select
                    value={formData.pdf_font_family}
                    onValueChange={(val) => updateField('pdf_font_family', val)}
                  >
                    <SelectTrigger id="pdf_font_family">
                      <SelectValue placeholder="Selecione a fonte" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Arial">Arial</SelectItem>
                      <SelectItem value="Times New Roman">Times New Roman</SelectItem>
                      <SelectItem value="Calibri">Calibri</SelectItem>
                      <SelectItem value="Helvetica">Helvetica</SelectItem>
                      <SelectItem value="Georgia">Georgia</SelectItem>
                      <SelectItem value="Verdana">Verdana</SelectItem>
                      <SelectItem value="Roboto">Roboto</SelectItem>
                      <SelectItem value="Open Sans">Open Sans</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="pdf_font_size">Tamanho da Fonte (pt)</Label>
                  <Input
                    id="pdf_font_size"
                    type="number"
                    min={8}
                    max={24}
                    value={formData.pdf_font_size}
                    onChange={(e) => updateField('pdf_font_size', Number(e.target.value))}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="pdf_line_height">Altura da Linha</Label>
                  <Input
                    id="pdf_line_height"
                    type="number"
                    min={1}
                    max={3}
                    step={0.1}
                    value={formData.pdf_line_height}
                    onChange={(e) => updateField('pdf_line_height', Number(e.target.value))}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="pdf_text_align">Alinhamento do Texto</Label>
                  <Select
                    value={formData.pdf_text_align}
                    onValueChange={(val) => updateField('pdf_text_align', val)}
                  >
                    <SelectTrigger id="pdf_text_align">
                      <SelectValue placeholder="Alinhamento" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="left">Esquerda</SelectItem>
                      <SelectItem value="center">Centro</SelectItem>
                      <SelectItem value="right">Direita</SelectItem>
                      <SelectItem value="justify">Justificado</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="pdf_paragraph_indent">Recuo do Paragrafo</Label>
                  <Input
                    id="pdf_paragraph_indent"
                    value={formData.pdf_paragraph_indent}
                    onChange={(e) => updateField('pdf_paragraph_indent', e.target.value)}
                    placeholder="Ex: 2em, 40px, 0"
                  />
                  <p className="text-[10px] text-muted-foreground">
                    Aceita valores CSS: 2em, 40px, 1.5cm
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="pdf_paragraph_spacing">Espacamento entre Paragrafos</Label>
                  <Input
                    id="pdf_paragraph_spacing"
                    value={formData.pdf_paragraph_spacing}
                    onChange={(e) => updateField('pdf_paragraph_spacing', e.target.value)}
                    placeholder="Ex: 1em, 16px"
                  />
                  <p className="text-[10px] text-muted-foreground">
                    Aceita valores CSS: 1em, 16px, 0.5cm
                  </p>
                </div>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* Margens */}
        <AccordionItem value="margins" className="border rounded-lg px-4">
          <AccordionTrigger className="hover:no-underline">
            <div className="flex items-center gap-2">
              <Layout className="h-4 w-4 text-primary" />
              <span className="text-sm font-semibold">Margens da Pagina</span>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <div className="space-y-4 pt-2">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="pdf_page_margin_top">Superior</Label>
                  <Input
                    id="pdf_page_margin_top"
                    value={formData.pdf_page_margin_top}
                    onChange={(e) => updateField('pdf_page_margin_top', e.target.value)}
                    placeholder="2cm"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="pdf_page_margin_bottom">Inferior</Label>
                  <Input
                    id="pdf_page_margin_bottom"
                    value={formData.pdf_page_margin_bottom}
                    onChange={(e) => updateField('pdf_page_margin_bottom', e.target.value)}
                    placeholder="2cm"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="pdf_page_margin_left">Esquerda</Label>
                  <Input
                    id="pdf_page_margin_left"
                    value={formData.pdf_page_margin_left}
                    onChange={(e) => updateField('pdf_page_margin_left', e.target.value)}
                    placeholder="3cm"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="pdf_page_margin_right">Direita</Label>
                  <Input
                    id="pdf_page_margin_right"
                    value={formData.pdf_page_margin_right}
                    onChange={(e) => updateField('pdf_page_margin_right', e.target.value)}
                    placeholder="2cm"
                  />
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                Aceita valores CSS como 2cm, 20mm, 1in. Padrao ABNT: Superior 3cm, Inferior 2cm, Esquerda 3cm, Direita 2cm.
              </p>
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* Cores e Estilo */}
        <AccordionItem value="colors" className="border rounded-lg px-4">
          <AccordionTrigger className="hover:no-underline">
            <div className="flex items-center gap-2">
              <Palette className="h-4 w-4 text-primary" />
              <span className="text-sm font-semibold">Cores e Estilo</span>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <div className="space-y-4 pt-2">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <ColorPicker
                  label="Cor Primaria"
                  value={formData.primary_color}
                  onChange={(color) => updateField('primary_color', color)}
                />
                <ColorPicker
                  label="Cor Secundaria"
                  value={formData.secondary_color}
                  onChange={(color) => updateField('secondary_color', color)}
                />
              </div>

              <Separator />

              <div className="space-y-2">
                <Label htmlFor="custom_css">CSS Personalizado</Label>
                <Textarea
                  id="custom_css"
                  value={formData.custom_css}
                  onChange={(e) => updateField('custom_css', e.target.value)}
                  placeholder={`/* Estilos personalizados para o PDF */\n.section-title {\n  color: #333;\n  font-weight: bold;\n}`}
                  rows={8}
                  className="font-mono text-xs"
                />
                <p className="text-[10px] text-muted-foreground">
                  CSS adicional aplicado ao documento PDF gerado. Use com cautela.
                </p>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>

      {/* Botao de salvar no rodape */}
      <div className="flex justify-end pt-2">
        <Button onClick={handleSave} disabled={isUpdatingBlueprint} size="lg">
          {isUpdatingBlueprint ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Save className="h-4 w-4 mr-2" />
          )}
          Salvar Customizações
        </Button>
      </div>
    </div>
  );
}

export default CustomizationStep;

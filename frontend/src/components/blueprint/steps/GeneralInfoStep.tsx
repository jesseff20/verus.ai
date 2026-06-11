'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { DocumentBlueprint } from '@/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Save, Loader2, ChevronDown } from 'lucide-react';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';
import { useToast } from '@/hooks/use-toast';
import api from '@/lib/api';

interface DocumentType {
  id: string;
  code: string;
  name: string;
  description?: string;
}

interface GeneralInfoStepProps {
  blueprint?: DocumentBlueprint;
  onSaved: (blueprint: DocumentBlueprint) => void;
  isNew?: boolean;
}

export function GeneralInfoStep({ blueprint, onSaved, isNew = false }: GeneralInfoStepProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Form state
  const [name, setName] = useState(blueprint?.name || '');
  const [description, setDescription] = useState(blueprint?.description || '');
  const [documentTypeId, setDocumentTypeId] = useState(blueprint?.document_type_id || blueprint?.document_type || '');
  const [version, setVersion] = useState(blueprint?.version || '1.0');
  const [legalBasis, setLegalBasis] = useState(blueprint?.legal_basis || '');
  const [isActive, setIsActive] = useState(blueprint?.is_active ?? true);
  const [isDefault, setIsDefault] = useState(blueprint?.is_default ?? false);

  // Sync form state when blueprint prop changes (e.g., after refetch)
  useEffect(() => {
    if (blueprint) {
      setName(blueprint.name || '');
      setDescription(blueprint.description || '');
      setDocumentTypeId(blueprint.document_type_id || blueprint.document_type || '');
      setVersion(blueprint.version || '1.0');
      setLegalBasis(blueprint.legal_basis || '');
      setIsActive(blueprint.is_active ?? true);
      setIsDefault(blueprint.is_default ?? false);
    }
  }, [blueprint]);

  // Fetch document types
  const { data: documentTypes, isLoading: isLoadingTypes } = useQuery({
    queryKey: ['document-types'],
    queryFn: async () => {
      const response = await api.get<{ results?: DocumentType[]; document_types?: DocumentType[] } | DocumentType[]>(
        '/api/v1/core/document-types/'
      );
      const data = response.data;
      // Handle different API response shapes
      if (Array.isArray(data)) return data;
      if ('results' in data && data.results) return data.results;
      if ('document_types' in data && data.document_types) return data.document_types;
      return [];
    },
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: async (payload: Record<string, any>) => {
      const response = await api.post<DocumentBlueprint>(
        '/api/v1/intelligent-assistant/blueprints/create/',
        payload
      );
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['blueprints'] });
      toast({ title: 'Blueprint criado com sucesso!' });
      onSaved(data);
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || error?.response?.data?.error || 'Erro ao criar blueprint.';
      toast({ title: 'Erro', description: message, variant: 'destructive' });
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: async (payload: Record<string, any>) => {
      const response = await api.patch<DocumentBlueprint>(
        `/api/v1/intelligent-assistant/blueprints/${blueprint!.id}/update/`,
        payload
      );
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['blueprints'] });
      queryClient.invalidateQueries({ queryKey: ['blueprint', blueprint!.id] });
      toast({ title: 'Blueprint atualizado com sucesso!' });
      onSaved(data);
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || error?.response?.data?.error || 'Erro ao atualizar blueprint.';
      toast({ title: 'Erro', description: message, variant: 'destructive' });
    },
  });

  const isSaving = createMutation.isPending || updateMutation.isPending;

  const handleSave = () => {
    // Validation
    if (!name.trim()) {
      toast({ title: 'Nome obrigatorio', description: 'Informe o nome do blueprint.', variant: 'destructive' });
      return;
    }
    if (!documentTypeId) {
      toast({ title: 'Tipo de documento obrigatorio', description: 'Selecione o tipo de documento.', variant: 'destructive' });
      return;
    }

    const payload: Record<string, any> = {
      name: name.trim(),
      description: description.trim(),
      document_type: documentTypeId,
      version: version.trim() || '1.0',
      legal_basis: legalBasis.trim(),
      is_active: isActive,
      is_default: isDefault,
    };

    if (isNew) {
      createMutation.mutate(payload);
    } else {
      updateMutation.mutate(payload);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Dados Gerais</CardTitle>
          <CardDescription>
            Informações básicas do blueprint de documento.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          {/* Name */}
          <div className="space-y-2">
            <Label htmlFor="bp-name">
              Nome <span className="text-destructive">*</span>
            </Label>
            <Input
              id="bp-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex: Petição Inicial - 12 Seções"
              disabled={isSaving}
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="bp-description">Descricao</Label>
            <div className="relative">
              <Textarea
                id="bp-description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Descreva o objetivo e escopo deste blueprint..."
                rows={3}
                disabled={isSaving}
                className="resize-none pr-32"
              />
              <div className="absolute top-1 right-1">
                <AIEnhanceButton
                  value={description}
                  onEnhance={setDescription}
                  context="descrição de blueprint de documento jurídico"
                  disabled={isSaving}
                />
              </div>
            </div>
          </div>

          {/* Document Type */}
          <div className="space-y-2">
            <Label htmlFor="bp-document-type">
              Tipo de Documento <span className="text-destructive">*</span>
            </Label>
            {isLoadingTypes ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Carregando tipos...
              </div>
            ) : (
              <Select
                value={documentTypeId}
                onValueChange={setDocumentTypeId}
                disabled={isSaving}
              >
                <SelectTrigger id="bp-document-type">
                  <SelectValue placeholder="Selecione o tipo de documento" />
                </SelectTrigger>
                <SelectContent>
                  {(documentTypes || []).map((dt) => (
                    <SelectItem key={dt.id} value={dt.id}>
                      {dt.name} ({dt.code})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>

          {/* Version */}
          <div className="space-y-2">
            <Label htmlFor="bp-version">Versao</Label>
            <Input
              id="bp-version"
              value={version}
              onChange={(e) => setVersion(e.target.value)}
              placeholder="1.0"
              disabled={isSaving}
              className="max-w-[200px]"
            />
          </div>

          {/* Legal Basis - collapsible */}
          <Accordion type="single" collapsible>
            <AccordionItem value="legal-basis" className="border-none">
              <AccordionTrigger className="py-2 text-sm hover:no-underline">
                Base Legal (opcional)
              </AccordionTrigger>
              <AccordionContent>
                <div className="relative">
                  <Textarea
                    id="bp-legal-basis"
                    value={legalBasis}
                    onChange={(e) => setLegalBasis(e.target.value)}
                    placeholder="Informe a base legal deste tipo de documento (leis, decretos, normativas)..."
                    rows={4}
                    disabled={isSaving}
                    className="resize-none pr-32"
                  />
                  <div className="absolute top-1 right-1">
                    <AIEnhanceButton
                      value={legalBasis}
                      onEnhance={setLegalBasis}
                      context="base legal de documento jurídico"
                      objective="Melhore a precisão e completude das referências legais"
                      disabled={isSaving}
                    />
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>

          {/* Switches */}
          <div className="flex flex-col gap-4 pt-2">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="bp-active" className="text-sm font-medium">Ativo</Label>
                <p className="text-xs text-muted-foreground">
                  Blueprint disponivel para uso no sistema.
                </p>
              </div>
              <Switch
                id="bp-active"
                checked={isActive}
                onCheckedChange={setIsActive}
                disabled={isSaving}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="bp-default" className="text-sm font-medium">Padrao</Label>
                <p className="text-xs text-muted-foreground">
                  Utilizar como blueprint padrao para o tipo de documento selecionado.
                </p>
              </div>
              <Switch
                id="bp-default"
                checked={isDefault}
                onCheckedChange={setIsDefault}
                disabled={isSaving}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Save button */}
      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={isSaving}>
          {isSaving ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Salvando...
            </>
          ) : (
            <>
              <Save className="h-4 w-4 mr-2" />
              {isNew ? 'Criar Blueprint' : 'Salvar Alterações'}
            </>
          )}
        </Button>
      </div>
    </div>
  );
}

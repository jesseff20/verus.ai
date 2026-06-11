'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { FormBuilder } from './FormBuilder';
import { useBlueprints } from '@/hooks/use-blueprints';
import { Loader2, Blocks } from 'lucide-react';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';



interface CreateFormDialogProps {
  trigger: React.ReactNode;
  onSuccess?: () => void;
}

export function CreateFormDialog({ trigger, onSuccess }: CreateFormDialogProps) {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(1); // 1: Info básica, 2: Builder
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    blueprint: '' as string | undefined,
    fields: [] as any[],
  });

  // Buscar Blueprints ativos
  const { blueprints, isLoading: loadingBlueprints } = useBlueprints();

  const handleNext = () => {
    if (step === 1 && formData.name) {
      setStep(2);
    }
  };

  const handleBack = () => {
    setStep(1);
  };

  const handleSave = () => {
    setOpen(false);
    setStep(1);
    setFormData({
      name: '',
      description: '',
      blueprint: undefined,
      fields: [],
    });
    onSuccess?.();
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {step === 1 ? 'Novo Formulário - Informações Básicas' : 'Construir Formulário - Adicionar Campos'}
          </DialogTitle>
          <DialogDescription className="sr-only">Criar novo formulário com campos personalizados</DialogDescription>
        </DialogHeader>

        {step === 1 ? (
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="name">
                Nome do Formulário <span className="text-red-500">*</span>
              </Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Ex: Formulário de Petição Inicial"
              />
            </div>

            <div>
              <Label htmlFor="description">Descrição</Label>
              <div className="relative">
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Descreva o propósito e uso deste formulário"
                  rows={3}
                  className="pr-32"
                />
                <div className="absolute top-1 right-1">
                  <AIEnhanceButton
                    value={formData.description}
                    onEnhance={(text) => setFormData({ ...formData, description: text })}
                    context="descrição de formulário jurídico"
                  />
                </div>
              </div>
            </div>

            <div>
              <Label htmlFor="blueprint">
                <Blocks className="inline h-4 w-4 mr-1" />
                Blueprint (Opcional)
              </Label>
              <p className="text-xs text-muted-foreground mb-2">
                Selecione o blueprint que define a estrutura do documento e os agentes especialistas disponíveis
              </p>
              {loadingBlueprints ? (
                <div className="flex items-center justify-center py-4 border rounded-md">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                  <span className="ml-2 text-sm text-muted-foreground">Carregando blueprints...</span>
                </div>
              ) : (
                <Select
                  value={formData.blueprint || 'none'}
                  onValueChange={(v) => setFormData({ ...formData, blueprint: v === 'none' ? undefined : v })}
                >
                  <SelectTrigger id="blueprint">
                    <SelectValue placeholder="Nenhum blueprint selecionado" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">
                      <span className="text-muted-foreground">Nenhum (pode ser vinculado depois)</span>
                    </SelectItem>
                    {blueprints.map((blueprint) => (
                      <SelectItem key={blueprint.id} value={blueprint.id}>
                        <div className="flex items-center gap-2">
                          <Blocks className="h-4 w-4" />
                          <span>{blueprint.name}</span>
                          <span className="text-xs text-muted-foreground">
                            ({blueprint.section_count} seções)
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
              {blueprints.length === 0 && !loadingBlueprints && (
                <p className="text-xs text-amber-600 mt-1">
                  Nenhum blueprint ativo disponível. Configure em Assistente Inteligente.
                </p>
              )}
            </div>

            <div className="flex justify-end pt-4 border-t">
              <Button onClick={handleNext} disabled={!formData.name}>
                Próximo: Adicionar Campos →
              </Button>
            </div>
          </div>
        ) : (
          <FormBuilder
            formData={formData}
            onSave={handleSave}
            onBack={handleBack}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}

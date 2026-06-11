'use client';

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Loader2, Edit } from 'lucide-react';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';
import { useForms } from '@/hooks/use-forms';
import { useToast } from '@/hooks/use-toast';
import type { FormTemplate } from '@/types';

interface EditFormDialogProps {
  form: FormTemplate;
  onSuccess?: () => void;
  children?: React.ReactNode;
}

export function EditFormDialog({ form, onSuccess, children }: EditFormDialogProps) {
  const [open, setOpen] = useState(false);
  const { updateForm, isUpdating } = useForms();
  const { toast } = useToast();

  const [formData, setFormData] = useState({
    name: form.name,
    description: form.description || '',
    is_active: form.is_active,
  });

  useEffect(() => {
    if (open) {
      setFormData({
        name: form.name,
        description: form.description || '',
        is_active: form.is_active,
      });
    }
  }, [open, form]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      toast({
        title: 'Campo obrigatório',
        description: 'O nome do formulário é obrigatório.',
        variant: 'destructive',
      });
      return;
    }

    try {
      await updateForm({
        id: form.id,
        data: {
          name: formData.name,
          description: formData.description,
          is_active: formData.is_active,
        },
      });

      toast({
        title: 'Formulário atualizado!',
        description: `O formulário "${formData.name}" foi atualizado com sucesso.`,
      });

      setOpen(false);
      onSuccess?.();
    } catch (error: any) {
      toast({
        title: 'Erro ao atualizar',
        description: error.response?.data?.detail || 'Não foi possível atualizar o formulário.',
        variant: 'destructive',
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      {children ? (
        <div onClick={() => setOpen(true)}>{children}</div>
      ) : (
        <Button variant="outline" onClick={() => setOpen(true)}>
          <Edit className="mr-2 h-4 w-4" />
          Editar
        </Button>
      )}

      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Editar Formulário</DialogTitle>
          <DialogDescription>
            Atualize as informações básicas do formulário. Os campos não podem ser editados aqui.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="edit-name">
              Nome do Formulário <span className="text-red-500">*</span>
            </Label>
            <Input
              id="edit-name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Ex: Formulário de Petição Inicial"
              required
            />
          </div>

          <div>
            <Label htmlFor="edit-description">Descrição</Label>
            <div className="relative">
              <Textarea
                id="edit-description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Descreva o propósito deste formulário"
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

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="edit-is-active"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="h-4 w-4 rounded border-gray-300"
            />
            <Label htmlFor="edit-is-active" className="cursor-pointer">
              Formulário ativo
            </Label>
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isUpdating}>
              {isUpdating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Salvando...
                </>
              ) : (
                'Salvar Alterações'
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { ChevronLeft, ChevronRight, Save, FileCheck } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { FormField } from './FormField';
import { AIAssistantButton } from './AIAssistantButton';

interface Field {
  name: string;
  label: string;
  type: 'text' | 'textarea' | 'select' | 'date' | 'number' | 'email';
  required?: boolean;
  placeholder?: string;
  options?: string[];
  section?: string;
  help_text?: string;
  ai_assist?: boolean;
  ai_prompt_types?: string[];
}

interface FormTemplate {
  sections: {
    title: string;
    description?: string;
    fields: Field[];
  }[];
}

interface DynamicFormWizardProps {
  formTemplate: FormTemplate;
  documentTemplate: string;
  initialData?: Record<string, any>;
  initialTitle?: string;
  initialNumeroProcesso?: string;
  onSave: (data: Record<string, any>, progress: number, metadata: { title?: string; numero_processo?: string }) => Promise<void>;
  onComplete: (data: Record<string, any>, progress: number, metadata: { title?: string; numero_processo?: string }) => Promise<void>;
  isSaving?: boolean;
  isCompleting?: boolean;
}

export function DynamicFormWizard({
  formTemplate,
  documentTemplate,
  initialData = {},
  initialTitle = '',
  initialNumeroProcesso = '',
  onSave,
  onComplete,
  isSaving = false,
  isCompleting = false,
}: DynamicFormWizardProps) {
  const [currentSection, setCurrentSection] = useState(0);
  const [formData, setFormData] = useState<Record<string, any>>(initialData);
  const [title, setTitle] = useState(initialTitle);
  const [numeroProcesso, setNumeroProcesso] = useState(initialNumeroProcesso);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const { toast } = useToast();

  // Auto-save a cada 30 segundos
  useEffect(() => {
    const interval = setInterval(() => {
      handleAutoSave();
    }, 30000);

    return () => clearInterval(interval);
  }, [formData]);

  const handleAutoSave = async () => {
    try {
      const progress = calculateProgress();
      await onSave(formData, progress, { title, numero_processo: numeroProcesso });
      setLastSaved(new Date());
    } catch (error) {
      console.error('Auto-save failed:', error);
    }
  };

  const handleFieldChange = (fieldName: string, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [fieldName]: value,
    }));
  };

  const calculateProgress = () => {
    const allFields = formTemplate.sections.flatMap((section) => section.fields);
    const filledFields = allFields.filter((field) => {
      const value = formData[field.name];
      return value !== undefined && value !== null && value !== '';
    });
    return Math.round((filledFields.length / allFields.length) * 100);
  };

  const validateCurrentSection = () => {
    const section = formTemplate.sections[currentSection];
    const requiredFields = section.fields.filter((f) => f.required);

    for (const field of requiredFields) {
      const value = formData[field.name];
      if (!value || value === '') {
        toast({
          title: 'Campo obrigatório',
          description: `O campo "${field.label}" é obrigatório.`,
          variant: 'destructive',
        });
        return false;
      }
    }
    return true;
  };

  const handleNext = () => {
    if (validateCurrentSection()) {
      if (currentSection < formTemplate.sections.length - 1) {
        setCurrentSection(currentSection + 1);
        handleAutoSave();
      }
    }
  };

  const handlePrevious = () => {
    if (currentSection > 0) {
      setCurrentSection(currentSection - 1);
    }
  };

  const handleSave = async () => {
    try {
      const progress = calculateProgress();
      await onSave(formData, progress, { title, numero_processo: numeroProcesso });
      setLastSaved(new Date());
      toast({
        title: 'Rascunho salvo',
        description: 'Seus dados foram salvos com sucesso.',
      });
    } catch (error: any) {
      toast({
        title: 'Erro ao salvar',
        description: error.message || 'Ocorreu um erro ao salvar o rascunho.',
        variant: 'destructive',
      });
    }
  };

  const handleComplete = async () => {
    // Validar todas as seções
    for (let i = 0; i < formTemplate.sections.length; i++) {
      const section = formTemplate.sections[i];
      const requiredFields = section.fields.filter((f) => f.required);

      for (const field of requiredFields) {
        const value = formData[field.name];
        if (!value || value === '') {
          toast({
            title: 'Campos obrigatórios pendentes',
            description: `Por favor, preencha todos os campos obrigatórios da seção "${section.title}".`,
            variant: 'destructive',
          });
          setCurrentSection(i);
          return;
        }
      }
    }

    try {
      const progress = calculateProgress();
      await onComplete(formData, progress, { title, numero_processo: numeroProcesso });
      toast({
        title: 'Documento criado!',
        description: 'Seu documento foi criado com sucesso.',
      });
    } catch (error: any) {
      toast({
        title: 'Erro ao criar documento',
        description: error.message || 'Ocorreu um erro ao criar o documento.',
        variant: 'destructive',
      });
    }
  };

  const progress = calculateProgress();
  const currentSectionData = formTemplate.sections[currentSection];

  return (
    <div className="space-y-6">
      {/* Header com progresso */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between mb-4">
            <div className="flex-1">
              <CardTitle>Criar Novo Documento</CardTitle>
              <CardDescription>
                Etapa {currentSection + 1} de {formTemplate.sections.length}
              </CardDescription>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-primary">{progress}%</div>
              <div className="text-xs text-muted-foreground">Completo</div>
            </div>
          </div>

          {/* Campos editáveis */}
          <div className="grid md:grid-cols-2 gap-4 mb-4">
            <div className="space-y-2">
              <Label htmlFor="wizard-title">Título do Documento</Label>
              <Input
                id="wizard-title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Ex: Petição Inicial Cível"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="wizard-numero-processo">Número do Processo</Label>
              <Input
                id="wizard-numero-processo"
                value={numeroProcesso}
                onChange={(e) => setNumeroProcesso(e.target.value)}
                placeholder="Ex: 2024/001"
              />
            </div>
          </div>

          <Progress value={progress} className="h-2" />
        </CardHeader>
      </Card>

      {/* Navegação entre seções */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {formTemplate.sections.map((section, index) => (
          <Button
            key={index}
            variant={currentSection === index ? 'default' : 'outline'}
            size="sm"
            onClick={() => setCurrentSection(index)}
            className="whitespace-nowrap"
          >
            {index + 1}. {section.title}
          </Button>
        ))}
      </div>

      {/* Formulário da seção atual */}
      <Card>
        <CardHeader>
          <CardTitle>{currentSectionData.title}</CardTitle>
          {currentSectionData.description && (
            <CardDescription>{currentSectionData.description}</CardDescription>
          )}
        </CardHeader>
        <CardContent className="space-y-6">
          {currentSectionData.fields.map((field) => {
            // Mapear tipos de IA para ações
            const aiTypeToAction: Record<string, 'corrigir' | 'melhorar' | 'exemplo' | 'consultar' | 'resumir' | 'expandir' | 'simplificar'> = {
              'corretor': 'corrigir',
              'sugestao': 'melhorar',
              'exemplo': 'exemplo',
              'analise': 'consultar',
              'resumo': 'resumir',
              'expansao': 'expandir',
              'simplificacao': 'simplificar',
            };

            // Determinar quais botões de IA mostrar (com tipo original para key única)
            const aiButtonsData = field.ai_assist && field.ai_prompt_types && field.ai_prompt_types.length > 0
              ? field.ai_prompt_types
                  .map(type => ({
                    type,  // Tipo original (corretor, sugestao, exemplo, analise, resumo, expansao, simplificacao)
                    action: aiTypeToAction[type],  // Ação mapeada
                  }))
                  .filter(item => item.action)
              : [];

            return (
              <div key={field.name} className="space-y-2">
                <FormField
                  field={field}
                  value={formData[field.name] || ''}
                  onChange={(value) => handleFieldChange(field.name, value)}
                />

                {/* Botões de IA - renderizar apenas os configurados */}
                {aiButtonsData.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {aiButtonsData.map((item) => (
                      <AIAssistantButton
                        key={item.type}  // Usar tipo original como key (único)
                        action={item.action}
                        assistantType={item.type}  // Passar tipo original
                        fieldName={field.name}
                        fieldValue={formData[field.name]}
                        fieldLabel={field.label}
                        formContext={formData}
                        documentTitle={title}
                        onResult={(result) => handleFieldChange(field.name, result)}
                      />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </CardContent>
      </Card>

      {/* Footer com ações */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                onClick={handlePrevious}
                disabled={currentSection === 0}
              >
                <ChevronLeft className="mr-2 h-4 w-4" />
                Anterior
              </Button>

              {currentSection < formTemplate.sections.length - 1 ? (
                <Button onClick={handleNext}>
                  Próxima
                  <ChevronRight className="ml-2 h-4 w-4" />
                </Button>
              ) : (
                <Button onClick={handleComplete} disabled={isCompleting}>
                  {isCompleting ? (
                    <>Criando...</>
                  ) : (
                    <>
                      <FileCheck className="mr-2 h-4 w-4" />
                      Criar Documento
                    </>
                  )}
                </Button>
              )}
            </div>

            <div className="flex items-center gap-4">
              {lastSaved && (
                <span className="text-xs text-muted-foreground">
                  Salvo às {lastSaved.toLocaleTimeString('pt-BR')}
                </span>
              )}
              <Button variant="outline" onClick={handleSave} disabled={isSaving}>
                <Save className="mr-2 h-4 w-4" />
                {isSaving ? 'Salvando...' : 'Salvar Rascunho'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

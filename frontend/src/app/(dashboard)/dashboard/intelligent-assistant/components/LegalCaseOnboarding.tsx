'use client';

import * as React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import {
  ArrowLeft,
  ArrowRight,
  Check,
  FileText,
  Scale,
  Search,
  ClipboardList,
  Send,
  Briefcase,
  Gavel,
  BookOpen,
  FileSignature,
  Building2,
  Users,
  AlertCircle,
} from 'lucide-react';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type CaseType =
  | 'civel'
  | 'trabalhista'
  | 'tributario'
  | 'previdenciario'
  | 'criminal'
  | 'consumidor'
  | 'familia'
  | 'extrajudicial'
  | 'administrativo'
  | 'eleitoral';

export interface CaseTypeOption {
  value: CaseType;
  label: string;
  description: string;
  icon: React.ReactNode;
}

export interface InstrumentOption {
  value: string;
  label: string;
  description: string;
  icon: React.ReactNode;
}

export interface CollectedData {
  [key: string]: any;
}

export interface LegalCaseOnboardingProps {
  /** Etapa atual (0-4) */
  currentStep?: number;
  /** Callback quando a etapa muda */
  onStepChange?: (step: number) => void;
  /** Callback com os dados coletados ao finalizar */
  onComplete?: (data: OnboardingData) => void;
  /** Opções de tipos de caso */
  caseTypes?: CaseTypeOption[];
  /** Opções de instrumentos jurídicos */
  instruments?: InstrumentOption[];
  /** Dados iniciais */
  initialData?: Partial<OnboardingData>;
}

export interface OnboardingData {
  caseDescription: string;
  caseType: CaseType | '';
  instrument: string;
  collectedData: CollectedData;
  partName: string;
  partType: 'physical' | 'legal' | '';
  cpf_cnpj: string;
  processNumber: string;
  court: string;
}

// ---------------------------------------------------------------------------
// Default options
// ---------------------------------------------------------------------------

const DEFAULT_CASE_TYPES: CaseTypeOption[] = [
  { value: 'civel', label: 'Cível', description: 'Ações cíveis em geral, contratos, indenizações', icon: <Scale className="h-5 w-5" /> },
  { value: 'trabalhista', label: 'Trabalhista', description: 'Reclamações trabalhistas, acordos, rescisões', icon: <Briefcase className="h-5 w-5" /> },
  { value: 'tributario', label: 'Tributário', description: 'Execuções fiscais, mandados de segurança tributários', icon: <FileText className="h-5 w-5" /> },
  { value: 'previdenciario', label: 'Previdenciário', description: 'Benefícios do INSS, aposentadoria, pensão', icon: <Users className="h-5 w-5" /> },
  { value: 'criminal', label: 'Criminal', description: 'Queixa-crime, defesa penal, habeas corpus', icon: <Gavel className="h-5 w-5" /> },
  { value: 'consumidor', label: 'Consumidor', description: 'Relações de consumo, CDC, reclamações', icon: <ShoppingCartIcon className="h-5 w-5" /> },
  { value: 'familia', label: 'Família e Sucessões', description: 'Divórcio, guarda, alimentos, inventário', icon: <Users className="h-5 w-5" /> },
  { value: 'extrajudicial', label: 'Extrajudicial', description: 'Contratos, notificações, procurações', icon: <FileSignature className="h-5 w-5" /> },
  { value: 'administrativo', label: 'Administrativo', description: 'Processos administrativos, licitações, servidores', icon: <Building2 className="h-5 w-5" /> },
  { value: 'eleitoral', label: 'Eleitoral', description: 'Ações eleitorais, registros, prestação de contas', icon: <Gavel className="h-5 w-5" /> },
];

const DEFAULT_INSTRUMENTS: InstrumentOption[] = [
  { value: 'peticao_inicial', label: 'Petição Inicial', description: 'Propositura de ação judicial', icon: <FileText className="h-5 w-5" /> },
  { value: 'contestacao', label: 'Contestação', description: 'Defesa em ação judicial', icon: <ShieldIcon className="h-5 w-5" /> },
  { value: 'recurso', label: 'Recurso', description: 'Apelação, agravo, embargos', icon: <ArrowRight className="h-5 w-5" /> },
  { value: 'parecer', label: 'Parecer Jurídico', description: 'Análise técnica-jurídica', icon: <BookOpen className="h-5 w-5" /> },
  { value: 'contrato', label: 'Contrato', description: 'Instrumento contratual', icon: <FileSignature className="h-5 w-5" /> },
  { value: 'notificação', label: 'Notificação Extrajudicial', description: 'Comunicação formal entre partes', icon: <Send className="h-5 w-5" /> },
  { value: 'mandado_seguranca', label: 'Mandado de Segurança', description: 'Proteção de direito líquido e certo', icon: <ShieldIcon className="h-5 w-5" /> },
  { value: 'etp', label: 'Documento Técnico', description: 'Geração assistida de documento jurídico ou técnico', icon: <ClipboardList className="h-5 w-5" /> },
];

function ShoppingCartIcon(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="9" cy="21" r="1" />
      <circle cx="20" cy="21" r="1" />
      <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
    </svg>
  );
}

function ShieldIcon(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Steps configuration
// ---------------------------------------------------------------------------

const STEPS = [
  { label: 'Descrição do Caso', icon: <FileText className="h-4 w-4" /> },
  { label: 'Triagem', icon: <Search className="h-4 w-4" /> },
  { label: 'Instrumento', icon: <FileSignature className="h-4 w-4" /> },
  { label: 'Dados Complementares', icon: <ClipboardList className="h-4 w-4" /> },
  { label: 'Confirmação', icon: <Check className="h-4 w-4" /> },
];

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function LegalCaseOnboarding({
  currentStep: externalStep,
  onStepChange,
  onComplete,
  caseTypes = DEFAULT_CASE_TYPES,
  instruments = DEFAULT_INSTRUMENTS,
  initialData = {},
}: LegalCaseOnboardingProps) {
  const [internalStep, setInternalStep] = React.useState(0);
  const step = externalStep ?? internalStep;

  const [data, setData] = React.useState<OnboardingData>({
    caseDescription: initialData.caseDescription || '',
    caseType: initialData.caseType || '',
    instrument: initialData.instrument || '',
    collectedData: initialData.collectedData || {},
    partName: initialData.partName || '',
    partType: initialData.partType || '',
    cpf_cnpj: initialData.cpf_cnpj || '',
    processNumber: initialData.processNumber || '',
    court: initialData.court || '',
  });

  const updateField = <K extends keyof OnboardingData>(
    field: K,
    value: OnboardingData[K]
  ) => {
    setData((prev) => ({ ...prev, [field]: value }));
  };

  const goToStep = (newStep: number) => {
    if (externalStep === undefined) {
      setInternalStep(newStep);
    }
    onStepChange?.(newStep);
  };

  const nextStep = () => {
    if (step < STEPS.length - 1) {
      goToStep(step + 1);
    } else {
      onComplete?.(data);
    }
  };

  const prevStep = () => {
    if (step > 0) {
      goToStep(step - 1);
    }
  };

  const canProceed = (): boolean => {
    switch (step) {
      case 0:
        return data.caseDescription.trim().length >= 10;
      case 1:
        return data.caseType !== '';
      case 2:
        return data.instrument !== '';
      case 3:
        return data.partName.trim().length >= 3;
      case 4:
        return true;
      default:
        return false;
    }
  };

  const progressPercent = ((step + 1) / STEPS.length) * 100;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          {STEPS.map((s, i) => (
            <div
              key={i}
              className={cn(
                'flex items-center gap-1.5 text-xs font-medium transition-colors',
                i <= step ? 'text-primary' : 'text-muted-foreground'
              )}
            >
              {s.icon}
              <span className="hidden sm:inline">{s.label}</span>
            </div>
          ))}
        </div>
        <Progress value={progressPercent} className="h-2" />
      </div>

      {/* Step Content */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{STEPS[step].label}</CardTitle>
          <CardDescription>
            {step === 0 && 'Descreva detalhadamente o caso jurídico'}
            {step === 1 && 'Selecione a área do direito mais adequada'}
            {step === 2 && 'Escolha o instrumento jurídico a ser gerado'}
            {step === 3 && 'Informe dados complementares para a peça'}
            {step === 4 && 'Revise as informações antes de prosseguir'}
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Step 0: Descrição do Caso */}
          {step === 0 && (
            <div className="space-y-3">
              <Label htmlFor="case-description">
                Descreva o caso jurídico em detalhes
              </Label>
              <div className="relative">
                <Textarea
                  id="case-description"
                  placeholder="Ex: Meu cliente, João Silva, sofreu um acidente de trabalho em 15/01/2025 na empresa XYZ Ltda. Ele era funcionário registrado desde 2020 e sofreu fratura no braço direito durante o expediente. A empresa se recusou a emitir a CAT e está negando os direitos trabalhistas..."
                  value={data.caseDescription}
                  onChange={(e) => updateField('caseDescription', e.target.value)}
                  rows={8}
                  className="pr-32"
                />
                <div className="absolute top-1 right-1">
                  <AIEnhanceButton
                    value={data.caseDescription}
                    onEnhance={(text) => updateField('caseDescription', text)}
                    context="descrição detalhada de caso jurídico para geração de documento"
                    objective="Melhore a clareza, organize os fatos cronologicamente e adicione precisão jurídica"
                  />
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                Quanto mais detalhes você fornecer, melhor será o resultado gerado.
                Mínimo de 10 caracteres.
              </p>
            </div>
          )}

          {/* Step 1: Triagem - Tipo de Caso */}
          {step === 1 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {caseTypes.map((ct) => (
                <button
                  key={ct.value}
                  type="button"
                  onClick={() => updateField('caseType', ct.value)}
                  className={cn(
                    'flex items-start gap-3 p-4 rounded-lg border text-left transition-all',
                    data.caseType === ct.value
                      ? 'border-primary bg-primary/5 ring-1 ring-primary'
                      : 'border-border hover:border-primary/50'
                  )}
                >
                  <div
                    className={cn(
                      'mt-0.5',
                      data.caseType === ct.value
                        ? 'text-primary'
                        : 'text-muted-foreground'
                    )}
                  >
                    {ct.icon}
                  </div>
                  <div>
                    <p
                      className={cn(
                        'font-medium text-sm',
                        data.caseType === ct.value && 'text-primary'
                      )}
                    >
                      {ct.label}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {ct.description}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Step 2: Seleção de Instrumento */}
          {step === 2 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {instruments.map((inst) => (
                <button
                  key={inst.value}
                  type="button"
                  onClick={() => updateField('instrument', inst.value)}
                  className={cn(
                    'flex items-start gap-3 p-4 rounded-lg border text-left transition-all',
                    data.instrument === inst.value
                      ? 'border-primary bg-primary/5 ring-1 ring-primary'
                      : 'border-border hover:border-primary/50'
                  )}
                >
                  <div
                    className={cn(
                      'mt-0.5',
                      data.instrument === inst.value
                        ? 'text-primary'
                        : 'text-muted-foreground'
                    )}
                  >
                    {inst.icon}
                  </div>
                  <div>
                    <p
                      className={cn(
                        'font-medium text-sm',
                        data.instrument === inst.value && 'text-primary'
                      )}
                    >
                      {inst.label}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {inst.description}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Step 3: Coleta de Dados */}
          {step === 3 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="part-name">Nome da Parte</Label>
                <Input
                  id="part-name"
                  placeholder="Nome completo"
                  value={data.partName}
                  onChange={(e) => updateField('partName', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="part-type">Tipo de Parte</Label>
                <select
                  id="part-type"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                  value={data.partType}
                  onChange={(e) => updateField('partType', e.target.value as any)}
                >
                  <option value="">Selecione...</option>
                  <option value="physical">Pessoa Física</option>
                  <option value="legal">Pessoa Jurídica</option>
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="cpf-cnpj">
                  {data.partType === 'legal' ? 'CNPJ' : 'CPF'}
                </Label>
                <Input
                  id="cpf-cnpj"
                  placeholder={data.partType === 'legal' ? '00.000.000/0000-00' : '000.000.000-00'}
                  value={data.cpf_cnpj}
                  onChange={(e) => updateField('cpf_cnpj', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="process-number">Número do Processo (opcional)</Label>
                <Input
                  id="process-number"
                  placeholder="0000000-00.0000.0.00.0000"
                  value={data.processNumber}
                  onChange={(e) => updateField('processNumber', e.target.value)}
                />
              </div>
              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="court">Tribunal / Foro (opcional)</Label>
                <Input
                  id="court"
                  placeholder="Ex: Justiça do Trabalho - 1ª Vara do Trabalho de São Paulo"
                  value={data.court}
                  onChange={(e) => updateField('court', e.target.value)}
                />
              </div>
            </div>
          )}

          {/* Step 4: Confirmação */}
          {step === 4 && (
            <div className="space-y-3">
              <div className="bg-muted/30 rounded-lg p-4 space-y-3">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-muted-foreground">Área:</span>
                    <p className="font-medium">
                      {caseTypes.find((ct) => ct.value === data.caseType)?.label || data.caseType}
                    </p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Instrumento:</span>
                    <p className="font-medium">
                      {instruments.find((i) => i.value === data.instrument)?.label || data.instrument}
                    </p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Parte:</span>
                    <p className="font-medium">{data.partName}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Tipo:</span>
                    <p className="font-medium">
                      {data.partType === 'physical' ? 'Pessoa Física' : data.partType === 'legal' ? 'Pessoa Jurídica' : '-'}
                    </p>
                  </div>
                </div>
                <div>
                  <span className="text-sm text-muted-foreground">Descrição do Caso:</span>
                  <p className="text-sm mt-1 bg-background rounded p-2 border">
                    {data.caseDescription}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
                <AlertCircle className="h-4 w-4 text-blue-600 mt-0.5" />
                <div className="text-sm text-blue-800">
                  <p className="font-medium">Pronto para gerar!</p>
                  <p className="text-blue-600">
                    Ao confirmar, o Verus.AI iniciará a geração da peça jurídica
                    com base nas informações fornecidas.
                  </p>
                </div>
              </div>
            </div>
          )}
        </CardContent>

        <CardFooter className="flex justify-between border-t pt-4">
          <div>
            {step > 0 && (
              <Button variant="outline" onClick={prevStep}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Anterior
              </Button>
            )}
          </div>
          <Button onClick={nextStep} disabled={!canProceed()}>
            {step === STEPS.length - 1 ? (
              <>
                Finalizar
                <Check className="h-4 w-4 ml-2" />
              </>
            ) : (
              <>
                Próximo
                <ArrowRight className="h-4 w-4 ml-2" />
              </>
            )}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}

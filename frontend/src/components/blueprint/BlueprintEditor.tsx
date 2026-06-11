'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';
import type { DocumentBlueprint } from '@/types';
import { GeneralInfoStep } from './steps/GeneralInfoStep';
import { SectionsStep } from './steps/SectionsStep';
import { KnowledgeBaseStep } from './steps/KnowledgeBaseStep';
import { AgentsConfigStep } from './steps/AgentsConfigStep';
import { CustomizationStep } from './steps/CustomizationStep';
import { TestStep } from './steps/TestStep';
import { FileText, Layers, Bot, Database, Palette, Play, Check, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

// Steps configuration
const STEPS = [
  { id: 'general', label: 'Dados Gerais', icon: FileText },
  { id: 'sections', label: 'Seções', icon: Layers },
  { id: 'agents', label: 'Agentes', icon: Bot },
  { id: 'knowledge', label: 'Bases de Conhecimento', icon: Database },
  { id: 'customization', label: 'Personalização PDF', icon: Palette },
  { id: 'test', label: 'Teste', icon: Play },
] as const;

type StepId = (typeof STEPS)[number]['id'];

interface BlueprintEditorProps {
  blueprint?: DocumentBlueprint;
  isNew?: boolean;
}

export function BlueprintEditor({ blueprint: initialBlueprint, isNew = false }: BlueprintEditorProps) {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState<StepId>('general');
  const [blueprintData, setBlueprintData] = useState<DocumentBlueprint | undefined>(initialBlueprint);
  const [completedSteps, setCompletedSteps] = useState<Set<StepId>>(
    initialBlueprint ? new Set(['general']) : new Set()
  );

  // After blueprint is created/saved on GeneralInfoStep, unlock remaining steps
  const handleBlueprintSaved = useCallback((saved: DocumentBlueprint) => {
    setBlueprintData(saved);
    setCompletedSteps((prev) => new Set([...prev, 'general']));

    // If it was a new blueprint, navigate to its real URL without full reload
    if (isNew) {
      window.history.replaceState(null, '', `/dashboard/blueprints/${saved.id}`);
    }
  }, [isNew]);

  // Update blueprint data from child steps
  const handleBlueprintUpdate = useCallback((updated: DocumentBlueprint) => {
    setBlueprintData(updated);
  }, []);

  // Mark a step as completed
  const markStepCompleted = useCallback((stepId: StepId) => {
    setCompletedSteps((prev) => new Set([...prev, stepId]));
  }, []);

  // For new blueprints, only step 1 is available until the blueprint is created
  const isStepAvailable = (stepId: StepId): boolean => {
    if (stepId === 'general') return true;
    return !!blueprintData; // Other steps require blueprint to exist
  };

  // Navigate to step
  const goToStep = (stepId: StepId) => {
    if (isStepAvailable(stepId)) {
      setCurrentStep(stepId);
    }
  };

  // Render active step content
  const renderStepContent = () => {
    switch (currentStep) {
      case 'general':
        return (
          <GeneralInfoStep
            blueprint={blueprintData}
            onSaved={handleBlueprintSaved}
            isNew={isNew && !blueprintData}
          />
        );
      case 'sections':
        if (!blueprintData) return null;
        return (
          <SectionsStep
            blueprint={blueprintData}
            onUpdate={handleBlueprintUpdate}
          />
        );
      case 'agents':
        if (!blueprintData) return null;
        return <AgentsConfigStep blueprint={blueprintData} onUpdate={handleBlueprintUpdate} />;
      case 'knowledge':
        if (!blueprintData) return null;
        return <KnowledgeBaseStep blueprint={blueprintData} />;
      case 'customization':
        if (!blueprintData) return null;
        return (
          <CustomizationStep
            blueprint={blueprintData}
            onUpdate={handleBlueprintUpdate}
          />
        );
      case 'test':
        if (!blueprintData) return null;
        return <TestStep blueprint={blueprintData} />;
      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col min-h-[calc(100vh-5rem)]">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/dashboard/blueprints')}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Voltar
        </Button>
        <div>
          <h1 className="text-xl font-bold">
            {isNew && !blueprintData ? 'Novo Blueprint' : blueprintData?.name || 'Editar Blueprint'}
          </h1>
          {blueprintData && (
            <p className="text-sm text-muted-foreground">
              {blueprintData.document_type_display} &middot; v{blueprintData.version}
              {blueprintData.section_count > 0 && ` \u00B7 ${blueprintData.section_count} secoes`}
            </p>
          )}
        </div>
      </div>

      {/* Layout: Stepper sidebar + Content area */}
      <div className="flex gap-6 flex-1">
        {/* Lateral Stepper */}
        <nav className="w-64 shrink-0">
          <div className="sticky top-4 space-y-1">
            {STEPS.map((step, index) => {
              const Icon = step.icon;
              const isActive = currentStep === step.id;
              const isCompleted = completedSteps.has(step.id);
              const isAvailable = isStepAvailable(step.id);

              return (
                <button
                  key={step.id}
                  onClick={() => goToStep(step.id)}
                  disabled={!isAvailable}
                  className={cn(
                    'w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-all',
                    'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary',
                    isActive && 'bg-primary/10 text-primary border border-primary/20',
                    !isActive && isAvailable && 'hover:bg-muted/50 text-foreground',
                    !isAvailable && 'opacity-40 cursor-not-allowed text-muted-foreground',
                    isCompleted && !isActive && 'text-green-700'
                  )}
                >
                  {/* Step indicator */}
                  <div
                    className={cn(
                      'flex items-center justify-center h-8 w-8 rounded-full shrink-0 transition-colors',
                      isActive && 'bg-primary text-primary-foreground',
                      isCompleted && !isActive && 'bg-green-100 text-green-700',
                      !isActive && !isCompleted && 'bg-muted text-muted-foreground'
                    )}
                  >
                    {isCompleted && !isActive ? (
                      <Check className="h-4 w-4" />
                    ) : (
                      <Icon className="h-4 w-4" />
                    )}
                  </div>

                  {/* Step label */}
                  <div className="flex-1 min-w-0">
                    <p className={cn(
                      'text-sm font-medium truncate',
                      isActive && 'text-primary'
                    )}>
                      {step.label}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Etapa {index + 1} de {STEPS.length}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>
        </nav>

        {/* Content Area */}
        <div className="flex-1 min-w-0">
          {renderStepContent()}
        </div>
      </div>
    </div>
  );
}

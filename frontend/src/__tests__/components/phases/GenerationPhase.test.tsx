import React from 'react';
import { GenerationPhase } from '@/components/phases/GenerationPhase';

describe('GenerationPhase Component', () => {
  const baseProps = {
    sessionDetail: { id: 'session-1' },
    blueprintName: 'Modelo Padrão',
    sectionNames: { 1: 'Partes', 2: 'Objeto', 3: 'Cláusulas' },
    sectionFieldsMap: {} as Record<number, any[]>,
    sectionFieldsValues: {} as Record<number, Record<string, any>>,
    onSectionFieldsChange: jest.fn(),
    subSectionsMap: {} as Record<number, any[]>,
    subSectionDecisions: {} as Record<number, Record<string, boolean>>,
    onSubSectionDecisionChange: jest.fn(),
    selectedSections: new Set<number>([1, 2]),
    totalSections: 3,
    allSelected: false,
    onToggleSection: jest.fn(),
    onToggleAll: jest.fn(),
    generationProgress: {
      status: 'idle' as const,
      sections: {},
      cancelled: false,
      result: null,
    },
    expandedSections: new Set<number>(),
    onToggleExpand: jest.fn(),
    onGenerate: jest.fn().mockResolvedValue(undefined),
    onCancel: jest.fn(),
    onReset: jest.fn(),
    onAdvance: jest.fn(),
    isLoadingSections: false,
    onRegenerateSection: jest.fn(),
    regeneratingSection: null,
    className: '',
  };

  it('renders section selection in idle state', () => {
    const { container } = render(<GenerationPhase {...baseProps} />);
    expect(container.textContent).toContain('Seções para Gerar');
    expect(container.textContent).toContain('1. Partes');
    expect(container.textContent).toContain('2. Objeto');
    expect(container.textContent).toContain('3. Cláusulas');
  });

  it('shows selected section count', () => {
    const { container } = render(<GenerationPhase {...baseProps} />);
    expect(container.textContent).toContain('2/3');
  });

  it('shows toggle all button', () => {
    const { container } = render(<GenerationPhase {...baseProps} />);
    expect(container.textContent).toContain('Selecionar Todas');
  });

  it('calls onToggleAll when toggle button is clicked', () => {
    const onToggleAll = jest.fn();
    const { container } = render(
      <GenerationPhase {...baseProps} onToggleAll={onToggleAll} />
    );
    const toggleBtn = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Selecionar Todas')
    )!;
    fireEvent.click(toggleBtn);
    expect(onToggleAll).toHaveBeenCalledWith(true);
  });

  it('calls onToggleSection when section is clicked', () => {
    const onToggleSection = jest.fn();
    const { container } = render(
      <GenerationPhase {...baseProps} onToggleSection={onToggleSection} />
    );
    const sectionBtn = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('1. Partes')
    )!;
    fireEvent.click(sectionBtn);
    expect(onToggleSection).toHaveBeenCalledWith(1);
  });

  it('shows generate button when sections selected', () => {
    const { container } = render(<GenerationPhase {...baseProps} />);
    expect(container.textContent).toContain('Gerar Documento (2 seções)');
  });

  it('calls onGenerate when generate button is clicked', () => {
    const onGenerate = jest.fn().mockResolvedValue(undefined);
    const { container } = render(
      <GenerationPhase {...baseProps} onGenerate={onGenerate} />
    );
    const generateBtn = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Gerar Documento')
    )!;
    fireEvent.click(generateBtn);
    expect(onGenerate).toHaveBeenCalledTimes(1);
  });

  it('shows loading spinner when isLoadingSections is true', () => {
    const { container } = render(
      <GenerationPhase {...baseProps} isLoadingSections={true} />
    );
    const spinner = container.querySelector('svg.lucide-loader-2');
    expect(spinner).toBeInTheDocument();
  });

  it('shows generation progress when status is generating', () => {
    const props = {
      ...baseProps,
      generationProgress: {
        status: 'generating' as const,
        sections: {
          '1': { section_number: 1, section_name: 'Partes', status: 'completed' as const, score: 85 },
          '2': { section_number: 2, section_name: 'Objeto', status: 'generating' as const },
        },
        cancelled: false,
        result: null,
      },
    };
    const { container } = render(<GenerationPhase {...props} />);
    expect(container.textContent).toContain('Gerando Documento...');
    expect(container.textContent).toContain('Cancelar');
  });

  it('shows progress bar during generation', () => {
    const props = {
      ...baseProps,
      generationProgress: {
        status: 'generating' as const,
        sections: {
          '1': { section_number: 1, section_name: 'Partes', status: 'completed' as const, score: 85 },
          '2': { section_number: 2, section_name: 'Objeto', status: 'generating' as const },
        },
        cancelled: false,
        result: null,
      },
    };
    const { container } = render(<GenerationPhase {...props} />);
    const progressBar = container.querySelector('[role="progressbar"]') || container.querySelector('.h-2');
    expect(progressBar).toBeInTheDocument();
    expect(container.textContent).toContain('50%');
  });

  it('shows cancel button during generation', () => {
    const onCancel = jest.fn();
    const props = {
      ...baseProps,
      generationProgress: {
        status: 'generating' as const,
        sections: {},
        cancelled: false,
        result: null,
      },
      onCancel,
    };
    const { container } = render(<GenerationPhase {...props} />);
    const cancelBtn = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Cancelar')
    )!;
    fireEvent.click(cancelBtn);
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('shows completed state with actions', () => {
    const props = {
      ...baseProps,
      generationProgress: {
        status: 'completed' as const,
        sections: {
          '1': { section_number: 1, section_name: 'Partes', status: 'completed' as const, score: 85, content: 'Conteúdo' },
          '2': { section_number: 2, section_name: 'Objeto', status: 'completed' as const, score: 90, content: 'Objeto' },
        },
        cancelled: false,
        result: {
          success: true,
          generationSessionId: 'gen-1',
          totalTokensUsed: 1500,
          validSections: 2,
          averageScore: 87,
          generationTime: 30,
          documentId: 'doc-1',
          pdfUrl: '',
        },
      },
    };
    const { container } = render(<GenerationPhase {...props} />);
    expect(container.textContent).toContain('Geração Concluída');
    expect(container.textContent).toContain('Regenerar');
    expect(container.textContent).toContain('Avaliar Seções');
  });

  it('shows error state with retry button', () => {
    const onReset = jest.fn();
    const props = {
      ...baseProps,
      generationProgress: {
        status: 'error' as const,
        sections: {},
        cancelled: false,
        result: null,
        error: 'Falha na geração',
      },
      onReset,
    };
    const { container } = render(<GenerationPhase {...props} />);
    expect(container.textContent).toContain('Erro na Geração');
    expect(container.textContent).toContain('Falha na geração');
    const retryBtn = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Tentar Novamente')
    )!;
    fireEvent.click(retryBtn);
    expect(onReset).toHaveBeenCalledTimes(1);
  });

  it('applies custom className', () => {
    const { container } = render(
      <GenerationPhase {...baseProps} className="custom-phase" />
    );
    const outerDiv = container.firstElementChild as HTMLElement;
    expect(outerDiv).toHaveClass('custom-phase');
  });
});

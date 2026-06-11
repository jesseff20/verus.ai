import React from 'react';
import { AnalysisPhase } from '@/components/phases/AnalysisPhase';

describe('AnalysisPhase Component', () => {
  const baseProps = {
    generatedContent: {
      section_01: 'Conteúdo da seção 1',
      section_02: 'Conteúdo da seção 2',
      section_03: 'Conteúdo da seção 3',
    },
    sectionNames: { 1: 'Partes', 2: 'Objeto', 3: 'Cláusulas' },
    sections: {
      '1': { section_number: 1, section_name: 'Partes', content: 'Texto', score: 85, status: 'completed' },
      '2': { section_number: 2, section_name: 'Objeto', content: 'Texto', score: 70, status: 'completed' },
      '3': { section_number: 3, section_name: 'Cláusulas', content: 'Texto', score: 45, status: 'completed' },
    },
    generationMetadata: {
      total_tokens_used: 2500,
      valid_sections: 3,
      average_score: 67,
      generation_time: 45,
      document_id: 'doc-1',
      generation_session_id: 'gen-1',
    },
    totalSections: 5,
    approvalStatus: { 1: 'approved', 2: 'improved', 3: 'pending' } as Record<number, any>,
    onSetApproval: jest.fn(),
    onAdvance: jest.fn(),
    className: '',
  };

  it('renders analysis header', () => {
    const { container } = render(<AnalysisPhase {...baseProps} />);
    expect(container.textContent).toContain('Análise do Documento');
  });

  it('renders stats grid', () => {
    const { container } = render(<AnalysisPhase {...baseProps} />);
    expect(container.textContent).toContain('Score Médio');
    expect(container.textContent).toContain('Seções Válidas');
    expect(container.textContent).toContain('Tokens Utilizados');
    expect(container.textContent).toContain('Tempo de Geração');
  });

  it('displays average score', () => {
    const { container } = render(<AnalysisPhase {...baseProps} />);
    expect(container.textContent).toContain('67%');
  });

  it('displays valid sections count', () => {
    const { container } = render(<AnalysisPhase {...baseProps} />);
    expect(container.textContent).toContain('3/5');
  });

  it('displays total tokens', () => {
    const { container } = render(<AnalysisPhase {...baseProps} />);
    expect(container.textContent).toContain('2500');
  });

  it('displays generation time', () => {
    const { container } = render(<AnalysisPhase {...baseProps} />);
    expect(container.textContent).toContain('45s');
  });

  it('renders approval summary', () => {
    const { container } = render(<AnalysisPhase {...baseProps} />);
    expect(container.textContent).toContain('Resumo de Aprovações');
    expect(container.textContent).toContain('1 aprovadas');
    expect(container.textContent).toContain('1 melhoradas');
    expect(container.textContent).toContain('1 pendentes');
  });

  it('renders all section cards', () => {
    const { container } = render(<AnalysisPhase {...baseProps} />);
    expect(container.textContent).toContain('1. Partes');
    expect(container.textContent).toContain('2. Objeto');
    expect(container.textContent).toContain('3. Cláusulas');
  });

  it('shows score for each section', () => {
    const { container } = render(<AnalysisPhase {...baseProps} />);
    expect(container.textContent).toContain('85%');
    expect(container.textContent).toContain('70%');
    expect(container.textContent).toContain('45%');
  });

  it('shows approve/improve buttons for sections', () => {
    const { container } = render(<AnalysisPhase {...baseProps} />);
    // There should be ThumbsUp and AlertTriangle buttons for each section
    const thumbsUpButtons = container.querySelectorAll('svg.lucide-thumbs-up');
    const alertTriangleButtons = container.querySelectorAll('svg.lucide-alert-triangle');
    expect(thumbsUpButtons.length).toBe(3);
    expect(alertTriangleButtons.length).toBe(3);
  });

  it('calls onSetApproval when thumbs up is clicked', () => {
    const onSetApproval = jest.fn();
    const { container } = render(
      <AnalysisPhase {...baseProps} onSetApproval={onSetApproval} />
    );
    const thumbsUpBtns = container.querySelectorAll('svg.lucide-thumbs-up');
    const firstBtn = thumbsUpBtns[0].closest('button')!;
    fireEvent.click(firstBtn);
    expect(onSetApproval).toHaveBeenCalledWith(1, 'approved');
  });

  it('calls onSetApproval when alert triangle is clicked', () => {
    const onSetApproval = jest.fn();
    const { container } = render(
      <AnalysisPhase {...baseProps} onSetApproval={onSetApproval} />
    );
    const alertBtns = container.querySelectorAll('svg.lucide-alert-triangle');
    const firstBtn = alertBtns[0].closest('button')!;
    fireEvent.click(firstBtn);
    expect(onSetApproval).toHaveBeenCalledWith(1, 'improved');
  });

  it('shows advance button', () => {
    const { container } = render(<AnalysisPhase {...baseProps} />);
    expect(container.textContent).toContain('Ver Resultado');
  });

  it('calls onAdvance when advance button is clicked', () => {
    const onAdvance = jest.fn();
    const { container } = render(
      <AnalysisPhase {...baseProps} onAdvance={onAdvance} />
    );
    const advanceBtn = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Ver Resultado')
    )!;
    fireEvent.click(advanceBtn);
    expect(onAdvance).toHaveBeenCalledTimes(1);
  });

  it('shows content preview for sections', () => {
    const { container } = render(<AnalysisPhase {...baseProps} />);
    expect(container.textContent).toContain('Conteúdo da seção 1');
  });

  it('shows progress bar for each section', () => {
    const { container } = render(<AnalysisPhase {...baseProps} />);
    const progressBars = container.querySelectorAll('[role="progressbar"]');
    // Each section has a progress bar
    expect(progressBars.length).toBeGreaterThanOrEqual(3);
  });

  it('handles 0 generationTime gracefully', () => {
    const props = {
      ...baseProps,
      generationMetadata: {
        ...baseProps.generationMetadata,
        generation_time: 0,
      },
    };
    const { container } = render(<AnalysisPhase {...props} />);
    expect(container.textContent).toContain('N/A');
  });

  it('applies custom className', () => {
    const { container } = render(
      <AnalysisPhase {...baseProps} className="custom-phase" />
    );
    const outerDiv = container.firstElementChild as HTMLElement;
    expect(outerDiv).toHaveClass('custom-phase');
  });
});

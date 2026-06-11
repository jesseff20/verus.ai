import React from 'react';
import { EvaluationPhase } from '@/components/phases/EvaluationPhase';

describe('EvaluationPhase Component', () => {
  const baseProps = {
    generatedContent: {
      section_01: 'Conteúdo da seção 1',
      section_02: 'Conteúdo da seção 2',
    },
    sectionNames: { 1: 'Partes', 2: 'Objeto' },
    sections: {
      '1': { section_number: 1, section_name: 'Partes', content: 'Conteúdo partes', score: 85, status: 'completed' },
      '2': { section_number: 2, section_name: 'Objeto', content: 'Conteúdo objeto', score: 90, status: 'completed' },
    },
    sectionAgentInfo: {},
    sectionRatings: {} as Record<number, number>,
    onRate: jest.fn(),
    editingSection: null,
    editedContent: {} as Record<number, string>,
    onStartEdit: jest.fn(),
    onCancelEdit: jest.fn(),
    onSaveEdit: jest.fn(),
    onEditChange: jest.fn(),
    savingFeedback: {} as Record<number, boolean>,
    evaluatedSections: {} as Record<number, 'approved' | 'improved'>,
    onSaveFeedback: jest.fn().mockResolvedValue(undefined),
    approvalStatus: {} as Record<number, any>,
    onSetApproval: jest.fn(),
    onAdvance: jest.fn().mockResolvedValue(undefined),
    updatingDocument: false,
    className: '',
  };

  it('renders evaluation header', () => {
    const { container } = render(<EvaluationPhase {...baseProps} />);
    expect(container.textContent).toContain('Avaliação de Seções');
  });

  it('renders all sections', () => {
    const { container } = render(<EvaluationPhase {...baseProps} />);
    expect(container.textContent).toContain('1. Partes');
    expect(container.textContent).toContain('2. Objeto');
  });

  it('shows evaluated count', () => {
    const { container } = render(<EvaluationPhase {...baseProps} />);
    expect(container.textContent).toContain('0/2 avaliadas');
  });

  it('shows advance button', () => {
    const { container } = render(<EvaluationPhase {...baseProps} />);
    const advanceBtn = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Avançar')
    );
    expect(advanceBtn).toBeInTheDocument();
  });

  it('advance button is disabled when not all evaluated', () => {
    const { container } = render(<EvaluationPhase {...baseProps} />);
    const advanceBtn = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Avançar')
    );
    expect(advanceBtn).toBeDisabled();
  });

  it('advance button is enabled when all evaluated', () => {
    const props = {
      ...baseProps,
      evaluatedSections: { 1: 'approved', 2: 'approved' },
    };
    const { container } = render(<EvaluationPhase {...props} />);
    const advanceBtn = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Avançar')
    );
    expect(advanceBtn).toBeEnabled();
  });

  it('shows score badge for each section', () => {
    const { container } = render(<EvaluationPhase {...baseProps} />);
    expect(container.textContent).toContain('Score: 85');
    expect(container.textContent).toContain('Score: 90');
  });

  it('renders star rating buttons', () => {
    const { container } = render(<EvaluationPhase {...baseProps} />);
    const starIcons = container.querySelectorAll('svg.lucide-star');
    expect(starIcons.length).toBeGreaterThanOrEqual(5); // At least one section has 5 stars
  });

  it('calls onRate when star is clicked', () => {
    const onRate = jest.fn();
    const { container } = render(
      <EvaluationPhase {...baseProps} onRate={onRate} />
    );
    const starButtons = container.querySelectorAll('button');
    // Find a star button (inside the card header area)
    const starBtn = Array.from(starButtons).find(
      (b) => b.querySelector('svg.lucide-star')
    );
    if (starBtn) {
      fireEvent.click(starBtn);
      expect(onRate).toHaveBeenCalled();
    }
  });

  it('shows evaluated badge when section is evaluated', () => {
    const props = {
      ...baseProps,
      evaluatedSections: { 1: 'approved' },
    };
    const { container } = render(<EvaluationPhase {...props} />);
    expect(container.textContent).toContain('Aprovada');
  });

  it('calls onStartEdit when edit button is clicked', () => {
    const onStartEdit = jest.fn();
    const { container } = render(
      <EvaluationPhase {...baseProps} onStartEdit={onStartEdit} />
    );
    const editBtn = container.querySelector('svg.lucide-edit-3')?.closest('button')!;
    fireEvent.click(editBtn);
    expect(onStartEdit).toHaveBeenCalled();
  });

  it('shows textarea when editing', () => {
    const props = {
      ...baseProps,
      editingSection: 1,
      editedContent: { 1: 'Conteúdo editado' },
    };
    const { container } = render(<EvaluationPhase {...props} />);
    const textarea = container.querySelector('textarea');
    expect(textarea).toBeInTheDocument();
    expect(textarea).toHaveValue('Conteúdo editado');
  });

  it('shows approve and improve buttons', () => {
    const { container } = render(<EvaluationPhase {...baseProps} />);
    expect(container.textContent).toContain('Aprovar');
    expect(container.textContent).toContain('Precisa Melhorar');
  });

  it('calls onSetApproval when approve button is clicked', () => {
    const onSetApproval = jest.fn();
    const { container } = render(
      <EvaluationPhase {...baseProps} onSetApproval={onSetApproval} />
    );
    const approveBtn = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.trim() === 'Aprovar'
    )!;
    fireEvent.click(approveBtn);
    expect(onSetApproval).toHaveBeenCalledWith(1, 'approved');
  });

  it('shows "Salvar Avaliação" button for each section', () => {
    const { container } = render(<EvaluationPhase {...baseProps} />);
    const saveButtons = Array.from(container.querySelectorAll('button')).filter(
      (b) => b.textContent?.includes('Salvar Avaliação')
    );
    expect(saveButtons.length).toBe(2);
  });

  it('shows empty state when no sections', () => {
    const props = {
      ...baseProps,
      generatedContent: {},
      sections: {},
    };
    const { container } = render(<EvaluationPhase {...props} />);
    expect(container.textContent).toContain('Nenhuma seção gerada para avaliar');
  });

  it('calls onAdvance when advance button is clicked (all evaluated)', () => {
    const onAdvance = jest.fn().mockResolvedValue(undefined);
    const props = {
      ...baseProps,
      evaluatedSections: { 1: 'approved', 2: 'approved' },
      onAdvance,
    };
    const { container } = render(<EvaluationPhase {...props} />);
    const advanceBtn = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Avançar')
    )!;
    fireEvent.click(advanceBtn);
    expect(onAdvance).toHaveBeenCalledTimes(1);
  });

  it('shows loading spinner when updatingDocument', () => {
    const props = {
      ...baseProps,
      evaluatedSections: { 1: 'approved', 2: 'approved' },
      updatingDocument: true,
    };
    const { container } = render(<EvaluationPhase {...props} />);
    const spinner = container.querySelector('svg.lucide-loader-2');
    expect(spinner).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <EvaluationPhase {...baseProps} className="custom-phase" />
    );
    const outerDiv = container.firstElementChild as HTMLElement;
    expect(outerDiv).toHaveClass('custom-phase');
  });
});

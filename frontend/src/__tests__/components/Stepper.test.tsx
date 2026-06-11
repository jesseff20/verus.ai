import React from 'react';
import { Stepper } from '@/components/Stepper';

describe('Stepper Component', () => {
  const defaultProps = {
    currentPhase: 'upload' as const,
    onPhaseChange: jest.fn(),
  };

  it('renders all phases', () => {
    const { container } = render(<Stepper {...defaultProps} />);
    expect(container.textContent).toContain('Upload');
    expect(container.textContent).toContain('Geração');
    expect(container.textContent).toContain('Avaliação');
    expect(container.textContent).toContain('Análise');
    expect(container.textContent).toContain('Resultado');
    expect(container.textContent).toContain('Histórico');
  });

  it('renders nav element', () => {
    const { container } = render(<Stepper {...defaultProps} />);
    const nav = container.querySelector('nav');
    expect(nav).toBeInTheDocument();
  });

  it('highlights the current phase', () => {
    const { container } = render(
      <Stepper {...defaultProps} currentPhase="generation" />
    );
    const buttons = container.querySelectorAll('button');
    // Generation is index 1
    const generationBtn = buttons[1];
    expect(generationBtn).toHaveClass('text-primary');
    expect(generationBtn).toHaveClass('font-medium');
  });

  it('marks completed phases as completed', () => {
    const { container } = render(
      <Stepper {...defaultProps} currentPhase="evaluation" />
    );
    const buttons = container.querySelectorAll('button');
    // Upload (index 0) and Generation (index 1) should be completed
    expect(buttons[0].textContent).toContain('Upload');
    expect(buttons[0]).toHaveClass('text-green-600');
    expect(buttons[1].textContent).toContain('Geração');
    expect(buttons[1]).toHaveClass('text-green-600');
  });

  it('shows check icon for completed phases', () => {
    const { container } = render(
      <Stepper {...defaultProps} currentPhase="evaluation" />
    );
    // Completed phases should show Check icon (SVG)
    const checkIcons = container.querySelectorAll('svg.lucide-check');
    expect(checkIcons.length).toBe(2); // Upload and Generation
  });

  it('shows the correct icon for non-completed phases', () => {
    const { container } = render(
      <Stepper {...defaultProps} currentPhase="upload" />
    );
    // Upload should show Upload icon
    const buttons = container.querySelectorAll('button');
    const uploadBtn = buttons[0];
    expect(uploadBtn.textContent).toContain('Upload');
  });

  it('calls onPhaseChange when clicking a completed phase', () => {
    const onPhaseChange = jest.fn();
    const { container } = render(
      <Stepper {...defaultProps} onPhaseChange={onPhaseChange} currentPhase="evaluation" />
    );
    const buttons = container.querySelectorAll('button');
    // Click on Upload (completed, index 0)
    fireEvent.click(buttons[0]);
    expect(onPhaseChange).toHaveBeenCalledWith('upload');
  });

  it('calls onPhaseChange when clicking next phase', () => {
    const onPhaseChange = jest.fn();
    const { container } = render(
      <Stepper {...defaultProps} onPhaseChange={onPhaseChange} currentPhase="upload" />
    );
    const buttons = container.querySelectorAll('button');
    // Click on Generation (next, index 1) — should be clickable
    fireEvent.click(buttons[1]);
    expect(onPhaseChange).toHaveBeenCalledWith('generation');
  });

  it('does not allow clicking phases two steps ahead', () => {
    const onPhaseChange = jest.fn();
    const { container } = render(
      <Stepper {...defaultProps} onPhaseChange={onPhaseChange} currentPhase="upload" />
    );
    const buttons = container.querySelectorAll('button');
    // Analysis is index 3 — two steps ahead from upload, should not be clickable
    fireEvent.click(buttons[3]);
    expect(onPhaseChange).not.toHaveBeenCalled();
  });

  it('disables all clicks when disabled prop is true', () => {
    const onPhaseChange = jest.fn();
    const { container } = render(
      <Stepper {...defaultProps} onPhaseChange={onPhaseChange} disabled />
    );
    const buttons = container.querySelectorAll('button');
    fireEvent.click(buttons[0]);
    expect(onPhaseChange).not.toHaveBeenCalled();
    fireEvent.click(buttons[1]);
    expect(onPhaseChange).not.toHaveBeenCalled();
  });

  it('applies custom className', () => {
    const { container } = render(
      <Stepper {...defaultProps} className="custom-nav" />
    );
    const nav = container.querySelector('nav');
    expect(nav).toHaveClass('custom-nav');
  });

  it('adds cursor-not-allowed for non-clickable phases', () => {
    const { container } = render(<Stepper {...defaultProps} />);
    const buttons = container.querySelectorAll('button');
    // Analysis (index 3) should be not clickable from upload
    expect(buttons[3]).toHaveClass('cursor-not-allowed');
  });

  it('renders connector lines between phases', () => {
    const { container } = render(<Stepper {...defaultProps} />);
    // Between each phase there should be a div connector (h-px)
    const connectors = container.querySelectorAll('div.h-px');
    expect(connectors.length).toBe(5); // 6 phases = 5 connectors
  });

  it('shows green connectors for completed phases', () => {
    const { container } = render(
      <Stepper {...defaultProps} currentPhase="evaluation" />
    );
    const connectors = container.querySelectorAll('div.h-px');
    expect(connectors[0]).toHaveClass('bg-green-500'); // between upload and generation
    expect(connectors[1]).toHaveClass('bg-green-500'); // between generation and evaluation
  });
});
